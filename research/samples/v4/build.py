"""v4 sample builder (motion-graphics explainer): per-sentence Korean TTS -> exact timeline.js + synthesized SFX track.
usage: python build.py <voice spec> <outdir>
voice spec: "supertonic F1" | "qwen17 Sohee [instruct]" | "qwen17design <instruct>" | "chatterbox" | "none"
"""
import sys, os, json, math, re
import numpy as np, soundfile as sf

HERE = os.path.dirname(os.path.abspath(__file__))
SR = 24000
# (scene id, spoken text, caption chunks; **x** = highlighted)
LINES = [
    ("s1", "카드값 보다가, 이거 뭐지? 싶었던 적 있죠.", ["카드값 보다가", "이거 뭐지? 싶었던 적 있죠"]),
    ("s2", "카드 앱에서 이번 달 내역을 통째로 복사하고,", ["카드 앱에서 이번 달 내역", "통째로 복사하고"]),
    ("s3", "AI 채팅창에 그대로 붙여 넣어요.", ["AI 채팅창에", "그대로 붙여 넣어요"]),
    ("s4", "그리고 딱 한 줄. 매달 반복 결제만 표로 뽑아 줘.", ["그리고 딱 한 줄", "반복 결제만 표로 뽑아 줘"]),
    ("s5", "그러면 몇 초 만에 이렇게 정리돼요.", ["몇 초 만에", "이렇게 정리돼요"]),
    ("s6", "영상, 음악, 클라우드. 두 개씩 겹쳐 있었네요.", ["영상 · 음악 · 클라우드", "두 개씩 겹쳐 있었네요"]),
    ("s7", "하나씩만 남기면,", ["하나씩만 남기면"]),
    ("s8", "한 달에 이만 칠천이백 원, 일 년이면 삼십이만 원이 넘어요.", ["한 달에 2만 7,200원", "1년이면 32만 원 넘게"]),
    ("s9", "쓴 프롬프트는 캡션에 그대로 적어 뒀어요. 저장해 두세요.", ["쓴 프롬프트는 캡션에 그대로", "저장해 두세요"]),
]
LEAD, GAP, TAIL = 0.12, 0.16, 1.3


def resample(x, sr):
    if sr == SR: return x.astype(np.float32)
    n = int(len(x) * SR / sr)
    return np.interp(np.linspace(0, len(x) - 1, n), np.arange(len(x)), x).astype(np.float32)


def trim(x, thr=0.01):
    idx = np.where(np.abs(x) > thr)[0]
    if len(idx) == 0: return x
    a, b = max(0, idx[0] - int(0.03 * SR)), min(len(x), idx[-1] + int(0.06 * SR))
    return x[a:b]


def atempo(x, t):
    if abs(t - 1) < 1e-3: return x
    import subprocess, tempfile
    d = tempfile.mkdtemp(); a, b = f"{d}/a.wav", f"{d}/b.wav"
    sf.write(a, x, SR)
    subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-i", a, "-filter:a", f"atempo={t}", b], check=True)
    y, _ = sf.read(b); return y.astype(np.float32)


def make_tts(spec):
    tempo = 1.0
    if "@" in spec:
        spec, _, tp = spec.rpartition("@"); spec = spec.strip(); tempo = float(tp)
    base = _make_tts(spec)
    return lambda t: atempo(base(t), tempo)


def _make_tts(spec):
    eng, *rest = spec.split(maxsplit=1)
    arg = rest[0] if rest else ""
    if eng == "none":
        return lambda t: np.zeros(int(SR * (0.12 * len(t) / 1.0) / 1.6), np.float32)
    if eng == "supertonic":
        import inspect
        from supertonic import TTS
        tts = TTS(auto_download=True); st = tts.get_voice_style(voice_name=arg or "F1")
        sig = str(inspect.signature(tts.synthesize))
        def f(t):
            kw = {"voice_style": st}
            if "lang" in sig: kw["lang"] = "ko"
            wav, _ = tts.synthesize(t, **kw)
            w = np.asarray(wav, dtype=np.float32).reshape(-1)
            return resample(w, getattr(tts, "sample_rate", 44100))
        return f
    if eng.startswith("qwen"):
        import torch
        from qwen_tts import Qwen3TTSModel
        if eng == "qwen17design":
            m = Qwen3TTSModel.from_pretrained("Qwen/Qwen3-TTS-12Hz-1.7B-VoiceDesign", device_map="cpu", dtype=torch.float32)
            def f(t):
                w, sr = m.generate_voice_design(text=t, language="Korean", instruct=arg)
                return resample(np.asarray(w[0], np.float32), sr)
            return f
        size = "0.6B" if eng == "qwen06" else "1.7B"
        m = Qwen3TTSModel.from_pretrained(f"Qwen/Qwen3-TTS-12Hz-{size}-CustomVoice", device_map="cpu", dtype=torch.float32)
        spk, _, inst = arg.partition(" ")
        def f(t):
            kw = dict(text=t, language="Korean", speaker=(spk or "sohee").lower())
            if inst: kw["instruct"] = inst
            w, sr = m.generate_custom_voice(**kw)
            return resample(np.asarray(w[0], np.float32), sr)
        return f
    if eng == "chatterbox":
        from chatterbox.mtl_tts import ChatterboxMultilingualTTS
        m = ChatterboxMultilingualTTS.from_pretrained(device="cpu")
        def f(t):
            w = m.generate(t, language_id="ko")
            return resample(w.squeeze(0).numpy(), m.sr)
        return f
    if eng == "file":  # user's own recording per line: assets/voice/s1.wav ...
        def f(t, _c=[0]):
            _c[0] += 1
            x, sr = sf.read(os.path.join(HERE, "assets", "voice", f"s{_c[0]}.wav"))
            if x.ndim > 1: x = x.mean(1)
            return resample(x, sr)
        return f
    raise SystemExit("unknown engine " + eng)


def cap_html(s):
    return re.sub(r"\*\*(.+?)\*\*", r"<b>\1</b>", s)


def synth_sfx(cues, dur):
    n = int(SR * (dur + 1)); out = np.zeros(n, np.float32); rng = np.random.default_rng(3)
    def put(t, x, g):
        i = int(t * SR); j = min(n, i + len(x))
        if 0 <= i < n: out[i:j] += g * x[: j - i]
    def env(L, a=0.004, r=None):
        t = np.arange(L) / SR; r = r or L / SR
        return np.minimum(1, t / a) * np.exp(-t / (r / 4))
    def whoosh(L=0.38):
        m = int(L * SR); x = rng.standard_normal(m).astype(np.float32)
        y = np.zeros_like(x); c = np.linspace(0.02, 0.35, m) ** 1.5
        for k in range(1, m): y[k] = y[k - 1] + c[k] * (x[k] - y[k - 1])
        w = np.sin(np.linspace(0, math.pi, m)) ** 2
        return y * w * 0.9
    def pop(f0=900, f1=420, L=0.09):
        m = int(L * SR); t = np.arange(m) / SR; f = np.linspace(f0, f1, m)
        return np.sin(2 * math.pi * np.cumsum(f) / SR) * env(m, 0.002, L)
    def click(L=0.018):
        m = int(L * SR); return rng.standard_normal(m) * env(m, 0.0005, L) * 0.6
    def ding():
        m = int(0.9 * SR); t = np.arange(m) / SR
        return (np.sin(2 * math.pi * 1318.5 * t) + 0.6 * np.sin(2 * math.pi * 1975.5 * t)) * np.exp(-t * 5) * 0.5
    for t in cues["whoosh"]: put(t, whoosh(), 0.55)
    for t in cues["pop"]: put(t, pop(), 0.45)
    for t in cues["tick"]: put(t, pop(1500, 1200, 0.04), 0.22)
    k = cues["type0"]
    while k < cues["type1"]:
        put(k, click(), 0.35); k += 0.06 + rng.random() * 0.05
    put(cues["send"], pop(600, 300, 0.07), 0.6)
    for t in cues["swish"]: put(t, whoosh(0.22), 0.4)
    put(cues["count0"] + 1.0, ding(), 0.55)
    return out[: int(SR * dur)]


def main():
    spec, out = sys.argv[1], sys.argv[2]
    os.makedirs(out, exist_ok=True)
    tts = make_tts(spec)
    clips, s, caps, t = [], {}, [], LEAD
    for sid, text, chunks in LINES:
        w = trim(tts(text))
        d = len(w) / SR
        clips.append((t, w)); s[sid] = [t, t + d]
        tot = sum(len(re.sub(r"\*", "", c)) for c in chunks); u = t
        for c in chunks:
            cd = d * len(re.sub(r"\*", "", c)) / tot
            caps.append([round(u, 3), round(u + cd, 3), cap_html(c), sid]); u += cd
        t += d + GAP
    dur = round(t - GAP + TAIL, 2)
    # scene windows: each scene runs until the next scene's speech starts
    ids = [l[0] for l in LINES]; win = {}
    for i, sid in enumerate(ids):
        a = 0.0 if i == 0 else s[sid][0] - 0.08
        b = (s[ids[i + 1]][0] - 0.08) if i + 1 < len(ids) else dur
        win[sid] = [round(a, 3), round(b, 3)]
    sp = s
    W = lambda k: win[k]
    # cues inside scenes (absolute seconds)
    s4 = sp["s4"]; half = s4[0] + 0.42 * (s4[1] - s4[0])
    t1 = max(half + 0.8, s4[1] - 0.25)
    cue = {
        "copy": round(W("s2")[0] + 0.55 * (W("s2")[1] - W("s2")[0]), 3),
        "paste": round(W("s3")[0] + 0.45 * (W("s3")[1] - W("s3")[0]), 3),
        "type0": round(half, 3), "type1": round(t1, 3), "send": round(t1 + 0.12, 3),
        "rows": round(W("s5")[0] + 0.15, 3),
        "drop": round(W("s5")[0] + 0.62 * (W("s5")[1] - W("s5")[0]), 3),
        "pair1": round(sp["s6"][0] + 0.05, 3),
        "pair2": round(sp["s6"][0] + 0.17 * (sp["s6"][1] - sp["s6"][0]), 3),
        "pair3": round(sp["s6"][0] + 0.32 * (sp["s6"][1] - sp["s6"][0]), 3),
        "stamp": round(sp["s6"][0] + 0.55 * (sp["s6"][1] - sp["s6"][0]), 3),
        "x0": round(W("s7")[0] + 0.15, 3),
        "count0": round(W("s8")[0] + 0.1, 3),
        "year": round(sp["s8"][0] + 0.52 * (sp["s8"][1] - sp["s8"][0]), 3),
        "save": round(sp["s9"][0] + 0.62 * (sp["s9"][1] - sp["s9"][0]), 3),
    }
    tl = {"dur": dur, "s": win, "caps": caps, "cue": cue}
    open(os.path.join(HERE, "timeline.js"), "w", encoding="utf-8").write("window.TL = " + json.dumps(tl, ensure_ascii=False) + ";\n")
    html = open(os.path.join(HERE, "index.html"), encoding="utf-8").read()
    html = re.sub(r'data-duration="[^"]*"( data-width)', f'data-duration="{dur}"\\1', html, count=1)
    open(os.path.join(HERE, "index.html"), "w", encoding="utf-8").write(html)
    # narration track
    nar = np.zeros(int(SR * dur), np.float32)
    for t0, w in clips:
        i = int(t0 * SR); nar[i:i + len(w)] += w[: len(nar) - i]
    pk = np.abs(nar).max() or 1; nar = nar / pk * 0.89
    sf.write(os.path.join(out, "narration.wav"), nar, SR)
    sfxc = {
        "whoosh": [win[k][0] for k in ["s2", "s3", "s5", "s6", "s8", "s9"]],
        "pop": [0.5, 0.85, 1.2, cue["copy"], cue["paste"], cue["pair1"], cue["pair2"], cue["pair3"], cue["save"]],
        "tick": [cue["rows"] + 0.1 * k for k in range(8)],
        "swish": [cue["stamp"], cue["x0"], cue["x0"] + 0.25, cue["x0"] + 0.5, cue["year"]],
        "type0": cue["type0"], "type1": cue["type1"], "send": cue["send"], "count0": cue["count0"],
    }
    sf.write(os.path.join(out, "sfx.wav"), synth_sfx(sfxc, dur), SR)
    json.dump(tl, open(os.path.join(out, "timeline.json"), "w"), ensure_ascii=False, indent=1)
    print("dur", dur)


if __name__ == "__main__":
    main()
