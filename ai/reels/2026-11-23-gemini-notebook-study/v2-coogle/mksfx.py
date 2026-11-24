import json,numpy as np,wave
T=json.load(open('ov/tl.json'));SR=48000;D=T['dur'];EV=T['ev'];SC={s[0]:s for s in T['scenes']}
rng=np.random.default_rng(3);y=np.zeros(int(SR*(D+1)))
def add(t,sig,g=1.0):
    i=max(0,int(t*SR));n=min(len(sig),len(y)-i);y[i:i+n]+=sig[:n]*g
def lp(x,k0,k1):
    out=np.zeros(len(x));a=0;ks=np.linspace(k0,k1,len(x))
    for i in range(len(x)): a+=ks[i]*(x[i]-a);out[i]=a
    return out
def whoosh(d=.42): n=int(SR*d);return lp(rng.standard_normal(n),.02,.45)*np.sin(np.linspace(0,np.pi,n))**2*1.1
def riser(d=1.0): n=int(SR*d);t=np.arange(n)/SR;return lp(rng.standard_normal(n),.01,.6)*(t/d)**2*0.8+np.sin(2*np.pi*np.cumsum(200+600*(t/d)**2)/SR)*(t/d)**2*0.15
def sub(d=1.2,f0=55): n=int(SR*d);t=np.arange(n)/SR;f=f0*np.exp(-t*2)+38;return np.sin(2*np.pi*np.cumsum(f)/SR)*np.exp(-t*2.2)*1.3+rng.standard_normal(n)*np.exp(-t*45)*.35
def tick(): n=int(SR*.03);t=np.arange(n)/SR;return np.sin(2*np.pi*3200*t)*np.exp(-t*260)*.5+rng.standard_normal(n)*np.exp(-t*400)*.2
def ding(f=1480,d=.7): n=int(SR*d);t=np.arange(n)/SR;return (np.sin(2*np.pi*f*t)+.35*np.sin(2*np.pi*f*2.01*t))*np.exp(-t*6)*.4
def flap(): n=int(SR*.18);return lp(rng.standard_normal(n),.3,.05)*np.exp(-np.arange(n)/SR*25)*.9
def suck(d=.5): n=int(SR*d);t=np.arange(n)/SR;return lp(rng.standard_normal(n),.5,.01)*np.sin(np.linspace(0,np.pi,n))*.9
def key(): n=int(SR*.05);t=np.arange(n)/SR;return rng.standard_normal(n)*np.exp(-t*160)*.35
# transitions
for k in ['burst','zero','fifty','quizArch','flash','dm']: add(SC[k][1]-.2,whoosh(),.8)
add(EV['strike']-0.05,whoosh(.3),.6)               # strike swipe
add(max(0,SC['burst'][1]-0.6),riser(0.6),.35)        # riser into burst
add(SC['burst'][1]+0.35,suck(),.8)                  # pdf sucked
for j in range(10): add(SC['burst'][1]+0.95+j*0.08,tick(),.8)   # cards ratchet
add(EV['scramble'],np.concatenate([tick()*((-1)**j) for j in range(14)]),.5)
add(EV['zeroSlam']-0.03,sub(.6,80),.6); add(EV['zeroSlam'],ding(2093,.5),.5)                  # 0원 sub-drop
s0=SC['src'][1]
for j in range(4): add(s0+0.55+j*0.22,tick(),.9)
add(SC['fifty'][1]-0.05,ding(1760,.6),.8)
add(SC['quiz'][1]+0.6,ding(1320,.4),.6)
add(SC['cite'][1]+1.0,ding(2200,.5),.4)
add(SC['flash'][1]+0.9,flap(),1.0)
add(SC['save'][1]+0.32,sub(.5,90),.5)
for j in range(2): add(EV['typing']+j*0.22,key(),.9)
add(EV['dmArrive']+0.05,ding(1568,.8),.8)
y=y/(np.max(np.abs(y))+1e-9)*0.85
w=wave.open('sfx.wav','wb');w.setnchannels(1);w.setsampwidth(2);w.setframerate(SR);w.writeframes((y*32767).astype(np.int16).tobytes());w.close();print('ok',D)
