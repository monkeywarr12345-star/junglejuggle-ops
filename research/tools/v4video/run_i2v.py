"""Wan2.2 TI2V-5B image-to-video on CPU via stable-diffusion.cpp. usage: run_i2v.py <idx> <sd-cli> <outdir>"""
import sys, os, subprocess, time, json, glob
from huggingface_hub import hf_hub_download, list_repo_files
idx, sd, out = int(sys.argv[1]), sys.argv[2], sys.argv[3]
os.makedirs(out, exist_ok=True)
JOBS = {
  0: ("research/results/v3tools/imghq/img3.jpg",
      "a young Korean woman with a black bob haircut, round glasses and an orange cardigan smiles and points upward with her hand, gentle natural body motion, hair sways slightly, static camera, flat vector illustration style, clean lines"),
  1: ("research/results/v3tools/imghq/img0.jpg",
      "a young woman on a sofa looks at her phone in surprise, her eyes widen, a long paper receipt flutters, small coins float, slow camera push in, flat vector illustration style"),
}
img, prompt = JOBS[idx]
fs = list_repo_files("QuantStack/Wan2.2-TI2V-5B-GGUF")
dm_name = next((f for f in fs if f.endswith("Q4_K_M.gguf")), None) or next(f for f in fs if f.endswith(".gguf"))
dm = hf_hub_download("QuantStack/Wan2.2-TI2V-5B-GGUF", dm_name)
te = hf_hub_download("city96/umt5-xxl-encoder-gguf", "umt5-xxl-encoder-Q4_K_M.gguf")
vae = hf_hub_download("Comfy-Org/Wan_2.2_ComfyUI_Repackaged", "split_files/vae/wan2.2_vae.safetensors")
from PIL import Image
Image.open(img).convert("RGB").resize((480, 832), Image.LANCZOS).save(f"{out}/in{idx}.png")
cmd = [sd, "-M", "vid_gen", "--diffusion-model", dm, "--vae", vae, "--t5xxl", te,
       "-p", prompt, "-n", "blurry, distorted face, extra fingers, deformed hands, text, watermark, jitter, flicker",
       "-i", f"{out}/in{idx}.png", "-W", "480", "-H", "832", "--video-frames", "33", "--steps", "20",
       "--cfg-scale", "5.0", "--sampling-method", "euler", "--flow-shift", "3.0", "--seed", "11",
       "-t", str(os.cpu_count()), "-o", f"{out}/vid{idx}.avi"]
t = time.time()
r = subprocess.run(cmd, capture_output=True, text=True)
info = {"model": dm_name, "sec": round(time.time() - t), "rc": r.returncode, "cmd": " ".join(cmd[1:3]),
        "tail": (r.stdout[-2500:] + "\n---\n" + r.stderr[-2500:]), "files": sorted(os.listdir(out))}
json.dump(info, open(f"{out}/vid{idx}.json", "w"), ensure_ascii=False, indent=1)
print(json.dumps({k: info[k] for k in ("model", "sec", "rc", "files")}))
