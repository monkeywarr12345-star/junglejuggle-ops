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

KEYWORD = "반대"
# (id, spoken, on-screen (**x** = yellow box), small line)
LINES = [
    ("s1", "AI가 좋은 생각이에요, 라고 하면 의심부터 하세요.", "AI가 '좋은 생각이에요' 하면 **의심부터** 하세요.", "끝까지 보면 반대 프롬프트 공개"),
    ("s2", "AI는 원래 내 말에 맞장구치는 성향이 있거든요.", "AI는 원래 **맞장구**치는 성향이 있어요.", "연구자들은 '아첨 성향'이라고 불러요"),
    ("s3", "그래서 질문 끝에 이 한 줄만 붙이세요.", "질문 끝에 **이 한 줄**만 붙이세요.", "Claude · ChatGPT · Gemini 다 돼요"),
    ("s4", "반대 입장에서, 가장 약한 부분 세 가지를 짚어 줘.", "\"반대 입장에서 **약한 부분 3가지** 짚어 줘\"", "근거 + 보완책까지 같이 요청"),
    ("s5", "그러면 칭찬 대신, 진짜 허점과 보완책이 나와요.", "칭찬 대신 **진짜 허점**이 나와요.", "예) 수익 구조 · 시간 · 장비비"),
    ("s6", "더 세게 가려면, 냉정한 심사역이라고 생각하고, 를 앞에 붙이세요.", "더 세게: **'냉정한 심사역'**으로 시키기", "거절 사유 3가지 + 통과 조건"),
    ("s7", "팔로우하고 댓글에 반대, 남기면 프롬프트 전체본 보내드려요.", "팔로우하고 댓글에 **'반대'** 남기면 전체본 보내드려요.", "상황별 반대 프롬프트 5개"),
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
    sfx = {"whoosh": [win[k][0] for k in ids[1:]], "pop": [0.45, W("s4", 0.45), W("s7", 0.35), W("s7", 0.7)],
           "tick": [], "type0": W("s4", 0.05), "type1": W("s4", 0.5), "send": W("s4", 0.9), "swish": [W("s5", 0.1)], "count0": -10}
    try:
        sf.write(os.path.join(out, "sfx.wav"), v4.synth_sfx(sfx, dur), SR)
    except Exception as e:
        print("sfx skipped", e)
    tl = {"dur": dur, "s": win, "sp": sp, "words": words, "meta": meta, "kw": KEYWORD}
    json.dump(tl, open(os.path.join(out, "timeline.json"), "w"), ensure_ascii=False, indent=1)
    print("dur", dur)


if __name__ == "__main__":
    main()
