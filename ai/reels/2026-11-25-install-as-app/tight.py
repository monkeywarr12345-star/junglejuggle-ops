import numpy as np,wave,json,subprocess,re
w=wave.open('v_orig.wav');sr=w.getframerate();x=np.frombuffer(w.readframes(w.getnframes()),np.int16).astype(np.float32);w.close()
e=subprocess.run(['ffmpeg','-nostdin','-i','v_orig.wav','-af','silencedetect=noise=-38dB:d=0.12','-f','null','-'],capture_output=True,text=True).stderr
v=[float(a) for a in re.findall(r'silence_(?:start|end): ([0-9.]+)',e)];sil=list(zip(v[0::2],v[1::2]))
sil=[s for s in sil if s[0]>0.05 and s[1]<len(x)/sr-0.05]
# map: original time -> new time, piecewise
out=[];tmap=[];t=0;pos=0.0;PAD=0.03
for a,b in sil:
    g=b-a;ng=min(g,0.26) if g>=0.3 else g
    keep_end=a+ (ng/2); skip_to=b-(ng/2)
    out.append(x[int(pos*sr):int(keep_end*sr)]);tmap.append((pos,keep_end,t));t+=keep_end-pos;pos=skip_to
out.append(x[int(pos*sr):]);tmap.append((pos,len(x)/sr,t));t+=len(x)/sr-pos
y=np.concatenate(out)
w=wave.open('v_fit.wav','wb');w.setnchannels(1);w.setsampwidth(2);w.setframerate(sr);w.writeframes(np.clip(y,-32768,32767).astype(np.int16).tobytes());w.close()
json.dump(tmap,open('tmap.json','w'));print('dur',len(y)/sr)
