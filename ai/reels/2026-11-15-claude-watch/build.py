"""topic-4 reel builder (claude watch skill) (v6 jungle style) (dark stage + 3D mascot): per-sentence TTS -> timeline.js with word captions + SFX.
usage: python build.py <voice spec> <outdir>   (voice spec as in ai/template/build.py)
"""
import sys, os, json, re, importlib.util
import numpy as np, soundfile as sf

HERE = os.path.dirname(os.path.abspath(__file__))
_spec = importlib.util.spec_from_file_location("v4", os.path.join(HERE, "..", "..", "template", "build.py"))
v4 = importlib.util.module_from_spec(_spec); _spec.loader.exec_module(v4)
SR = v4.SR

KEYWORD = "와치"
P0 = "클로드에 눈 달기"
P1 = "Watch 스킬"
# (scene id, spoken text, on-screen words (**x** = yellow punch box), small line, title pill, chapter chip)
LINES = [
    ("s1", "영상 못 보던 클로드한테, 눈을 달아 줬어요.", "영상 못 보던 클로드한테, **눈**을 달아 줬어요.", "Claude Code + Watch 스킬", P0, ""),
    ("s2", "원래는 유튜브 링크를 줘도, 영상은 못 본다고 해요.", "원래는 링크를 줘도 **영상은 못 봐요**.", "링크만으로는 장면을 못 읽어요", P0, ""),
    ("s3", "그래서 매번 캡처하고, 자막 복사해서 설명해 줬죠.", "그래서 매번 **캡처**하고 자막 복사해서 설명했죠.", "화면 캡처 · 자막 복사 · 상황 설명", P0, ""),
    ("s4", "근데 와치 스킬을 깔았더니, 클로드가 눈을 떴어요.", "근데 Watch 스킬 깔았더니, 클로드가 **눈을 떴어요**.", "Watch · 무료 오픈소스 스킬(MIT)", P1, ""),
    ("s5", "이제 링크만 주면, 영상을 직접 보고 답해요.", "이제 **링크만** 주면 영상을 직접 보고 답해요.", "영상 링크 · 내 영상 파일 모두 OK", P1, ""),
    ("s6", "장면은 사진으로, 말은 글자로 바꿔서 같이 읽거든요.", "장면은 사진, 말은 **글자**로 바꿔 같이 읽어요.", "장면 캡처 + 자막(없으면 받아쓰기)", P1, ""),
    ("s7", "그래서 몇 분 몇 초에 뭐가 나왔는지도 짚어 줘요.", "**몇 분 몇 초**에 뭐가 나왔는지도 짚어 줘요.", "타임스탬프로 장면 위치까지", P1, ""),
    ("s8", "클로드 코드에서, 명령어 두 줄이면 설치 끝이에요.", "**Claude Code**에서 명령어 두 줄이면 설치 끝.", "Claude Code 터미널 · 데스크톱 앱 플러그인", "설치는 2줄", ""),
    ("s9", "팔로우하고 댓글에 와치, 남기면 설치법이랑 프롬프트 전체본 디엠으로 보내드려요.", "팔로우하고 댓글에 **'와치'** 남기면 설치법·프롬프트 전체본 DM으로 보내드려요.", "설치 2줄 + 바로 쓰는 영상 프롬프트", "전체본 보내 드려요", ""),
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
    tl["open"] = round(sp["s4"][0] + 0.62 * (sp["s4"][1] - sp["s4"][0]), 3)
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
    T4 = sp["s4"][0] + 0.62 * (sp["s4"][1] - sp["s4"][0])
    tl_open = round(T4, 3)
    sfx = {
        "whoosh": [win[k][0] for k in ["s2", "s3", "s4", "s5", "s6", "s7", "s8", "s9"]],
        "pop": [0.45, W("s2", 0.3), W("s2", 0.55), W("s3", 0.15), W("s3", 0.3), W("s3", 0.45), W("s3", 0.75), tl_open, W("s5", 0.6), W("s6", 0.35), W("s6", 0.5), W("s7", 0.55), W("s9", 0.25), W("s9", 0.6)],
        "tick": [W("s5", 0.3) + 0.2 * k for k in range(4)],
        "type0": W("s8", 0.1), "type1": W("s8", 0.5), "send": W("s8", 0.52),
        "swish": [tl_open - 0.05, W("s6", 0.2)], "count0": W("s9", 0.72) - 1.0,
    }
    sf.write(os.path.join(out, "sfx.wav"), v4.synth_sfx(sfx, dur), SR)
    json.dump(tl, open(os.path.join(out, "timeline.json"), "w"), ensure_ascii=False, indent=1)
    print("dur", dur)


if __name__ == "__main__":
    main()
