#!/usr/bin/env python3
"""Publish due items from queue/ to Instagram.

Uses the Instagram API with Instagram Login (IG_LOGIN_TOKEN, no Facebook needed) when set,
and the older Facebook Login setup (IG_ACCESS_TOKEN + IG_USER_ID) as a fallback when the
first one rejects the login (see scripts/ig_api.py).

Each queue item is a JSON file in queue/. When its publish_at time has passed,
it is published and moved to posted/ with the result recorded.

Queue item fields:
  type        "feed" | "story" | "reel" | "carousel"   (default "feed")
  image       repo path (e.g. "media/2026-11-09.jpg") or full https URL
  video       repo path or https URL (story video / reel)
  cover       reel only, optional: cover image (repo path or URL); thumb_offset (ms) picks a video frame instead
  items       for carousel: list of {"image": ...} or {"video": ...} (2-10)
  caption     text (ignored for stories)
  publish_at  ISO 8601 time, e.g. "2026-11-09T09:00:00+09:00" (omit = now)

Only the Python standard library is used.
"""
import json
import os
import shutil
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
from datetime import datetime, timedelta, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
QUEUE = ROOT / "queue"
POSTED = ROOT / "posted"
FAILED = ROOT / "failed"
SKIPPED = ROOT / "skipped"
# Stories paused until 1,000 followers (2026-11-10 user decision): with 0 followers they reach no one
# but double the number of API posts per day, which keeps tripping Instagram's "API access blocked".
# Story items found in queue/ are moved to skipped/ unpublished. Set to False to turn stories back on.
STORIES_PAUSED = True

sys.path.insert(0, str(Path(__file__).resolve().parent))
import ig_api  # noqa: E402

REPO = os.environ.get("GITHUB_REPOSITORY", "")
BRANCH = os.environ.get("GITHUB_REF_NAME", "main")
DRY_RUN = os.environ.get("DRY_RUN", "") == "1"
BLOCK_SIGNS = ("API access blocked", "2207051", "2207050")
BLOCK_BACKOFF_MIN = 90


def media_url(value):
    """Turn a repo-relative path into a public raw.githubusercontent.com URL."""
    if not value:
        return None
    if value.startswith("http://") or value.startswith("https://"):
        return value
    if not REPO:
        raise ValueError(f"Cannot build URL for {value!r}: GITHUB_REPOSITORY is unset")
    if not (ROOT / value).exists():
        raise FileNotFoundError(f"{value} is not in the repository")
    return f"https://raw.githubusercontent.com/{REPO}/{BRANCH}/{urllib.parse.quote(value)}"


def wait_ready(api, container_id, timeout=600):
    """Poll a media container until Instagram has finished processing it."""
    deadline = time.time() + timeout
    while time.time() < deadline:
        status = api.call("GET", container_id, {"fields": "status_code,status"})
        code = status.get("status_code")
        if code == "FINISHED":
            return
        if code in ("ERROR", "EXPIRED"):
            raise RuntimeError(f"Container {container_id} {code}: {status.get('status')}")
        time.sleep(10)
    raise TimeoutError(f"Container {container_id} not ready after {timeout}s")


def media_params(entry):
    if entry.get("video"):
        return {"video_url": media_url(entry["video"])}, True
    if entry.get("image"):
        return {"image_url": media_url(entry["image"])}, False
    raise ValueError("Item needs an 'image' or 'video'")


def with_photo_credit(item, caption):
    """Photo credits are no longer drawn on the cards/reels; they belong in the caption.
    If the caption has no '📷' line, append media/<id>/photo_credit.txt (written by remote_render.py)."""
    paths = [item.get("image"), item.get("video")] + [c.get("image") or c.get("video") for c in item.get("items", [])]
    dirs = [ROOT / Path(p).parent for p in paths if p and p.startswith("media/")]
    for mark, name in (("📷", "photo_credit.txt"), ("🎵", "music_credit.txt")):  # CC BY needs both credits
        if mark in caption:
            continue
        has_video = bool(item.get("video") or any(c.get("video") for c in item.get("items", [])))
        if mark == "🎵" and not has_video:  # image-only feed posts carry no music (2026-11-09), so no music credit
            continue
        for d in dirs:
            f = d / name
            if f.exists():
                line = f.read_text(encoding="utf-8").strip()
                caption = f"{caption}\n{line}" if caption else line
                break
    return caption


def create_container(api, item):
    kind = item.get("type", "feed")
    caption = with_photo_credit(item, item.get("caption", "")) if item.get("type", "feed") != "story" else ""

    if kind == "carousel":
        children = []
        for child in item.get("items", []):
            params, is_video = media_params(child)
            params["is_carousel_item"] = "true"
            if is_video:
                params["media_type"] = "VIDEO"
            cid = api.call("POST", f"{api.user}/media", params)["id"]
            wait_ready(api, cid)
            children.append(cid)
        if not 2 <= len(children) <= 10:
            raise ValueError("Carousel needs 2-10 items")
        params = {"media_type": "CAROUSEL", "children": ",".join(children), "caption": caption}
    elif kind == "story":
        img = item.get("image")
        if img and img.startswith("media/") and not img.endswith("story.jpg"):
            # 4:5 cards get cropped on all sides in stories: use the 9:16 story.jpg rendered next to them
            safe = Path(img).parent / "story.jpg"
            if (ROOT / safe).exists():
                item = dict(item, image=str(safe))
            else:
                print(f"  warning: {img} is not story-shaped and no story.jpg exists (it will be cropped)", file=sys.stderr)
        params, _ = media_params(item)
        params["media_type"] = "STORIES"
    elif kind == "reel":
        if not item.get("video"):
            raise ValueError("Reel needs a 'video'")
        params = {"media_type": "REELS", "video_url": media_url(item["video"]), "caption": caption}
        if item.get("cover"):  # optional cover image (repo path or URL) shown in the grid/feed before playback
            params["cover_url"] = media_url(item["cover"])
        elif item.get("thumb_offset") is not None:  # or a frame of the video, in milliseconds
            params["thumb_offset"] = str(int(item["thumb_offset"]))
    elif kind == "feed":
        params, is_video = media_params(item)
        if is_video:
            params["media_type"] = "REELS"
        params["caption"] = caption
    else:
        raise ValueError(f"Unknown type {kind!r}")

    return api.call("POST", f"{api.user}/media", params)["id"]


def publish_item(item):
    """Try each configured login in turn. Only a rejected login moves on to the next one:
    Instagram turns that request away, so nothing was posted and retrying elsewhere cannot double-post."""
    apis = ig_api.backends()
    if item.get("type") == "reel" or (item.get("type", "feed") == "feed" and item.get("video")):
        # Reels: Instagram Login token first when set, then the Facebook Login token (it posted every reel
        # on 11-09), and the system token last: since the 11-09 23:11 switch to it, every reel failed at
        # media_publish with "Fatal [OAuthException (-1)]" while carousels went through (2026-11-10).
        order = {"instagram": 0, "facebook": 1, "system": 2}
        apis = sorted(apis, key=lambda b: order.get(b.name, 9))
    for i, api in enumerate(apis):
        stage = "container"
        try:
            container = create_container(api, item)
            wait_ready(api, container)
            stage = "publish"
            return api.call("POST", f"{api.user}/media_publish", {"creation_id": container})["id"], api.name
        except Exception as exc:
            # A media_publish error can still leave the post live (2026-11-10: "Fatal [OAuthException (-1)]"
            # on both logins for the same reel). Never retry it on another login: that risks a double post.
            if stage == "publish":
                raise RuntimeError(f"{exc} [publish step: check the app, the post may be live]") from None
            if i + 1 < len(apis) and ig_api.is_auth_error(exc) and not any(k in str(exc) for k in BLOCK_SIGNS):
                print(f"  {api.name} login rejected ({exc}); trying {apis[i + 1].name}", file=sys.stderr)
                continue
            raise


def is_due(item, now):
    when = item.get("publish_at")
    if not when:
        return True
    ts = datetime.fromisoformat(when)
    if ts.tzinfo is None:
        raise ValueError("publish_at needs a timezone, e.g. +09:00")
    return ts <= now


def main():
    now = datetime.now(timezone.utc)
    POSTED.mkdir(exist_ok=True)
    FAILED.mkdir(exist_ok=True)
    files = sorted(QUEUE.glob("*.json"))
    published = errors = 0

    for path in files:
        try:
            item = json.loads(path.read_text(encoding="utf-8"))
            if not is_due(item, now):
                continue
            if (POSTED / path.name).exists():  # already published by an earlier run: never post twice
                print(f"  skip {path.name}: already in posted/")
                path.unlink()
                continue
            if STORIES_PAUSED and item.get("type") == "story":
                SKIPPED.mkdir(exist_ok=True)
                item["_skipped"] = {"reason": "stories paused until 1,000 followers", "at": now.isoformat()}
                (SKIPPED / path.name).write_text(json.dumps(item, ensure_ascii=False, indent=2), encoding="utf-8")
                path.unlink()
                print(f"  skip {path.name}: stories paused (moved to skipped/)")
                continue
            print(f"Publishing {path.name} ({item.get('type', 'feed')})")
            if DRY_RUN:
                print("  dry run: skipped")
                continue
            media_id, used = publish_item(item)
            item["_result"] = {"media_id": media_id, "published_at": now.isoformat(), "api": used}
            (POSTED / path.name).write_text(json.dumps(item, ensure_ascii=False, indent=2), encoding="utf-8")
            path.unlink()
            published += 1
            print(f"  published media {media_id}")
        except Exception as exc:  # keep going with the rest of the queue
            if any(k in str(exc) for k in BLOCK_SIGNS):
                # Instagram is temporarily blocking this account/app: retrying now makes it worse.
                # Leave the item in the queue, push it back an hour, and stop this run.
                retry_at = now + timedelta(minutes=BLOCK_BACKOFF_MIN)
                item["publish_at"] = retry_at.isoformat()
                item.setdefault("_deferred", []).append({"reason": str(exc)[:200], "at": now.isoformat()})
                path.write_text(json.dumps(item, ensure_ascii=False, indent=2), encoding="utf-8")
                print(f"  BLOCKED {path.name}: {exc} -> retry after {retry_at.isoformat()}; stopping this run", file=sys.stderr)
                errors += 1
                break
            errors += 1
            print(f"  FAILED {path.name}: {exc}", file=sys.stderr)
            try:
                item = json.loads(path.read_text(encoding="utf-8"))
            except Exception:
                item = {"_raw": path.read_text(encoding="utf-8", errors="replace")}
            item["_error"] = {"message": str(exc), "at": now.isoformat()}
            (FAILED / path.name).write_text(json.dumps(item, ensure_ascii=False, indent=2), encoding="utf-8")
            path.unlink()

    print(f"Done: {published} published, {errors} failed, {len(files) - published - errors} waiting")
    return 1 if errors else 0


if __name__ == "__main__":
    sys.exit(main())
