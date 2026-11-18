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

KEYWORD = "재판"
# (id, spoken, on-screen (**x** = yellow box), small line)
LINES = [
    ("s1", "칭찬만 하던 클로드가, 내 아이디어에 유죄를 때려요.", "칭찬만 하던 클로드가 **'유죄'** 판결", ""),
    ("s2", "클로드 열두 명을 배심원으로 앉히는 무료 스킬, 코트예요.", "클로드 **12명** 배심원 · 무료 스킬", ""),
    ("s3", "AI한테 어때, 하고 물으면 대부분 좋은 생각이래요. 그래서 아예 재판에 세우는 거예요.", "'좋은 생각이에요' 대신 **재판**", ""),
    ("s4", "첫째, 검사 클로드가 이 아이디어가 왜 망할지 공격하고,", "① 검사: **왜 망할지** 공격", ""),
    ("s5", "둘째, 변호인 클로드가 왜 될 수 있는지 반박해요.", "② 변호인: **왜 되는지** 반박", ""),
    ("s6", "셋째, 배심원 열두 명이 서로 안 보고 따로 투표해요. 회계사, 경쟁자, 은퇴한 판사까지요.", "③ 배심원 **12명** 따로 투표", ""),
    ("s7", "마지막에 판사가 판결과 함께, 표를 뒤집으려면 뭘 바꿔야 하는지 알려 줘요.", "판결 + **표 뒤집는 조건**", ""),
    ("s8", "팔로우하고 댓글에 재판, 남기면 프롬프트 전체본 보내드려요.", "팔로우하고 댓글에 **'재판'** 남기면 프롬프트 전체본 보내드려요.", ""),
]
LEAD, GAP, TAIL = 0.05, 0.12, 1.2


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
    sfx = {"whoosh": [win[k][0] for k in ("s2", "s4", "s7", "s8")], "pop": [0.45, W("s4", 0.15), W("s5", 0.15), W("s6", 0.15), W("s8", 0.3)],
           "tick": [], "type0": W("s8", 0.45), "type1": W("s8", 0.6), "send": W("s8", 0.75), "swish": [W("s3", 0.02), W("s7", 0.5)], "count0": -10}
    try:
        sf.write(os.path.join(out, "sfx.wav"), v4.synth_sfx(sfx, dur), SR)
    except Exception as e:
        print("sfx skipped", e)
    tl = {"dur": dur, "s": win, "sp": sp, "words": words, "meta": meta, "kw": KEYWORD}
    json.dump(tl, open(os.path.join(out, "timeline.json"), "w"), ensure_ascii=False, indent=1)
    print("dur", dur)


if __name__ == "__main__":
    main()
