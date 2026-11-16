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
    ("s1", "워런 버핏 포트폴리오, 펠로시가 산 주식까지. 이제 클로드가 공짜로 다 찾아 줘요.", "버핏 포트폴리오·**펠로시 주식**까지", ""),
    ("s2", "돈 내고 리딩방 듣던 시대, 진짜 끝났어요.", "돈 내는 **리딩방** 시대 끝", ""),
    ("s3", "이름은 트레이더 스킬. 깃허브 별 천오백 개 넘는데, 무료에, 가입도, 에이피아이 키도 필요 없어요.", "트레이더 스킬 · **완전 무료**", ""),
    ("s4", "스킬 하나가 아니라, 무려 열한 개가 한 세트예요.", "스킬 **11개**가 한 세트", ""),
    ("s5", "카피캣은 버핏 같은 대가가 공시한 보유 종목을, 내가 따라 살 비율로 바꿔 줘요.", "① 대가 포트폴리오를 **내 비율로**", ""),
    ("s6", "뉴스는 내 종목 속보와 공시를 훑어서, 영향 있는 것만 골라 줘요.", "② 내 종목 **속보·공시** 감시", ""),
    ("s7", "제일 놀라운 건 펠로시 스킬. 미국 하원의원들이 신고한 주식 거래가 올라오면, 누가 뭘 샀는지 바로 정리해서 알려 줘요.", "③ **미국 의원 주식 거래** 자동 추적", ""),
    ("s8", "예산 스킬은 내 돈에 맞춰 몇 주 살지 나눠 주고, 리스크 스킬은 한도를 넘는 주문을 막아요.", "④ 예산 맞춤 · **리스크 차단**", ""),
    ("s9", "그리고 내가 승인하지 않으면, 어떤 주문도 절대 실행되지 않아요.", "**내 승인 없이는** 주문 안 나가요", ""),
    ("s10", "설치는 깃허브 링크 붙여 넣고, 스킬 설치, 한 마디면 끝이에요.", "링크 붙여 넣고 **'스킬 설치'**", ""),
    ("s11", "팔로우하고 댓글에 주식, 남기면 설치법 전체 보내드려요.", "팔로우하고 댓글에 **'주식'** 남기면 설치법 보내드려요.", ""),
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
    sfx = {"whoosh": [win[k][0] for k in ids[1:]], "pop": [0.45, W("s4", 0.45), W("s11", 0.35), W("s11", 0.7)],
           "tick": [], "type0": W("s10", 0.25), "type1": W("s10", 0.45), "send": W("s10", 0.6), "swish": [W("s5", 0.02), W("s7", 0.02), W("s9", 0.02)], "count0": -10}
    try:
        sf.write(os.path.join(out, "sfx.wav"), v4.synth_sfx(sfx, dur), SR)
    except Exception as e:
        print("sfx skipped", e)
    tl = {"dur": dur, "s": win, "sp": sp, "words": words, "meta": meta, "kw": KEYWORD}
    json.dump(tl, open(os.path.join(out, "timeline.json"), "w"), ensure_ascii=False, indent=1)
    print("dur", dur)


if __name__ == "__main__":
    main()
