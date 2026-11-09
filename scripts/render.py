#!/usr/bin/env python3
"""Render JungleJuggle card slides from a content spec (JSON) to PNG files.

Usage: python scripts/render.py content/<id>.json media/<id>
Runs where Chromium + Playwright + Noto Sans CJK KR are available (Claude's sandbox).

Slide types: list_cover, item, end, ledger, photo_cover (photo = repo path or https URL).
Brand v2: ink #111111, violet #6C3BFF, white, paper #F4F2FA, breaking red #FF3B30.
"""
import base64
import html
import json
import sys
from pathlib import Path

from playwright.sync_api import sync_playwright

INK, VIOLET, WHITE, PAPER, MUTED = "#111111", "#6C3BFF", "#FFFFFF", "#F4F2FA", "#8C8796"
W, H = 1080, 1350

CSS = f"""<style>
*{{margin:0;padding:0;box-sizing:border-box}}
body{{font-family:'Noto Sans CJK KR','Noto Sans KR',sans-serif;-webkit-font-smoothing:antialiased;word-break:keep-all}}
.kw{{background:{VIOLET};color:#fff;padding:0 12px;border-radius:8px;box-decoration-break:clone;-webkit-box-decoration-break:clone}}
.tag{{display:inline-block;background:{VIOLET};color:#fff;font-weight:900;font-size:30px;padding:8px 18px;border-radius:8px}}
.wm{{font-weight:900;letter-spacing:-1px}}
.page{{width:{W}px;height:{H}px;position:relative;overflow:hidden}}
</style>"""


def esc(s):
    return html.escape(str(s))


def with_kw(text, kw):
    """Escape text and wrap the first occurrence of kw in the violet box."""
    t = esc(text)
    if kw and esc(kw) in t:
        t = t.replace(esc(kw), f'<span class="kw">{esc(kw)}</span>', 1)
    return t.replace("\n", "<br>")


def list_cover(s):
    rows = "".join(
        f'<div style="display:flex;gap:22px"><span style="color:{VIOLET};min-width:62px">{i:02d}</span><span>{esc(x)}</span></div>'
        for i, x in enumerate(s["items"], 1))
    return f"""<div class="page" style="background:{INK};color:#fff;padding:104px 80px;display:flex;flex-direction:column">
<div><span class="tag">{esc(s['tag'])}</span><span style="font-size:30px;color:{MUTED};margin-left:16px">{esc(s.get('date',''))}</span></div>
<div style="margin-top:44px;font-size:84px;font-weight:900;line-height:1.34;letter-spacing:-2px">{with_kw(s['title'], s.get('kw'))}</div>
<div style="margin-top:64px;display:flex;flex-direction:column;gap:36px;font-size:46px;font-weight:800;line-height:1.3">{rows}</div>
<div style="margin-top:auto;display:flex;justify-content:space-between;font-size:30px"><span class="wm">정글저글</span><span style="color:{MUTED}">넘겨서 하나씩 →</span></div></div>"""


def photo_uri(photo, root):
    if isinstance(photo, str) and photo and not photo.startswith("http") and root is not None:
        # Embed local photos as data URIs: a page loaded with set_content cannot read file:// URLs.
        local = (root / photo).resolve()
        mime = {".png": "image/png", ".webp": "image/webp"}.get(local.suffix.lower(), "image/jpeg")
        return f"data:{mime};base64,{base64.b64encode(local.read_bytes()).decode()}"
    return photo if isinstance(photo, str) and photo else None


def item(s, root=None):
    # Optional "photo" (repo path or dict resolved in Actions): a rounded photo band between the title and the
    # bullets, like a news card. With a photo, keep bullets to 2-3 short lines so nothing overflows.
    bullets = "".join(f'<div>· {esc(b)}</div>' for b in s["bullets"])
    so = f'<div style="color:#fff;font-weight:800">⇒ {esc(s["so"])}</div>' if s.get("so") else ""
    uri = photo_uri(s.get("photo"), root)
    band = ""
    if uri:
        cr = (f'<div style="position:absolute;right:16px;bottom:12px;font-size:22px;color:rgba(255,255,255,.85);text-shadow:0 1px 3px #000">📷 {esc(s["credit"])}</div>'
              if s.get("credit") and s.get("credit_on_image") else "")  # credits go in the caption (user request 2026-11-09)
        band = (f'<div style="margin-top:44px;height:{s.get("photo_h", 500)}px;border-radius:24px;position:relative;'
                f'background:url(\'{uri}\') {s.get("photo_pos", "center")}/cover">{cr}</div>')
    gap_top, fs, gap = (44, 40, 26) if uri else (64, 44, 40)
    return f"""<div class="page" style="background:{INK};color:#fff;padding:{'88' if uri else '104'}px 80px;display:flex;flex-direction:column">
<div style="font-size:30px;color:{MUTED};font-weight:700">{esc(s['n'])}</div>
<div style="margin-top:{'28' if uri else '40'}px;font-size:{'68' if uri else '74'}px;font-weight:900;line-height:1.3;letter-spacing:-1.5px">{with_kw(s['title'], s.get('kw'))}</div>{band}
<div style="margin-top:{gap_top}px;display:flex;flex-direction:column;gap:{gap}px;font-size:{fs}px;line-height:1.45;color:#E7E4EE">{bullets}{so}</div>
<div style="margin-top:auto;display:flex;justify-content:space-between;align-items:flex-end;font-size:26px;color:{MUTED}">
<span class="wm" style="font-size:30px;color:#fff">정글저글</span><span>{esc(s.get('src',''))}</span></div></div>"""


def end(s):
    ctas = "".join(f'<div>{esc(c)}</div>' for c in s.get("ctas", []))
    return f"""<div class="page" style="background:{VIOLET};color:#fff;padding:104px 80px;display:flex;flex-direction:column">
<div style="font-size:30px;font-weight:700;opacity:.8">{esc(s.get('n',''))}</div>
<div style="margin-top:40px;font-size:30px;font-weight:800;opacity:.9">한 줄 요약</div>
<div style="margin-top:20px;font-size:68px;font-weight:900;line-height:1.28;letter-spacing:-2px">{esc(s['summary']).replace(chr(10), '<br>')}</div>
<div style="margin-top:64px;display:flex;flex-direction:column;gap:26px;font-size:40px;font-weight:800">{ctas}</div>
<div style="margin-top:auto;font-size:26px;line-height:1.6;opacity:.85">{esc(s.get('sources','')).replace(chr(10), '<br>')}</div>
<div class="wm" style="margin-top:28px;font-size:36px;color:{INK}">정글저글</div></div>"""


def ledger(s):
    # Waterfall bars from revenue down to net income. s["bars"] = [[label, value], ...], first = total.
    bars = s["bars"]
    top = float(bars[0][1])
    area_h, bw, gap, x0 = 600, 150, 40, 10
    parts, level = [], top
    for i, (label, value) in enumerate(bars):
        v = float(value)
        if i == 0:
            bottom, height, color = 0, area_h, VIOLET
        elif i == len(bars) - 1:
            bottom, height, color = 0, area_h * v / top, INK
        else:
            level_after = level - abs(v)
            bottom, height, color = area_h * level_after / top, area_h * abs(v) / top, "#C9C2DD"
            level = level_after
        x = x0 + i * (bw + gap)
        parts.append(
            f'<div style="position:absolute;left:{x}px;bottom:{bottom}px;width:{bw}px;height:{max(height, 4)}px;background:{color};border-radius:10px 10px 0 0"></div>'
            f'<div style="position:absolute;left:{x}px;bottom:{bottom + height + 10}px;width:{bw}px;text-align:center;font-size:30px;font-weight:900">{esc(s["fmt"][i])}</div>'
            f'<div style="position:absolute;left:{x - 10}px;bottom:-58px;width:{bw + 20}px;text-align:center;font-size:28px;font-weight:700">{esc(label)}</div>')
    return f"""<div class="page" style="background:{PAPER};color:{INK};padding:96px 72px;display:flex;flex-direction:column">
<span class="tag" style="align-self:flex-start">기업 가계부</span>
<div style="margin-top:28px;font-size:66px;font-weight:900;letter-spacing:-2px;line-height:1.22">{with_kw(s['title'], s.get('kw'))}</div>
<div style="font-size:26px;color:{MUTED};margin-top:14px">{esc(s.get('basis',''))}</div>
<div style="margin-top:70px;position:relative;height:{area_h}px;border-bottom:3px solid {INK}">{''.join(parts)}</div>
<div style="margin-top:auto;display:flex;justify-content:space-between;font-size:26px;color:{MUTED}"><span class="wm" style="font-size:30px;color:{INK}">정글저글</span><span>{esc(s.get('src',''))}</span></div></div>"""


def photo_cover(s, root):
    photo = s.get("photo")
    if isinstance(photo, str) and photo and not photo.startswith("http"):
        # Embed local photos as data URIs: a page loaded with set_content cannot read file:// URLs.
        local = (root / photo).resolve()
        mime = {".png": "image/png", ".webp": "image/webp"}.get(local.suffix.lower(), "image/jpeg")
        photo = f"data:{mime};base64,{base64.b64encode(local.read_bytes()).decode()}"
    if isinstance(photo, str) and photo:
        backdrop = f"background:url('{photo}') center/cover"
    else:  # no photo could be found: graphic fallback so the post is never blocked
        backdrop = (f"background:radial-gradient(circle at 78% 22%,{VIOLET} 0,rgba(108,59,255,.55) 22%,rgba(17,17,17,0) 55%),"
                    f"radial-gradient(circle at 15% 70%,rgba(108,59,255,.35) 0,rgba(17,17,17,0) 40%),{INK}")
        s = dict(s, credit=s.get("credit") if isinstance(s.get("photo"), str) and s.get("photo") else "")
    bubble = (f'<div style="position:absolute;top:{s.get("bubble_top", 420)}px;left:{s.get("bubble_left", 560)}px;background:#fff;color:{INK};'
              f'font-weight:800;border-radius:999px;padding:22px 34px;font-size:38px;box-shadow:0 4px 0 {INK}">{esc(s["bubble"])}</div>') if s.get("bubble") else ""
    credit = f"📷 {esc(s['credit'])}" if s.get("credit") and s.get("credit_on_image") else ""  # caption carries credits
    # breaking-news label, e.g. "tag": "속보 · 14:05" (red pill, top-left)
    tag = (f'<div style="position:absolute;top:72px;left:72px;background:#FF3B30;color:#fff;font-weight:900;font-size:34px;'
           f'padding:10px 22px;border-radius:10px">{esc(s["tag"])}</div>') if s.get("tag") else ""
    return f"""<div class="page" style="color:#fff">
<div style="position:absolute;inset:0;{backdrop}"></div>
<div style="position:absolute;inset:0;background:linear-gradient(180deg,rgba(0,0,0,0) 38%,rgba(0,0,0,.82) 78%,rgba(0,0,0,.92) 100%)"></div>{bubble}{tag}
<div style="position:absolute;left:72px;right:72px;bottom:150px;font-size:80px;font-weight:900;line-height:1.28;letter-spacing:-2px">{with_kw(s['title'], s.get('kw'))}</div>
<div style="position:absolute;left:72px;right:72px;bottom:64px;display:flex;justify-content:space-between;font-size:28px;color:rgba(255,255,255,.8)">
<span class="wm" style="color:#fff">정글저글</span><span>{credit}</span></div></div>"""


RENDERERS = {"list_cover": list_cover, "item": item, "end": end, "ledger": ledger}


def main(spec_path, out_dir):
    spec = json.loads(Path(spec_path).read_text(encoding="utf-8"))
    out = Path(out_dir)
    out.mkdir(parents=True, exist_ok=True)
    root = Path(__file__).resolve().parent.parent
    files = []
    with sync_playwright() as p:
        browser = p.chromium.launch()
        page = browser.new_page(viewport={"width": W, "height": H})
        for i, s in enumerate(spec["slides"], 1):
            body = photo_cover(s, root) if s["t"] == "photo_cover" else (item(s, root) if s["t"] == "item" else RENDERERS[s["t"]](s))
            page.set_content(f"<html><head>{CSS}</head><body>{body}</body></html>", wait_until="networkidle")
            path = out / f"{i:02d}.jpg"
            page.screenshot(path=str(path), type="jpeg", quality=92)
            files.append(str(path))
        browser.close()
    if files:  # story-safe 9:16 version of the cover (a 4:5 image gets cropped in stories)
        sys.path.insert(0, str(Path(__file__).resolve().parent))
        from make_story import make_story
        files.append(str(make_story(files[0], out / "story.jpg")))
    print("\n".join(files))


if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2])
