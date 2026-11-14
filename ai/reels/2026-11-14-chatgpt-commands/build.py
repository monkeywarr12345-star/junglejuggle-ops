"""topic-3 reel builder (v6 jungle style) (dark stage + 3D mascot): per-sentence TTS -> timeline.js with word captions + SFX.
usage: python build.py <voice spec> <outdir>   (voice spec as in ai/template/build.py)
"""
import sys, os, json, re, importlib.util
import numpy as np, soundfile as sf

HERE = os.path.dirname(os.path.abspath(__file__))
_spec = importlib.util.spec_from_file_location("v4", os.path.join(HERE, "..", "..", "template", "build.py"))
v4 = importlib.util.module_from_spec(_spec); _spec.loader.exec_module(v4)
SR = v4.SR

KEYWORD = "명령어"
P0 = "숨은 명령어 5개"
SUB0 = "ChatGPT 무료 플랜 기준 · 질문 앞에 붙이기만"
# (scene id, spoken text, on-screen words (**x** = yellow punch box), small line, title pill, chapter chip)
LINES = [
    ("s1", "챗지피티 쓰면서, 이 명령어 다섯 개 모르면 손해예요.", "ChatGPT 쓰면서, **이 명령어 5개** 모르면 손해예요.", SUB0, P0, ""),
    ("s2", "질문 앞에 한 줄만 붙여도 답이 확 달라지거든요.", "질문 앞에 **한 줄**만 붙여도 답이 확 달라져요.", SUB0, P0, ""),
    ("s3", "첫 번째, 이엘아이 파이브. 어려운 내용을 아주 쉽게 풀어 줘요.", "첫 번째, **ELI5**. 어려운 내용을 아주 쉽게 풀어 줘요.", "Explain Like I'm 5 · 다섯 살한테 설명하듯", "① 쉽게 풀기", "1|ELI5"),
    ("s4", "두 번째, 티엘디알. 긴 글을 핵심만 짧게 줄여 줘요.", "두 번째, **TL;DR**. 긴 글을 핵심만 짧게 줄여 줘요.", "Too Long; Didn't Read · 3줄로 붙이면 3줄", "② 핵심 요약", "2|TL;DR"),
    ("s5", "세 번째, 너는 면접관이야. 역할을 주면 그 사람처럼 답해요.", "세 번째, **역할 주기**. '너는 면접관이야' 하면 그 사람처럼 답해요.", "너는 ○○야 · 전문가·면접관·선생님", "③ 역할 주기", "3|역할"),
    ("s6", "네 번째, 단계별로. 복잡한 일을 순서대로 쪼개 줘요.", "네 번째, **단계별로**. 복잡한 일을 순서대로 쪼개 줘요.", "Step by step · 계획·풀이에 강해요", "④ 단계별로", "4|단계별"),
    ("s7", "다섯 번째, 먼저 질문해 줘. 필요한 걸 물어본 다음 답해요.", "다섯 번째, **먼저 질문해 줘**. 필요한 걸 물어보고 답해요.", "엉뚱한 답이 확 줄어요", "⑤ 먼저 질문받기", "5|질문 먼저"),
    ("s8", "이 다섯 개, 무료 플랜에서도 다 돼요.", "이 5개, **무료 플랜**에서도 다 돼요.", "ELI5 · TL;DR · 역할 · 단계별로 · 질문 먼저", P0, ""),
    ("s9", "팔로우하고 댓글에 명령어, 남기면 프롬프트 전체본 디엠으로 보내드려요.", "팔로우하고 댓글에 **'명령어'** 남기면 프롬프트 전체본 DM으로 보내드려요.", "명령어 5개 + 바로 쓰는 예시 프롬프트", "프롬프트 보내 드려요", ""),
]
LEAD, GAP, TAIL = 0.12, 0.18, 1.4


def chunks(text):
    """split on-screen text into 1~2 word pieces (max ~8 chars); **x** words become orange punch boxes"""
    import html
    toks, on = [], False
    for raw in text.replace(",", ",|").replace(". ", ".| ").split():
        brk = raw.endswith("|"); raw = raw.rstrip("|")
        st = raw.startswith("**") or on
        if raw.startswith("**"): raw = raw[2:]; on = True
        end = "**" in raw
        if end:
            a, _, b = raw.partition("**"); raw = a; tail = b; on = False
        else:
            tail = ""
        toks.append((raw, st, tail, brk))
    out, cur, n = [], [], 0
    for w, mark, tail, brk in toks:
        L = len(w + tail)
        if cur and n + L > 8:
            out.append(cur); cur, n = [], 0
        cur.append((w, mark, tail)); n += L
        if brk:
            out.append(cur); cur, n = [], 0
    if cur: out.append(cur)
    res = []
    for c in out:
        parts = []
        for w, mark, tail in c:
            w2 = html.escape(w.rstrip(",")); t2 = html.escape(tail.rstrip(","))
            parts.append((f"<b>{w2}</b>" if mark and w2 else w2) + t2)
        res.append((" ".join(parts).replace("</b> <b>", " "), sum(len(w + t) for w, _, t in c)))
    return res


def main():
    spec, out = sys.argv[1], sys.argv[2]
    os.makedirs(out, exist_ok=True)
    tts = v4.make_tts(spec)
    clips, sp, words, t = [], {}, [], LEAD
    meta = {}
    for sid, say, show, sub, pill, chip in LINES:
        w = v4.trim(tts(say)); d = len(w) / SR
        clips.append((t, w)); sp[sid] = [round(t, 3), round(t + d, 3)]
        meta[sid] = {"sub": sub, "pill": pill, "chip": chip}
        cs = chunks(show); tot = sum(n + 1.5 for _, n in cs); u = t
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
    tl = {"dur": dur, "s": win, "sp": sp, "words": words, "meta": meta, "kw": KEYWORD, "cover_t": 0.8}
    open(os.path.join(HERE, "timeline.js"), "w", encoding="utf-8").write("window.TL = " + json.dumps(tl, ensure_ascii=False) + ";\n")
    html = open(os.path.join(HERE, "index.html"), encoding="utf-8").read()
    html = re.sub(r'data-duration="[^"]*"( data-width)', f'data-duration="{dur}"\\1', html, count=1)
    open(os.path.join(HERE, "index.html"), "w", encoding="utf-8").write(html)
    nar = np.zeros(int(SR * dur), np.float32)
    for t0, w in clips:
        i = int(t0 * SR); nar[i:i + len(w)] += w[: len(nar) - i]
    nar = nar / (np.abs(nar).max() or 1) * 0.89
    sf.write(os.path.join(out, "narration.wav"), nar, SR)
    W = lambda k, f: round(win[k][0] + f * (win[k][1] - win[k][0]), 3)
    sfx = {
        "whoosh": [win[k][0] for k in ["s2", "s3", "s4", "s5", "s6", "s7", "s8", "s9"]],
        "pop": [0.45, W("s2", 0.3), W("s2", 0.4), W("s2", 0.5), W("s3", 0.6), W("s4", 0.6), W("s5", 0.6), W("s6", 0.5), W("s6", 0.65), W("s6", 0.8), W("s7", 0.6), W("s9", 0.25), W("s9", 0.6)],
        "tick": [W("s8", 0.1) + 0.2 * k for k in range(5)],
        "type0": W("s3", 0.12), "type1": W("s3", 0.4), "send": W("s3", 0.42),
        "swish": [W("s4", 0.45), W("s7", 0.8)], "count0": W("s9", 0.72) - 1.0,
    }
    sf.write(os.path.join(out, "sfx.wav"), v4.synth_sfx(sfx, dur), SR)
    json.dump(tl, open(os.path.join(out, "timeline.json"), "w"), ensure_ascii=False, indent=1)
    print("dur", dur)


if __name__ == "__main__":
    main()
