import json,sys,numpy as np,wave
T=json.load(open(sys.argv[1]));out=sys.argv[2];SR=48000;E=T['dur'];S=T['s']
y=np.zeros(int(SR*(E+1)))
def add(t,sig):
    i=int(t*SR);n=min(len(sig),len(y)-i);y[i:i+n]+=sig[:n]
def whoosh(d=.45):
    n=int(SR*d);x=np.random.randn(n);env=np.sin(np.linspace(0,np.pi,n))**2
    # sweep lowpass via cumulative smoothing
    out=np.zeros(n);a=0
    for i in range(n):
        k=0.02+0.5*(i/n);a=a+k*(x[i]-a);out[i]=a
    return out*env*0.9
def impact(d=.5):
    n=int(SR*d);t=np.arange(n)/SR;f=60*np.exp(-t*6)+40
    return (np.sin(2*np.pi*np.cumsum(f)/SR)*np.exp(-t*7)*1.0+np.random.randn(n)*np.exp(-t*40)*.3)
def ding(f=1320,d=.6):
    n=int(SR*d);t=np.arange(n)/SR
    return (np.sin(2*np.pi*f*t)+.4*np.sin(2*np.pi*f*2*t))*np.exp(-t*6)*.45
def click():
    n=int(SR*.04);t=np.arange(n)/SR;return np.random.randn(n)*np.exp(-t*200)*.5
for k in ['s3','s4','s7','s8']:
    add(max(0,S[k][0]-.18),whoosh())
add(S['s2'][0],impact())
add(S['s5'][0],ding(990,.35)); add(S['s6'][0],ding(1180,.35))
a7=S['s7'][0]
for j in range(4): add(a7+.35+.32*(j+1)+.16*j,click())
s8=S['s8']; add(s8[0]+.4,click()); add(s8[0]+(s8[1]-s8[0])*.55,ding())
y=y/ (np.max(np.abs(y))+1e-9)*0.8
w=wave.open(out,'wb');w.setnchannels(1);w.setsampwidth(2);w.setframerate(SR);w.writeframes((y*32767).astype(np.int16).tobytes());w.close();print('ok')
