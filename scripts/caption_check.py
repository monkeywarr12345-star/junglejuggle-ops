#!/usr/bin/env python3
"""Stop captions (and reel/card copy) from falling into the same pattern every time.

Usage: python scripts/caption_check.py content/<id>.caption.txt [content/<id>.json | .reel.json ...] [--replaces=<posted file name> ...]
(--replaces: leave out posts that this one is a corrected re-upload of)
Compares the new caption with the last RECENT published/queued captions and fails (exit 1) when:
  - a reaction word/emoticon (ㄷㄷ, ㅋㅋ, 실화?, 미쳤다 ...) was already used in any of them,
  - the same reaction word is used more than once in this post,
  - the hook (first line) or the comment prompt reuses the shape of a recent one (similar text),
  - the caption does not have exactly 5 hashtags including #정글저글 (user decision 2026-11-09),
  - a body line other than the fixed footer (출처/정보 제공/@junglejuggle/해시태그) is nearly identical to a recent one,
  - (클립 트랙, 2026-11-10) a reel spec has a "clip" scene but the caption lacks the line
    '📹 영상: @원작자 (플랫폼 · 원본 링크 · 등급 X)', or a grade-C clip would make this KST month's grade-C reels
    exceed CLIP_C_MONTHLY (counted from data/clips/ledger.json; Instagram drops accounts that post unoriginal
    reels 10+ times in 30 days from recommendations).
Extra files (card/reel specs) are checked for reaction words too, so on-screen copy also varies.
"""
import difflib
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
RECENT = 6
HASHTAGS = 5
REACTIONS = ["ㄷㄷ", "ㅎㄷㄷ", "ㅋㅋ", "ㅠㅠ", "ㅜㅜ", "실화?", "실화임", "미쳤", "대박", "헐", "레전드", "소름", "역대급", "충격",
             "말이 됨?", "이게 맞나", "와우", "ㄹㅇ", "찐", "킹받", "어질어질", "후덜덜", "덜덜", "눈물", "웃프", "개꿀", "띠용", "😱", "🤯", "😳"]
FOOTER = re.compile(r"(출처|정보 제공|투자 권유|@junglejuggle|^#|원문을 재작성|🎵|📷|📹)")
CLIP_C_MONTHLY = 9


def reactions_in(text):
    return [r for r in REACTIONS if r in text]


def recent_captions(exclude, skip=()):
    caps = []
    for folder in ("posted", "queue"):
        for f in (ROOT / folder).glob("*.json"):
            try:
                d = json.loads(f.read_text(encoding="utf-8"))
            except Exception:
                continue
            if d.get("caption") and f.name not in skip:
                caps.append((d.get("publish_at", ""), d["caption"], f.name))
    caps.sort(reverse=True)
    return [(c, n) for _, c, n in caps if c.strip() != exclude.strip()][:RECENT]


def benchmark_first_lines():
    """First lines of competitor posts (skeletons) from the newest weekly + daily snapshots."""
    out = []
    bench = ROOT / "data" / "benchmark"
    files = sorted(bench.glob("20??-??-??/*.json"))[-7:] + sorted(f for f in (bench / "daily").glob("*.json") if "radar" not in f.name)[-3:]
    for f in files:
        try:
            d = json.loads(f.read_text(encoding="utf-8"))
        except Exception:
            continue
        groups = [d.get("posts", [])] + [a.get("posts", []) for a in d.get("accounts", {}).values()]
        for posts in groups:
            out += [(p.get("skeleton") or {}).get("first_line", "") for p in posts]
    return [l for l in out if l]


def copied_phrase(text, others, n=6):
    """True when any n consecutive words of text also appear in one of the competitor lines."""
    words = text.split()
    grams = {" ".join(words[i:i + n]) for i in range(len(words) - n + 1)}
    return next((o for o in others if any(g in o for g in grams)), None)


def lines(text):
    return [l.strip() for l in text.splitlines() if l.strip() and not FOOTER.search(l.strip())]


def comment_prompt(text):
    return next((l for l in lines(text) if "정글러님들" in l or "댓글" in l), "")


def clip_problems(cap, spec_paths):
    """클립 트랙: on-screen credit must be repeated in the caption, and grade C stays under the monthly cap."""
    from datetime import datetime, timedelta, timezone
    out = []
    for sp in spec_paths:
        try:
            spec = json.loads(Path(sp).read_text(encoding="utf-8"))
        except Exception:
            continue
        for sc in spec.get("scenes", []):
            if sc.get("t") != "clip":
                continue
            grade = sc.get("grade")
            handle = (re.findall(r"@[\w.]+", sc.get("credit", "")) or [""])[0]
            line = next((l for l in cap.splitlines() if l.strip().startswith("📹") and "영상" in l), "")
            if not line:
                out.append("클립 장면이 있는데 캡션에 '📹 영상: @원작자 (플랫폼 · 원본 링크 · 등급 X)' 줄이 없음")
            else:
                if handle and handle not in line:
                    out.append(f"📹 줄에 화면 표기와 같은 원작자 {handle}가 없음")
                if f"등급 {grade}" not in line:
                    out.append(f"📹 줄에 '등급 {grade}' 표기가 없음")
                if "http" not in line:
                    out.append("📹 줄에 원본 링크가 없음")
            if grade == "C":
                kst = timezone(timedelta(hours=9))
                month = datetime.now(kst).strftime("%Y-%m")
                try:
                    ledger = json.loads((ROOT / "data" / "clips" / "ledger.json").read_text(encoding="utf-8"))
                except Exception:
                    ledger = []
                used = [e for e in ledger if e.get("grade") == "C" and str(e.get("posted_at", "")).startswith(month)
                        and e.get("status") != "removed" and e.get("reel") != spec.get("id")]
                if len(used) + 1 > CLIP_C_MONTHLY:
                    out.append(f"이번 달 C등급 클립 릴스가 이미 {len(used)}개 — 월 {CLIP_C_MONTHLY}개 한도 초과(B 소재로 바꾸거나 글자 릴스로)")
    return out


def main(args):
    skip = {a.split("=", 1)[1] for a in args if a.startswith("--replaces=")}
    paths = [a for a in args if not a.startswith("--")]
    cap = Path(paths[0]).read_text(encoding="utf-8")
    problems = []
    mine = reactions_in(cap)
    for r in set(mine):
        if cap.count(r) > 1:
            problems.append(f"반응어 '{r}'를 한 게시물에서 {cap.count(r)}번 씀")
    for extra in paths[1:]:
        for r in reactions_in(Path(extra).read_text(encoding="utf-8")):
            if r in mine:
                problems.append(f"반응어 '{r}'가 캡션과 화면 문구에 중복")
            mine.append(r)
    recent = recent_captions(cap, skip)
    for old, name in recent:
        used = set(reactions_in(old)) & set(mine)
        if used:
            problems.append(f"반응어 {sorted(used)}는 최근 게시물({name})에서 이미 씀")
        if lines(cap) and lines(old) and difflib.SequenceMatcher(None, lines(cap)[0], lines(old)[0]).ratio() > 0.6:
            problems.append(f"첫 줄(훅)이 최근 게시물({name})과 비슷함")
        a, b = comment_prompt(cap), comment_prompt(old)
        if a and b and difflib.SequenceMatcher(None, a, b).ratio() > 0.55:
            problems.append(f"댓글 유도 문구가 최근 게시물({name})과 비슷함: '{b[:30]}'")
        for l in lines(cap)[1:]:
            if len(l) > 12 and any(difflib.SequenceMatcher(None, l, o).ratio() > 0.85 for o in lines(old)):
                problems.append(f"문장 반복({name}): '{l[:30]}'")
    others = benchmark_first_lines()
    for l in lines(cap):
        hit = copied_phrase(l, others)
        if hit:
            problems.append(f"경쟁 계정 문장과 6어절 이상 같음(베끼기 금지): '{hit[:40]}'")
    problems += clip_problems(cap, paths[1:])
    tags = re.findall(r"(?<![\w#])#[^\s#]+", cap)
    if len(tags) != HASHTAGS:  # 2026-11-09 user decision: always 5 (Instagram's per-post cap since Dec 2025)
        problems.append(f"해시태그 {len(tags)}개 — 정확히 {HASHTAGS}개로(인물·기업 2 + 주제 2 + #정글저글, 인스타 상한 5개)")
    elif "#정글저글" not in tags:
        problems.append("해시태그에 #정글저글이 없음")
    if problems:
        print("캡션 패턴 검사 FAIL")
        for p in dict.fromkeys(problems):
            print(" -", p)
        print("사용 가능한 반응어 예시(최근에 안 쓴 것으로): " + ", ".join(r for r in REACTIONS
              if not any(r in o for o, _ in recent))[:200])
        return 1
    print("캡션 패턴 검사 PASS")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
