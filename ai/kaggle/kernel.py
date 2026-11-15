"""jungle.gcc Kaggle GPU tools (T4): 1) Real-ESRGAN upscale of the Ludyte clips -> 1080x1920,
2) faster-whisper large-v3 check of the reel narration against the script, 3) heavier Korean TTS candidates
scored by the same whisper. Inputs are pulled from the public ops repo; everything lands in /kaggle/working."""
import os, subprocess, json, time, re, difflib, urllib.request, glob, sys, traceback
W, T = "/kaggle/working", "/tmp/jj"
os.makedirs(T, exist_ok=True)
os.environ.setdefault("HF_HOME", "/tmp/hf")
RAW = "https://raw.githubusercontent.com/monkeywarr12345-star/junglejuggle-ops/main/"
REEL = "media/ai/2026-11-15-claude-watch/"
LOG = []
STEPS = [s.strip() for s in os.environ.get("JJ_STEPS", "tts").split(",")]  # upscale done 11-15 14:39
try:
    STEPS = [s.strip() for s in open(f"{T}/steps.txt").read().split(",")]
except Exception:
    pass


def sh(c, timeout=None):
    print("$", c[:240], flush=True)
    r = subprocess.run(c, shell=True, capture_output=True, text=True, timeout=timeout)
    if r.returncode:
        print((r.stdout + r.stderr)[-1500:], flush=True)
    return r


def note(**d):
    LOG.append(d)
    json.dump(LOG, open(f"{W}/status.json", "w"), ensure_ascii=False, indent=1)
    print(json.dumps(d, ensure_ascii=False)[:800], flush=True)


def get(rel, dst):
    if not os.path.exists(dst):
        urllib.request.urlretrieve(RAW + rel, dst)
    return dst


note(step="gpu", gpu=sh("nvidia-smi --query-gpu=name,memory.total,compute_cap --format=csv,noheader").stdout.strip().splitlines(),
     cpus=os.cpu_count(), steps=STEPS)
FF = "ffmpeg"
if sh("ffmpeg -version").returncode:
    sh("pip install -q imageio-ffmpeg")
    import imageio_ffmpeg
    FF = imageio_ffmpeg.get_ffmpeg_exe()

# the 9 spoken lines of the 11-15 claude-watch reel (ai/reels/2026-11-15-claude-watch/build.py)
LINES = [
    "영상 못 보던 클로드한테, 눈을 달아 줬어요.",
    "원래는 유튜브 링크를 줘도, 영상은 못 본다고 해요.",
    "그래서 매번 캡처하고, 자막 복사해서 설명해 줬죠.",
    "근데 와치 스킬을 깔았더니, 클로드가 눈을 떴어요.",
    "이제 링크만 주면, 영상을 직접 보고 답해요.",
    "장면은 사진으로, 말은 글자로 바꿔서 같이 읽거든요.",
    "그래서 몇 분 몇 초에 뭐가 나왔는지도 짚어 줘요.",
    "클로드 코드에서, 명령어 두 줄이면 설치 끝이에요.",
    "팔로우하고 댓글에 와치, 남기면 설치법이랑 프롬프트 전체본 디엠으로 보내드려요.",
]
norm = lambda s: re.sub(r"[^가-힣A-Za-z0-9]", "", s)


def cer(ref, hyp):
    a, b = norm(ref), norm(hyp)
    d = list(range(len(b) + 1))
    for i, ca in enumerate(a, 1):
        p, d[0] = d[0], i
        for j, cb in enumerate(b, 1):
            p, d[j] = d[j], min(d[j] + 1, d[j - 1] + 1, p + (ca != cb))
    return round(d[-1] / max(1, len(a)), 3)


def diffs(ref, hyp):
    a, b = norm(ref), norm(hyp)
    out = []
    for op, i1, i2, j1, j2 in difflib.SequenceMatcher(None, a, b, autojunk=False).get_opcodes():
        if op != "equal":
            out.append({"ref": a[max(0, i1 - 3):i2 + 3], "heard": b[max(0, j1 - 3):j2 + 3], "op": op})
    return out


# ------------------------------------------------------------------ 1. upscale
def upscale():
    import numpy as np, torch
    sh("pip install -q spandrel")
    from spandrel import ModelLoader
    wpath = f"{T}/RealESRGAN_x2plus.pth"
    if not os.path.exists(wpath):
        urllib.request.urlretrieve("https://github.com/xinntao/Real-ESRGAN/releases/download/v0.2.1/RealESRGAN_x2plus.pth", wpath)
    desc = ModelLoader().load_from_file(wpath)
    model = desc.model.cuda().eval().half()
    S = desc.scale

    @torch.inference_mode()
    def run(img):  # HxWx3 uint8 -> (H*S)x(W*S)x3 uint8, tiled with overlap
        x = torch.from_numpy(img).cuda().permute(2, 0, 1)[None].half() / 255.0
        _, _, H, Wd = x.shape
        tile, pad = 448, 16
        out = torch.zeros((1, 3, H * S, Wd * S), device="cuda", dtype=torch.half)
        for y0 in range(0, H, tile):
            for x0 in range(0, Wd, tile):
                y1, x1 = min(y0 + tile, H), min(x0 + tile, Wd)
                ya, xa, yb, xb = max(0, y0 - pad), max(0, x0 - pad), min(H, y1 + pad), min(Wd, x1 + pad)
                o = model(x[:, :, ya:yb, xa:xb])
                out[:, :, y0 * S:y1 * S, x0 * S:x1 * S] = o[:, :, (y0 - ya) * S:(y0 - ya + y1 - y0) * S, (x0 - xa) * S:(x0 - xa + x1 - x0) * S]
        return (out[0].clamp(0, 1) * 255).round().byte().permute(1, 2, 0).cpu().numpy()

    for name in ["cut1", "cutA", "cutB"]:
        t0 = time.time()
        src = get(REEL + f"ludyte_src/{name}.mp4", f"{T}/{name}.mp4")
        w, h, fr = 756, 1344, "24"  # all Ludyte 768p 9:16 outputs
        dec = subprocess.Popen([FF, "-v", "error", "-i", src, "-f", "rawvideo", "-pix_fmt", "rgb24", "-"], stdout=subprocess.PIPE)
        enc = subprocess.Popen([FF, "-v", "error", "-y", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{w * S}x{h * S}", "-r", fr, "-i", "-",
                                "-i", src, "-map", "0:v", "-map", "1:a?", "-vf", "scale=1080:1920:flags=lanczos",
                                "-c:v", "libx264", "-preset", "slow", "-crf", "14", "-pix_fmt", "yuv420p", "-c:a", "copy",
                                f"{W}/{name}_up.mp4"], stdin=subprocess.PIPE)
        n = 0
        while True:
            buf = dec.stdout.read(w * h * 3)
            if len(buf) < w * h * 3:
                break
            enc.stdin.write(run(np.frombuffer(buf, np.uint8).reshape(h, w, 3)).tobytes())
            n += 1
        enc.stdin.close(); enc.wait(); dec.wait()
        note(step="upscale", clip=name, frames=n, sec=round(time.time() - t0), model="RealESRGAN_x2plus", out=f"{name}_up.mp4")
    del model
    torch.cuda.empty_cache()


# ------------------------------------------------------------------ 2/3. whisper + tts
_wm = []


def whisper():
    if not _wm:
        sh("pip install -q -U faster-whisper av")
        import ctypes, site
        for pat in ["nvidia/cublas/lib/libcublas*.so*", "nvidia/cudnn/lib/libcudnn*.so*"]:
            for sp in site.getsitepackages():
                for lib in sorted(glob.glob(os.path.join(sp, pat))):
                    try:
                        ctypes.CDLL(lib, mode=ctypes.RTLD_GLOBAL)
                    except OSError:
                        pass
        from faster_whisper import WhisperModel
        try:
            m = WhisperModel("large-v3", device="cuda", compute_type="float16")
            import numpy as np
            list(m.transcribe(np.zeros(16000, np.float32), language="ko")[0])
            note(step="whisper_load", device="cuda")
        except Exception as e:
            note(step="whisper_load", device="cpu", why=repr(e)[:300])
            m = WhisperModel("large-v3", device="cpu", compute_type="int8")
        _wm.append(m)
    return _wm[0]


def transcribe(path, words=False):
    import numpy as np, soundfile as sf
    sh(f"{FF} -v error -y -i {path} -ac 1 -ar 16000 {T}/_w16.wav")
    audio, _ = sf.read(f"{T}/_w16.wav", dtype="float32")
    segs, _ = whisper().transcribe(audio, language="ko", beam_size=5, word_timestamps=words, vad_filter=False)
    segs = list(segs)
    return segs, "".join(s.text for s in segs).strip()


def check_reel():
    t0 = time.time()
    reel = get(REEL + "reel_ludyte_nomusic.mp4", f"{T}/reel.mp4")
    sh(f"{FF} -v error -y -i {reel} -vn -ac 1 -ar 16000 {T}/reel.wav")
    segs, hyp = transcribe(f"{T}/reel.wav", words=True)
    ref = " ".join(LINES)
    words = [[round(w.start, 2), round(w.end, 2), w.word, round(w.probability, 2)] for s in segs for w in (s.words or [])]
    low = [w for w in words if w[3] < 0.6]
    res = {"cer_total": cer(ref, hyp), "heard": hyp, "diffs": diffs(ref, hyp), "low_confidence_words": low,
           "segments": [[round(s.start, 2), round(s.end, 2), s.text.strip()] for s in segs], "sec": round(time.time() - t0)}
    json.dump(res, open(f"{W}/whisper_reel.json", "w"), ensure_ascii=False, indent=1)
    note(step="whisper_reel", cer=res["cer_total"], ndiff=len(res["diffs"]), nlow=len(low), sec=res["sec"])


def tts():
    import numpy as np, soundfile as sf, torch
    SR = 24000

    def rs(x, sr):
        x = np.asarray(x, np.float32).reshape(-1)
        if sr == SR:
            return x
        import scipy.signal as ss
        return ss.resample_poly(x, SR, sr).astype(np.float32)

    def score(tag, fn):
        t0 = time.time()
        try:
            parts, per = [], []
            for i, line in enumerate(LINES):
                w = fn(line)
                p = f"{T}/{tag}_{i}.wav"; sf.write(p, w, SR)
                _, hyp = transcribe(p)
                per.append({"line": i + 1, "cer": cer(line, hyp), "heard": hyp, "sec": round(len(w) / SR, 2)})
                parts += [w, np.zeros(int(SR * 0.12), np.float32)]
            full = np.concatenate(parts)
            full = full / (np.abs(full).max() or 1) * 0.89
            sf.write(f"{T}/{tag}.wav", full, SR)
            sh(f"{FF} -v error -y -i {T}/{tag}.wav -c:a libmp3lame -b:a 128k {W}/tts_{tag}.mp3")
            tot = sum(len(norm(l)) for l in LINES)
            note(step="tts", tag=tag, ok=True, cer_mean=round(sum(p["cer"] for p in per) / len(per), 3),
                 sec_total=round(len(full) / SR, 1), chars_per_sec=round(tot / (len(full) / SR), 2), gen_sec=round(time.time() - t0), lines=per)
        except Exception as e:
            note(step="tts", tag=tag, ok=False, err=repr(e)[:600], tb=traceback.format_exc()[-1200:])

    # current voice (baseline): Supertonic M1 at 1.3x speed (pitch kept) - what the reel uses now
    try:
        sh("pip install -q supertonic")
        import inspect
        from supertonic import TTS
        st_tts = TTS(auto_download=True)
        sty = st_tts.get_voice_style(voice_name="M1")
        sig = str(inspect.signature(st_tts.synthesize))
        sr0 = getattr(st_tts, "sample_rate", 44100)

        def sup(t):
            kw = {"voice_style": sty}
            if "lang" in sig: kw["lang"] = "ko"
            if "speed" in sig: kw["speed"] = 1.3
            wav, _ = st_tts.synthesize(t, **kw)
            x = rs(wav, sr0)
            if "speed" not in sig:
                sf.write(f"{T}/_s.wav", x, SR)
                sh(f"{FF} -v error -y -i {T}/_s.wav -filter:a atempo=1.3 {T}/_s13.wav")
                x, _ = sf.read(f"{T}/_s13.wav", dtype="float32")
            return x
        score("supertonic_M1_x1.3", sup)
        # keyword pronunciation check: which spelling does whisper hear as the on-screen keyword?
        kw = []
        for v in ["와치", "워치", "와-치", "Watch"]:
            line = f"팔로우하고 댓글에 {v}, 남기면 프롬프트 전체본 보내드려요."
            p = f"{T}/kw_{len(kw)}.wav"; sf.write(p, sup(line), SR)
            sh(f"{FF} -v error -y -i {p} -c:a libmp3lame -b:a 128k {W}/kw_{len(kw)}.mp3")
            _, hyp = transcribe(p); kw.append({"spelling": v, "heard": hyp, "file": f"kw_{len(kw)}.mp3"})
        note(step="keyword_pronunciation", results=kw)
    except Exception as e:
        note(step="tts", tag="supertonic_M1_x1.3", ok=False, err=repr(e)[:600])

    sh("pip install -q -U qwen-tts")
    sh('pip install -q -U "huggingface_hub>=0.34,<1.0" "transformers<5"')
    try:
        from qwen_tts import Qwen3TTSModel
        dt = torch.float32  # T4 has no bf16; fp32 avoids fp16 NaNs
        d = Qwen3TTSModel.from_pretrained("Qwen/Qwen3-TTS-12Hz-1.7B-VoiceDesign", device_map="cuda", dtype=dt)
        inst = "20대 후반 한국 남성, 밝고 친근하고 또렷한 목소리, 인스타 릴스 AI 꿀팁 채널 내레이션, 빠르고 경쾌한 템포, 해요체"

        def qd(t):
            w, sr = d.generate_voice_design(text=t, language="Korean", instruct=inst)
            return rs(w[0], sr)
        score("qwen17_design_male", qd)
        del d; torch.cuda.empty_cache()
    except Exception as e:
        note(step="tts", tag="qwen17_design_male", ok=False, err=repr(e)[:600], tb=traceback.format_exc()[-1200:])

    try:  # clone the current Supertonic M1 narration so the channel voice stays the same, but with a bigger model
        from qwen_tts import Qwen3TTSModel
        reel = get(REEL + "reel_ludyte_nomusic.mp4", f"{T}/reel.mp4")
        sh(f"{FF} -v error -y -ss 2.15 -t 2.45 -i {reel} -vn -ac 1 -ar 24000 {T}/ref.wav")  # line 2 has no sfx under it
        b = Qwen3TTSModel.from_pretrained("Qwen/Qwen3-TTS-12Hz-1.7B-Base", device_map="cuda", dtype=torch.float32)
        fn = getattr(b, "generate_voice_clone")
        import inspect; note(step="qwen_clone_sig", sig=str(inspect.signature(fn)))

        def qc(t):
            w, sr = fn(text=t, language="Korean", ref_audio=f"{T}/ref.wav", ref_text=LINES[1])
            return rs(w[0], sr)
        score("qwen17_clone_current", qc)
        del b; torch.cuda.empty_cache()
    except Exception as e:
        note(step="tts", tag="qwen17_clone_current", ok=False, err=repr(e)[:600], tb=traceback.format_exc()[-1200:])


for name, fn in [("upscale", upscale), ("whisper", check_reel), ("tts", tts)]:
    if name in STEPS:
        try:
            fn()
        except Exception as e:
            note(step=name, ok=False, err=repr(e)[:800], tb=traceback.format_exc()[-1500:])
note(step="done")
