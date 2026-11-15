"""Narration-only builder (no HyperFrames scene): per-line TTS -> narration.wav + sfx.wav + timeline.json.
Used for reels whose picture comes from outside (e.g. Ludyte clips) and is composited later.
usage: python build.py <voice spec> <outdir>"""
import sys, os, json, importlib.util
import numpy as np, soundfile as sf

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.join(HERE, "..", "..")
_t = importlib.util.spec_from_file_location("v4", os.path.join(ROOT, "template", "build.py"))
v4 = importlib.util.module_from_spec(_t); _t.loader.exec_module(v4)
_w = importlib.util.spec_from_file_location("cw", os.path.join(ROOT, "reels", "2026-11-15-claude-watch", "build.py"))
cw = importlib.util.module_from_spec(_w); _w.loader.exec_module(cw)
SR = v4.SR

KEYWORD = "와치"
# (id, spoken, on-screen (**x** = yellow box), small line)
LINES = [
    ("s1", "유튜브 링크만 주면, 클로드가 영상을 직접 봐요.", "유튜브 링크만 주면 클로드가 **영상을 직접** 봐요.", "끝까지 보면 설치 2줄 공개"),
    ("s2", "원래는 링크를 줘도 못 봤거든요.", "원래는 링크를 줘도 **못 봤거든요**.", "링크만으로는 장면을 못 읽었어요"),
    ("s3", "와치 스킬 하나 깔면, 장면은 사진으로, 말은 글자로 읽어요.", "Watch 스킬 하나면 장면은 사진, 말은 **글자**로 읽어요.", "Watch · 무료 오픈소스 스킬(MIT)"),
    ("s4", "몇 분 몇 초에 뭐가 나오는지도 짚어 줘요.", "**몇 분 몇 초**에 나오는지도 짚어 줘요.", "타임스탬프로 장면 위치까지"),
    ("s5", "클로드 코드에서 명령어 두 줄이면 끝.", "**Claude Code**에서 명령어 두 줄이면 끝.", "Claude Code 전용 · 일반 채팅창에선 안 돼요"),
    ("s6", "팔로우하고 댓글에 와치, 남기면 프롬프트 전체본 보내드려요.", "팔로우하고 댓글에 **'와치'** 남기면 전체본 보내드려요.", "설치 2줄 + 바로 쓰는 영상 프롬프트"),
]
LEAD, GAP, TAIL = 0.05, 0.12, 1.4


def main():
    spec, out = sys.argv[1], sys.argv[2]
    os.makedirs(out, exist_ok=True)
    tts = v4.make_tts(spec)
    clips, sp, words, meta, t = [], {}, [], {}, LEAD
    for sid, say, show, sub in LINES:
        w = v4.trim(tts(say)); d = len(w) / SR
        clips.append((t, w)); sp[sid] = [round(t, 3), round(t + d, 3)]; meta[sid] = {"sub": sub}
        cs = cw.chunks(show); tot = sum(n + 1.5 for _, n in cs); u = t
        for c, n in cs:
            cd = d * (n + 1.5) / tot
            words.append([round(u, 3), round(u + cd, 3), c, sid]); u += cd
        t += d + GAP
    dur = round(t - GAP + TAIL, 2)
    ids = [l[0] for l in LINES]; win = {}
    for i, sid in enumerate(ids):
        a = 0.0 if i == 0 else sp[sid][0] - 0.1
        b = (sp[ids[i + 1]][0] - 0.1) if i + 1 < len(ids) else dur
        win[sid] = [round(a, 3), round(b, 3)]
    nar = np.zeros(int(SR * dur), np.float32)
    for t0, w in clips:
        i = int(t0 * SR); nar[i:i + len(w)] += w[: len(nar) - i]
    nar = nar / (np.abs(nar).max() or 1) * 0.89
    sf.write(os.path.join(out, "narration.wav"), nar, SR)
    W = lambda k, f: round(win[k][0] + f * (win[k][1] - win[k][0]), 3)
    sfx = {"whoosh": [win[k][0] for k in ids[1:]], "pop": [0.45, W("s4", 0.45), W("s6", 0.35), W("s6", 0.7)],
           "tick": [], "type0": W("s5", 0.15), "type1": W("s5", 0.55), "send": W("s5", 0.6), "swish": [W("s3", 0.1)], "count0": -10}
    try:
        sf.write(os.path.join(out, "sfx.wav"), v4.synth_sfx(sfx, dur), SR)
    except Exception as e:
        print("sfx skipped", e)
    tl = {"dur": dur, "s": win, "sp": sp, "words": words, "meta": meta, "kw": KEYWORD}
    json.dump(tl, open(os.path.join(out, "timeline.json"), "w"), ensure_ascii=False, indent=1)
    print("dur", dur)


if __name__ == "__main__":
    main()
