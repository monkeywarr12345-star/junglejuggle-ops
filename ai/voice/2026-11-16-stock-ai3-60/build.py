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

KEYWORD = "주식"
# (id, spoken, on-screen (**x** = yellow box), small line)
LINES = [
    ("s1", "지금 이 순간에도, AI 열두 명이 남의 주식을 대신 분석하고 있어요.", "지금도 **AI 12명**이 남의 주식을 분석 중", ""),
    ("s2", "근데 아직도 혼자, 감으로 사세요?", "아직도 혼자 **감으로** 사세요?", ""),
    ("s3", "모르면 계속 손해 보는 주식 AI 도구, 딱 세 개만 알려 드릴게요. 끝까지 보세요.", "모르면 **손해** 보는 주식 AI 3개", ""),
    ("s4", "첫째, 데이 트레이더 스킬. 미국 주식 약 오천구백 개 차트에서, 돌파, 깃발, 과매도 반등 자리를 알아서 찾아 줘요.", "① 차트 **5,900개**를 알아서 훑기", ""),
    ("s5", "고른 종목은 사기 전에 남은 장을 만 번 돌려서, 목표가가 먼저 올지 손절가가 먼저 올지 비율로 보여줘요.", "사기 전에 **1만 번** 돌려 보기", ""),
    ("s6", "둘째, 트레이딩 에이전츠. 깃허브 별 십이만 개. 월가 팀처럼 분석가, 강세와 약세 리서처, 트레이더, 리스크팀, 매니저까지, AI 열두 명이 한 종목을 놓고 싸워요.", "② **AI 12명**이 한 종목 놓고 토론", ""),
    ("s7", "셋째, 트레이딩뷰 엠씨피. 추세선 그려 줘, 한 줄이면 클로드가 차트에 선과 상자를 직접 그리고, 아침엔 모닝 브리핑까지 해 줘요.", "③ 한 줄이면 **차트에 직접** 그려요", ""),
    ("s8", "이걸 모르고 감으로만 사면, 그게 진짜 손해예요.", "감으로만 사면 **진짜 손해**예요", ""),
    ("s9", "팔로우하고 댓글에 주식, 남기면 설치법 전체 보내드려요.", "팔로우하고 댓글에 **'주식'** 남기면 설치법 보내드려요.", ""),
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
    sfx = {"whoosh": [win[k][0] for k in ids[1:]], "pop": [0.45, W("s4", 0.45), W("s9", 0.35), W("s9", 0.7)],
           "tick": [], "type0": W("s7", 0.25), "type1": W("s7", 0.45), "send": W("s7", 0.5), "swish": [W("s4", 0.02), W("s6", 0.02), W("s7", 0.02)], "count0": -10}
    try:
        sf.write(os.path.join(out, "sfx.wav"), v4.synth_sfx(sfx, dur), SR)
    except Exception as e:
        print("sfx skipped", e)
    tl = {"dur": dur, "s": win, "sp": sp, "words": words, "meta": meta, "kw": KEYWORD}
    json.dump(tl, open(os.path.join(out, "timeline.json"), "w"), ensure_ascii=False, indent=1)
    print("dur", dur)


if __name__ == "__main__":
    main()
