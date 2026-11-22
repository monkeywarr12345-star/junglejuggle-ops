"""2026-11-23 reel builder (gemini notebook study) (v6 jungle style) (dark stage + 3D mascot): per-sentence TTS -> timeline.js with word captions + SFX.
usage: python build.py <voice spec> <outdir>   (voice spec as in ai/template/build.py)
"""
import sys, os, json, re, importlib.util
import numpy as np, soundfile as sf

HERE = os.path.dirname(os.path.abspath(__file__))
_spec = importlib.util.spec_from_file_location("v4", os.path.join(HERE, "..", "..", "template", "build.py"))
v4 = importlib.util.module_from_spec(_spec); _spec.loader.exec_module(v4)
SR = v4.SR

KEYWORD = "공부"
P0 = "제미나이 노트북"
P1 = "① 자료 넣기"
P2 = "② 퀴즈 만들기"
P3 = "③ 외우고 듣기"
# (scene id, spoken text, on-screen words (**x** = yellow punch box), small line, title pill, chapter chip)
LINES = [
    ("s1", "시험 범위 PDF 하나 올리면, 퀴즈랑 암기 카드가 공짜로 쏟아져요.", "시험 범위 PDF 하나 올리면, **퀴즈**랑 암기 카드가 공짜로 쏟아져요.", "😵 형광펜 밤샘 VS 🧠 PDF 1개 · 끝까지 보면 프롬프트 5개", P0, ""),
    ("s2", "밤새 형광펜 긋던 벼락치기, 이제 안 해도 돼요.", "밤새 형광펜 긋던 **벼락치기**, 이제 안 해도 돼요.", "😵 형광펜 밤샘 VS 🧠 제미나이 노트북", P0, ""),
    ("s3", "구글 제미나이 노트북이에요. 옛 이름은 노트북 엘엠이에요.", "구글 **제미나이 노트북**이에요. 옛 이름은 NotebookLM이에요.", "notebook.google · 구글 계정으로 무료 시작", P0, ""),
    ("s4", "첫째, 강의 PDF랑 유튜브 링크를 소스로 넣어요.", "첫째, 강의 PDF랑 **유튜브 링크**를 소스로 넣어요.", "PDF · 유튜브 · 웹사이트 · 구글 문서", P1, ""),
    ("s5", "그러면 내가 넣은 자료만 읽고, 핵심을 정리해 줘요.", "그러면 **내가 넣은 자료만** 읽고, 핵심을 정리해 줘요.", "답마다 자료 속 근거 번호가 붙어요", P1, ""),
    ("s6", "둘째, 퀴즈 버튼을 누르면 내 자료로 시험 문제를 만들어 줘요.", "둘째, **퀴즈** 버튼을 누르면, 내 자료로 시험 문제를 만들어 줘요.", "객관식 문제 자동 생성 · 화면은 예시", P2, ""),
    ("s7", "헷갈리는 건 물어보면, 자료 속 근거를 달아서 답해요.", "헷갈리는 건 물어보면, 자료 속 **근거**를 달아서 답해요.", "근거 번호를 누르면 원문 위치로 이동", P2, ""),
    ("s8", "셋째, 플래시카드로 외우고, 오디오 개요로 들으면서 복습해요.", "셋째, **플래시카드**로 외우고, 오디오 개요로 들으면서 복습해요.", "플래시카드 · 오디오 개요 · 마인드맵", P3, ""),
    ("s9", "구글 계정만 있으면 무료로 시작할 수 있어요.", "구글 계정만 있으면 **무료**로 시작해요.", "무료 사용량엔 하루 한도가 있어요", P3, ""),
    ("s10", "팔로우하고 댓글에 공부, 남기면 시험 공부 프롬프트 전체본 디엠으로 보내드려요.", "팔로우하고 댓글에 **'공부'** 남기면 공부 프롬프트 전체본 DM으로 보내드려요.", "따라 하기 3단계 + 바로 쓰는 공부 프롬프트 5개", "전체본 보내 드려요", ""),
]
LEAD, GAP, TAIL = 0.05, 0.12, 1.6


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
    tl["open"] = round(sp["s6"][0] + 0.62 * (sp["s6"][1] - sp["s6"][0]), 3)
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
        "whoosh": [win[k][0] for k in ["s2", "s3", "s4", "s5", "s6", "s7", "s8", "s9", "s10"]],
        "pop": [0.45, W("s2", 0.2), W("s2", 0.5), W("s2", 0.75), W("s3", 0.3), W("s3", 0.6), W("s4", 0.15), W("s4", 0.3), W("s4", 0.45), W("s4", 0.6),
                W("s5", 0.3), W("s5", 0.5), W("s5", 0.7), W("s6", 0.62), W("s7", 0.5), W("s8", 0.3), W("s8", 0.6), W("s9", 0.4), W("s10", 0.25), W("s10", 0.6)],
        "tick": [W("s6", 0.25) + 0.15 * k for k in range(4)],
        "type0": W("s7", 0.05), "type1": W("s7", 0.25), "send": W("s7", 0.27),
        "swish": [W("s8", 0.45), W("s2", 0.45)], "count0": W("s10", 0.72) - 1.0,
    }
    sf.write(os.path.join(out, "sfx.wav"), v4.synth_sfx(sfx, dur), SR)
    json.dump(tl, open(os.path.join(out, "timeline.json"), "w"), ensure_ascii=False, indent=1)
    print("dur", dur)


if __name__ == "__main__":
    main()
