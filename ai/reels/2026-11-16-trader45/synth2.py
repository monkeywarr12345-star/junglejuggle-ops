import numpy as np,subprocess,scipy.signal as ss
sr=48000;bpm=118;beat=60/bpm;DUR=47.0;n=int(DUR*sr);t=np.arange(n)/sr
nt=lambda m:440*2**((m-69)/12)
prog=[[57,60,64],[53,57,60],[48,52,55],[55,59,62]]  # Am F C G
roots=[45,41,48,43];bar=4*beat
rng=np.random.default_rng(3)
def lp(x,fc,o=2):
    b,a=ss.butter(o,fc/(sr/2));return ss.lfilter(b,a,x)
pulse=np.zeros(n);pad=np.zeros(n);lead=np.zeros(n);sub=np.zeros(n)
k=0;tt=0.0
while tt<DUR:
    i0=int(tt*sr);ch=prog[k%4];r=roots[k%4]
    # 16th pulse bass: root, octave pattern
    pat=[0,12,0,7,0,12,0,7,0,12,0,7,0,12,3,7]
    for j in range(16):
        s0=i0+int(j*beat/4*sr);L=int(beat/4*sr*0.9)
        if s0+L>n:break
        tl=np.arange(L)/sr;f=nt(r+pat[j]+12)
        w=(2*((tl*f)%1)-1)*np.exp(-tl*14)
        pulse[s0:s0+L]+=w*(0.55 if j%4==0 else 0.38)
    L=min(int(bar*sr)+int(0.2*sr),n-i0);tl=np.arange(L)/sr;w=np.zeros(L)
    for m in ch+[ch[0]+12]:
        for det in(-0.1,0,0.1):
            w+=2*((tl*nt(m)*2**(det/12)+rng.random())%1)-1
    env=np.minimum(1,tl/0.6)*np.minimum(1,(L/sr-tl)/0.3)
    pad[i0:i0+L]+=w*env/12
    sub[i0:i0+L]+=np.sin(2*np.pi*nt(r-12)*tl)*env*0.6
    # bell lead on beats 1 and 3 every other bar
    if k%2==1:
        for j,m in enumerate([ch[2]+24,ch[1]+24,ch[0]+24]):
            s0=i0+int(j*beat*1.333*sr);Lp=int(1.2*sr)
            if s0+Lp>n:break
            tp=np.arange(Lp)/sr;f=nt(m)
            lead[s0:s0+Lp]+=(np.sin(2*np.pi*f*tp)+0.4*np.sin(2*np.pi*3.01*f*tp)*np.exp(-tp*6))*np.exp(-tp*3)*0.25
    k+=1;tt+=bar
pulse=lp(pulse,900,2);pad=lp(pad,1600,2)
# filter swell on pad every 4 bars
ph=(t%(4*bar))/(4*bar);pad*=0.55+0.45*ph
# reverb-ish: simple multi-tap
def verb(x):
    y=x.copy()
    for d,g in [(0.031,.35),(0.047,.3),(0.071,.25),(0.113,.2),(0.167,.15),(0.233,.1)]:
        D=int(d*sr);y[D:]+=x[:-D]*g
    return y
lead=verb(lead);pad=verb(pad)*0.8
# riser noise at end of every 4 bars
noise=lp(rng.standard_normal(n),5000,1)*0.0
for b4 in np.arange(4*bar,DUR,4*bar):
    s=int((b4-beat*2)*sr);e=int(b4*sr)
    if e>n:break
    noise[s:e]+=lp(rng.standard_normal(e-s),3000,1)*np.linspace(0,0.12,e-s)
mix=pulse*0.8+pad*0.9+sub*0.6+lead*0.9+noise
L=lead*0.9;mixL=mix+np.roll(L,int(0.011*sr))*0.15;mixR=mix+np.roll(pad,int(0.013*sr))*0.1
y=np.stack([mixL,mixR],1);y[:int(0.4*sr)]*=np.linspace(0,1,int(0.4*sr))[:,None];y/=np.abs(y).max()*1.12
subprocess.run(['ffmpeg','-y','-v','error','-f','f32le','-ar',str(sr),'-ac','2','-i','-','pulse.wav'],input=y.astype(np.float32).tobytes());print('ok')
