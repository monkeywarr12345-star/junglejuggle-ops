#!/usr/bin/env python3
"""Find and download a usable photo from several free sources (runs in GitHub Actions).

A slide's "photo" can be:
  "https://..."                                   one direct URL (official press photo, korea.kr, Unsplash image URL ...)
  {"urls": [...], "query": "...", "queries": [...]}  try the URLs in order, then search each query in every source

Sources, tried in this order for each query (optional "sources": ["unsplash", ...] limits them):
  1. Unsplash       (needs UNSPLASH_ACCESS_KEY secret) Unsplash License, free commercial use
  2. Pexels         (needs PEXELS_API_KEY secret)   Pexels License, free commercial use
  3. Pixabay        (needs PIXABAY_API_KEY secret)  Pixabay Content License, free commercial use
  4. Openverse      (no key) CC0 / public domain / CC BY / CC BY-SA, commercial use + modification allowed
  5. Wikimedia Commons (no key) public domain, CC0, CC BY, CC BY-SA
Every pick is recorded with its credit and license in media/<id>/src/credits.json.
"""
import hashlib
import json
import os
import re
import urllib.parse
import urllib.request
from pathlib import Path

UA = "junglejuggle-render/1.0 (+https://github.com/monkeywarr12345-star/junglejuggle-ops)"
PHOTO_TYPES = {"image/jpeg": ".jpg", "image/png": ".png", "image/webp": ".webp"}
MIN_SIDE = 1000
OK_WIKI = re.compile(r"^(public domain|pd|cc0|cc[- ]by(-sa)?[- ]?[0-9.]*)", re.I)


def _get_json(url, headers=None):
    req = urllib.request.Request(url, headers={"User-Agent": UA, **(headers or {})})
    with urllib.request.urlopen(req, timeout=30) as resp:
        return json.load(resp)


def download(url, dest_dir, headers=None):
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0 " + UA, **(headers or {})})
    with urllib.request.urlopen(req, timeout=60) as resp:
        ctype = resp.headers.get_content_type()
        data = resp.read()
    if ctype not in PHOTO_TYPES:
        raise ValueError(f"not an image ({ctype})")
    if len(data) < 20_000:
        raise ValueError("image too small")
    dest_dir.mkdir(parents=True, exist_ok=True)
    path = dest_dir / (hashlib.sha1(url.encode()).hexdigest()[:12] + PHOTO_TYPES[ctype])
    path.write_bytes(data)
    return path


def _strip_html(s):
    return re.sub(r"<[^>]+>", "", s or "").strip()


def openverse(query):
    q = urllib.parse.urlencode({"q": query, "license_type": "commercial,modification", "size": "large",
                                "page_size": 20, "mature": "false"})
    for r in _get_json(f"https://api.openverse.org/v1/images/?{q}").get("results", []):
        if min(r.get("width") or 0, r.get("height") or 0) < MIN_SIDE * 0.7:
            continue
        lic = f"CC {r['license'].upper()} {r.get('license_version') or ''}".strip() if r["license"] not in ("cc0", "pdm") else "Public Domain/CC0"
        src = {"wikimedia": "Wikimedia Commons", "flickr": "Flickr"}.get(r.get("source"), (r.get("source") or "Openverse").title())
        yield r["url"], {"credit": f"{r.get('creator') or 'Unknown'} / {src}", "license": lic,
                         "page": r.get("foreign_landing_url"), "source": "openverse"}


def wikimedia(query):
    q = urllib.parse.urlencode({"action": "query", "format": "json", "generator": "search", "gsrnamespace": 6,
                                "gsrsearch": f"{query} filetype:bitmap", "gsrlimit": 20, "prop": "imageinfo",
                                "iiprop": "url|extmetadata|size|mime", "iiurlwidth": 1600})
    pages = _get_json(f"https://commons.wikimedia.org/w/api.php?{q}").get("query", {}).get("pages", {})
    for p in sorted(pages.values(), key=lambda x: x.get("index", 99)):
        info = (p.get("imageinfo") or [{}])[0]
        meta = info.get("extmetadata", {})
        lic = _strip_html(meta.get("LicenseShortName", {}).get("value"))
        if not OK_WIKI.match(lic) or "nc" in lic.lower() or "nd" in lic.lower().replace("and", ""):
            continue
        if min(info.get("width", 0), info.get("height", 0)) < MIN_SIDE * 0.7:
            continue
        artist = _strip_html(meta.get("Artist", {}).get("value")) or "Wikimedia Commons"
        yield info.get("thumburl") or info["url"], {"credit": f"{artist[:60]} / Wikimedia Commons", "license": lic,
                                                    "page": info.get("descriptionurl"), "source": "wikimedia"}


def pexels(query):
    key = os.environ.get("PEXELS_API_KEY")
    if not key:
        return
    q = urllib.parse.urlencode({"query": query, "per_page": 15, "orientation": "portrait"})
    for ph in _get_json(f"https://api.pexels.com/v1/search?{q}", {"Authorization": key}).get("photos", []):
        yield ph["src"]["large2x"], {"credit": f"{ph['photographer']} / Pexels", "license": "Pexels License",
                                     "page": ph["url"], "source": "pexels"}


def unsplash(query):
    key = os.environ.get("UNSPLASH_ACCESS_KEY")
    if not key:
        return
    q = urllib.parse.urlencode({"query": query, "per_page": 15, "orientation": "portrait", "content_filter": "high"})
    auth = {"Authorization": f"Client-ID {key}"}
    for r in _get_json(f"https://api.unsplash.com/search/photos?{q}", auth).get("results", []):
        if r.get("premium") or r.get("plus"):
            continue
        try:  # Unsplash API guideline: register the download
            _get_json(r["links"]["download_location"], auth)
        except Exception:
            pass
        yield r["urls"]["regular"], {"credit": f"{r['user']['name']} / Unsplash", "license": "Unsplash License",
                                     "page": r["links"]["html"], "source": "unsplash"}


def pixabay(query):
    key = os.environ.get("PIXABAY_API_KEY")
    if not key:
        return
    q = urllib.parse.urlencode({"key": key, "q": query, "image_type": "photo", "per_page": 20, "safesearch": "true", "min_width": 1080})
    for h in _get_json(f"https://pixabay.com/api/?{q}").get("hits", []):
        yield h["largeImageURL"], {"credit": f"{h['user']} / Pixabay", "license": "Pixabay Content License",
                                   "page": h["pageURL"], "source": "pixabay"}


# Stock libraries first (cleaner, cover-quality photos), then open archives (good for specific real places/things).
SEARCHERS = [unsplash, pexels, pixabay, openverse, wikimedia]


def resolve(photo, dest_dir, used=()):
    """Return (local_path, credit_dict) or raise RuntimeError listing every attempt."""
    if isinstance(photo, str):
        photo = {"urls": [photo]}
    attempts = []
    for url in photo.get("urls", []):
        try:
            return download(url, dest_dir), {"credit": photo.get("credit", ""), "license": photo.get("license", "공식 제공/라이선스 확인됨"),
                                            "page": url, "source": "direct"}
        except Exception as exc:
            attempts.append(f"direct {url[:80]}: {exc}")
    queries = [q for q in [photo.get("query"), *photo.get("queries", [])] if q]
    searchers = [f for f in SEARCHERS if not photo.get("sources") or f.__name__ in photo["sources"]]
    for query in queries:
        for search in searchers:
            try:
                for url, credit in search(query) or []:
                    if url in used:
                        continue
                    try:
                        return download(url, dest_dir), credit
                    except Exception as exc:
                        attempts.append(f"{credit['source']} {url[:60]}: {exc}")
            except Exception as exc:
                attempts.append(f"{search.__name__} '{query}': {exc}")
    raise RuntimeError("no usable photo; tried: " + " | ".join(attempts[-12:]) if attempts else "no urls or queries given")
