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

KEYWORD = "무료"
# (id, spoken, on-screen (**x** = yellow box), small line)
LINES = [
    ("s1", "매달 나가는 유료 구독, 무료 오픈소스로 바꾸면 영 원이에요.", "매달 나가는 유료 구독, **무료 오픈소스**로 바꾸면 **0원**이에요.", ""),
    ("s2", "코드가 공개돼서, 누구나 공짜로 쓰는 프로그램이에요.", "코드가 공개돼서, 누구나 **공짜로** 쓰는 프로그램이에요.", ""),
    ("s3", "첫째, 노션 대신 앱플로위. 문서, 할 일, 표까지 다 돼요.", "첫째, 노션 대신 AppFlowy. 문서, 할 일, **표까지** 다 돼요.", ""),
    ("s4", "둘째, 챗지피티 대신 올라마. 딥시크, 젬마 같은 AI를 내 컴퓨터에서 무료로 돌려요.", "둘째, ChatGPT 대신 Ollama. 딥시크, 젬마 같은 AI를 **내 컴퓨터**에서 무료로 돌려요.", ""),
    ("s5", "셋째, 캡컷 대신 케이덴라이브. 자동 자막까지 되는 무료 영상 편집기예요.", "셋째, 캡컷 대신 Kdenlive. **자동 자막**까지 되는 무료 영상 편집기예요.", ""),
    ("s6", "쉽게 말해, 사 먹던 밥을 공개 레시피로 집에서 해 먹는 거예요.", "쉽게 말해, 사 먹던 밥을 공개 레시피로 **집에서** 해 먹는 거예요.", ""),
    ("s7", "내 구독 목록을 클로드한테 주면, 바꿀 오픈소스를 찾아 줘요.", "내 구독 목록을 **클로드**한테 주면, 바꿀 오픈소스를 찾아 줘요.", ""),
    ("s8", "팔로우하고 댓글에 무료, 남기면 프롬프트 전체본 디엠으로 보내드려요.", "팔로우하고 댓글에 **'무료'** 남기면, 프롬프트 전체본 DM으로 보내드려요.", ""),
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
    sfx = {"whoosh": [win[k][0] for k in ("s2", "s3", "s4", "s5", "s6", "s7", "s8")],
           "pop": [0.45, 1.6, W("s2", 0.5), W("s3", 0.3), W("s4", 0.3), W("s5", 0.3), W("s6", 0.5), W("s7", 0.5), W("s8", 0.3)],
           "tick": [W("s7", 0.45) + 0.18 * k for k in range(4)], "type0": W("s8", 0.42), "type1": W("s8", 0.55), "send": W("s8", 0.7),
           "swish": [W("s3", 0.6), W("s4", 0.6), W("s5", 0.6)], "count0": -10}
    try:
        sf.write(os.path.join(out, "sfx.wav"), v4.synth_sfx(sfx, dur), SR)
    except Exception as e:
        print("sfx skipped", e)
    tl = {"dur": dur, "s": win, "sp": sp, "words": words, "meta": meta, "kw": KEYWORD}
    json.dump(tl, open(os.path.join(out, "timeline.json"), "w"), ensure_ascii=False, indent=1)
    print("dur", dur)


if __name__ == "__main__":
    main()
