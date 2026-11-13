"""v5 sample builder (dark stage + 3D mascot): per-sentence TTS -> timeline.js with word captions + SFX.
usage: python build.py <voice spec> <outdir>   (voice spec as in ai/template/build.py)
"""
import sys, os, json, re, importlib.util
import numpy as np, soundfile as sf

HERE = os.path.dirname(os.path.abspath(__file__))
_spec = importlib.util.spec_from_file_location("v4", os.path.join(HERE, "..", "..", "template", "build.py"))
v4 = importlib.util.module_from_spec(_spec); _spec.loader.exec_module(v4)
SR = v4.SR

KEYWORD = "기능"
# (scene id, spoken text, on-screen words, small line under the words, title pill)
P0 = "클로드 숨은 기능 3가지"
# (scene id, spoken text, on-screen words (**x** = orange punch box), small line, title pill, chapter chip)
LINES = [
    ("s1", "클로드, 아직 대화만 하고 있다면 완전 손해예요.", "클로드, 아직 대화만 하고 있다면 **완전 손해**예요.", "Claude 무료 플랜 기준 · 2026년 11월", P0, ""),
    ("s2", "무료로도 되는 숨은 기능 세 개, 지금 바로 켜 보세요.", "무료로도 되는 **숨은 기능** 3개, 지금 바로 켜 보세요.", "Claude 무료 플랜 기준 · 2026년 11월", "무료로 켜는 숨은 기능 3", ""),
    ("s3", "첫 번째, 아티팩트.", "첫 번째, **아티팩트**.", "대화 옆 창에 결과물이 바로 생겨요", "① 아티팩트", ""),
    ("s4", "표나 문서를 부탁하면, 대화 옆 창에 결과물이 바로 만들어져요. 복사도 다운로드도 버튼 하나면 끝.", "표나 문서를 부탁하면, 대화 옆 창에 결과물이 **바로** 만들어져요. 복사도 다운로드도 버튼 하나면 끝.", "문서·표·간단한 앱까지 (무료 플랜 가능)", "대화 옆에 결과물이 바로", "1|아티팩트"),
    ("s5", "설정의 기능 메뉴에서, 딱 한 번만 켜 두면 돼요.", "설정의 기능 메뉴에서, 딱 **한 번만** 켜 두면 돼요.", "설정 › 기능 · 메뉴 이름은 버전마다 조금 달라요", "설정 › 기능에서 켜기", "1|아티팩트"),
    ("s6", "두 번째, 프로젝트.", "두 번째, **프로젝트**.", "2026년 3월부터 무료 플랜도 사용 가능", "② 프로젝트", ""),
    ("s7", "자료랑 대화를 한곳에 모아 두는 작업실이에요. 올해 삼월부터 무료가 됐어요.", "자료랑 대화를 한곳에 모아 두는 작업실이에요. 올해 3월부터 **무료**가 됐어요.", "파일을 올려 두면 그 프로젝트의 대화가 계속 참고해요", "자료 + 대화를 한곳에", "2|프로젝트"),
    ("s8", "세 번째, 나에 대한 설명.", "세 번째, **나에 대한 설명**.", "설정 › 내 Claude(Your Claude)", "③ 나에 대한 설명", ""),
    ("s9", "내 직업이랑 원하는 말투를 한 번 적어 두면, 모든 대화에 알아서 반영돼요.", "내 직업이랑 원하는 말투를 한 번 적어 두면, 모든 대화에 **알아서** 반영돼요.", "매번 '짧게 써 줘'라고 안 해도 돼요", "한 번 적으면 계속", "3|나에 대한 설명"),
    ("s10", "이 세 개만 켜도, 클로드가 완전히 달라져요.", "이 3개만 켜도, 클로드가 **완전히** 달라져요.", "아티팩트 · 프로젝트 · 나에 대한 설명", P0, ""),
    ("s11", "팔로우하고 댓글에 기능, 남기면 설정법 전체본 디엠으로 보내드려요.", "팔로우하고 댓글에 **'기능'** 남기면 설정법 전체본 DM으로 보내드려요.", "켜는 위치까지 캡처로 정리했어요", "설정법 보내 드려요", ""),
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
        "whoosh": [win[k][0] for k in ["s3", "s6", "s8", "s10", "s11"]],
        "pop": [0.45, W("s3", 0.2), W("s4", 0.15), W("s4", 0.45), W("s5", 0.5), W("s6", 0.2), W("s7", 0.2), W("s7", 0.35), W("s7", 0.5), W("s8", 0.2), W("s11", 0.25), W("s11", 0.6)],
        "tick": [W("s10", 0.1) + 0.25 * k for k in range(3)],
        "type0": W("s9", 0.15), "type1": W("s9", 0.55), "send": W("s9", 0.57),
        "swish": [W("s2", 0.5), W("s10", 0.6)], "count0": W("s11", 0.72) - 1.0,
    }
    sf.write(os.path.join(out, "sfx.wav"), v4.synth_sfx(sfx, dur), SR)
    json.dump(tl, open(os.path.join(out, "timeline.json"), "w"), ensure_ascii=False, indent=1)
    print("dur", dur)


if __name__ == "__main__":
    main()
