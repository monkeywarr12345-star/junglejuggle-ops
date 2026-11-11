#!/usr/bin/env python3
"""Collect performance data into data/ (runs in GitHub Actions, where the Graph API is reachable).

  python scripts/collect.py insights    -> data/insights/<date>.json  (our recent posts: reach, saves, shares, ...)
  python scripts/collect.py benchmark   -> data/benchmark/<date>/<account>.json (weekly, Sunday night: up to 1,000 / 100 posts)
  python scripts/collect.py bench_daily -> data/benchmark/daily/<KST date>.json (newest 15-30 posts per account, every morning)
  Benchmark captions are stored only as skeletons and covers only as features (scripts/bench_features.py).

Only the Python standard library is used.
insights uses IG_LOGIN_TOKEN (Instagram Login, no Facebook) when set, else IG_ACCESS_TOKEN + IG_USER_ID.
The benchmark modes read other accounts through business_discovery, which only the Facebook Login
setup offers, so they need IG_ACCESS_TOKEN + IG_USER_ID (see scripts/ig_api.py).
"""
import json
import os
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))
import ig_api  # noqa: E402

API = None  # the backend in use, set in __main__
BENCHMARKS = ["ekke.now", "newneek.official", "byte._.bites", "careet.official", "eyesmag", "longblack.co", "3protv.official"]
PAGES_PER_ACCOUNT = {"ekke.now": 20}  # 50 posts per page; ekke.now gets up to 1,000, others 100
DEFAULT_PAGES = 2


def get(path, params):
    try:
        return API.get(path, params)
    except ig_api.ApiError as exc:
        raise RuntimeError(str(exc)) from None


def insights():
    media = get(f"{API.user}/media", {"fields": "id,caption,media_type,media_product_type,timestamp,permalink,like_count,comments_count", "limit": 50})
    rows = []
    for m in media.get("data", []):
        metrics = "reach,saved,shares,likes,comments,total_interactions"
        if m.get("media_product_type") == "REELS":
            metrics += ",views,ig_reels_avg_watch_time"
        errors = []
        # the Unified-login business token may lack instagram_manage_insights: try every configured login
        for api in [API] + [b for b in ig_api.backends() if b.name != API.name]:
            try:
                data = api.get(f"{m['id']}/insights", {"metric": metrics}).get("data", [])
                m["insights"] = {d["name"]: (d.get("values") or [{}])[0].get("value", d.get("total_value", {}).get("value")) for d in data}
                m.pop("insights_error", None)
                m["insights_via"] = api.name
                break
            except RuntimeError as exc:
                errors.append(str(exc))
                m["insights_error"] = " | ".join(errors)
        rows.append(m)
    account = get(API.user, {"fields": "followers_count,media_count"})
    out = ROOT / "data" / "insights" / f"{datetime.now(timezone.utc):%Y-%m-%d}.json"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps({"account": account, "media": rows}, ensure_ascii=False, indent=1), encoding="utf-8")
    print(f"saved {len(rows)} posts -> {out}")


def _discover(name, pages, limit, with_children=True):
    base = "id,caption,media_type,media_product_type,timestamp,permalink,like_count,comments_count,media_url,thumbnail_url"
    fields = base + (",children{media_type}" if with_children else "")
    posts, after, info = [], None, {}
    for _ in range(pages):
        page_arg = f".after({after})" if after else ""
        q = f"business_discovery.username({name}){{followers_count,media_count,media.limit({limit}){page_arg}{{{fields}}}}}"
        try:
            bd = get(API.user, {"fields": q})["business_discovery"]
        except RuntimeError as exc:
            if with_children and "children" in str(exc).lower():
                return _discover(name, pages, limit, with_children=False)
            if not posts:
                raise
            print(f"{name}: stopped paging ({exc})", file=sys.stderr)
            break
        info = {"followers_count": bd.get("followers_count"), "media_count": bd.get("media_count")}
        media = bd.get("media", {})
        posts += media.get("data", [])
        after = media.get("paging", {}).get("cursors", {}).get("after")
        if not after:
            break
    for p in posts:  # carousel length only; children ids are not kept
        kids = p.pop("children", None)
        if kids:
            p["slides"] = len(kids.get("data", []))
    return posts, info


def benchmark(daily=False):
    """Weekly full pull (Sunday night) or a light daily pull of the newest posts (topic radar + age curve).
    Captions are reduced to skeletons and covers to features by bench_features.enrich (nothing copied)."""
    sys.path.insert(0, str(ROOT / "scripts"))
    import bench_features
    now = datetime.now(timezone.utc)
    collected_at = now.isoformat(timespec="seconds")
    failures, daily_rows = 0, {}
    for name in BENCHMARKS:
        pages, limit = (1, 30 if name == "ekke.now" else 15) if daily else (PAGES_PER_ACCOUNT.get(name, DEFAULT_PAGES), 50)
        try:
            posts, info = _discover(name, pages, limit)
        except RuntimeError as exc:
            print(f"{name}: {exc}", file=sys.stderr)
            failures += 1
            continue
        for p in posts:
            p["collected_at"] = collected_at
        posts = bench_features.enrich(name, posts)
        if daily:
            daily_rows[name] = {**info, "posts": posts}
        else:
            out = ROOT / "data" / "benchmark" / f"{now:%Y-%m-%d}" / f"{name}.json"
            out.parent.mkdir(parents=True, exist_ok=True)
            out.write_text(json.dumps({"account": name, "collected_at": collected_at, **info, "posts": posts},
                                      ensure_ascii=False, indent=1), encoding="utf-8")
        print(f"{name}: {len(posts)} posts")
    if daily:
        out = ROOT / "data" / "benchmark" / "daily" / f"{now + timedelta(hours=9):%Y-%m-%d}.json"
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(json.dumps({"collected_at": collected_at, "accounts": daily_rows}, ensure_ascii=False, indent=1), encoding="utf-8")
    return failures


def study():
    """One-off growth study (2026-11-11): post timelines of the accounts in data/study/accounts.json.
    {"accounts": {"<handle>": <max pages of 50>, ...}} -> data/study/<handle>.json with per-post date, type,
    like/comment counts, slide count and the caption skeleton only (no caption text, no images)."""
    sys.path.insert(0, str(ROOT / "scripts"))
    import bench_features
    cfg = json.loads((ROOT / "data" / "study" / "accounts.json").read_text(encoding="utf-8"))
    now = datetime.now(timezone.utc).isoformat(timespec="seconds")
    failed = {}
    for name, pages in cfg["accounts"].items():
        out = ROOT / "data" / "study" / f"{name}.json"
        if out.exists() and json.loads(out.read_text(encoding="utf-8")).get("pages", 0) >= pages:
            continue
        try:
            posts, info = _discover(name, pages, 50)
        except RuntimeError as exc:
            failed[name] = str(exc)[:200]
            print(f"{name}: {exc}", file=sys.stderr)
            continue
        rows = []
        for p in posts:
            rows.append({"timestamp": p.get("timestamp"), "media_type": p.get("media_type"),
                         "media_product_type": p.get("media_product_type"), "permalink": p.get("permalink"),
                         "like_count": p.get("like_count"), "comments_count": p.get("comments_count"),
                         "slides": p.get("slides"), "skeleton": bench_features.skeleton(p.get("caption") or "")})
        out.write_text(json.dumps({"account": name, "collected_at": now, "pages": pages, **info, "posts": rows},
                                  ensure_ascii=False, indent=0), encoding="utf-8")
        print(f"{name}: {len(rows)} posts, followers {info.get('followers_count')}")
    (ROOT / "data" / "study" / "failed.json").write_text(json.dumps(failed, ensure_ascii=False, indent=1), encoding="utf-8")


def use_backend(mode):
    global API
    if mode == "insights":
        for i, api in enumerate(apis := ig_api.backends()):
            try:
                api.user  # resolves the account ID and checks the login
                API = api
                return
            except ig_api.ApiError as exc:
                if i + 1 == len(apis):
                    raise
                print(f"{api.name} login failed ({exc}); trying {apis[i + 1].name}", file=sys.stderr)
    API = ig_api.facebook_backend()
    if API is None:
        print("benchmark needs the Facebook Login setup (IG_ACCESS_TOKEN + IG_USER_ID): "
              "business_discovery is not available with Instagram Login. Skipped.", file=sys.stderr)
        sys.exit(0)


if __name__ == "__main__":
    mode = sys.argv[1] if len(sys.argv) > 1 else "insights"
    if mode not in ("insights", "benchmark", "bench_daily", "study"):
        sys.exit(f"unknown mode {mode}")
    use_backend(mode)
    print(f"using {API.name} API")
    if mode == "insights":
        insights()
    elif mode == "benchmark":
        sys.exit(1 if benchmark() == len(BENCHMARKS) else 0)
    elif mode == "bench_daily":
        sys.exit(1 if benchmark(daily=True) == len(BENCHMARKS) else 0)
    elif mode == "study":
        study()
    else:
        sys.exit(f"unknown mode {mode}")
