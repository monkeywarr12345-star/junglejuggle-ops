# 0~5초 훅 v3: 선수가 카메라로 달려와 바통을 렌즈로 내밀고, 바통이 화면을 다 덮는 순간 하얗게 → 흑백 화면
import numpy as np, subprocess
from PIL import Image, ImageFilter
FPS=30; D=5.0; W,H=1080,1920; T0=4.7
sm=lambda a,b,x: (lambda v: v*v*(3-2*v))(min(1,max(0,(x-a)/(b-a))))
p=subprocess.Popen(['ffmpeg','-nostdin','-y','-loglevel','error','-f','rawvideo','-pix_fmt','rgb24','-s',f'{W}x{H}','-r',str(FPS),'-i','-','-c:v','libx264','-preset','slow','-crf','14','-pix_fmt','yuv420p','lud/intro3.mp4'],stdin=subprocess.PIPE)
N=int(D*FPS)
for i in range(N):
    t=i/FPS; n=min(119,int(t*24))
    img=Image.open(f'hk3/f{n:03d}.png').convert('RGB').resize((W,H),Image.LANCZOS)
    a=np.asarray(img).astype(np.float32)
    if t>=T0:
        u=min(1,(t-T0)/(D-1/FPS-T0))
        lum=a.mean(2)
        br=np.clip((lum-140)/80,0,1); br[:int(H*0.1)]=0
        bl=np.asarray(Image.fromarray((br*255).astype(np.uint8)).filter(ImageFilter.GaussianBlur(25+70*u))).astype(np.float32)/255
        a=np.clip(a*(1+2.5*u*u),0,255)
        b=np.clip(bl*(0.7+1.3*u),0,1)[...,None]*255
        a=255-(255-a)*(255-b)/255
        g=sm(0.55,1,u); a=a+(255-a)*g
        if i==N-1: a[:]=255
    p.stdin.write(np.clip(a,0,255).astype(np.uint8).tobytes())
p.stdin.close();p.wait();print('ok')
