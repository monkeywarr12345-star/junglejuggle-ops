import glob, json, re, os
import numpy as np, librosa
from faster_whisper import WhisperModel
ref = open("research/tools/v3/script_ko.txt", encoding="utf-8").read().strip()
norm = lambda s: re.sub(r"[^가-힣A-Za-z0-9]", "", s)
def cer(a, b):
    a, b = norm(a), norm(b); d = list(range(len(b) + 1))
    for i, ca in enumerate(a, 1):
        p, d[0] = d[0], i
        for j, cb in enumerate(b, 1):
            p, d[j] = d[j], min(d[j] + 1, d[j - 1] + 1, p + (ca != cb))
    return d[-1] / max(1, len(a))
m = WhisperModel("medium", device="cpu", compute_type="int8")
res = []
for f in sorted(glob.glob("research/results/v3tools/tts_*/*.mp3")):
    y, sr = librosa.load(f, sr=16000)
    segs, _ = m.transcribe(f, language="ko", beam_size=5)
    hyp = "".join(s.text for s in segs)
    f0, vf, _ = librosa.pyin(y, fmin=70, fmax=400, sr=sr)
    f0v = f0[~np.isnan(f0)]
    semis = 12 * np.log2(f0v / np.median(f0v)) if len(f0v) else np.array([0])
    res.append({"file": os.path.basename(f), "sec": round(len(y) / sr, 1), "cer": round(cer(ref, hyp), 3),
                "chars_per_sec": round(len(norm(ref)) / (len(y) / sr), 2), "pitch_range_semitones": round(float(np.percentile(semis, 95) - np.percentile(semis, 5)), 1),
                "hyp": hyp})
    print(res[-1], flush=True)
json.dump(res, open("research/results/v3tools/eval.json", "w"), ensure_ascii=False, indent=1)
