#!/usr/bin/env python3
"""Render specs that need the internet (photos, library music) inside GitHub Actions.

A content spec opts in with "render_in_actions": true.
  - Card specs (content/<id>.json): every slide "photo" that is an https URL is downloaded to
    media/<id>/src/, then scripts/render.py writes media/<id>/01.jpg ...
  - Reel specs (content/<id>.reel.json): a "music": {"url": ..., "license": ..., "title": ...} track is
    downloaded to music/library/ and recorded in music/LICENSES.md. A grade-B clip scene may give
    "clip": {"url", "license", "license_page"}: the official video is downloaded to clips/ and logged in
    media/<id>/src/clip_credits.json (A·C clips must already be in clips/inbox/). Then scripts/make_reel.py writes
    media/<id>/reel.mp4.
A spec is re-rendered only when its content changes (hash stored in media/<id>/.rendered).
Claude pulls the result, looks at the images, has them reviewed, and only then adds a queue item.
"""
import hashlib
import json
import re
import subprocess
import sys
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
UA = "Mozilla/5.0 (compatible; junglejuggle-render/1.0; +https://github.com/monkeywarr12345-star/junglejuggle-ops)"
PHOTO_TYPES = {"image/jpeg": ".jpg", "image/png": ".png", "image/webp": ".webp"}


VIDEO_TYPES = {"video/mp4": ".mp4", "video/quicktime": ".mov", "video/webm": ".webm"}


def download(url, dest_dir, allowed, max_mb=25):
    req = urllib.request.Request(url, headers={"User-Agent": UA})
    with urllib.request.urlopen(req, timeout=120) as resp:
        ctype = resp.headers.get_content_type()
        if ctype not in allowed:
            raise ValueError(f"{url}: unexpected content type {ctype}")
        data = resp.read()
    if len(data) > max_mb * 1024 * 1024:
        raise ValueError(f"{url}: file larger than {max_mb} MB")
    name = hashlib.sha1(url.encode()).hexdigest()[:12] + allowed[ctype]
    dest_dir.mkdir(parents=True, exist_ok=True)
    path = dest_dir / name
    path.write_bytes(data)
    return path


def spec_hash(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def clean_author(name):
    """Wikimedia author fields can carry file names, line breaks and 'derivative work' notes; keep one short name."""
    name = re.sub(r"\s+", " ", name or "").strip()
    src = ""
    m = re.search(r"\s*/\s*(Wikimedia Commons|Unsplash|Pexels|Pixabay|Openverse)$", name)
    if m:
        src, name = m.group(0), name[: m.start()]
    name = re.sub(r"^.*?\.(jpe?g|png|tiff?|webp)\s*:\s*", "", name, flags=re.I)  # "File.jpg: Author"
    name = re.split(r"\s*(derivative wor|derivative:|\(talk\)|,? ?cropped)", name, flags=re.I)[0].strip(" ,;:-")
    if len(name) > 40:
        name = name[:40].rsplit(" ", 1)[0]
    return (name or "Unknown") + src


def write_photo_credit(out, credits, spec_items):
    """media/<id>/photo_credit.txt: one caption line with every photo's author / source (license).
    Photo credits are not drawn on the cards any more; publish.py appends this line if the caption lacks one."""
    parts, seen = [], set()
    for c in credits:
        idx = c.get("slide") or c.get("scene")
        name = c.get("credit") or (spec_items[idx - 1].get("credit") if idx and idx <= len(spec_items) else "") or ""
        if not name:
            page = c.get("page") or ""
            name = page.split("/")[2] if page.count("/") >= 2 else "공식 제공"
        name = clean_author(name)
        lic = c.get("license") or ""
        label = f"{name} ({lic})" if lic and lic not in name and "공식" not in lic else name
        if label not in seen:
            seen.add(label)
            parts.append(label)
    f = out / "photo_credit.txt"
    if parts:
        f.write_text("📷 사진: " + ", ".join(parts) + "\n", encoding="utf-8")
    else:
        f.unlink(missing_ok=True)


def render_cards(spec_path, spec):
    sys.path.insert(0, str(ROOT / "scripts"))
    import photo_sources

    out = ROOT / "media" / spec["id"]
    resolved = json.loads(json.dumps(spec))
    credits, notes = [], []
    for i, slide in enumerate(resolved["slides"], 1):
        photo = slide.get("photo")
        if not photo or (isinstance(photo, str) and not photo.startswith("http")):
            continue
        try:
            local, credit = photo_sources.resolve(photo, out / "src", used={c["page"] for c in credits})
            slide["photo"] = str(local.relative_to(ROOT))
            if credit.get("credit") and (credit["source"] != "direct" or not slide.get("credit")):
                slide["credit"] = credit["credit"]
            credits.append({"slide": i, **credit, "file": slide["photo"]})
        except Exception as exc:  # never block a post on a photo: render the graphic fallback instead
            slide["photo"] = None
            notes.append(f"slide {i}: photo fallback to graphic ({exc})")
    (out / "src").mkdir(parents=True, exist_ok=True)
    (out / "src" / "credits.json").write_text(json.dumps(credits, ensure_ascii=False, indent=1), encoding="utf-8")
    write_photo_credit(out, credits, spec["slides"])
    fallback_note = out / "src" / "photo_fallback.txt"
    if notes:
        fallback_note.write_text("\n".join(notes) + "\n", encoding="utf-8")
    else:
        fallback_note.unlink(missing_ok=True)
    tmp_spec = out / "src" / "spec.resolved.json"
    tmp_spec.parent.mkdir(parents=True, exist_ok=True)
    tmp_spec.write_text(json.dumps(resolved, ensure_ascii=False, indent=1), encoding="utf-8")
    subprocess.run([sys.executable, str(ROOT / "scripts" / "render.py"), str(tmp_spec), str(out)], check=True)
    # 2026-11-09 user decision: feed posts go up as plain images (no music); the user adds Instagram app music by hand.
    if spec.get("feed_video", False) and len(spec["slides"]) >= 2:
        subprocess.run([sys.executable, str(ROOT / "scripts" / "make_feed_video.py"), str(tmp_spec), str(out)], check=True)
    return out


def render_reel(spec_path, spec):
    out = ROOT / "media" / spec["id"]
    sys.path.insert(0, str(ROOT / "scripts"))
    import photo_sources
    spec = json.loads(json.dumps(spec))
    credits, notes = [], []
    for i, sc in enumerate(spec.get("scenes", []), 1):  # real photos for the hook scene (and any other scene)
        photo = sc.get("photo")
        if not photo or (isinstance(photo, str) and not photo.startswith("http")):
            continue
        try:
            local, credit = photo_sources.resolve(photo, out / "src", used={c["page"] for c in credits})
            sc["photo"] = str(local.relative_to(ROOT))
            if credit.get("credit") and (credit["source"] != "direct" or not sc.get("credit")):
                sc["credit"] = credit["credit"]
            credits.append({"scene": i, **credit, "file": sc["photo"]})
        except Exception as exc:
            sc["photo"] = None
            notes.append(f"scene {i}: photo fallback to graphic ({exc})")
    clip_log = []
    for i, sc in enumerate(spec.get("scenes", []), 1):  # 클립 트랙 B등급: official/licensed video by direct URL
        clip = sc.get("clip")
        if sc.get("t") != "clip" or not isinstance(clip, dict):
            continue
        if sc.get("grade") != "B" or not clip.get("url") or not clip.get("license") or not clip.get("license_page"):
            raise ValueError(f"scene {i}: a clip URL is only for grade B and needs url, license and license_page "
                             "(A·C 등급 파일은 clips/inbox/에 올린 것만 쓴다)")
        local = download(clip["url"], ROOT / "clips", VIDEO_TYPES, max_mb=150)
        sc["clip"] = str(local.relative_to(ROOT))
        clip_log.append({"scene": i, "file": sc["clip"], "url": clip["url"], "license": clip["license"],
                         "license_page": clip["license_page"], "credit": sc.get("credit", "")})
    (out / "src").mkdir(parents=True, exist_ok=True)
    if clip_log:
        (out / "src" / "clip_credits.json").write_text(json.dumps(clip_log, ensure_ascii=False, indent=1), encoding="utf-8")
    (out / "src" / "reel_credits.json").write_text(json.dumps(credits, ensure_ascii=False, indent=1), encoding="utf-8")
    write_photo_credit(out, credits, spec.get("scenes", []))
    fb = out / "src" / "reel_photo_fallback.txt"
    fb.write_text("\n".join(notes) + "\n", encoding="utf-8") if notes else fb.unlink(missing_ok=True)
    music = spec.get("music", {})
    if music.get("url"):
        if not music.get("license"):
            raise ValueError(f"{spec_path}: music.url needs a license note")
        lib = ROOT / "music" / "library"
        track = download(music["url"], lib, {"audio/mpeg": ".mp3", "audio/mp3": ".mp3", "audio/wav": ".wav", "audio/x-wav": ".wav"})
        lic = ROOT / "music" / "LICENSES.md"
        line = f"| {track.name} | {music.get('title', '')} | {music['license']} | {music['url']} |\n"
        if not lic.exists():
            lic.write_text("# 릴스 음원 라이선스 기록\n\n| 파일 | 곡 | 라이선스 | 원본 |\n| --- | --- | --- | --- |\n", encoding="utf-8")
        if track.name not in lic.read_text(encoding="utf-8"):
            with lic.open("a", encoding="utf-8") as f:
                f.write(line)
        spec = dict(spec, music={"file": str(track.relative_to(ROOT))})
    tmp_spec = out / "src" / "reel.resolved.json"
    tmp_spec.parent.mkdir(parents=True, exist_ok=True)
    tmp_spec.write_text(json.dumps(spec, ensure_ascii=False, indent=1), encoding="utf-8")
    subprocess.run([sys.executable, str(ROOT / "scripts" / "make_reel.py"), str(tmp_spec), str(out / "reel.mp4")], check=True)
    return out


def main():
    failures = 0
    for spec_path in sorted((ROOT / "content").glob("*.json")):
        try:
            spec = json.loads(spec_path.read_text(encoding="utf-8"))
        except json.JSONDecodeError as exc:
            print(f"skip {spec_path.name}: {exc}")
            continue
        if not spec.get("render_in_actions"):
            continue
        spec.setdefault("id", spec_path.name.split(".")[0])
        marker = ROOT / "media" / spec["id"] / (".rendered-reel" if spec_path.name.endswith(".reel.json") else ".rendered")
        digest = spec_hash(spec_path)
        if marker.exists() and marker.read_text().strip() == digest:
            continue
        try:
            out = render_reel(spec_path, spec) if spec_path.name.endswith(".reel.json") else render_cards(spec_path, spec)
            marker.write_text(digest)
            (out / "src" / "error.txt").unlink(missing_ok=True)
            print(f"rendered {spec_path.name} -> {out.relative_to(ROOT)}")
        except Exception as exc:  # record the error next to the media so Claude can see it after pulling
            failures += 1
            err_dir = ROOT / "media" / spec["id"] / "src"
            err_dir.mkdir(parents=True, exist_ok=True)
            (err_dir / "error.txt").write_text(f"{spec_path.name}: {exc}\n", encoding="utf-8")
            print(f"FAILED {spec_path.name}: {exc}")
    return failures


if __name__ == "__main__":
    sys.exit(1 if main() else 0)
