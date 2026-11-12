"""When do Korean AI-tips accounts post, and which slots do best?

Official Business Discovery API only (no scraping). Stores only timestamps, type and counts
(no captions, no images). Output: research/out/bench_timing.json
"""
import json, os, statistics, urllib.parse, urllib.request, datetime as dt

ACCOUNTS = ["gpt_haterz", "grappt_", "adu.aihub", "ai.trend.kr", "ai_newpd", "sebia.ai", "lazy_owen",
            "oaiwan.kr", "pickit_.official", "joshproductletter", "trenddalkak.ai"]
G = "https://graph.facebook.com/v23.0"
TOK, UID = os.environ["IG_ACCESS_TOKEN"], os.environ["IG_USER_ID"]
KST = dt.timezone(dt.timedelta(hours=9))
DAYS = ["월", "화", "수", "목", "금", "토", "일"]


def get(params):
    params["access_token"] = TOK
    with urllib.request.urlopen(f"{G}/{UID}?" + urllib.parse.urlencode(params), timeout=40) as r:
        return json.load(r)


def fetch(user, pages=6):
    media, after, prof = [], None, {}
    for _ in range(pages):
        mf = "media.limit(50)" + (f".after({after})" if after else "") + "{timestamp,media_product_type,like_count,comments_count}"
        d = get({"fields": f"business_discovery.username({user}){{followers_count,media_count,{mf}}}"})["business_discovery"]
        prof = {"followers": d.get("followers_count"), "media_count": d.get("media_count")}
        m = d.get("media", {})
        media += m.get("data", [])
        after = (m.get("paging", {}).get("cursors") or {}).get("after")
        if not after or not m.get("paging", {}).get("next"):
            break
    return prof, media


out = {"generated_at": dt.datetime.now(KST).isoformat(), "accounts": {}}
for u in ACCOUNTS:
    try:
        prof, media = fetch(u)
    except Exception as e:
        out["accounts"][u] = {"error": str(e)[:200]}
        continue
    rows = []
    for m in media:
        t = dt.datetime.fromisoformat(m["timestamp"].replace("+0000", "+00:00")).astimezone(KST)
        rows.append({"t": t.strftime("%Y-%m-%d %H:%M"), "dow": t.weekday(), "hour": t.hour, "type": m.get("media_product_type"),
                     "eng": (m.get("like_count") or 0) + 3 * (m.get("comments_count") or 0), "comments": m.get("comments_count") or 0})
    rows.sort(key=lambda r: r["t"])
    med = statistics.median([r["eng"] for r in rows]) if rows else 0
    for r in rows:
        r["x"] = round(r["eng"] / med, 2) if med else None  # vs this account's own median
    span = None
    if len(rows) > 1:
        d0 = dt.datetime.strptime(rows[0]["t"], "%Y-%m-%d %H:%M"); d1 = dt.datetime.strptime(rows[-1]["t"], "%Y-%m-%d %H:%M")
        span = max(1, (d1 - d0).days)
    recent = [r for r in rows if r["t"] >= (dt.datetime.now(KST) - dt.timedelta(days=28)).strftime("%Y-%m-%d")]
    out["accounts"][u] = {**prof, "n": len(rows), "span_days": span, "per_week_all": round(len(rows) / span * 7, 1) if span else None,
                          "per_week_last28d": round(len(recent) / 4, 1), "reels_share": round(sum(r["type"] == "REELS" for r in rows) / max(1, len(rows)), 2),
                          "rows": rows}

# pooled view: each post weighted equally across accounts, performance = multiple of own median
pool = [r for a in out["accounts"].values() for r in a.get("rows", []) if r.get("x") is not None]
def agg(key, labels):
    res = {}
    for k in sorted(set(r[key] for r in pool)):
        xs = [r["x"] for r in pool if r[key] == k]
        res[labels(k)] = {"posts": len(xs), "share": round(len(xs) / len(pool), 3), "median_x": round(statistics.median(xs), 2),
                          "top_rate": round(sum(x >= 2 for x in xs) / len(xs), 2)}
    return res
out["pooled"] = {"n": len(pool), "by_dow": agg("dow", lambda k: DAYS[k]), "by_hour": agg("hour", lambda k: f"{k:02d}시")}
os.makedirs("research/out", exist_ok=True)
json.dump(out, open("research/out/bench_timing.json", "w"), ensure_ascii=False, indent=1)
print(json.dumps({u: {k: v for k, v in a.items() if k != "rows"} for u, a in out["accounts"].items()}, ensure_ascii=False, indent=1))
print(json.dumps(out["pooled"], ensure_ascii=False, indent=1))
