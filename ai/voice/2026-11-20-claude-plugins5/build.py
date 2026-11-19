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

KEYWORD = "장착"
# (id, spoken, on-screen (**x** = yellow box), small line)
LINES = [
    ("s1", "클로드 코드에 이 다섯 개만 깔면, 완전히 딴 물건이 돼요. 전부 무료로 깔려요.", "클로드 코드에 이 **5개**만 깔면, 완전히 딴 물건이 돼요. 전부 **무료**로 깔려요.", ""),
    ("s2", "첫째, 클로드 멤. 지난 작업을 기억해 뒀다가, 다음 대화에 알아서 넣어 줘요.", "첫째, 클로드 멤. 지난 작업을 **기억**해 뒀다가, 다음 대화에 알아서 넣어 줘요.", ""),
    ("s3", "둘째, 프리 엘엘엠 에이피아이. 무료 AI 천삼백여 개를 묶어서, 한도가 차면 다음 모델로 넘겨요.", "둘째, 프리 LLM API. 무료 AI **1,300여 개**를 묶어서, 한도가 차면 다음 모델로 넘겨요.", ""),
    ("s4", "셋째, 앤트로픽 공식 클로드 코드 셋업. 내 코드를 훑고, 딱 맞는 도구를 골라 줘요.", "셋째, **앤트로픽 공식** 클로드 코드 셋업. 내 코드를 훑고, 딱 맞는 도구를 골라 줘요.", ""),
    ("s5", "넷째, 구글이 만든 엘리펀트 골드피시. 계획은 코끼리처럼, 검토는 금붕어처럼 해요.", "넷째, **구글**이 만든 엘리펀트 골드피시. 계획은 코끼리처럼, 검토는 금붕어처럼 해요.", ""),
    ("s6", "다섯째, 이십일 에스티 엠씨피. 만 개 넘는 UI 부품을 검색해서 꺼내 써요.", "다섯째, 21st MCP. **1만 개** 넘는 UI 부품을 검색해서 꺼내 써요.", ""),
    ("s7", "팔로우하고 댓글에 장착, 남기면 프롬프트 전체본 디엠으로 보내드려요.", "팔로우하고 댓글에 **'장착'** 남기면, 프롬프트 전체본 DM으로 보내드려요.", ""),
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
           "tick": [W("s3", 0.45) + 0.18 * k for k in range(4)], "type0": W("s7", 0.42), "type1": W("s7", 0.55), "send": W("s7", 0.7),
           "swish": [W("s5", 0.5), W("s6", 0.4)], "count0": -10}
    try:
        sf.write(os.path.join(out, "sfx.wav"), v4.synth_sfx(sfx, dur), SR)
    except Exception as e:
        print("sfx skipped", e)
    tl = {"dur": dur, "s": win, "sp": sp, "words": words, "meta": meta, "kw": KEYWORD}
    json.dump(tl, open(os.path.join(out, "timeline.json"), "w"), ensure_ascii=False, indent=1)
    print("dur", dur)


if __name__ == "__main__":
    main()
