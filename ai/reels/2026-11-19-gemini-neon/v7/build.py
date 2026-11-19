"""2026-11-20 reel builder (Gemini 4 Neon news, from a card-news reference) — v7 jungle style.
Captions = the spoken sentence itself, split at commas/periods; split times follow the pauses in the TTS audio.
usage: python build.py <voice spec> <outdir>   (voice spec as in ai/template/build.py)
"""
import sys, os, json, re, html, importlib.util
import numpy as np, soundfile as sf

HERE = os.path.dirname(os.path.abspath(__file__))
_spec = importlib.util.spec_from_file_location("v4", os.path.join(HERE, "..", "..", "template", "build.py"))
v4 = importlib.util.module_from_spec(_spec); _spec.loader.exec_module(v4)
SR = v4.SR

KEYWORD = "네온"
# (scene id, spoken text (TTS), on-screen text = same sentence (**x** = yellow highlight))
LINES = [
    ("s1", "구글 제미나이 포 둘째, 네온이, 큰형 카본을 이겼어요.", "구글 제미나이 4 둘째, 네온이, **큰형 카본**을 이겼어요."),
    ("s2", "깊게 생각하는 큰형 카본, 빠른 막내 하이드로젠, 그 사이 둘째가 네온이에요.", "깊게 생각하는 큰형 카본, 빠른 막내 하이드로젠, 그 사이 **둘째**가 네온이에요."),
    ("s3", "점수는요, 에이아이 종합 지수 육십일 점, 카본보다 높은 전체 삼 위예요.", "점수는요, AI 종합 지수 61점, 카본보다 높은 **전체 3위**예요."),
    ("s4", "비용은요, 같은 일을 맡기면, 일 하나당 비용이 카본보다 삼십이 퍼센트 적대요.", "비용은요, 같은 일을 맡기면, 일 하나당 비용이 카본보다 **32% 적대요**."),
    ("s5", "코딩은요, 같은 네온도 구글 안티그래비티에서 돌리면, 버그 고치기 점수가 세 배, 삼십구 퍼센트예요.", "코딩은요, 같은 네온도 구글 안티그래비티에서 돌리면, 버그 고치기 점수가 **3배**, 39%예요."),
    ("s6", "쓰는 법은, 지금 열린 프로, 울트라 구독자라면, 제미나이 앱 모델 고르기에서 네온만 누르면 끝이에요.", "쓰는 법은, 지금 열린 프로, 울트라 구독자라면, 제미나이 앱 모델 고르기에서 **네온만** 누르면 끝이에요."),
    ("s7", "팔로우하고 댓글에 네온, 남기면 프롬프트 전체본 디엠으로 보내드려요.", "팔로우하고 댓글에 **'네온'** 남기면, 프롬프트 전체본 DM으로 보내드려요."),
]
LEAD, GAP, TAIL = 0.05, 0.12, 1.2
# progress chips (top-left): scene -> active node
STEP = {"s3": 1, "s4": 2, "s5": 3, "s6": 4}


def segs(text):
    """split a sentence into caption pieces at , and . (keeps punctuation); **x** -> <b>x</b>"""
    parts = [p.strip() for p in re.split(r"(?<=[,.])\s+", text) if p.strip()]
    out = []
    for p in parts:
        h = html.escape(p)
        h = re.sub(r"\*\*(.+?)\*\*", r"<b>\1</b>", h)
        out.append((h, len(re.sub(r"\*\*", "", p))))
    return out


def pauses(w, k, expect):
    """split times inside clip w: for each expected (proportional) boundary pick the nearest pause; fall back to expectation"""
    if k <= 0: return []
    hop = int(SR * 0.01); n = len(w) // hop
    if n < 10: return list(expect)
    e = np.array([np.sqrt(np.mean(w[i * hop:(i + 1) * hop] ** 2)) for i in range(n)])
    thr = max(1e-4, 0.1 * np.percentile(e, 90))
    sil = e < thr; cand = []; i = 0
    while i < n:
        if sil[i]:
            j = i
            while j < n and sil[j]: j += 1
            if i > 5 and j < n - 5 and j - i >= 3: cand.append((i + j) / 2 * 0.01)
            i = j
        else:
            i += 1
    d = len(w) / SR; out = []; prev = 0.0
    for x in expect:
        ok = [c for c in cand if c > prev + 0.25 and abs(c - x) < 0.18 * d]
        y = min(ok, key=lambda c: abs(c - x)) if ok else max(x, prev + 0.3)
        out.append(y); prev = y
    return out


def main():
    spec, out = sys.argv[1], sys.argv[2]
    os.makedirs(out, exist_ok=True)
    tts = v4.make_tts(spec)
    clips, sp, words, t = [], {}, [], LEAD
    meta = {}
    for sid, say, show in LINES:
        w = v4.trim(tts(say)); d = len(w) / SR
        clips.append((t, w)); sp[sid] = [round(t, 3), round(t + d, 3)]
        meta[sid] = {"sub": "", "pill": "", "chip": "", "step": STEP.get(sid, 0)}
        cs = segs(show)
        tot = sum(n + 2 for _, n in cs); acc = 0; ex = []
        for _, n in cs[:-1]:
            acc += n + 2; ex.append(d * acc / tot)
        ps = pauses(w, len(cs) - 1, ex)
        bounds = [0.0] + list(ps) + [d]
        for i, (c, n) in enumerate(cs):
            words.append([round(t + bounds[i], 3), round(t + bounds[i + 1], 3), c, sid])
        t += d + GAP
    dur = round(t - GAP + TAIL, 2)
    ids = [l[0] for l in LINES]; win = {}
    for i, sid in enumerate(ids):
        a = 0.0 if i == 0 else sp[sid][0] - 0.1
        b = (sp[ids[i + 1]][0] - 0.1) if i + 1 < len(ids) else dur
        win[sid] = [round(a, 3), round(b, 3)]
    tl = {"dur": dur, "s": win, "sp": sp, "words": words, "meta": meta, "kw": KEYWORD, "cover_t": 0.8}
    open(os.path.join(HERE, "timeline.js"), "w", encoding="utf-8").write("window.TL = " + json.dumps(tl, ensure_ascii=False) + ";\n")
    page = open(os.path.join(HERE, "index.html"), encoding="utf-8").read()
    page = re.sub(r'data-duration="[^"]*"( data-width)', f'data-duration="{dur}"\\1', page, count=1)
    open(os.path.join(HERE, "index.html"), "w", encoding="utf-8").write(page)
    nar = np.zeros(int(SR * dur), np.float32)
    for t0, w in clips:
        i = int(t0 * SR); nar[i:i + len(w)] += w[: len(nar) - i]
    nar = nar / (np.abs(nar).max() or 1) * 0.89
    sf.write(os.path.join(out, "narration.wav"), nar, SR)
    W = lambda k, f: round(win[k][0] + f * (win[k][1] - win[k][0]), 3)
    sfx = {
        "whoosh": [win[k][0] for k in ["s2", "s3", "s4", "s5", "s6", "s7"]],
        "pop": [0.45, W("s2", 0.15), W("s2", 0.35), W("s2", 0.55), W("s3", 0.45), W("s4", 0.6), W("s5", 0.55),
                W("s6", 0.35), W("s7", 0.25), W("s7", 0.6)],
        "tick": [W("s3", 0.25) + 0.18 * k for k in range(4)],
        "type0": W("s7", 0.3), "type1": W("s7", 0.45), "send": W("s7", 0.62),
        "swish": [W("s4", 0.5), W("s6", 0.2)], "count0": -10,
    }
    sf.write(os.path.join(out, "sfx.wav"), v4.synth_sfx(sfx, dur), SR)
    json.dump(tl, open(os.path.join(out, "timeline.json"), "w"), ensure_ascii=False, indent=1)
    print("dur", dur)


if __name__ == "__main__":
    main()
