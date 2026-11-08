#!/usr/bin/env python3
"""Collect performance data into data/ (runs in GitHub Actions, where the Graph API is reachable).

  python scripts/collect.py insights    -> data/insights/<date>.json  (our recent posts: reach, saves, shares, ...)
  python scripts/collect.py benchmark   -> data/benchmark/<date>/<account>.json (public posts via Business Discovery)

Only the Python standard library is used. Needs IG_ACCESS_TOKEN and IG_USER_ID.
"""
import json
import os
import sys
import urllib.error
import urllib.parse
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

API = "https://graph.facebook.com/v27.0"
ROOT = Path(__file__).resolve().parent.parent
TOKEN = os.environ["IG_ACCESS_TOKEN"]
IG_USER = os.environ["IG_USER_ID"]
BENCHMARKS = ["ekke.now", "newneek.official", "byte._.bites", "careet.official", "eyesmag", "longblack.co", "3protv.official"]
PAGES_PER_ACCOUNT = {"ekke.now": 20}  # 50 posts per page; ekke.now gets up to 1,000, others 100
DEFAULT_PAGES = 2


def get(path, params):
    params = dict(params, access_token=TOKEN)
    url = f"{API}/{path}?{urllib.parse.urlencode(params)}"
    try:
        with urllib.request.urlopen(url, timeout=60) as resp:
            return json.load(resp)
    except urllib.error.HTTPError as err:
        body = err.read().decode(errors="replace")
        raise RuntimeError(f"GET {path} failed ({err.code}): {body[:300]}") from None


def insights():
    media = get(f"{IG_USER}/media", {"fields": "id,caption,media_type,media_product_type,timestamp,permalink,like_count,comments_count", "limit": 50})
    rows = []
    for m in media.get("data", []):
        metrics = "reach,saved,shares,likes,comments,total_interactions"
        if m.get("media_product_type") == "REELS":
            metrics += ",views,ig_reels_avg_watch_time"
        try:
            data = get(f"{m['id']}/insights", {"metric": metrics}).get("data", [])
            m["insights"] = {d["name"]: (d.get("values") or [{}])[0].get("value", d.get("total_value", {}).get("value")) for d in data}
        except RuntimeError as exc:
            m["insights_error"] = str(exc)
        rows.append(m)
    account = get(IG_USER, {"fields": "followers_count,media_count"})
    out = ROOT / "data" / "insights" / f"{datetime.now(timezone.utc):%Y-%m-%d}.json"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps({"account": account, "media": rows}, ensure_ascii=False, indent=1), encoding="utf-8")
    print(f"saved {len(rows)} posts -> {out}")


def benchmark():
    day = f"{datetime.now(timezone.utc):%Y-%m-%d}"
    fields = "caption,media_type,media_product_type,timestamp,permalink,like_count,comments_count,media_url,thumbnail_url"
    failures = 0
    for name in BENCHMARKS:
        posts, after, info = [], None, {}
        for _ in range(PAGES_PER_ACCOUNT.get(name, DEFAULT_PAGES)):
            page_arg = f".after({after})" if after else ""
            q = f"business_discovery.username({name}){{followers_count,media_count,media.limit(50){page_arg}{{{fields}}}}}"
            try:
                bd = get(IG_USER, {"fields": q})["business_discovery"]
            except RuntimeError as exc:
                print(f"{name}: {exc}", file=sys.stderr)
                failures += 1
                break
            info = {"followers_count": bd.get("followers_count"), "media_count": bd.get("media_count")}
            media = bd.get("media", {})
            posts += media.get("data", [])
            after = media.get("paging", {}).get("cursors", {}).get("after")
            if not after:
                break
        out = ROOT / "data" / "benchmark" / day / f"{name}.json"
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(json.dumps({"account": name, **info, "posts": posts}, ensure_ascii=False, indent=1), encoding="utf-8")
        print(f"{name}: {len(posts)} posts")
    return failures


if __name__ == "__main__":
    mode = sys.argv[1] if len(sys.argv) > 1 else "insights"
    if mode == "insights":
        insights()
    elif mode == "benchmark":
        sys.exit(1 if benchmark() == len(BENCHMARKS) else 0)
    else:
        sys.exit(f"unknown mode {mode}")
