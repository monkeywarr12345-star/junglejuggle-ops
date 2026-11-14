"""Kaggle GPU kernel: Wan2.2 TI2V-5B image-to-video via stable-diffusion.cpp (CUDA).
Same inputs/prompts as research/tools/v4video/run_i2v.py (CPU test) so the two can be compared.
Pushed and collected by .github/workflows/research-kaggle.yml. Outputs land in /kaggle/working.""" (rev2)
import os, subprocess, time, json, sys, shutil
W, T = "/kaggle/working", "/tmp/jj"
os.makedirs(T, exist_ok=True)
os.environ["HF_HOME"] = "/tmp/hf"
LOG = []

def sh(c, timeout=None):
    print("$", c[:200], flush=True)
    return subprocess.run(c, shell=True, capture_output=True, text=True, timeout=timeout)

def note(**d):
    LOG.append(d)
    json.dump(LOG, open(f"{W}/status.json", "w"), ensure_ascii=False, indent=1)
    print(json.dumps(d, ensure_ascii=False)[:600], flush=True)

gpu = sh("nvidia-smi --query-gpu=name,memory.total,compute_cap --format=csv,noheader").stdout.strip().splitlines()
note(step="gpu", gpu=gpu, cpus=os.cpu_count())
cap = (gpu[0].split(",")[-1].strip().replace(".", "") if gpu else "") or "75"

t = time.time()
r = sh(f"git clone -q --recursive --depth 1 https://github.com/leejet/stable-diffusion.cpp {T}/sd && cd {T}/sd && "
       f"cmake -B build -DCMAKE_BUILD_TYPE=Release -DSD_CUDA=ON -DCMAKE_CUDA_ARCHITECTURES={cap} > {T}/cmake.log 2>&1 && "
       f"cmake --build build -j{os.cpu_count()} --config Release > {T}/build.log 2>&1; tail -c 1500 {T}/cmake.log {T}/build.log")
sd = next((p for p in (f"{T}/sd/build/bin/sd-cli", f"{T}/sd/build/bin/sd") if os.path.exists(p)), None)
note(step="build", sec=round(time.time() - t), ok=bool(sd), tail=(r.stdout + r.stderr)[-1500:])
if not sd:
    sys.exit(1)

ff = shutil.which("ffmpeg")
if not ff:
    sh("pip install -q imageio-ffmpeg")
    try:
        import imageio_ffmpeg
        ff = imageio_ffmpeg.get_ffmpeg_exe()
    except Exception:
        ff = None

from huggingface_hub import hf_hub_download, list_repo_files
import urllib.request
from PIL import Image

BASE = "https://raw.githubusercontent.com/monkeywarr12345-star/junglejuggle-ops/research/ai-tools-2026-11/research/results/v3tools/imghq/"
JOBS = {
    0: ("img3.jpg", "a young Korean woman with a black bob haircut, round glasses and an orange cardigan smiles and points upward with her hand, gentle natural body motion, hair sways slightly, static camera, flat vector illustration style, clean lines"),
    1: ("img0.jpg", "a young woman on a sofa looks at her phone in surprise, her eyes widen, a long paper receipt flutters, small coins float, slow camera push in, flat vector illustration style"),
}
NEG = "blurry, distorted face, extra fingers, deformed hands, text, watermark, jitter, flicker"
for i, (name, _) in JOBS.items():
    urllib.request.urlretrieve(BASE + name, f"{T}/src{i}.jpg")

dm_files = list_repo_files("QuantStack/Wan2.2-TI2V-5B-GGUF")
te_files = list_repo_files("city96/umt5-xxl-encoder-gguf")
def dm(q): return hf_hub_download("QuantStack/Wan2.2-TI2V-5B-GGUF", next(f for f in dm_files if f.endswith(q + ".gguf")))
def te(q): return hf_hub_download("city96/umt5-xxl-encoder-gguf", next(f for f in te_files if f.endswith(q + ".gguf")))
vae = hf_hub_download("Comfy-Org/Wan_2.2_ComfyUI_Repackaged", "split_files/vae/wan2.2_vae.safetensors")

# (tag, job, quant, W, H, frames, steps). First pair = exact CPU-test settings (speed comparison); second = quality try.
RUNS = [("q4_480p", 0, "Q4_K_M", 480, 832, 33, 20), ("q4_480p", 1, "Q4_K_M", 480, 832, 33, 20),
        ("q8_720p", 0, "Q8_0", 704, 1280, 81, 30), ("q8_720p", 1, "Q8_0", 704, 1280, 81, 30)]
for tag, j, q, w, h, nf, steps in RUNS:
    try:
        inp = f"{T}/in{j}_{w}.png"
        Image.open(f"{T}/src{j}.jpg").convert("RGB").resize((w, h), Image.LANCZOS).save(inp)
        base = [sd, "-M", "vid_gen", "--diffusion-model", dm(q), "--vae", vae, "--t5xxl", te(q),
                "-p", JOBS[j][1], "-n", NEG, "-i", inp, "-W", str(w), "-H", str(h), "--video-frames", str(nf),
                "--steps", str(steps), "--cfg-scale", "5.0", "--sampling-method", "euler", "--flow-shift", "3.0",
                "--seed", "11", "-o", f"{T}/{tag}_{j}.avi"]
        extra = ["--diffusion-fa"] + (["--vae-tiling"] if w > 480 else [])
        t = time.time()
        r = subprocess.run(base + extra, capture_output=True, text=True, timeout=4 * 3600)
        out = r.stdout + r.stderr
        if r.returncode != 0 and ("unknown" in out.lower() or "invalid" in out.lower()):
            t = time.time()
            r = subprocess.run(base, capture_output=True, text=True, timeout=4 * 3600)
            out = r.stdout + r.stderr
        sec = round(time.time() - t)
        made = [f for f in os.listdir(T) if f.startswith(f"{tag}_{j}")]
        mp4 = None
        if ff and made:
            src = f"{T}/{sorted(made)[0]}"
            mp4 = f"{W}/{tag}_{j}.mp4"
            sh(f'"{ff}" -nostdin -y -loglevel error -i "{src}" -c:v libx264 -crf 18 -pix_fmt yuv420p "{mp4}"')
        note(step="gen", tag=tag, job=j, quant=q, size=f"{w}x{h}", frames=nf, steps=steps, sec=sec,
             rc=r.returncode, files=made, mp4=bool(mp4 and os.path.exists(mp4)), tail=out[-1500:])
    except Exception as e:
        note(step="gen", tag=tag, job=j, error=repr(e)[:800])
note(step="done")
