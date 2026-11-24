import numpy as np, wave, json
w=wave.open('el_orig.wav');sr=w.getframerate();x=np.frombuffer(w.readframes(w.getnframes()),dtype=np.int16).astype(np.float32);w.close()
sil=[(0.76,1.00),(2.95,3.51),(6.36,6.91),(8.40,8.87),(11.02,11.44),(13.21,13.92),(14.45,14.69),(15.44,16.09),(19.03,19.71),(20.21,20.49),(21.20,21.76),(23.36,23.79),(26.18,26.92),(27.47,27.73),(28.37,28.97),(30.09,30.24),(31.72,32.22),(33.36,33.63),(34.34,34.89),(36.36,36.51)]
internal={0,6,9,13,15,19}   # comma-type pauses inside a phrase
words=["시험공부,","요약 노트 이제 안 만들어도 돼요","강의 PDF 하나 넣으면 퀴즈가 쏟아지거든요","구글 제미나이 노트북이에요","옛 이름은 노트북LM이고요","구글 계정만 있으면 0원이에요","첫 번째,","자료 넣기","PDF랑 유튜브 링크까지 한 번에 50개 돼요","두 번째,","퀴즈 버튼","내 자료로만 문제를 내 줘요","틀린 건 물어보면 근거를 짚어서 답해요","세 번째,","플래시카드","저는 이걸로 외우고","출근길엔 오디오로 들어요","시험 전날 꺼내 봐요","저장해 두세요","댓글에 '공부' 남기면","공부 프롬프트 DM 드려요"]
GAP_IN, GAP_SENT, PAD = 0.08, 0.18, 0.03
segs=[];s=0.0
for a,b in sil: segs.append((s,a)); s=b
segs.append((s,38.0))
out=[];marks=[];t=0.0
fade=int(0.012*sr)
for i,(a,b) in enumerate(segs):
    A=max(0,int((a-PAD)*sr));B=min(len(x),int((b+PAD)*sr));y=x[A:B].copy()
    y[:fade]*=np.linspace(0,1,fade);y[-fade:]*=np.linspace(1,0,fade)
    marks.append({"i":i,"t0":round(t+PAD if i else t,3),"t1":round(t+len(y)/sr-PAD,3),"text":words[i]})
    out.append(y);t+=len(y)/sr
    if i<len(sil):
        g=GAP_IN if i in internal else GAP_SENT
        g=min(g,sil[i][1]-sil[i][0]);n=int(g*sr);out.append(np.zeros(n,np.float32));t+=g
out.append(np.zeros(int(0.10*sr),np.float32))
y=np.concatenate(out);print('dur',len(y)/sr)
w=wave.open('el_tight.wav','wb');w.setnchannels(1);w.setsampwidth(2);w.setframerate(sr);w.writeframes(np.clip(y,-32768,32767).astype(np.int16).tobytes());w.close()
json.dump(marks,open('marks.json','w'),ensure_ascii=False,indent=0)
for m in marks: print(m['t0'],m['t1'],m['text'])
