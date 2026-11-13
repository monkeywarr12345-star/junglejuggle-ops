"""Synthesize one line with several voices so we can compare (output: media/ai/voicetest/<name>.wav + list.txt)."""
import sys, os, importlib.util, traceback
import numpy as np, soundfile as sf
HERE = os.path.dirname(os.path.abspath(__file__))
spec = importlib.util.spec_from_file_location("v4", os.path.join(HERE, "..", "template", "build.py"))
v4 = importlib.util.module_from_spec(spec); spec.loader.exec_module(v4)
LINE = sys.argv[1]; OUT = sys.argv[2]; os.makedirs(OUT, exist_ok=True)
voices = [l.strip() for l in open(sys.argv[3], encoding="utf-8") if l.strip() and not l.startswith("#")]
with open(os.path.join(OUT, "list.txt"), "w", encoding="utf-8") as lst:
    for i, v in enumerate(voices):
        name = f"v{i+1}"
        try:
            w = v4.trim(v4.make_tts(v)(LINE))
            sf.write(os.path.join(OUT, name + ".wav"), w / (np.abs(w).max() or 1) * 0.89, v4.SR)
            lst.write(f"{name}\t{v}\t{len(w)/v4.SR:.2f}s\n"); print("ok", name, v, flush=True)
        except Exception as e:
            lst.write(f"{name}\t{v}\tFAILED {type(e).__name__}: {e}\n"); traceback.print_exc()
