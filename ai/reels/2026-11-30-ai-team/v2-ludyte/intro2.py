# 0~5초 훅: 계주 영상 → 바통으로 줌인, 바통이 하얗게 화면을 다 덮는 순간 흑백 화면으로
import numpy as np, subprocess, math
from PIL import Image, ImageFilter
FPS=30; D=5.0; T1=4.25; SRC_FPS=24; S_AT_T1=86/24
W,H=1080,1920
def src_time(t):
    return t*(S_AT_T1/T1) if t<=T1 else S_AT_T1
def frame(s):
    n=min(119,int(round(s*SRC_FPS)));return n,Image.open(f'hk/f{n:03d}.png').convert('RGB')
# 바통 추적: 밝고 채도 낮은 화소를 이전 위치 근처에서 찾음
track={};c=(158,545)
for n in range(84,100):
    a=np.asarray(Image.open(f'hk/f{n:03d}.png').convert('RGB')).astype(int)
    mx=a.max(2);mn=a.min(2);m=(mx>175)&((mx-mn)<40)
    yy,xx=np.mgrid[0:a.shape[0],0:a.shape[1]];m&=((xx-c[0])**2+(yy-c[1])**2)<90**2
    ys,xs=np.nonzero(m)
    if len(xs)>40: c=(float(np.median(xs)),float(np.median(ys)))
    track[n]=c
print({k:(int(v[0]),int(v[1])) for k,v in track.items()})
ZMAX=24.0
p=subprocess.Popen(['ffmpeg','-nostdin','-y','-loglevel','error','-f','rawvideo','-pix_fmt','rgb24','-s',f'{W}x{H}','-r',str(FPS),'-i','-','-c:v','libx264','-preset','slow','-crf','14','-pix_fmt','yuv420p','lud/intro2.mp4'],stdin=subprocess.PIPE)
N=int(D*FPS)
for i in range(N):
    t=i/FPS; s=src_time(t); n,img=frame(s)
    sw,sh=img.size
    if t<T1:
        out=img.resize((W,H),Image.LANCZOS)
    else:
        u=min(1.0,(t-T1)/(D-T1-1/FPS))
        bx,by=151.,608.
        z=math.exp((u**1.8)*math.log(ZMAX)); e=1-(1-min(1,u*1.6))**3
        cx=378+(bx-378)*e; cy=672+(by-672)*e
        vw,vh=sw/z,sh/z
        x0=min(max(cx-vw/2,0),sw-vw); y0=min(max(cy-vh/2,0),sh-vh)
        yy,xx=np.mgrid[0:sh,0:sw].astype(np.float32)
        P0=np.array([171.,518.]);P1=np.array([131.,698.]);dv=P1-P0;L2=(dv**2).sum()
        tt=np.clip(((xx-P0[0])*dv[0]+(yy-P0[1])*dv[1])/L2,0,1)
        dist=np.sqrt((xx-P0[0]-tt*dv[0])**2+(yy-P0[1]-tt*dv[1])**2)
        ms=(np.clip((19-dist)/2.5,0,1)*255).astype(np.uint8)
        msk=Image.fromarray(ms)
        box=(int(x0*4),int(y0*4),int((x0+vw)*4),int((y0+vh)*4))
        crop=img.resize((sw*4,sh*4),Image.BICUBIC).crop(box).resize((W,H),Image.BICUBIC)
        mc=msk.resize((sw*4,sh*4),Image.BILINEAR).crop(box).resize((W,H),Image.BILINEAR).filter(ImageFilter.GaussianBlur(3+45*u*u))
        a=np.asarray(crop).astype(np.float32); m=np.asarray(mc).astype(np.float32)/255
        sm=lambda a_,b_,x: min(1,max(0,(x-a_)/(b_-a_)))**2*(3-2*min(1,max(0,(x-a_)/(b_-a_))))
        wl=sm(0.35,0.85,u); g=sm(0.82,1.0,u)
        k=np.clip(np.clip(m*1.6,0,1)*wl+g,0,1)[...,None]
        a=a+(255-a)*k
        if i==N-1: a[:]=255
        out=Image.fromarray(np.clip(a,0,255).astype(np.uint8))
    p.stdin.write(np.asarray(out,dtype=np.uint8).tobytes())
p.stdin.close();p.wait();print('ok')
