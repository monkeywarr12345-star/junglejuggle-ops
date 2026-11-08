#!/usr/bin/env python3
"""Build a 9:16 reel (MP4) from a reel spec: text scenes rendered as frames, joined with a slow zoom.

Usage: python scripts/make_reel.py content/<id>.reel.json media/<id>/reel.mp4
Spec: {"scenes": [{"top": "headline (2 lines max)", "kw": "word to box", "sub": "subtitle line", "sec": 3.5}, ...],
       "cover": "optional title for the cover frame"}
Audio: silent track (Instagram accepts it); add licensed music later if needed.
Brand v2 colors. Requires Playwright/Chromium, Noto Sans CJK KR and ffmpeg (Claude's sandbox).
"""
import html
import json
import subprocess
import sys
import tempfile
from pathlib import Path

from playwright.sync_api import sync_playwright

INK, VIOLET = "#111111", "#6C3BFF"
W, H, FPS = 1080, 1920, 30


def esc(s):
    return html.escape(str(s))


def frame_html(scene, idx, total):
    top = esc(scene["top"])
    if scene.get("kw") and esc(scene["kw"]) in top:
        top = top.replace(esc(scene["kw"]), f'<span style="background:{VIOLET};padding:0 14px;border-radius:10px">{esc(scene["kw"])}</span>', 1)
    top = top.replace("\n", "<br>")
    sub = esc(scene.get("sub", "")).replace("\n", "<br>")
    big = esc(scene.get("big", ""))
    big_html = f'<div style="font-size:150px;font-weight:900;color:{VIOLET};letter-spacing:-4px;margin-top:40px">{big}</div>' if big else ""
    return f"""<html><head><style>*{{margin:0;padding:0;box-sizing:border-box}}
body{{width:{W}px;height:{H}px;background:{INK};color:#fff;font-family:'Noto Sans CJK KR',sans-serif;word-break:keep-all;overflow:hidden}}</style></head>
<body><div style="position:absolute;top:300px;left:80px;right:80px;text-align:center">
<div style="display:inline-block;background:#fff;color:{VIOLET};font-weight:900;font-size:34px;padding:6px 18px;border-radius:8px">정글저글</div>
<div style="margin-top:36px;font-size:88px;font-weight:900;line-height:1.3;letter-spacing:-2px">{top}</div>{big_html}</div>
<div style="position:absolute;bottom:430px;left:90px;right:90px;text-align:center;font-size:50px;font-weight:800;line-height:1.5">{sub}</div>
<div style="position:absolute;bottom:360px;left:0;right:0;text-align:center;font-size:28px;color:#8C8796">{idx} / {total}</div>
</body></html>"""


def main(spec_path, out_path):
    spec = json.loads(Path(spec_path).read_text(encoding="utf-8"))
    scenes = spec["scenes"]
    out = Path(out_path)
    out.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory() as tmp, sync_playwright() as p:
        browser = p.chromium.launch()
        page = browser.new_page(viewport={"width": W, "height": H})
        clips = []
        for i, sc in enumerate(scenes, 1):
            png = Path(tmp) / f"s{i:02d}.png"
            page.set_content(frame_html(sc, i, len(scenes)))
            page.screenshot(path=str(png))
            sec = float(sc.get("sec", 3.5))
            clip = Path(tmp) / f"c{i:02d}.mp4"
            frames = int(sec * FPS)
            subprocess.run([
                "ffmpeg", "-y", "-loglevel", "error", "-loop", "1", "-i", str(png),
                "-vf", f"scale={W*2}:{H*2},zoompan=z='min(zoom+0.0006,1.06)':d={frames}:s={W}x{H}:fps={FPS},format=yuv420p",
                "-t", str(sec), "-c:v", "libx264", "-preset", "veryfast", "-crf", "20", str(clip)], check=True)
            clips.append(clip)
        browser.close()
        listing = Path(tmp) / "list.txt"
        listing.write_text("".join(f"file '{c}'\n" for c in clips))
        joined = Path(tmp) / "joined.mp4"
        subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-f", "concat", "-safe", "0", "-i", str(listing), "-c", "copy", str(joined)], check=True)
        subprocess.run([
            "ffmpeg", "-y", "-loglevel", "error", "-i", str(joined), "-f", "lavfi", "-i", "anullsrc=r=44100:cl=stereo",
            "-shortest", "-c:v", "copy", "-c:a", "aac", "-b:a", "128k", "-movflags", "+faststart", str(out)], check=True)
    print(out)


if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2])
