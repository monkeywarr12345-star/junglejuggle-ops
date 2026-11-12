import sys, time, json, os, inspect
engine, out = sys.argv[1], sys.argv[2]
os.makedirs(out, exist_ok=True)
TEXT = open(os.path.join(os.path.dirname(__file__), "script_ko.txt"), encoding="utf-8").read().strip()
log = {"engine": engine, "runs": []}
def rec(name, fn):
    t = time.time()
    try:
        path = fn()
        log["runs"].append({"name": name, "sec": round(time.time()-t, 1), "file": path})
    except Exception as e:
        log["runs"].append({"name": name, "sec": round(time.time()-t, 1), "error": repr(e)[:800]})
    json.dump(log, open(f"{out}/log.json", "w"), ensure_ascii=False, indent=1)
    print(log["runs"][-1], flush=True)

if engine.startswith("qwen"):
    import torch, soundfile as sf
    from qwen_tts import Qwen3TTSModel
    size = "0.6B" if engine == "qwen06" else "1.7B"
    m = Qwen3TTSModel.from_pretrained(f"Qwen/Qwen3-TTS-12Hz-{size}-CustomVoice", device_map="cpu", dtype=torch.float32)
    spk = m.get_supported_speakers(); log["speakers"] = list(spk)
    ko = [s for s in spk if "sohee" in s.lower()] or list(spk)[:1]
    for inst in ["", "밝고 경쾌한 숏폼 내레이션, 조금 빠르게"]:
        def f(inst=inst):
            kw = dict(text=TEXT, language="Korean", speaker=ko[0])
            if inst: kw["instruct"] = inst
            w, sr = m.generate_custom_voice(**kw)
            p = f"{out}/{engine}_{ko[0]}_{'inst' if inst else 'plain'}.wav"; sf.write(p, w[0], sr); return p
        rec(f"{ko[0]} {inst or 'plain'}", f)
    if engine == "qwen17":
        del m
        d = Qwen3TTSModel.from_pretrained("Qwen/Qwen3-TTS-12Hz-1.7B-VoiceDesign", device_map="cpu", dtype=torch.float32)
        for tag, inst in [("design_f", "20대 후반 한국 여성, 또렷하고 밝은 목소리, 유튜브 숏폼 정보 채널 내레이션, 빠른 템포"),
                          ("design_m", "20대 후반 한국 남성, 차분하지만 친근한 목소리, 정보 채널 내레이션, 약간 빠른 템포")]:
            def g(tag=tag, inst=inst):
                w, sr = d.generate_voice_design(text=TEXT, language="Korean", instruct=inst)
                p = f"{out}/{engine}_{tag}.wav"; sf.write(p, w[0], sr); return p
            rec(tag, g)
elif engine == "supertonic":
    from supertonic import TTS
    tts = TTS(auto_download=True)
    sig = str(inspect.signature(tts.synthesize)); log["sig"] = sig
    for v in ["F1", "F2", "F3", "M1", "M2"]:
        def f(v=v):
            st = tts.get_voice_style(voice_name=v)
            kw = {"voice_style": st}
            if "lang" in sig: kw["lang"] = "ko"
            if "language" in sig: kw["language"] = "ko"
            wav, dur = tts.synthesize(TEXT, **kw)
            p = f"{out}/supertonic_{v}.wav"; tts.save_audio(wav, p); return p
        rec(v, f)
elif engine == "chatterbox":
    import torchaudio as ta
    from chatterbox.mtl_tts import ChatterboxMultilingualTTS
    m = ChatterboxMultilingualTTS.from_pretrained(device="cpu")
    def f():
        w = m.generate(TEXT, language_id="ko"); p = f"{out}/chatterbox_ko.wav"; ta.save(p, w, m.sr); return p
    rec("ko default", f)
