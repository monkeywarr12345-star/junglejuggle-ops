#!/usr/bin/env python3
"""External free-music library for reels: weekly refresh of new and popular tracks, and rotation.

  python scripts/music_library.py refresh        (GitHub Actions, needs internet) fetch + download + trim tracks
  python scripts/music_library.py pick <mood> <reel_id>   print JSON {file, credit} and record the use

Sources (only licenses that allow commercial use and editing; attribution goes in the caption):
  - Jamendo API, ordered by this week's popularity and by newest releases (needs JAMENDO_CLIENT_ID secret, free)
  - Openverse audio API (no key): CC0 / CC BY / CC BY-SA music from Jamendo, ccMixter, Wikimedia and others
Library: music/library/<mood>/*.mp3 (60-second trimmed, loudness-normalised), metadata in music/library.json,
license table in music/LICENSES.md, usage history in music/usage.json.
Selection (user request 2026-11-09: "the music is bland"): prefer songs with vocals and real listener popularity.
  - Jamendo is queried with vocalinstrumental=vocal over this month's / this week's / all-time popularity,
    plus a smaller instrumental fallback; each track gets a score from listens (stats) and chart rank.
  - Library entries carry "vocal" (bool) and "score"; old entries are backfilled from the Jamendo API on refresh.
  - pick(): vocal tracks only (2026-11-09), least recently used, then highest score. Prune keeps the best-scored tracks.
Rotation: never reuse a track within the last 12 reels of that mood.
"""
import hashlib
import html
import json
import math
import os
import re
import subprocess
import sys
import tempfile
import urllib.parse
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
MUSIC = ROOT / "music"
LIB_JSON = MUSIC / "library.json"
USAGE_JSON = MUSIC / "usage.json"
UA = "junglejuggle-music/1.0 (+https://github.com/monkeywarr12345-star/junglejuggle-ops)"
MAX_PER_MOOD = 24
NEW_PER_REFRESH = 10
RECENT_BLOCK = 12
MOODS = {
    "upbeat": {"jamendo_tags": ["pop", "dance", "indiepop", "rnb", "funk", "electronic"],
               "openverse": ["pop song vocals", "upbeat pop", "dance pop", "funk", "pop"]},
    "tense": {"jamendo_tags": ["rock", "hiphop", "dark", "cinematic", "epic", "electronic"],
              "openverse": ["rock song", "hip hop", "dark pop", "cinematic tension", "dramatic epic"]},
    "chill": {"jamendo_tags": ["indie", "acoustic", "rnb", "lofi", "chillout", "jazz"],
              "openverse": ["acoustic song vocals", "indie pop", "lofi", "chillout", "jazz"]},
}
OK_LICENSE = re.compile(r"(publicdomain|/zero/|/by/|/by-sa/|^cc0$|^by$|^by-sa$|^pdm$)", re.I)


def _json(url, default=None):
    req = urllib.request.Request(url, headers={"User-Agent": UA})
    try:
        with urllib.request.urlopen(req, timeout=40) as resp:
            return json.load(resp)
    except Exception as exc:
        print(f"warn: {url[:90]}: {exc}", file=sys.stderr)
        return default


def load(path, default):
    return json.loads(path.read_text(encoding="utf-8")) if path.exists() else default


def save(path, data):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=1), encoding="utf-8")


def license_label(lic):
    lic = lic.lower()
    if "zero" in lic or lic.startswith(("cc0", "pdm")) or "publicdomain" in lic:
        return "CC0/Public Domain"
    ver = re.search(r"(\d\.\d)", lic)
    return ("CC BY-SA" if "by-sa" in lic else "CC BY") + (f" {ver.group(1)}" if ver else "")


def commercial_mode():
    """music/config.json {"commercial": true} once the account earns money (sponsorship, ads, affiliate).
    Jamendo's free API is for non-commercial use only, so commercial mode stops using it and every
    Jamendo-hosted track; CC0 / CC BY tracks from other sources and generated music remain."""
    return load(MUSIC / "config.json", {}).get("commercial", False)


def is_jamendo(t):
    return "jamendo" in t.get("source", "") or "jamendo" in (t.get("page") or "")


VOCAL_HINT = re.compile(r"(feat\.|ft\.|vocal|lyrics|\bsong\b|singer)", re.I)
INSTR_HINT = re.compile(r"(instrumental|karaoke|backing track|\bbgm\b|loop)", re.I)


def popularity_score(t, rank=0, order=""):
    """Listener popularity: log-scaled total listens + favourites, plus chart rank for this query."""
    st = t.get("stats") or {}
    listens = int(st.get("rate_listened_total") or st.get("listened") or 0)
    favs = int(st.get("favorited") or 0) + int(st.get("playlisted") or 0)
    bonus = {"popularity_month": 30, "popularity_week": 25, "popularity_total": 20}.get(order, 0)
    return round(40 * math.log10(1 + listens) + 15 * math.log10(1 + favs) + (20 - rank) + bonus, 1)


def is_vocal_jamendo(t):
    vi = ((t.get("musicinfo") or {}).get("vocalinstrumental") or "").lower()
    if vi:
        return vi == "vocal"
    return bool(VOCAL_HINT.search(t.get("name") or "")) and not INSTR_HINT.search(t.get("name") or "")


def jamendo_candidates(mood):
    cid = os.environ.get("JAMENDO_CLIENT_ID")
    if not cid or commercial_mode():
        return []
    out = []
    # vocal songs over three popularity windows, then a small instrumental fallback
    plan = [(o, "vocal") for o in ("popularity_month", "popularity_week", "popularity_total")] + [("popularity_week", "instrumental")]
    for order, vi in plan:
        for tag in MOODS[mood]["jamendo_tags"]:
            q = urllib.parse.urlencode({"client_id": cid, "format": "json", "limit": 20 if vi == "vocal" else 8, "order": order,
                                        "tags": tag, "vocalinstrumental": vi, "audiodownload_allowed": "true",
                                        "include": "licenses musicinfo stats", "groupby": "artist_id"})
            data = _json(f"https://api.jamendo.com/v3.0/tracks/?{q}", {}) or {}
            for rank, t in enumerate(data.get("results", [])):
                lic = t.get("license_ccurl", "")
                if not OK_LICENSE.search(lic) or "-nc" in lic or "-nd" in lic or not t.get("audiodownload"):
                    continue
                if not 90 <= int(t.get("duration") or 0) <= 360:
                    continue
                vocal = vi == "vocal" and is_vocal_jamendo(t)
                score = popularity_score(t, rank, order)
                out.append({"source": "jamendo", "src_id": f"jamendo-{t['id']}", "title": t["name"], "artist": t["artist_name"],
                            "license": license_label(lic), "license_url": lic, "page": t.get("shareurl"), "audio": t["audiodownload"],
                            "released": t.get("releasedate"), "vocal": vocal, "score": score + (1000 if vocal else 0)})
    return out


def jamendo_lookup(track_ids):
    """{id: track} with musicinfo + stats, for backfilling older library entries."""
    cid = os.environ.get("JAMENDO_CLIENT_ID")
    out = {}
    if not cid:
        return out
    ids = list(track_ids)
    for i in range(0, len(ids), 50):
        q = urllib.parse.urlencode({"client_id": cid, "format": "json", "limit": 50, "id": "+".join(ids[i:i + 50]).replace("+", " "),
                                    "include": "musicinfo stats"})
        for t in (_json(f"https://api.jamendo.com/v3.0/tracks/?{q}", {}) or {}).get("results", []):
            out[str(t["id"])] = t
    return out


def jamendo_id(entry):
    m = re.search(r"jamendo\.com/track/(\d+)", entry.get("page") or "") or re.match(r"jamendo-(\d+)$", entry.get("src_id", ""))
    return m.group(1) if m else None


def backfill(lib):
    todo = {jamendo_id(t): t for t in lib if "vocal" not in t and jamendo_id(t)}
    found = jamendo_lookup(todo) if todo else {}
    for t in lib:
        if "vocal" in t:
            continue
        jt = found.get(jamendo_id(t) or "")
        if jt:
            t["vocal"] = is_vocal_jamendo(jt)
            t["score"] = popularity_score(jt) + (1000 if t["vocal"] else 0)
        else:
            t["vocal"] = bool(VOCAL_HINT.search(t["title"])) and not INSTR_HINT.search(t["title"])
            t["score"] = (1000 if t["vocal"] else 0)


def openverse_candidates(mood):
    out = []
    for query in MOODS[mood]["openverse"]:
        q = urllib.parse.urlencode({"q": query, "license": "cc0,pdm,by,by-sa", "category": "music", "page_size": 20, "mature": "false"})
        data = _json(f"https://api.openverse.org/v1/audio/?{q}", {}) or {}
        print(f"openverse '{query}': {len(data.get('results', []))} results", file=sys.stderr)
        for rank, r in enumerate(data.get("results", [])):
            dur = (r.get("duration") or 0) / 1000
            if not 60 <= dur <= 420 or not r.get("url") or (commercial_mode() and "jamendo" in (r.get("source") or "") + r["url"]):
                continue
            out.append({"source": f"openverse/{r.get('source', '')}", "src_id": f"ov-{r['id']}", "title": html.unescape(r.get("title") or "Untitled"),
                        "artist": html.unescape(r.get("creator") or "Unknown"), "license": license_label(r["license"] + (r.get("license_version") or "")),
                        "license_url": r.get("license_url"), "page": r.get("foreign_landing_url"), "audio": r["url"],
                        "released": None, "vocal": bool(VOCAL_HINT.search(r.get("title") or "")) and not INSTR_HINT.search(r.get("title") or ""),
                        "score": 20 - rank})
    for c in out:
        if c["vocal"]:
            c["score"] += 1000
    return out


def fetch_track(cand, dest):
    with tempfile.TemporaryDirectory() as tmp:
        raw = Path(tmp) / "raw"
        req = urllib.request.Request(cand["audio"], headers={"User-Agent": "Mozilla/5.0 " + UA})
        with urllib.request.urlopen(req, timeout=90) as resp:
            raw.write_bytes(resp.read())
        dur = float(subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", str(raw)],
                                   capture_output=True, text=True, check=True).stdout.strip() or 0)
        start = max(0.0, min(dur * 0.2, dur - 62))  # skip the intro, keep a 60s section
        dest.parent.mkdir(parents=True, exist_ok=True)
        subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-ss", f"{start:.1f}", "-t", "60", "-i", str(raw),
                        "-af", "loudnorm=I=-16:TP=-1.5:LRA=11,afade=t=in:d=0.4", "-ac", "2", "-ar", "44100", "-b:a", "160k", str(dest)],
                       check=True)


def write_licenses(lib):
    rows = [f"| {t['file']} | {t['title']} | {t['artist']} | {t['license']} | {t.get('page') or ''} | {t['added'][:10]} |"
            for t in sorted(lib, key=lambda x: (x["mood"], x["added"]), reverse=True)]
    (MUSIC / "LICENSES.md").write_text(
        "# 릴스 음원 라이선스 기록\n\n외부 무료 음원은 상업적 이용·편집이 허용된 라이선스(CC0, CC BY, CC BY-SA)만 쓴다.\n"
        "CC BY/BY-SA 곡은 캡션에 크레딧(곡명 - 아티스트, 라이선스)을 반드시 넣는다. 자체 제작 음악(scripts/music.py)은 기록 대상이 아니다.\n\n"
        "| 파일 | 곡 | 아티스트 | 라이선스 | 원본 | 추가일 |\n| --- | --- | --- | --- | --- | --- |\n" + "\n".join(rows) + "\n",
        encoding="utf-8")


def refresh():
    lib = load(LIB_JSON, [])
    usage = load(USAGE_JSON, [])
    if commercial_mode():  # drop Jamendo tracks from the working library (already-published reels are untouched)
        for t in [t for t in lib if is_jamendo(t)]:
            (ROOT / t["file"]).unlink(missing_ok=True)
            lib.remove(t)
    backfill(lib)
    known = {t["src_id"] for t in lib} | {(t["title"].lower(), t["artist"].lower()) for t in lib}
    now = datetime.now(timezone.utc).isoformat(timespec="seconds")
    added = 0
    for mood in MOODS:
        cands = sorted(jamendo_candidates(mood) + openverse_candidates(mood), key=lambda c: -c["score"])
        seen, new = set(), 0
        for c in cands:
            if c["src_id"] in known or (c["title"].lower(), c["artist"].lower()) in known or c["src_id"] in seen or new >= NEW_PER_REFRESH:
                continue
            seen.add(c["src_id"])
            slug = re.sub(r"[^a-z0-9]+", "-", f"{c['artist']}-{c['title']}".lower()).strip("-")[:50] or "track"
            rel = f"music/library/{mood}/{slug}-{hashlib.sha1(c['src_id'].encode()).hexdigest()[:6]}.mp3"
            try:
                fetch_track(c, ROOT / rel)
            except Exception as exc:
                print(f"skip {c['src_id']}: {exc}", file=sys.stderr)
                continue
            lib.append({**{k: c[k] for k in ("source", "src_id", "title", "artist", "license", "license_url", "page", "released", "vocal", "score")},
                        "mood": mood, "file": rel, "added": now})
            known |= {c["src_id"], (c["title"].lower(), c["artist"].lower())}
            new += 1
            added += 1
        # prune: keep the best MAX_PER_MOOD per mood (vocal + popular first, newer on ties),
        # never delete a track used in the last 30 uses
        recent = {u["file"] for u in usage[-30:]}
        mood_tracks = sorted([t for t in lib if t["mood"] == mood], key=lambda t: (t.get("score", 0), t["added"]), reverse=True)
        for t in mood_tracks[MAX_PER_MOOD:]:
            if t["file"] in recent:
                continue
            (ROOT / t["file"]).unlink(missing_ok=True)
            lib.remove(t)
    save(LIB_JSON, lib)
    write_licenses(lib)
    counts = ", ".join(f"{m}: {sum(t['mood'] == m for t in lib)}" for m in MOODS)
    print(f"added {added} tracks; library now {len(lib)} ({counts})")


def pick(mood, reel_id):
    lib = [t for t in load(LIB_JSON, []) if t["mood"] == mood and (ROOT / t["file"]).exists()
           and not (commercial_mode() and is_jamendo(t))]
    if not lib:
        return None
    usage = load(USAGE_JSON, [])
    mood_use = [u["file"] for u in usage if u.get("mood") == mood]
    blocked = set(mood_use[-RECENT_BLOCK:])
    last_used = {f: i for i, f in enumerate(mood_use)}
    # 2026-11-09 user decision: reels use songs with lyrics only. Vocal tracks of this mood first,
    # then vocal tracks of any mood; instrumentals are never picked (no vocal track at all -> None -> self-made music).
    vocal = [t for t in lib if t.get("vocal")]
    if not vocal:
        vocal = [t for t in load(LIB_JSON, []) if t.get("vocal") and (ROOT / t["file"]).exists()
                 and not (commercial_mode() and is_jamendo(t))]
        print(f"music_library: no vocal track for mood {mood}; using vocal tracks from other moods", file=sys.stderr)
    if not vocal:
        print("music_library: WARNING no vocal track in library", file=sys.stderr)
        return None
    pool = [t for t in vocal if t["file"] not in blocked] or vocal
    # least recently used, then most popular
    pool.sort(key=lambda t: (last_used.get(t["file"], -1), -t.get("score", 0)))
    t = pool[0]
    usage.append({"reel": reel_id, "mood": mood, "file": t["file"], "at": datetime.now(timezone.utc).isoformat(timespec="seconds")})
    save(USAGE_JSON, usage[-500:])
    credit = f"🎵 {t['title']} - {t['artist']} ({t['license']})"
    return {"file": t["file"], "credit": credit, "page": t.get("page")}


if __name__ == "__main__":
    if sys.argv[1] == "refresh":
        refresh()
    elif sys.argv[1] == "pick":
        print(json.dumps(pick(sys.argv[2], sys.argv[3]), ensure_ascii=False))
