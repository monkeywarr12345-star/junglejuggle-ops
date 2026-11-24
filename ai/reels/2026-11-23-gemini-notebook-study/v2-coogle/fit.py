import subprocess,numpy as np
def env(f,sr=16000):
    x=np.frombuffer(subprocess.run(['ffmpeg','-nostdin','-v','error','-i',f,'-ac','1','-ar',str(sr),'-f','s16le','-'],capture_output=True).stdout,np.int16).astype(np.float32)
    h=sr//100;n=len(x)//h;e=np.sqrt((x[:n*h].reshape(n,h)**2).mean(1));return np.log1p(e)
res={}
import sys
for c,a,L in [x for x in [('gC1.mp4','el_p1.wav',12.01),('gC2.mp4','el_p2.wav',10.74),('gC3.mp4','el_p3.wav',10.06)] if x[0] in sys.argv[1:]]:
    ec,eo=env(c),env(a);eo=eo[:int(L*100)]
    t=np.arange(len(eo))/100.;best=(-9,0,0)
    for k in np.arange(0.90,1.10,0.0025):
        for b in np.arange(-0.4,0.4,0.01):
            # original time t corresponds to clip time (t-b)/k
            tc=(t-b)/k;ok=(tc>=0)&(tc<len(ec)/100-0.01)
            v=np.interp(tc[ok],np.arange(len(ec))/100.,ec)
            if ok.sum()<len(t)*0.9: continue
            r=np.corrcoef(v,eo[ok])[0,1]
            if r>best[0]: best=(r,k,b)
    res[c]=best;print(c,'corr %.3f  k %.4f  b %.3f'%best)
import json;F=json.load(open('fit.json'));F.update({k:[v[1],v[2]] for k,v in res.items()});json.dump(F,open('fit.json','w'))
