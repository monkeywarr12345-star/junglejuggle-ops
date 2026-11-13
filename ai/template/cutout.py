"""Cut a flat illustration off a plain background: flood-fill from the borders with a colour tolerance,
then feather the edge. Works for 'isolated on a plain flat background' generations."""
import sys
import numpy as np
from PIL import Image, ImageFilter
from scipy import ndimage

src, dst = sys.argv[1], sys.argv[2]
im = Image.open(src).convert("RGB")
a = np.asarray(im).astype(np.int16)
h, w, _ = a.shape
border = np.concatenate([a[0], a[-1], a[:, 0], a[:, -1]])
bg = np.median(border, axis=0)
dist = np.abs(a - bg).max(axis=2)
cand = dist < 22
lab, n = ndimage.label(cand)
edge_labels = set(np.unique(np.concatenate([lab[0], lab[-1], lab[:, 0], lab[:, -1]]))) - {0}
bgmask = np.isin(lab, list(edge_labels))
fg = ~bgmask
fg = ndimage.binary_opening(fg, iterations=1)
# keep the biggest connected foreground blob(s)
fl, fn = ndimage.label(fg)
if fn > 1:
    sizes = ndimage.sum(fg, fl, range(1, fn + 1))
    keep = [i + 1 for i, s in enumerate(sizes) if s > 0.02 * sizes.max()]
    fg = np.isin(fl, keep)
alpha = Image.fromarray((fg * 255).astype(np.uint8)).filter(ImageFilter.GaussianBlur(1.2))
out = im.convert("RGBA"); out.putalpha(alpha)
bbox = out.getbbox(); out = out.crop(bbox) if bbox else out
out.save(dst)
print(dst, out.size, round(fg.mean(), 3))
