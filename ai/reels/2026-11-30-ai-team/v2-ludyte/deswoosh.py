import numpy as np
from PIL import Image
from scipy import ndimage
import sys
R0,R1=int(sys.argv[1]),int(sys.argv[2]); Y0,Y1,X0,X1=[int(v) for v in sys.argv[3:7]]
for n in range(R0,R1):
    a=np.asarray(Image.open(f"hk3/f{n:03d}.png").convert('RGB')).astype(np.float32)
    lum=a.mean(2); mx=a.max(2); mn=a.min(2)
    reg=np.zeros_like(lum,bool); reg[Y0:Y1,X0:X1]=True
    br=(lum>85)&((mx-mn)<60)&reg
    dark=ndimage.uniform_filter((lum<45).astype(np.float32),35)
    DT=float(sys.argv[7]) if len(sys.argv)>7 else 0.5
    cand=br&(dark>DT)
    lab,k=ndimage.label(ndimage.binary_dilation(cand,iterations=2))
    m=np.zeros_like(cand)
    for i in range(1,k+1):
        s=lab==i
        if s.sum()<3000: m|=s
    out=a
    if m.any():
        mm=ndimage.binary_dilation(m,iterations=6)
        soft=ndimage.gaussian_filter(mm.astype(np.float32),2.5)[...,None]
        darkpix=a[(lum<45)&reg]; fill=np.median(darkpix,0) if len(darkpix) else np.array([15,15,15])
        out=a*(1-soft)+fill*soft
    Image.fromarray(np.clip(out,0,255).astype(np.uint8)).save(f'hk3/f{n:03d}.png')
