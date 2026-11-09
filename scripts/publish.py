#!/usr/bin/env python3
"""Publish due items from queue/ to Instagram via the Graph API.

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

API = "https://graph.facebook.com/v27.0"
ROOT = Path(__file__).resolve().parent.parent
QUEUE = ROOT / "queue"
POSTED = ROOT / "posted"
FAILED = ROOT / "failed"

TOKEN = os.environ["IG_ACCESS_TOKEN"]
IG_USER = os.environ["IG_USER_ID"]
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


def call(method, path, params=None):
    params = dict(params or {})
    params["access_token"] = TOKEN
    data = urllib.parse.urlencode(params).encode()
    url = f"{API}/{path}"
    if method == "GET":
        req = urllib.request.Request(f"{url}?{data.decode()}")
    else:
        req = urllib.request.Request(url, data=data, method="POST")
    try:
        with urllib.request.urlopen(req, timeout=60) as resp:
            return json.load(resp)
    except urllib.error.HTTPError as err:
        body = err.read().decode(errors="replace")
        try:
            msg = json.loads(body).get("error", {}).get("message", body)
        except ValueError:
            msg = body
        raise RuntimeError(f"{method} {path} failed ({err.code}): {msg}") from None


def wait_ready(container_id, timeout=600):
    """Poll a media container until Instagram has finished processing it."""
    deadline = time.time() + timeout
    while time.time() < deadline:
        status = call("GET", container_id, {"fields": "status_code,status"})
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
        for d in dirs:
            f = d / name
            if f.exists():
                line = f.read_text(encoding="utf-8").strip()
                caption = f"{caption}\n{line}" if caption else line
                break
    return caption


def create_container(item):
    kind = item.get("type", "feed")
    caption = with_photo_credit(item, item.get("caption", "")) if item.get("type", "feed") != "story" else ""

    if kind == "carousel":
        children = []
        for child in item.get("items", []):
            params, is_video = media_params(child)
            params["is_carousel_item"] = "true"
            if is_video:
                params["media_type"] = "VIDEO"
            cid = call("POST", f"{IG_USER}/media", params)["id"]
            wait_ready(cid)
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

    return call("POST", f"{IG_USER}/media", params)["id"]


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
            print(f"Publishing {path.name} ({item.get('type', 'feed')})")
            if DRY_RUN:
                print("  dry run: skipped")
                continue
            container = create_container(item)
            wait_ready(container)
            media_id = call("POST", f"{IG_USER}/media_publish", {"creation_id": container})["id"]
            item["_result"] = {"media_id": media_id, "published_at": now.isoformat()}
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
