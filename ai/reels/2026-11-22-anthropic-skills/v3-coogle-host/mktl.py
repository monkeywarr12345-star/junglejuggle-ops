"""mktl.py c1.mp4 c2.mp4 out.tl.json  — lines mapped to speech segments between detected pauses"""
import sys,re,subprocess,json
c1,c2,out=sys.argv[1:4]
def dur(f): return float(subprocess.run(["ffprobe","-v","error","-show_entries","format=duration","-of","csv=p=0",f],capture_output=True,text=True).stdout)
def segs(f,n_expected,mind=0.25):
    for th,d in [(-35,mind),(-33,0.2),(-38,0.3),(-30,0.18)]:
        e=subprocess.run(["ffmpeg","-nostdin","-i",f,"-af",f"silencedetect=n={th}dB:d={d}","-f","null","-"],capture_output=True,text=True).stderr
        ss=[float(x) for x in re.findall(r"silence_start: ([0-9.]+)",e)];se=[float(x) for x in re.findall(r"silence_end: ([0-9.]+)",e)]
        D=dur(f);sil=list(zip(ss,se+[D]*(len(ss)-len(se))))
        # speech segments
        sp=[];t=0
        for a,b in sil:
            if a>t+0.05: sp.append([t,a])
            t=b
        if t<D-0.05: sp.append([t,D])
        sp=[s for s in sp if s[1]-s[0]>0.15]
        if len(sp)==n_expected: return sp,D
        print(f,'th',th,d,'got',len(sp),'want',n_expected,[[round(a,2),round(b,2)] for a,b in sp],file=sys.stderr)
    raise SystemExit('segment mismatch')
# clip1 lines: L1,L2,L3,L4,L5 ; clip2: L6,L7,L8a,L8b,L9,L10,L11
s1,D1=segs(c1,5); s2,D2=segs(c2,7)
s2=[[a+D1,b+D1] for a,b in s2]; E=D1+D2
L=s1+s2
def mid(a,b,f): return a+(b-a)*f
# captions: (start,end,html,section)
L2a=mid(*L[1],0.42)
caps=[(0,L[1][0],"이거 안 켜면<br/>클로드 <b>반만</b> 쓰는 거예요","s1"),
 (L[1][0],L2a,"클로드 만든<br/>앤트로픽이","s1"),
 (L2a,L[2][0],"공식 스킬을<br/><b>19개</b>나 풀었거든요","s1"),
 (L[2][0],L[3][0],"돈은 <b>0원</b>이고요","s2"),
 (L[3][0],L[4][0],"제가 제일 먼저 켠 건<br/><b>PPT</b>랑 <b>엑셀</b>이에요","s2b"),
 (L[4][0],L[5][0],"말 한마디 했더니<br/><b>진짜 파일</b>이 떨어지더라고요","s3"),
 (L[5][0],L[6][0],"두 번째는<br/><b>프론트엔드 디자인</b>","s4"),
 (L[6][0],L[7][0],"AI 티 나는 화면이<br/><b>싹</b> 빠져요","s4"),
 (L[7][0],L[8][0],"세 번째<br/><b>스킬 크리에이터</b>는","s5"),
 (L[8][0],L[9][0],"제 업무 방식을<br/><b>스킬</b>로 만들어 줘요","s6"),
 (L[9][0],L[10][0],"켜는 데 <b>10초</b>예요","s7"),
 (L[10][0],L[11][0],"<b>저장</b>해 두고 켜요","s7"),
 (L[11][0],E,"댓글에 <b>'공식'</b> 남기면<br/>목록 DM 드려요","s8")]
caps=[[round(a,3),round(b,3),h,k] for a,b,h,k in caps]
S={}
for a,b,h,k in caps:
    S.setdefault(k,[a,b]);S[k][1]=b
S['s1'][0]=0.0
T={"dur":round(E,3),"s":S,"caps":caps,"kw":"공식","clip1":round(D1,3)}
json.dump(T,open(out,'w'),ensure_ascii=False)
open(out.replace('.json','.js'),'w').write('window.TL='+json.dumps(T,ensure_ascii=False)+';')
for c in caps: print(c)
print(S)
