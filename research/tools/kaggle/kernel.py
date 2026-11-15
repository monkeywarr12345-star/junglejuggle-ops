"""Kaggle GPU kernel (round 3): Wan2.2 TI2V-5B image-to-video via stable-diffusion.cpp (CUDA).
Round 3 tests: (1) prebuilt binary from private dataset sdcpp-cuda13-sm75 (skip the 40 min build),
(2) Turbo 4-step finetune (hum-ma/Wan2.2-TI2V-5B-Turbo-GGUF, Apache-2.0) vs the 30-step base,
(3) calmer prompt for the sofa shot (receipt popped up in round 2).
Run interactively on Kaggle (batch queue stalled) via a loader cell that exec()s this file at a pinned commit."""
import os, subprocess, time, json, sys, shutil, glob
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

# ---- 1. binary: prebuilt dataset first, else build (and save the build so it can be uploaded later)
def find_sd(root):
    return next((p for p in (f"{root}/sd-cli", f"{root}/sd") if os.path.exists(p)), None)

def works(sd):
    r = sh(f'LD_LIBRARY_PATH="{os.path.dirname(sd)}:$LD_LIBRARY_PATH" "{sd}" --help')
    return r.returncode == 0, (r.stdout + r.stderr)[-600:]

t = time.time(); sd = None; how = None; info = ""
tars = glob.glob("/kaggle/input/**/sd_bin.tar.gz", recursive=True)
clis = glob.glob("/kaggle/input/**/sd-cli", recursive=True)   # Kaggle auto-extracts uploaded archives
if tars or clis:
    if clis:   # input is read-only and loses +x: copy the folder out
        sh(f"mkdir -p {T}/pre/bin && cp -r {os.path.dirname(clis[0])}/. {T}/pre/bin/ && chmod +x {T}/pre/bin/*")
    else:
        sh(f"mkdir -p {T}/pre && tar xzf {tars[0]} -C {T}/pre")
    cand = find_sd(f"{T}/pre/bin")
    if cand:
        ok, info = works(cand)
        if ok:
            sd, how = cand, "prebuilt"
if not sd:
    libcuda = next((f"{d}/libcuda.so" for d in ("/usr/local/nvidia/lib64", "/usr/local/cuda/lib64/stubs",
                    "/usr/lib/x86_64-linux-gnu") if os.path.exists(f"{d}/libcuda.so")), "")
    drv = f"-DCUDA_cuda_driver_LIBRARY={libcuda}" if libcuda else ""
    if not find_sd(f"{T}/sd/build/bin"):
        if not os.path.exists(f"{T}/sd"):
            sh(f"git clone -q --recursive https://github.com/leejet/stable-diffusion.cpp {T}/sd && cd {T}/sd && "
               f"git checkout -q 5dcfa79 && git submodule update -q --init --recursive")
        sh(f"cd {T}/sd && rm -rf build && cmake -B build -DCMAKE_BUILD_TYPE=Release -DSD_CUDA=ON "
           f"-DCMAKE_CUDA_ARCHITECTURES={cap} {drv} > {T}/cmake.log 2>&1 && "
           f"cmake --build build -j{os.cpu_count()} --config Release > {T}/build.log 2>&1")
    sd = find_sd(f"{T}/sd/build/bin"); how = "built"
    if sd:
        sh(f"cd {T}/sd/build && mkdir -p /tmp/pk/bin && cp bin/* /tmp/pk/bin/ && find . -name '*.so*' -exec cp {{}} /tmp/pk/bin/ \\; "
           f"&& tar czf {W}/sd_bin.tar.gz -C /tmp/pk bin")
note(step="binary", how=how, sec=round(time.time() - t), ok=bool(sd), prebuilt_found=bool(tars or clis), info=info[-300:])
if not sd:
    sys.exit(1)
os.environ["LD_LIBRARY_PATH"] = os.path.dirname(sd) + ":" + os.environ.get("LD_LIBRARY_PATH", "")

ff = shutil.which("ffmpeg")
from huggingface_hub import hf_hub_download, list_repo_files
import urllib.request
from PIL import Image

BASE = "https://raw.githubusercontent.com/monkeywarr12345-star/junglejuggle-ops/research/ai-tools-2026-11/research/results/v3tools/imghq/"
IMG = {0: "img3.jpg", 1: "img0.jpg"}
P = {
    "p0": "a young Korean woman with a black bob haircut, round glasses and an orange cardigan smiles and points upward with her hand, gentle natural body motion, hair sways slightly, static camera, flat vector illustration style, clean lines",
    "p1": "a young woman on a sofa looks at her phone in surprise, her eyes widen, a long paper receipt flutters, small coins float, slow camera push in, flat vector illustration style",
    # calmer v2: the receipt stays on her lap and only curls, coins rise slowly, one continuous motion
    "p1v2": "a young woman sitting on a sofa looks at her phone, her eyes slowly widen in surprise and her mouth opens, the long paper receipt stays draped over her lap and its end curls gently, a few small gold coins rise slowly beside her, smooth continuous motion, static camera, flat vector illustration style, clean lines",
}
NEG = "blurry, distorted face, extra fingers, deformed hands, text, watermark, jitter, flicker"
NEG2 = NEG + ", sudden movement, objects popping in, teleporting, morphing, flying paper, scribbles on paper"
for i, name in IMG.items():
    urllib.request.urlretrieve(BASE + name, f"{T}/src{i}.jpg")

REPOS = {"base": "QuantStack/Wan2.2-TI2V-5B-GGUF", "turbo": "hum-ma/Wan2.2-TI2V-5B-Turbo-GGUF"}
_files = {}
def dm(model, q):
    repo = REPOS[model]
    _files.setdefault(repo, list_repo_files(repo))
    return hf_hub_download(repo, next(f for f in _files[repo] if f.endswith(q + ".gguf")))
te = hf_hub_download("city96/umt5-xxl-encoder-gguf", "umt5-xxl-encoder-Q8_0.gguf")
vae = hf_hub_download("Comfy-Org/Wan_2.2_ComfyUI_Repackaged", "split_files/vae/wan2.2_vae.safetensors")

# (tag, img, prompt, neg, model, steps, cfg, shift, seed). All 704x1280, 81 frames (5 s @16fps), Q8_0.
RUNS = [
    ("turbo_p0",    0, "p0",   NEG,  "turbo", 4,  1.0, 5.0, 11),
    ("turbo_p1",    1, "p1",   NEG,  "turbo", 4,  1.0, 5.0, 11),
    ("turbo_p1v2",  1, "p1v2", NEG2, "turbo", 4,  1.0, 5.0, 11),
    ("turbo_p1v2s", 1, "p1v2", NEG2, "turbo", 4,  1.0, 5.0, 22),
    ("turbo8_p1v2", 1, "p1v2", NEG2, "turbo", 8,  1.0, 5.0, 11),
    ("base_p1v2",   1, "p1v2", NEG2, "base",  30, 5.0, 3.0, 11),   # prompt effect alone, ~40 min: last
]
w, h, nf = 704, 1280, 81
for j in IMG:
    Image.open(f"{T}/src{j}.jpg").convert("RGB").resize((w, h), Image.LANCZOS).save(f"{T}/in{j}.png")
for tag, j, pk, neg, model, steps, cfg, shift, seed in RUNS:
    try:
        cmd = [sd, "-M", "vid_gen", "--diffusion-model", dm(model, "Q8_0"), "--vae", vae, "--t5xxl", te,
               "-p", P[pk], "-n", neg, "-i", f"{T}/in{j}.png", "-W", str(w), "-H", str(h), "--video-frames", str(nf),
               "--steps", str(steps), "--cfg-scale", str(cfg), "--sampling-method", "euler", "--flow-shift", str(shift),
               "--seed", str(seed), "--diffusion-fa", "--vae-tiling", "-o", f"{T}/{tag}.avi"]
        t = time.time()
        r = subprocess.run(cmd, capture_output=True, text=True, timeout=3 * 3600)
        sec = round(time.time() - t)
        out = r.stdout + r.stderr
        mp4 = None
        if ff and os.path.exists(f"{T}/{tag}.avi"):
            mp4 = f"{W}/{tag}.mp4"
            sh(f'"{ff}" -nostdin -y -loglevel error -i "{T}/{tag}.avi" -c:v libx264 -crf 18 -pix_fmt yuv420p "{mp4}"')
        note(step="gen", tag=tag, img=j, prompt=pk, model=model, steps=steps, cfg=cfg, shift=shift, seed=seed,
             sec=sec, rc=r.returncode, mp4=bool(mp4 and os.path.exists(mp4)), tail=out[-1200:])
    except Exception as e:
        note(step="gen", tag=tag, error=repr(e)[:800])
note(step="done")
