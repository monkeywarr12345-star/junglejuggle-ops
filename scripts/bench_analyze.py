#!/usr/bin/env python3
"""Numbers for the weekly benchmark review (method: playbook/benchmark_method.md).

  python scripts/bench_analyze.py weekly   -> data/analysis/<YYYY-Www>.json + playbook/benchmark/<YYYY-Www>-tables.md
  python scripts/bench_analyze.py uncoded [N] -> prints JSONL of posts that still need content coding (newest first)
  python scripts/bench_analyze.py radar    -> data/benchmark/daily/<date>.radar.json (topics 2+ accounts covered in 24h)

Score per post (comparable across accounts and formats):
  E = likes + 3*min(comments, cap)            cap = 3 x account median comments, only for giveaway posts
  B = median E of the same account+surface's previous 30 mature posts (age >= 72h), excluding itself
  s = clip(ln((E/f(age) + 1) / (B + 1)), -2.5, 2.5)     s = 0.69 means twice the usual reaction
  f(age): share of the final reaction reached at that age, estimated from daily snapshots when >= 10 pairs,
          otherwise 24h 0.75 / 48h 0.9 / 72h+ 1.0. Only mature posts (age >= 72h) enter code effects.
Code effects (content coding in data/benchmark/coded/<account>.jsonl, done weekly by Claude):
  lift = sum_a sqrt(n_a) * median(s_a) / sum_a sqrt(n_a)  (accounts first, so ekke.now cannot dominate)
  shrunk = n/(n+10) * lift; 90% CI by account-stratified bootstrap; P(s > ln2) with Wilson interval;
  grades: 확인 (n>=15, 3+ accounts, CI low > 0) / 유망 (n>=8, 2+ accounts, shrunk > 0.2) / 관찰;
  Benjamini-Hochberg q=0.1 across all codes tested this week. Window: last 26 weeks.
"""
import json
import math
import random
import re
import statistics as st
import sys
from collections import Counter, defaultdict
from datetime import datetime, timedelta, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
BENCH = ROOT / "data" / "benchmark"
KST = timezone(timedelta(hours=9))
DEFAULT_F = [(24, 0.75), (48, 0.9), (72, 1.0)]
CODE_DIMS = ["topic_major", "angle", "hook_cover", "hook_first", "structure", "tone", "density", "evidence", "devices", "series_flag", "visual"]


def ts(s):
    return datetime.fromisoformat(s.replace("Z", "+00:00").replace("+0000", "+00:00"))


def latest_weekly():
    dirs = sorted(d for d in BENCH.glob("20??-??-??") if d.is_dir())
    if not dirs:
        sys.exit("no weekly benchmark snapshot yet (data/benchmark/<date>/)")
    return dirs[-1]


def surface(p):
    return "REELS" if p.get("media_product_type") == "REELS" or p.get("media_type") == "VIDEO" else "FEED"


def engagement(p, cmt_median):
    likes, cm = p.get("like_count"), p.get("comments_count") or 0
    if p.get("skeleton", {}).get("giveaway"):
        cm = min(cm, 3 * max(cmt_median, 1))
    return (likes if likes is not None else 0) + 3 * cm


def age_curve():
    """f(age bucket) per surface from daily snapshots: E at age a / E at age >= 168h, median per 12h bucket."""
    seen = defaultdict(list)  # id -> [(age_h, E, surface)]
    for f in sorted((BENCH / "daily").glob("*.json")):
        if f.name.endswith(".radar.json"):
            continue
        d = json.loads(f.read_text(encoding="utf-8"))
        for acc in d.get("accounts", {}).values():
            for p in acc.get("posts", []):
                if p.get("like_count") is None:
                    continue
                a = (ts(p["collected_at"]) - ts(p["timestamp"])).total_seconds() / 3600
                seen[p["id"]].append((a, p["like_count"] + 3 * (p.get("comments_count") or 0), surface(p)))
    for d in sorted(latest_weekly().parent.glob("20??-??-??")):
        for f in d.glob("*.json"):
            for p in json.loads(f.read_text(encoding="utf-8")).get("posts", []):
                if p.get("id") and p.get("like_count") is not None and p.get("collected_at"):
                    a = (ts(p["collected_at"]) - ts(p["timestamp"])).total_seconds() / 3600
                    seen[p["id"]].append((a, p["like_count"] + 3 * (p.get("comments_count") or 0), surface(p)))
    ratios = defaultdict(list)
    for obs in seen.values():
        final = [e for a, e, _ in obs if a >= 168]
        if not final or max(final) <= 0:
            continue
        for a, e, sf in obs:
            if a < 72:
                ratios[(sf, int(a // 12))].append(e / max(final))
    return {k: st.median(v) for k, v in ratios.items() if len(v) >= 10}


def f_age(age_h, sf, curve):
    if age_h >= 72:
        return 1.0
    if (sf, int(age_h // 12)) in curve:
        return max(curve[(sf, int(age_h // 12))], 0.05)
    for limit, val in DEFAULT_F:
        if age_h < limit:
            return val
    return 1.0


def load_codes():
    codes = {}
    for f in (BENCH / "coded").glob("*.jsonl"):
        for line in f.read_text(encoding="utf-8").splitlines():
            if line.strip():
                d = json.loads(line)
                codes[d["id"]] = d.get("codes", {})
    return codes


def scored_posts():
    snap = latest_weekly()
    curve = age_curve()
    rows, accounts = [], {}
    for f in sorted(snap.glob("*.json")):
        d = json.loads(f.read_text(encoding="utf-8"))
        acc, posts = d["account"], d.get("posts", [])
        cmt_med = st.median([p.get("comments_count") or 0 for p in posts]) if posts else 0
        posts = sorted(posts, key=lambda p: p["timestamp"])
        hist = defaultdict(list)  # surface -> mature E history
        all_mature = [engagement(p, cmt_med) for p in posts
                      if (ts(p.get("collected_at", d["collected_at"])) - ts(p["timestamp"])).total_seconds() >= 72 * 3600]
        acc_med = st.median(all_mature) if all_mature else 0
        for p in posts:
            if (p.get("skeleton") or {}).get("ad"):
                continue  # paid/sponsored posts distort reactions
            sf = surface(p)
            age = (ts(p.get("collected_at", d["collected_at"])) - ts(p["timestamp"])).total_seconds() / 3600
            e = engagement(p, cmt_med)
            prev = hist[sf][-30:]
            base = st.median(prev) if len(prev) >= 10 else acc_med
            s = max(-2.5, min(2.5, math.log((e / f_age(age, sf, curve) + 1) / (base + 1))))
            rows.append({"id": p.get("id"), "account": acc, "surface": sf, "type": p.get("media_type"), "age_h": round(age, 1),
                         "timestamp": p["timestamp"], "E": e, "B": base, "s": round(s, 3), "mature": age >= 72,
                         "likes_hidden": p.get("like_count") is None, "slides": p.get("slides"),
                         "first_line": p.get("skeleton", {}).get("first_line", ""), "cover_text": (p.get("visual") or {}).get("cover_text", ""),
                         "visual_kind": (p.get("visual") or {}).get("visual"), "keywords": p.get("skeleton", {}).get("keywords", []),
                         "structure": p.get("skeleton", {}).get("structure", ""), "permalink": p.get("permalink")})
            if age >= 72:
                hist[sf].append(e)
        accounts[acc] = {"followers": d.get("followers_count"), "posts": len(posts), "median_E": acc_med,
                         "reels_share": round(sum(surface(p) == "REELS" for p in posts) / max(len(posts), 1), 2)}
    return rows, accounts, snap.name, curve


def wilson(k, n, z=1.645):
    if n == 0:
        return (0, 0)
    p = k / n
    d = 1 + z * z / n
    c = (p + z * z / (2 * n)) / d
    h = z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / d
    return (round(c - h, 3), round(c + h, 3))


def lift(groups):
    num = sum(math.sqrt(len(v)) * st.median(v) for v in groups.values() if v)
    den = sum(math.sqrt(len(v)) for v in groups.values() if v)
    return num / den if den else 0.0


def code_effects(rows, codes, rng):
    cutoff = datetime.now(timezone.utc) - timedelta(weeks=26)
    mature = [r for r in rows if r["mature"] and r["id"] in codes and ts(r["timestamp"]) >= cutoff]
    out = []
    for dim in CODE_DIMS:
        values = defaultdict(lambda: defaultdict(list))
        for r in mature:
            v = codes[r["id"]].get(dim)
            for val in (v if isinstance(v, list) else [v]):
                if val not in (None, "", []):
                    values[(val, r["surface"])][r["account"]].append(r["s"])
        for (val, sf), groups in values.items():
            n = sum(len(v) for v in groups.values())
            if n < 3:
                continue
            l = lift(groups)
            boots = []
            for _ in range(1000):
                g = {a: [rng.choice(v) for _ in v] for a, v in groups.items()}
                boots.append(lift(g))
            boots.sort()
            lo, hi = boots[int(0.05 * len(boots))], boots[int(0.95 * len(boots)) - 1]
            p_two = min(1.0, 2 * min(sum(b <= 0 for b in boots), sum(b >= 0 for b in boots)) / len(boots))
            k = sum(x > math.log(2) for v in groups.values() for x in v)
            shrunk = n / (n + 10) * l
            grade = ("확인" if n >= 15 and len(groups) >= 3 and lo > 0 else
                     "유망" if n >= 8 and len(groups) >= 2 and shrunk > 0.2 else "관찰")
            out.append({"dim": dim, "value": val, "surface": sf, "n": n, "accounts": len(groups), "lift": round(l, 3),
                        "shrunk": round(shrunk, 3), "ci90": [round(lo, 3), round(hi, 3)], "p": round(p_two, 4),
                        "share_2x": round(k / n, 3), "share_2x_ci": wilson(k, n), "grade": grade})
    ranked = sorted(out, key=lambda x: x["p"])  # Benjamini-Hochberg, q = 0.1
    m = len(ranked)
    passed = 0
    for i, r in enumerate(ranked, 1):
        if r["p"] <= 0.1 * i / max(m, 1):
            passed = i
    for i, r in enumerate(ranked, 1):
        r["bh_pass"] = i <= passed
        if not r["bh_pass"] and r["grade"] == "확인":
            r["grade"] = "유망"
    return sorted(out, key=lambda x: (x["dim"], -x["shrunk"]))


def rising(rows, codes):
    now = datetime.now(timezone.utc)
    recent = [r for r in rows if r["id"] in codes and ts(r["timestamp"]) >= now - timedelta(weeks=2)]
    before = [r for r in rows if r["id"] in codes and now - timedelta(weeks=8) <= ts(r["timestamp"]) < now - timedelta(weeks=2)]
    signals = []
    for dim in ["topic_major", "angle", "hook_cover", "structure"]:
        cnt_r = Counter(codes[r["id"]].get(dim) for r in recent)
        cnt_b = Counter(codes[r["id"]].get(dim) for r in before)
        N, Nb = len(recent), max(len(before), 1)
        for val, x in cnt_r.items():
            if not val:
                continue
            p0 = (cnt_b.get(val, 0) + 1) / (Nb + len(cnt_b) + 1)
            z = (x - N * p0) / math.sqrt(max(N * p0 * (1 - p0), 1e-9))
            accs = {r["account"] for r in recent if codes[r["id"]].get(dim) == val}
            wk = [r["s"] for r in recent if codes[r["id"]].get(dim) == val and ts(r["timestamp"]) >= now - timedelta(weeks=1)]
            freq = z >= 2 and x >= 4 and len(accs) >= 2
            perf = len(wk) >= 4 and st.median(wk) >= math.log(1.5) and len(accs) >= 2
            if freq or perf:
                signals.append({"dim": dim, "value": val, "z": round(z, 2), "count_2w": x, "accounts": len(accs),
                                "label": "급상승" if freq and perf else "업계 유행" if freq else "성과 신호"})
    return signals


def our_posts():
    files = sorted((ROOT / "data" / "insights").glob("*.json"))
    if not files:
        return []
    d = json.loads(files[-1].read_text(encoding="utf-8"))
    return d.get("media", [])


def radar(posts_by_acc, hours=24):
    now = datetime.now(timezone.utc)
    hits = defaultdict(set)
    for acc, posts in posts_by_acc.items():
        for p in posts:
            if ts(p["timestamp"]) < now - timedelta(hours=hours):
                continue
            words = set((p.get("skeleton") or {}).get("keywords", [])[:8])
            words |= set(re.findall(r"[가-힣]{2,}|[A-Za-z]{3,}", (p.get("visual") or {}).get("cover_text", "")))
            words = {w for w in words if re.search(r"[가-힣]", w) or len(w) >= 3}
            for w in words:
                hits[w].add(acc)
    ours = " ".join((m.get("caption") or "") for m in our_posts())
    common = {"정글러님들", "오늘", "이번", "지금", "우리", "여러분", "에디터", "링크", "프로필", "저장", "댓글"}
    out = [{"word": w, "accounts": sorted(a), "covered_by_us": w in ours}
           for w, a in hits.items() if len(a) >= 2 and w not in common]
    return sorted(out, key=lambda x: -len(x["accounts"]))[:40]


def md_table(head, rows):
    return "| " + " | ".join(head) + " |\n|" + "---|" * len(head) + "\n" + "\n".join("| " + " | ".join(str(c) for c in r) + " |" for r in rows) + "\n"


def weekly():
    rng = random.Random(7)
    rows, accounts, snap, curve = scored_posts()
    codes = load_codes()
    effects = code_effects(rows, codes, rng)
    sig = rising(rows, codes)
    now = datetime.now(timezone.utc)
    week = [r for r in rows if ts(r["timestamp"]) >= now - timedelta(days=7)]
    top = sorted(week, key=lambda r: -r["s"])[:10]
    bottom = sorted([r for r in week if r["mature"]], key=lambda r: r["s"])[:5]
    per_acc = defaultdict(list)
    for f in latest_weekly().glob("*.json"):
        d = json.loads(f.read_text(encoding="utf-8"))
        per_acc[d["account"]] = d.get("posts", [])
    rad = radar(per_acc, hours=24 * 7)
    iso = (now + timedelta(hours=9)).isocalendar()
    wk = f"{iso[0]}-W{iso[1]:02d}"
    result = {"week": wk, "snapshot": snap, "age_curve": {f"{k[0]}:{k[1] * 12}h": v for k, v in curve.items()},
              "accounts": accounts, "code_effects": effects, "rising": sig, "top": top, "bottom": bottom, "radar_7d": rad,
              "coded_share": round(sum(r["id"] in codes for r in rows) / max(len(rows), 1), 3)}
    out = ROOT / "data" / "analysis" / f"{wk}.json"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(result, ensure_ascii=False, indent=1), encoding="utf-8")
    md = [f"# 벤치마크 수치표 {wk} (스냅샷 {snap}, 코딩 비율 {result['coded_share']:.0%})\n",
          "## T1 계정 기준선\n", md_table(["계정", "팔로워", "수집 게시물", "릴스 비중", "성숙 게시물 E 중앙값"],
                                       [[a, v["followers"], v["posts"], v["reels_share"], v["median_E"]] for a, v in accounts.items()]),
          "\n## T2 코드 효과(누적 26주, 성숙 게시물)\n",
          md_table(["항목", "값", "형식", "n", "계정", "shrunk", "90% CI", "2배↑ 비율", "판정"],
                   [[e["dim"], e["value"], e["surface"], e["n"], e["accounts"], e["shrunk"], e["ci90"], e["share_2x"], e["grade"]]
                    for e in effects if e["grade"] != "관찰" or e["n"] >= 8]),
          "\n## T3 훅 × 형식(shrunk, n<5는 생략)\n",
          md_table(["훅", "형식", "n", "shrunk"], [[e["value"], e["surface"], e["n"], e["shrunk"]] for e in effects if e["dim"] == "hook_cover" and e["n"] >= 5]),
          "\n## T4 이번 주 상위 10 / 하위 5\n",
          md_table(["계정", "s", "형식", "첫 줄", "표지 문구", "링크"], [[r["account"], r["s"], r["type"], r["first_line"], r["cover_text"], r["permalink"]] for r in top + bottom]),
          "\n## 급상승 신호\n", md_table(["항목", "값", "z", "2주 등장", "계정", "판정"], [[x["dim"], x["value"], x["z"], x["count_2w"], x["accounts"], x["label"]] for x in sig]),
          "\n## 주제 레이더(7일, 2개 계정 이상)\n", md_table(["단어", "계정", "우리도 다룸"], [[x["word"], ", ".join(x["accounts"]), "O" if x["covered_by_us"] else "X"] for x in rad])]
    mdp = ROOT / "playbook" / "benchmark" / f"{wk}-tables.md"
    mdp.parent.mkdir(parents=True, exist_ok=True)
    mdp.write_text("".join(md), encoding="utf-8")
    print(f"wrote {out.relative_to(ROOT)} and {mdp.relative_to(ROOT)}; coded {result['coded_share']:.0%} of {len(rows)} posts")


def uncoded(limit):
    codes = load_codes()
    snap = latest_weekly()
    todo = []
    for f in sorted(snap.glob("*.json")):
        d = json.loads(f.read_text(encoding="utf-8"))
        for p in d.get("posts", []):
            if p.get("id") not in codes:
                todo.append({"id": p.get("id"), "account": d["account"], "timestamp": p["timestamp"], "type": p.get("media_type"),
                             "surface": surface(p), "slides": p.get("slides"), "skeleton": p.get("skeleton"),
                             "visual": p.get("visual"), "permalink": p.get("permalink")})
    todo.sort(key=lambda x: x["timestamp"], reverse=True)
    for t in todo[:limit]:
        print(json.dumps(t, ensure_ascii=False))
    print(f"# {len(todo)} posts still uncoded", file=sys.stderr)


def daily_radar():
    files = sorted(f for f in (BENCH / "daily").glob("*.json") if not f.name.endswith(".radar.json"))
    if not files:
        sys.exit("no daily benchmark file yet")
    d = json.loads(files[-1].read_text(encoding="utf-8"))
    rad = radar({a: v.get("posts", []) for a, v in d.get("accounts", {}).items()}, hours=24)
    out = files[-1].with_suffix(".radar.json")
    out.write_text(json.dumps(rad, ensure_ascii=False, indent=1), encoding="utf-8")
    print(json.dumps(rad[:15], ensure_ascii=False))


if __name__ == "__main__":
    cmd = sys.argv[1] if len(sys.argv) > 1 else "weekly"
    if cmd == "weekly":
        weekly()
    elif cmd == "uncoded":
        uncoded(int(sys.argv[2]) if len(sys.argv) > 2 else 200)
    elif cmd == "radar":
        daily_radar()
