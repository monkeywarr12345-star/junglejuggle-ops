import sys, subprocess, json, time, os
from huggingface_hub import hf_hub_download, list_repo_files
out = sys.argv[1]; idx = int(sys.argv[2]); sd = sys.argv[3]
os.makedirs(out, exist_ok=True)
files = list_repo_files("leejet/Z-Image-Turbo-GGUF")
pick = next((f for f in ["z_image_turbo-Q4_K.gguf", "z_image_turbo-Q4_0.gguf", "z_image_turbo-Q3_K.gguf"] if f in files), None) or [f for f in files if f.endswith(".gguf")][0]
dm = hf_hub_download("leejet/Z-Image-Turbo-GGUF", pick)
llm = hf_hub_download("unsloth/Qwen3-4B-Instruct-2507-GGUF", "Qwen3-4B-Instruct-2507-Q4_K_M.gguf")
try: vae = hf_hub_download("Comfy-Org/z_image_turbo", "split_files/vae/ae.safetensors")
except Exception: vae = hf_hub_download("black-forest-labs/FLUX.1-schnell", "ae.safetensors")
STYLE = "flat vector editorial illustration, clean thin outlines, soft warm pastel palette of beige cream and orange, subtle paper grain, minimal cozy background, modern Korean webtoon style, high quality, no text, no letters"
CHAR = "a young Korean woman with a short black bob haircut and round glasses, wearing an orange knit cardigan over a white t-shirt"
P = [
 f"{CHAR}, sitting on a beige sofa holding a smartphone, wide eyes surprised expression, a very long paper receipt unrolling to the floor, small floating coins, cozy living room. {STYLE}",
 f"{CHAR}, sitting at a wooden desk typing on an open laptop, warm desk lamp, small plant, mug, side view, calm focused expression. {STYLE}",
 f"{CHAR}, standing and smiling with relief, hugging a pink piggy bank, coins and sparkles around, simple cream background. {STYLE}",
]
p = P[idx]
t = time.time()
cmd = [sd, "--diffusion-model", dm, "--vae", vae, "--llm", llm, "-p", p, "--cfg-scale", "1.0", "--steps", "8",
       "-H", "1024", "-W", "576", "--seed", "7", "-t", str(os.cpu_count()), "-o", f"{out}/img{idx}.png", "--diffusion-fa"]
r = subprocess.run(cmd, capture_output=True, text=True)
json.dump({"model": pick, "sec": round(time.time()-t), "rc": r.returncode, "tail": (r.stdout[-1500:] + r.stderr[-1500:]), "prompt": p},
          open(f"{out}/img{idx}.json", "w"), ensure_ascii=False, indent=1)
