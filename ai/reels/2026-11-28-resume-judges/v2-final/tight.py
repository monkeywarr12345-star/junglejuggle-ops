import numpy as np,wave,json,subprocess,re
w=wave.open('v_orig.wav');sr=w.getframerate();x=np.frombuffer(w.readframes(w.getnframes()),np.int16).astype(np.float32);w.close()
e=subprocess.run(['ffmpeg','-nostdin','-i','v_orig.wav','-af','silencedetect=n=-40dB:d=0.12','-f','null','-'],capture_output=True,text=True).stderr
v=[float(a) for a in re.findall(r'silence_(?:start|end): ([0-9.]+)',e)];sil=list(zip(v[0::2],v[1::2]))
sil=[s for s in sil if s[0]>0.05 and s[1]<41.4]
CAP=0.24
out=[];tmap=[];t=0;pos=0.0
for a,b in sil:
    g=b-a;ng=min(g,CAP) if g>=0.28 else g
    ke=a+ng/2;sk=b-ng/2
    out.append(x[int(pos*sr):int(ke*sr)]);tmap.append((pos,ke,t));t+=ke-pos;pos=sk
end=41.40
out.append(x[int(pos*sr):int(end*sr)]);tmap.append((pos,end,t))
y=np.concatenate(out)
w=wave.open('v_cut.wav','wb');w.setnchannels(1);w.setsampwidth(2);w.setframerate(sr);w.writeframes(np.clip(y,-32768,32767).astype(np.int16).tobytes());w.close()
json.dump({'tmap':tmap,'sil':sil},open('tmap.json','w'));print('cut dur',len(y)/sr)
