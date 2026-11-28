import numpy as np,wave,json,subprocess,re
w=wave.open('v_orig.wav');sr=w.getframerate();x=np.frombuffer(w.readframes(w.getnframes()),np.int16).astype(np.float32);w.close()
e=subprocess.run(['ffmpeg','-nostdin','-i','v_orig.wav','-af','silencedetect=n=-40dB:d=0.12','-f','null','-'],capture_output=True,text=True).stderr
v=[float(a) for a in re.findall(r'silence_(?:start|end): ([0-9.]+)',e)];sil=list(zip(v[0::2],v[1::2]))
sil=[s for s in sil if s[0]>0.05 and s[1]<45.0]
CAP=0.28;TEMPO=1.1
out=[];tmap=[];t=0;pos=0.0
for a,b in sil:
    g=b-a;ng=min(g,CAP) if g>=0.28 else g
    ke=a+ng/2;sk=b-ng/2
    out.append(x[int(pos*sr):int(ke*sr)]);tmap.append((pos,ke,t));t+=ke-pos;pos=sk
end=45.2
out.append(x[int(pos*sr):int(end*sr)]);tmap.append((pos,end,t))
y=np.concatenate(out)
w=wave.open('v_cut.wav','wb');w.setnchannels(1);w.setsampwidth(2);w.setframerate(sr);w.writeframes(np.clip(y,-32768,32767).astype(np.int16).tobytes());w.close()
subprocess.run(['ffmpeg','-nostdin','-y','-loglevel','error','-i','v_cut.wav','-af',f'atempo={TEMPO}','v_fit.wav'],check=True)
def m(o):
    for a,b,tt in tmap:
        if a-0.01<=o<=b+0.01: return (tt+max(0,o-a))/TEMPO
    return None
json.dump({'tmap':tmap,'tempo':TEMPO},open('tmap.json','w'))
ons=[0.0,2.12,3.47,4.91,6.63,9.23,11.36,12.51,14.56,16.36,18.82,19.67,21.48,23.95,25.75,27.99,30.12,31.47,33.83,36.03,37.90,39.79,41.40,43.38]
H=5.0
print('voice dur',len(y)/sr/TEMPO)
print([round(H+m(o),2) for o in ons])
