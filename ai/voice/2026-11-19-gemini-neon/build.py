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

KEYWORD = "네온"
# (id, spoken, on-screen (**x** = yellow box), small line)
LINES = [
    ("s1", "구글 제미나이 포 둘째, 네온이, 큰형 카본을 이겼어요.", "구글 제미나이 4 둘째, 네온이, **큰형 카본**을 이겼어요.", ""),
    ("s2", "깊게 생각하는 큰형 카본, 빠른 막내 하이드로젠, 그 사이 둘째가 네온이에요.", "깊게 생각하는 큰형 카본, 빠른 막내 하이드로젠, 그 사이 **둘째**가 네온이에요.", ""),
    ("s3", "점수는요, 에이아이 종합 지수 육십일 점, 카본보다 높은 전체 삼 위예요.", "점수는요, AI 종합 지수 61점, 카본보다 높은 **전체 3위**예요.", ""),
    ("s4", "비용은요, 같은 일을 맡기면, 일 하나당 비용이 카본보다 삼십이 퍼센트 적대요.", "비용은요, 같은 일을 맡기면, 일 하나당 비용이 카본보다 **32% 적대요**.", ""),
    ("s5", "코딩은요, 같은 네온도 구글 안티그래비티에서 돌리면, 버그 고치기 점수가 세 배, 삼십구 퍼센트예요.", "코딩은요, 같은 네온도 구글 안티그래비티에서 돌리면, 버그 고치기 점수가 **3배**, 39%예요.", ""),
    ("s6", "쓰는 법은, 지금 열린 프로, 울트라 구독자라면, 제미나이 앱 모델 고르기에서 네온만 누르면 끝이에요.", "쓰는 법은, 지금 열린 프로, 울트라 구독자라면, 제미나이 앱 모델 고르기에서 **네온만** 누르면 끝이에요.", ""),
    ("s7", "팔로우하고 댓글에 네온, 남기면 프롬프트 전체본 디엠으로 보내드려요.", "팔로우하고 댓글에 **'네온'** 남기면, 프롬프트 전체본 DM으로 보내드려요.", ""),
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
    sfx = {"whoosh": [win[k][0] for k in ("s2", "s3", "s4", "s5", "s6", "s7")],
           "pop": [0.45, W("s2", 0.2), W("s2", 0.45), W("s2", 0.7), W("s3", 0.45), W("s4", 0.6), W("s5", 0.55), W("s6", 0.5), W("s7", 0.3)],
           "tick": [W("s3", 0.3) + 0.18 * k for k in range(4)], "type0": W("s7", 0.42), "type1": W("s7", 0.55), "send": W("s7", 0.7),
           "swish": [W("s4", 0.5), W("s6", 0.2)], "count0": -10}
    try:
        sf.write(os.path.join(out, "sfx.wav"), v4.synth_sfx(sfx, dur), SR)
    except Exception as e:
        print("sfx skipped", e)
    tl = {"dur": dur, "s": win, "sp": sp, "words": words, "meta": meta, "kw": KEYWORD}
    json.dump(tl, open(os.path.join(out, "timeline.json"), "w"), ensure_ascii=False, indent=1)
    print("dur", dur)


if __name__ == "__main__":
    main()
