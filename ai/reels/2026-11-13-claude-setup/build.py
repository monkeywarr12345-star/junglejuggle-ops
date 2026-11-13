"""topic-2 reel builder (v6 jungle style) (dark stage + 3D mascot): per-sentence TTS -> timeline.js with word captions + SFX.
usage: python build.py <voice spec> <outdir>   (voice spec as in ai/template/build.py)
"""
import sys, os, json, re, importlib.util
import numpy as np, soundfile as sf

HERE = os.path.dirname(os.path.abspath(__file__))
_spec = importlib.util.spec_from_file_location("v4", os.path.join(HERE, "..", "..", "template", "build.py"))
v4 = importlib.util.module_from_spec(_spec); _spec.loader.exec_module(v4)
SR = v4.SR

KEYWORD = "세팅"
P0 = "깔자마자 바꿀 설정 5"
SUB0 = "Claude 무료 플랜 기준 · 2026년 11월"
# (scene id, spoken text, on-screen words (**x** = yellow punch box), small line, title pill, chapter chip)
LINES = [
    ("s1", "클로드 깔았으면, 이 설정 다섯 개부터 바꾸세요.", "클로드 깔았으면, **이 설정 5개**부터 바꾸세요.", SUB0, P0, ""),
    ("s2", "그냥 두면 내 대화가 AI 학습에 쓰일 수도 있거든요.", "그냥 두면 내 대화가 **AI 학습**에 쓰일 수도 있거든요.", SUB0, P0, ""),
    ("s3", "첫 번째, 개인정보에서 AI 모델 개선을 꺼 두세요.", "첫 번째, 개인정보에서 **AI 모델 개선**을 꺼 두세요.", "설정 › 개인정보 보호 · Help improve our AI models", "① 내 대화 학습 끄기", "1|개인정보"),
    ("s4", "꺼 두면 새 대화는 학습에 안 쓰여요.", "꺼 두면 새 대화는 학습에 **안 쓰여요**.", "이미 학습에 쓰인 건 되돌려지지 않아요", "① 내 대화 학습 끄기", "1|개인정보"),
    ("s5", "두 번째, 지시사항. 내 직업이랑 원하는 말투를 한 번만 적어 두면 돼요.", "두 번째, **지시사항**. 내 직업이랑 원하는 말투를 한 번만 적어 두면 돼요.", "설정 › 내 Claude › 지시사항", "② 나를 한 번만 소개", "2|지시사항"),
    ("s6", "세 번째, 메모리. 클로드가 나에 대해 뭘 기억하는지 보고, 틀린 건 지우세요.", "세 번째, **메모리**. Claude가 나에 대해 뭘 기억하는지 보고, 틀린 건 지우세요.", "무료 플랜도 기본으로 켜져 있어요 · 설정 › 내 Claude", "③ 기억 점검하기", "3|메모리"),
    ("s7", "네 번째, 기능에서 코드 실행과 파일 생성 켜기. 표랑 문서를 파일로 바로 받아요.", "네 번째, 기능에서 **파일 생성** 켜기. 표랑 문서를 파일로 바로 받아요.", "설정 › 기능 › 코드 실행 및 파일 생성", "④ 파일로 바로 받기", "4|파일 생성"),
    ("s8", "다섯 번째, 플러스 버튼에서 웹 검색 켜기. 최신 정보로 답해 줘요.", "다섯 번째, + 버튼에서 **웹 검색** 켜기. 최신 정보로 답해 줘요.", "새 화면에선 필요할 때 알아서 검색해요", "⑤ 최신 정보로 답하기", "5|웹 검색"),
    ("s9", "이 다섯 개, 전부 무료 플랜에서 돼요.", "이 5개, 전부 **무료 플랜**에서 돼요.", "개인정보 · 지시사항 · 메모리 · 파일 생성 · 웹 검색", P0, ""),
    ("s10", "팔로우하고 댓글에 세팅, 남기면 설정 위치 전체본 디엠으로 보내드려요.", "팔로우하고 댓글에 **'세팅'** 남기면 설정 위치 전체본 DM으로 보내드려요.", "메뉴 위치 + 바로 쓰는 지시사항 문구까지", "설정법 보내 드려요", ""),
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
        "whoosh": [win[k][0] for k in ["s2", "s3", "s5", "s6", "s7", "s8", "s9", "s10"]],
        "pop": [0.45, W("s2", 0.3), W("s2", 0.4), W("s2", 0.5), W("s3", 0.75), W("s6", 0.3), W("s6", 0.45), W("s6", 0.6), W("s7", 0.55), W("s7", 0.7), W("s8", 0.35), W("s8", 0.6), W("s10", 0.25), W("s10", 0.6)],
        "tick": [W("s9", 0.1) + 0.2 * k for k in range(5)],
        "type0": W("s5", 0.3), "type1": W("s5", 0.65), "send": W("s5", 0.68),
        "swish": [W("s4", 0.1), W("s6", 0.8)], "count0": W("s10", 0.72) - 1.0,
    }
    sf.write(os.path.join(out, "sfx.wav"), v4.synth_sfx(sfx, dur), SR)
    json.dump(tl, open(os.path.join(out, "timeline.json"), "w"), ensure_ascii=False, indent=1)
    print("dur", dur)


if __name__ == "__main__":
    main()
