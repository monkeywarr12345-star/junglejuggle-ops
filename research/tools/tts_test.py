import time,json,subprocess,sys,os
res={}
text="구독료 정리, 프롬프트 세 줄이면 끝나요. 먼저 카드 명세서를 붙이고, 매달 반복 결제만 표로 뽑아 달라고 하세요."
os.makedirs('research/out',exist_ok=True)
t=time.time()
try:
    from melo.api import TTS
    m=TTS(language='KR',device='cpu');spk=m.hps.data.spk2id
    m.tts_to_file(text,spk['KR'],'research/out/tts_melo_kr.wav',speed=1.05)
    res['melotts']={'ok':True,'sec':round(time.time()-t,1)}
except Exception as e: res['melotts']={'ok':False,'err':repr(e)[:300]}
t=time.time()
try:
    from faster_whisper import WhisperModel
    wm=WhisperModel('small',device='cpu',compute_type='int8')
    segs,info=wm.transcribe('research/out/tts_melo_kr.wav',language='ko',word_timestamps=True)
    segs=list(segs)
    res['faster_whisper_small']={'ok':True,'sec':round(time.time()-t,1),'text':' '.join(s.text for s in segs),'words':sum(len(s.words or []) for s in segs)}
except Exception as e: res['faster_whisper_small']={'ok':False,'err':repr(e)[:300]}
json.dump(res,open('research/out/tts_test.json','w'),ensure_ascii=False,indent=1);print(json.dumps(res,ensure_ascii=False))
