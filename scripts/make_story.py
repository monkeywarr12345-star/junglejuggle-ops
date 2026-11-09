#!/usr/bin/env python3
"""Make a story-safe 9:16 image (1080x1920) from a 4:5 feed card so nothing gets cropped.

Usage: python scripts/make_story.py media/<id>/01.jpg media/<id>/story.jpg

Instagram fills the 9:16 story frame by zooming a 4:5 image, which cuts off the top, bottom and sides
(2026-11-09 user report). Here the whole card sits inside the story safe area (top 250px / bottom 340px are
covered by Instagram's UI) on a blurred, darkened copy of itself. Needs only Pillow (no fonts, no browser), so
render.py and publish.py can both call it.
"""
import sys
from pathlib import Path

from PIL import Image, ImageDraw, ImageFilter

W, H = 1080, 1920
CARD_W = 920
SAFE_TOP, SAFE_BOTTOM = 250, 340


def is_story_shaped(path):
    with Image.open(path) as im:
        w, h = im.size
    return abs(h / w - 16 / 9) < 0.03


def make_story(src, dest):
    src, dest = Path(src), Path(dest)
    card = Image.open(src).convert("RGB")
    # background: the same image, filling the frame, blurred and darkened
    scale = max(W / card.width, H / card.height)
    bg = card.resize((round(card.width * scale), round(card.height * scale)), Image.LANCZOS)
    left, top = (bg.width - W) // 2, (bg.height - H) // 2
    bg = bg.crop((left, top, left + W, top + H)).filter(ImageFilter.GaussianBlur(42))
    bg = Image.blend(bg, Image.new("RGB", (W, H), (10, 10, 14)), 0.5)
    # foreground: the whole card, centred inside the safe area, rounded corners + soft shadow
    ch = round(card.height * CARD_W / card.width)
    max_h = H - SAFE_TOP - SAFE_BOTTOM - 40
    cw = CARD_W
    if ch > max_h:
        cw, ch = round(CARD_W * max_h / ch), max_h
    fg = card.resize((cw, ch), Image.LANCZOS)
    x = (W - cw) // 2
    y = SAFE_TOP + (H - SAFE_TOP - SAFE_BOTTOM - ch) // 2
    mask = Image.new("L", (cw, ch), 0)
    ImageDraw.Draw(mask).rounded_rectangle((0, 0, cw - 1, ch - 1), radius=32, fill=255)
    shadow = Image.new("L", (W, H), 0)
    ImageDraw.Draw(shadow).rounded_rectangle((x, y + 18, x + cw, y + ch + 18), radius=36, fill=150)
    shadow = shadow.filter(ImageFilter.GaussianBlur(28))
    bg.paste(Image.new("RGB", (W, H), (0, 0, 0)), (0, 0), shadow)
    bg.paste(fg, (x, y), mask)
    dest.parent.mkdir(parents=True, exist_ok=True)
    bg.save(dest, "JPEG", quality=92)
    return dest


if __name__ == "__main__":
    print(make_story(sys.argv[1], sys.argv[2]))
