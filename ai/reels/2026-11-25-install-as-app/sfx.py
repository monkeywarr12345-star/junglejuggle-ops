import json,numpy as np,wave
T=json.load(open('ov/tl.json'));SR=48000;D=T['dur'];EV=T['ev']
rng=np.random.default_rng(5);y=np.zeros(int(SR*(D+1)))
def add(t,s,g=1):
    i=max(0,int(t*SR));n=min(len(s),len(y)-i);y[i:i+n]+=s[:n]*g
def lp(x,k0,k1):
    o=np.zeros(len(x));a=0;ks=np.linspace(k0,k1,len(x))
    for i in range(len(x)):a+=ks[i]*(x[i]-a);o[i]=a
    return o
def whoosh(d=.35):n=int(SR*d);return lp(rng.standard_normal(n),.03,.45)*np.sin(np.linspace(0,np.pi,n))**2
def pop():n=int(SR*.12);t=np.arange(n)/SR;return np.sin(2*np.pi*(900-3000*t)*t)*np.exp(-t*40)*.8
def thud():n=int(SR*.4);t=np.arange(n)/SR;return np.sin(2*np.pi*np.cumsum(70*np.exp(-t*3)+45)/SR)*np.exp(-t*7)*1.1+rng.standard_normal(n)*np.exp(-t*60)*.3
def ding(f=1568,d=.6):n=int(SR*d);t=np.arange(n)/SR;return (np.sin(2*np.pi*f*t)+.3*np.sin(2*np.pi*2*f*t))*np.exp(-t*6)*.4
def key():n=int(SR*.05);t=np.arange(n)/SR;return rng.standard_normal(n)*np.exp(-t*160)*.35
for s in T['scenes'][1:]: add(s['t0']-0.17,whoosh(),.7 if s['id'].startswith('m_') else .5)
for c in T['caps']: pass
for k in ['r0','r1','r2']: add(EV[k]+0.35,thud(),.8)
add(EV['free'],ding(1760,.5),.6)
for k in ['w0','w1']: add(EV[k]-0.1,pop(),.6)
add(EV['vsB']+0.1,thud(),.7)
add(EV['type'],key(),.9);add(EV['type']+.15,key(),.7);add(EV['dm'],ding(),.8)
for t in [0.5,6.0,10.2,10.7]: add(t,pop(),.5)
y=y/np.max(np.abs(y))*.85
w=wave.open('sfx.wav','wb');w.setnchannels(1);w.setsampwidth(2);w.setframerate(SR);w.writeframes((y*32767).astype(np.int16).tobytes());w.close();print('ok')
