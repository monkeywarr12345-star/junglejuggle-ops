#!/usr/bin/env python3
"""Turn benchmark posts into analysable features WITHOUT storing other accounts' content (public repo).

Caption -> skeleton: first line (<=60 chars), last question (<=60), line-type sequence, numbers, hashtags,
keywords, series prefix, lengths, emoji density. The full caption is never written to disk.
Cover image (media_url / reel thumbnail) -> OCR text (<=40 chars, Korean+English via tesseract), photo vs graphic,
face present, 2 dominant colours, OCR character count. The image itself is deleted right after.
Features are cached per post id in data/benchmark/features/<account>.jsonl, so each image is processed once.
Runs in GitHub Actions (needs: tesseract-ocr tesseract-ocr-kor, pip opencv-python-headless pillow numpy).
"""
import json
import re
import subprocess
import tempfile
import urllib.request
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
FEAT_DIR = ROOT / "data" / "benchmark" / "features"
EMOJI = re.compile("[\U0001F300-\U0001FAFF☀-➿⬀-⯿]")
NUM = re.compile(r"[+\-−▲▼]?\d[\d,]*(?:\.\d+)?\s?(?:%|%p|조|억|만|천|원|달러|배|위|명|개|년|월|일|bp)?")
STOP = set("그리고 하지만 그래서 이번 지금 오늘 우리 정말 진짜 너무 많이 이제 바로 위해 대한 통해 있는 없는 하는 했다 한다 있음 없음 했음 하면 해서 것 수 등 및 더 또 이 그 저 the and for with".split())


def line_type(line):
    s = line.strip()
    if not s:
        return None
    if s.startswith("#"):
        return "해시태그"
    if re.match(r"^(출처|📰|source)", s, re.I):
        return "출처"
    if re.match(r"^(\d+[.)]|[0-9]️⃣|[①-⑳])", s):
        return "번호"
    if s[0] in "-·•▪▶✔✅☑":
        return "항목"
    if s[0] in "⇒→👉➡":
        return "결론"
    if s.endswith("?") or s.endswith("?👇") or "👇" in s:
        return "질문"
    if EMOJI.match(s[0]) and len(s) <= 30:
        return "이모지소제목"
    return "문장"


def skeleton(caption):
    cap = caption or ""
    lines = [l for l in cap.splitlines() if l.strip()]
    types = [t for t in (line_type(l) for l in lines) if t]
    seq = []
    for t in types:  # run-length: 항목×3
        if seq and seq[-1][0] == t:
            seq[-1][1] += 1
        else:
            seq.append([t, 1])
    words = re.findall(r"[가-힣A-Za-z]{2,}", re.sub(r"#\S+", "", cap))
    kw = [w for w, _ in Counter(w for w in words if w not in STOP).most_common(12)]
    questions = [l.strip() for l in lines if "?" in l]
    def meaningful(l):
        t = re.sub(r"#\S+|\(?유료\s?광고\)?|\[?광고\]?|AD\b", "", l).strip()
        return len(re.findall(r"[가-힣A-Za-z0-9]", t)) >= 4
    first = next((l.strip() for l in lines if meaningful(l)), lines[0].strip() if lines else "")
    series = re.search(r"[\[【〈<]([^\]】〉>]{1,15})[\]】〉>]", first[:25])
    return {
        "first_line": first[:60],
        "last_question": questions[-1][:60] if questions else "",
        "structure": ">".join(f"{t}×{n}" if n > 1 else t for t, n in seq)[:200],
        "numbers": [n.strip() for n in NUM.findall(cap)][:15],
        "hashtags": re.findall(r"#[^\s#]+", cap)[:15],
        "keywords": kw,
        "series": series.group(1) if series else "",
        "chars": len(cap),
        "lines": len(lines),
        "emoji_per_100": round(100 * len(EMOJI.findall(cap)) / max(len(cap), 1), 2),
        "ends_with_question": bool(lines) and "?" in lines[-1],
        "giveaway": bool(re.search(r"추첨|이벤트|댓글 남기면|증정", cap)),
        "ad": bool(re.search(r"#광고|유료\s?광고|\[광고\]|협찬|#AD\b|paid partnership", cap, re.I)),
    }


def _image_features(url):
    import numpy as np
    from PIL import Image
    with tempfile.TemporaryDirectory() as tmp:
        path = Path(tmp) / "img"
        req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0 junglejuggle-bench"})
        with urllib.request.urlopen(req, timeout=40) as resp:
            path.write_bytes(resp.read())
        img = Image.open(path).convert("RGB")
        img.thumbnail((720, 900))
        arr = np.asarray(img)
        q = (arr // 32).reshape(-1, 3)
        keys, counts = np.unique(q[:, 0] * 64 + q[:, 1] * 8 + q[:, 2], return_counts=True)
        order = counts.argsort()[::-1]
        top5_share = counts[order[:5]].sum() / counts.sum()
        n_colors = int((counts > counts.sum() * 0.001).sum())
        colours = []
        for k in keys[order[:2]]:
            r, g, b = (k // 64) * 32 + 16, ((k // 8) % 8) * 32 + 16, (k % 8) * 32 + 16
            colours.append(f"#{r:02X}{g:02X}{b:02X}")
        face = False
        try:
            import cv2
            gray = cv2.cvtColor(arr, cv2.COLOR_RGB2GRAY)
            cascade = cv2.CascadeClassifier(cv2.data.haarcascades + "haarcascade_frontalface_default.xml")
            face = len(cascade.detectMultiScale(gray, 1.1, 6, minSize=(60, 60))) > 0
        except Exception:
            pass
        png = Path(tmp) / "x.png"
        img.save(png)
        tsv = subprocess.run(["tesseract", str(png), "-", "-l", "kor+eng", "--psm", "11", "tsv"], capture_output=True, text=True, timeout=60).stdout
        words = []
        for row in tsv.splitlines()[1:]:
            cols = row.split("\t")
            if len(cols) < 12 or not cols[11].strip():
                continue
            w, conf = cols[11].strip(), float(cols[10] or -1)
            if conf < 60:
                continue
            if re.search(r"[가-힣]{2,}", w) or re.fullmatch(r"[+\-−]?\d[\d,.]*[%조억만원배위]*", w) or re.fullmatch(r"[A-Za-z]{3,}|[A-Z]{2,}", w):
                words.append(w)
        text = " ".join(words)
        return {"cover_text": text[:40], "cover_chars": len(text.replace(" ", "")),
                "visual": "graphic" if top5_share > 0.6 and n_colors < 60 else "photo", "top5_share": round(float(top5_share), 3),
                "n_colors": n_colors, "face": bool(face), "colors": colours}


def load_cache(account):
    f = FEAT_DIR / f"{account}.jsonl"
    if not f.exists():
        return {}
    return {d["id"]: d for d in (json.loads(l) for l in f.read_text(encoding="utf-8").splitlines() if l.strip())}


def enrich(account, posts, max_new_images=400):
    """Replace captions with skeletons and attach cached/new image features. Returns the cleaned posts."""
    cache = load_cache(account)
    new_rows, done = [], 0
    for p in posts:
        p["skeleton"] = skeleton(p.pop("caption", ""))
        url = p.pop("media_url", None) if p.get("media_type") != "VIDEO" else None
        url = url or p.pop("thumbnail_url", None)
        p.pop("media_url", None), p.pop("thumbnail_url", None)
        if p.get("id") in cache:
            p["visual"] = cache[p["id"]].get("visual")
            continue
        if url and done < max_new_images:
            try:
                feat = _image_features(url)
                done += 1
            except Exception as exc:
                feat = {"error": str(exc)[:120]}
            p["visual"] = feat
            new_rows.append({"id": p.get("id"), "visual": feat})
    if new_rows:
        FEAT_DIR.mkdir(parents=True, exist_ok=True)
        with (FEAT_DIR / f"{account}.jsonl").open("a", encoding="utf-8") as f:
            for r in new_rows:
                f.write(json.dumps(r, ensure_ascii=False) + "\n")
    return posts
