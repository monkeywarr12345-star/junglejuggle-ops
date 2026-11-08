#!/usr/bin/env python3
"""Stop captions (and reel/card copy) from falling into the same pattern every time.

Usage: python scripts/caption_check.py content/<id>.caption.txt [content/<id>.json | .reel.json ...]
Compares the new caption with the last RECENT published/queued captions and fails (exit 1) when:
  - a reaction word/emoticon (ㄷㄷ, ㅋㅋ, 실화?, 미쳤다 ...) was already used in any of them,
  - the same reaction word is used more than once in this post,
  - the hook (first line) or the comment prompt reuses the shape of a recent one (similar text),
  - a body line other than the fixed footer (출처/정보 제공/@junglejuggle/해시태그) is nearly identical to a recent one.
Extra files (card/reel specs) are checked for reaction words too, so on-screen copy also varies.
"""
import difflib
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
RECENT = 6
REACTIONS = ["ㄷㄷ", "ㅎㄷㄷ", "ㅋㅋ", "ㅠㅠ", "ㅜㅜ", "실화?", "실화임", "미쳤", "대박", "헐", "레전드", "소름", "역대급", "충격",
             "말이 됨?", "이게 맞나", "와우", "ㄹㅇ", "찐", "킹받", "어질어질", "후덜덜", "덜덜", "눈물", "웃프", "개꿀", "띠용", "😱", "🤯", "😳"]
FOOTER = re.compile(r"(출처|정보 제공|투자 권유|@junglejuggle|^#|원문을 재작성|🎵|📷)")


def reactions_in(text):
    return [r for r in REACTIONS if r in text]


def recent_captions(exclude):
    caps = []
    for folder in ("posted", "queue"):
        for f in (ROOT / folder).glob("*.json"):
            try:
                d = json.loads(f.read_text(encoding="utf-8"))
            except Exception:
                continue
            if d.get("caption"):
                caps.append((d.get("publish_at", ""), d["caption"], f.name))
    caps.sort(reverse=True)
    return [(c, n) for _, c, n in caps if c.strip() != exclude.strip()][:RECENT]


def lines(text):
    return [l.strip() for l in text.splitlines() if l.strip() and not FOOTER.search(l.strip())]


def comment_prompt(text):
    return next((l for l in lines(text) if "정글러님들" in l or "댓글" in l), "")


def main(paths):
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
    recent = recent_captions(cap)
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
