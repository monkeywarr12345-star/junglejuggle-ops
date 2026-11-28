import subprocess,os,glob,math
import numpy as np
from PIL import Image,ImageFilter
from scipy import ndimage
FPS=30; Z0=4.6; Z1=5.2; N=int(round(Z1*FPS))
os.makedirs('intro',exist_ok=True); os.makedirs('intro/h',exist_ok=True); os.makedirs('intro/v',exist_ok=True)
for f in glob.glob('intro/*/*.png')+glob.glob('intro/*.png'): os.remove(f)
subprocess.run(['ffmpeg','-nostdin','-loglevel','error','-y','-i','lud/H1.mp4','-vf','fps=30,scale=1080:1920','-frames:v',str(int(Z0*FPS)+1),'intro/h/%05d.png'],check=True)
subprocess.run(['ffmpeg','-nostdin','-loglevel','error','-y','-i','vtmp0.mp4','-vf','scale=in_color_matrix=bt709:in_range=tv,format=rgb24','-frames:v',str(N+2),'intro/v/%05d.png'],check=True)
hs=sorted(glob.glob('intro/h/*.png')); vs=sorted(glob.glob('intro/v/*.png'))
base=np.array(Image.open(hs[min(len(hs)-1,int(Z0*FPS))]).convert('RGB')).astype(np.float32)
g=base.mean(2); sat=base.max(2)-base.min(2)
m=(g>165)&(sat<45); m=ndimage.binary_opening(m,iterations=3)
lab,n=ndimage.label(m); best=max(range(1,n+1),key=lambda k:((lab==k)&(np.arange(1920)[:,None]>1000)).sum())
mask=ndimage.binary_dilation(lab==best,iterations=4)
maskI=Image.fromarray((mask*255).astype(np.uint8)).filter(ImageFilter.GaussianBlur(3))
M=np.array(maskI).astype(np.float32)[...,None]/255
RE=(478,1240,124,220)  # target rect inside screen (9:16)
send=1080/RE[2]; c0=np.array([540,960.]); c1=np.array([RE[0]+RE[2]/2,RE[1]+RE[3]/2])
def ease(k): return k*k*(3-2*k)
for i in range(N):
    t=i/FPS
    if t<Z0:
        Image.open(hs[min(i,len(hs)-1)]).convert('RGB').save(f'intro/{i:05d}.png'); continue
    k=ease(min(1,(t-Z0)/(Z1-Z0)))
    s=math.exp(k*math.log(send))
    a=(1-1/s)/(1-1/send)
    c=c0+(c1-c0)*a
    vw,vh=1080/s,1920/s; vx,vy=c[0]-vw/2,c[1]-vh/2
    lit=min(1,(t-Z0)/0.15)
    canvas=base*(1-M*lit)+255*M*lit
    cim=Image.fromarray(np.clip(canvas,0,255).astype(np.uint8))
    out=cim.transform((1080,1920),Image.EXTENT,(vx,vy,vx+vw,vy+vh),Image.BICUBIC)
    ours=Image.open(vs[min(i,len(vs)-1)]).convert('RGB')
    rx,ry=(RE[0]-vx)*s,(RE[1]-vy)*s; rw,rh=RE[2]*s,RE[3]*s
    if rw>=4:
        o=ours.resize((max(1,int(round(rw))),max(1,int(round(rh)))),Image.LANCZOS)
        out.paste(o,(int(round(rx)),int(round(ry))))
    out.save(f'intro/{i:05d}.png')
subprocess.run(['ffmpeg','-nostdin','-y','-loglevel','error','-i','vtmp0.mp4','-framerate','30','-i','intro/%05d.png','-filter_complex',
 "[0:v]scale=in_color_matrix=bt709:in_range=tv,format=gbrp[a];[1:v]format=gbrp[b];[a][b]overlay=0:0:eof_action=pass:format=rgb,scale=out_color_matrix=bt709:out_range=tv,format=yuv420p[v]",
 '-map','[v]','-c:v','libx264','-preset','slow','-crf','16','-pix_fmt','yuv420p','-colorspace','bt709','-color_primaries','bt709','-color_trc','bt709','-color_range','tv','vtmp.mp4'],check=True)
print('intro ok')
