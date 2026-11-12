"""v3 sample builder: per-sentence Korean TTS -> exact timeline.js + synthesized SFX track.
usage: python build.py <voice spec> <outdir>
voice spec: "supertonic F1" | "qwen17 Sohee [instruct]" | "qwen17design <instruct>" | "chatterbox" | "none"
"""
import sys, os, json, math, re
import numpy as np, soundfile as sf

HERE = os.path.dirname(os.path.abspath(__file__))
SR = 24000
# (scene id, spoken text, caption chunks; **x** = highlighted)
LINES = [
    ("s1", "카드값 보다가, 이거 뭐지? 싶었던 적 있죠.", ["카드값 보다가", "**이거 뭐지?** 싶었던 적"]),
    ("s2", "카드 내역을 챗지피티에 그대로 붙여 넣고,", ["카드 내역을 **챗GPT**에", "그대로 붙여 넣고"]),
    ("s3", "매달 반복 결제만 표로 뽑아 달라고, 한 줄만 붙이세요.", ["**반복 결제만 표로**", "딱 한 줄만 붙이세요"]),
    ("s4", "보내면 몇 초 만에 표가 나와요.", ["몇 초 만에 **표 완성**"]),
    ("s5", "영상, 음악, 클라우드가 두 개씩 겹쳐 있네요.", ["영상·음악·클라우드", "**2개씩** 겹쳐 있네요"]),
    ("s6", "하나씩만 남기면, 한 달에 이만 칠천이백 원이 줄어요.", ["하나씩만 남기면", "한 달에 **2만 7,200원** 절약"]),
    ("s7", "프롬프트 세 개, 캡션에 그대로 적어 뒀어요.", ["프롬프트 3개", "**캡션에 그대로**"]),
]
# real screen recording (OpenScreen, 2576x1416). source times in seconds, crop = chat column.
REC = "assets/rec1.mp4"; REC_OUT = "assets/rec_cut.mp4"
REC_CROP = (1000, 100, 820, 1300)  # x, y, w, h in source px (camera coords in index.html use this crop)
REC_PROMPT, REC_SEND, REC_SEND_END, REC_ANS0, REC_TBL1, REC_DONE = 0.0, 3.3, 3.65, 9.6, 11.6, 15.0
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


CARD = (40, 470, 1000, 820)  # on-screen recording card: left, top, w, h (must match #rec in index.html)


def cam_at(cams, t):
    """camera (cx, cy, scale) in crop px at time t; smooth ease between keyframes."""
    if t <= cams[0][0]: return cams[0][1:]
    for (t0, *p0), (t1, *p1) in zip(cams, cams[1:]):
        if t <= t1:
            u = 0 if t1 <= t0 else (t - t0) / (t1 - t0)
            e = u * u * (3 - 2 * u)
            # interpolate zoom in log space so it feels even
            sc = math.exp(math.log(p0[2]) + (math.log(p1[2]) - math.log(p0[2])) * e)
            return (p0[0] + (p1[0] - p0[0]) * e, p0[1] + (p1[1] - p0[1]) * e, sc)
    return cams[-1][1:]


def to_screen(cam, x, y):
    cx, cy, sc = cam; L, T, W, H = CARD
    return (L + W / 2 + (x - cx) * sc, T + H / 2 + (y - cy) * sc)


def make_clip(segs, total, cams):
    """cut + retime + crop the screen recording, then bake the camera (zoom/pan) into a card-sized clip."""
    import subprocess
    from PIL import Image
    x, y, w, h = REC_CROP
    parts, labels = [], []
    for i, (a, b, d) in enumerate(segs):
        k = d / (b - a)
        parts.append(f"[0:v]trim=start={a}:end={b},setpts=(PTS-STARTPTS)*{k:.5f},crop={w}:{h}:{x}:{y},fps=30,setsar=1[v{i}]")
        labels.append(f"[v{i}]")
    used = sum(d for _, _, d in segs)
    fc = ";".join(parts) + ";" + "".join(labels) + f"concat=n={len(segs)}:v=1:a=0,tpad=stop_mode=clone:stop_duration={max(0.0, total - used) + 0.5:.3f}[v]"
    dec = subprocess.Popen(["ffmpeg", "-nostdin", "-loglevel", "error", "-i", os.path.join(HERE, REC), "-filter_complex", fc, "-map", "[v]",
                            "-t", f"{total:.3f}", "-f", "rawvideo", "-pix_fmt", "rgb24", "-"], stdout=subprocess.PIPE)
    _, _, W, H = CARD
    enc = subprocess.Popen(["ffmpeg", "-nostdin", "-y", "-loglevel", "error", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}", "-r", "30", "-i", "-",
                            "-c:v", "libx264", "-preset", "veryfast", "-crf", "16", "-g", "15", "-pix_fmt", "yuv420p", "-movflags", "+faststart",
                            os.path.join(HERE, REC_OUT)], stdin=subprocess.PIPE)
    n, fb = 0, w * h * 3
    while True:
        buf = dec.stdout.read(fb)
        if len(buf) < fb: break
        cx, cy, sc = cam_at(cams, n / 30)
        hw, hh = W / 2 / sc, H / 2 / sc
        cx = min(max(cx, hw), w - hw); cy = min(max(cy, hh), h - hh)
        im = Image.frombuffer("RGB", (w, h), buf, "raw", "RGB", 0, 1)
        enc.stdin.write(im.resize((W, H), Image.LANCZOS, box=(cx - hw, cy - hh, cx + hw, cy + hh)).tobytes())
        n += 1
    enc.stdin.close(); enc.wait(); dec.wait()
    print("rec clip", [(a, b, round(d, 2)) for a, b, d in segs], "frames", n, "total", round(total, 2))


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
    send = round(sp["s3"][1] + 0.05, 3)
    a0, a1 = win["s2"][0], win["s5"][1]
    s5a = win["s5"][0]
    cue = {
        "paste": round(win["s2"][0] + 0.95, 3),
        "type0": send, "type1": send, "send": send,
        "ans": round(send + (REC_SEND_END - REC_SEND), 3),
        "hl1": round(s5a + 0.6, 3),
        "hl2": round(s5a + 0.6 + 0.3 * max(0.6, sp["s5"][1] - s5a - 0.6), 3),
        "hl3": round(s5a + 0.6 + 0.6 * max(0.6, sp["s5"][1] - s5a - 0.6), 3),
        "count0": round(win["s6"][0] + 0.08, 3),
        "rec0": a0, "rec1": a1,
    }
    # piecewise retime of the recording to the narration: (src0, src1, out duration)
    segs = [
        (REC_PROMPT, REC_SEND, send - a0),                 # prompt visible until the click
        (REC_SEND, REC_SEND_END, REC_SEND_END - REC_SEND), # click + jump to the thread (1x)
        (REC_ANS0, REC_TBL1, max(0.4, s5a - 0.35 - cue["ans"])),  # thinking cut out; first table streams in
        (REC_TBL1, REC_DONE, 0.8),                         # rest of the answer, fast-forwarded, done before the highlights
    ]
    s3a, s4a = win["s3"][0], win["s4"][0]
    r = lambda t: round(t - a0, 3)
    WIDE, CAM_PROMPT, CAM_SEND, CAM_THREAD, CAM_TBL, CAM_DUP = (410, 640, 1.22), (300, 610, 1.85), (575, 630, 2.25), (410, 420, 1.22), (390, 440, 1.45), (300, 935, 1.75)
    cams = [
        (0.0, *WIDE), (0.9, *WIDE),
        (r(s3a), *CAM_PROMPT),                 # read the pasted statement
        (r(min(s3a + 0.8, send - 0.9)), *CAM_PROMPT),
        (r(min(s3a + 1.4, send - 0.3)), *CAM_SEND),  # the one-line request + send button
        (r(send + 0.12), *CAM_SEND),
        (r(cue["ans"] + 0.1), *CAM_THREAD),    # zoom out as the thread appears
        (r(s5a - 0.4), *CAM_TBL),
        (r(s5a + 0.3), *CAM_DUP),             # pan down to the overlap table
        (r(a1) + 1, *CAM_DUP),
    ]
    make_clip(segs, a1 - a0, cams)
    rip = [round(v, 1) for v in to_screen(CAM_SEND, 766, 686)]
    hl = []
    for yy in (901, 938, 975):  # overlap rows (OTT / music / cloud) in crop px
        x0, y0 = to_screen(CAM_DUP, 22, yy - 17); x1, y1 = to_screen(CAM_DUP, 798, yy + 17)
        L, T, W, H = CARD; x0 = max(x0, L + 6); x1 = min(x1, L + W - 6)
        hl.append([round(x0), round(y0), round(x1 - x0), round(y1 - y0)])
    tl = {"dur": dur, "s": win, "caps": caps, "cue": cue, "rip": rip, "hl": hl}
    open(os.path.join(HERE, "timeline.js"), "w", encoding="utf-8").write("window.TL = " + json.dumps(tl, ensure_ascii=False) + ";\n")
    html = open(os.path.join(HERE, "index.html"), encoding="utf-8").read()
    html = re.sub(r'data-duration="[^"]*"( data-width)', f'data-duration="{dur}"\\1', html, count=1)
    html = re.sub(r'(<video id="rec"[^>]*?)data-start="[^"]*" data-duration="[^"]*"', lambda m: f'{m.group(1)}data-start="{cue["rec0"]}" data-duration="{round(cue["rec1"] - cue["rec0"], 3)}"', html, count=1)
    open(os.path.join(HERE, "index.html"), "w", encoding="utf-8").write(html)
    # narration track
    nar = np.zeros(int(SR * dur), np.float32)
    for t0, w in clips:
        i = int(t0 * SR); nar[i:i + len(w)] += w[: len(nar) - i]
    pk = np.abs(nar).max() or 1; nar = nar / pk * 0.89
    sf.write(os.path.join(out, "narration.wav"), nar, SR)
    sfxc = {
        "whoosh": [win["s2"][0], cue["ans"] - 0.1, win["s5"][0], win["s6"][0], win["s7"][0]],
        "pop": [0.35, 0.75, 1.15, cue["paste"], win["s7"][0] + 0.9],
        "tick": [],
        "swish": [cue["hl1"], cue["hl2"], cue["hl3"]] + [win["s7"][0] + 0.15 + 0.18 * k for k in range(3)],
        "type0": cue["type0"], "type1": cue["type1"], "send": cue["send"], "count0": cue["count0"],
    }
    sf.write(os.path.join(out, "sfx.wav"), synth_sfx(sfxc, dur), SR)
    json.dump(tl, open(os.path.join(out, "timeline.json"), "w"), ensure_ascii=False, indent=1)
    print("dur", dur)


if __name__ == "__main__":
    main()
