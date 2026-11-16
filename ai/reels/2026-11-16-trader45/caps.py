import json, re, subprocess
M='/home/claude/main/media/ai/2026-11-16-trader45'
t=json.load(open(M+'/timeline.json'))
src=open('/home/claude/main/ai/voice/2026-11-16-trader45/build.py',encoding='utf-8').read()
lines=dict((m[0],m[1]) for m in re.findall(r'\("(s\w+)", "([^"]+)"',src))
out=subprocess.run(['ffmpeg','-nostdin','-i',M+'/narration.wav','-af','silencedetect=n=-38dB:d=0.08','-f','null','-'],capture_output=True,text=True).stderr
sil=list(zip([float(x) for x in re.findall(r'silence_start: ([0-9.]+)',out)],[float(x) for x in re.findall(r'silence_end: ([0-9.]+)',out)]))
DISP=[('열한 개','11개'),('천오백 개','1,500개'),('에이피아이','API'),('댓글에 주식','댓글에 \'주식\''),('스킬 설치, 한 마디','\'스킬 설치\' 한 마디')]
HL=['워런 버핏 포트폴리오','펠로시가 산 주식','공짜로','리딩방','트레이더 스킬','1,500개','무료','11개','카피캣','따라 살 비율','속보와 공시','펠로시 스킬','누가 뭘 샀는지','리스크 스킬','승인하지 않으면','절대','\'스킬 설치\'','\'주식\'','예산 스킬','뉴스']
OVR={"'스킬 설치' 한<br/>마디면 끝이에요":"<b>'스킬 설치'</b><br/>한 마디면 끝이에요",'제일 놀라운<br/>건 펠로시 스킬':'제일 놀라운 건<br/>펠로시 스킬','카피캣은 버핏<br/>같은 대가가':'카피캣은<br/>버핏 같은 대가가','영향 있는<br/>것만 골라 줘요':'영향 있는 것만<br/>골라 줘요','이제 클로드가<br/>공짜로 다 찾아 줘요':'이제 클로드가<br/>공짜로 다 찾아 줘요'}
def syl(s): return max(1,len(re.findall(r'[가-힣A-Za-z0-9]',s)))
def disp(s):
    for a,b in DISP: s=s.replace(a,b)
    return s.rstrip(',').strip()
caps=[]
for k in sorted(t['s'],key=lambda x:int(x[1:])):
    a,b=t['s'][k]
    # speech span: first silence end near a, silence start near b
    ss=max([e for s,e in sil if s<=a+0.05 and e<=a+0.5]+[a]); se=min([s for s,e in sil if s>=b-0.9 and s<=b+0.05]+[b])
    ph=[p.strip() for p in re.split(r'(?<=[,.?])\s+',lines[k]) if p.strip()]
    # merge short phrases (display <=12 chars) with next
    grp=[];cur=[]
    for p in ph:
        cur.append(p)
        if len(disp(' '.join(cur)))>=11: grp.append(' '.join(cur)); cur=[]
    if cur:
        if grp and len(disp(cur[0]))<=6: grp[-1]+=' '+' '.join(cur)
        else: grp.append(' '.join(cur))
    g2=[]
    for g in grp:
        if len(disp(g))>22:
            w=g.split(' '); n=len(w); best=None
            for j in range(1,n):
                l1=' '.join(w[:j]); sc=abs(len(l1)-len(g)/2)-(4 if l1.endswith(',') else 0)
                if best is None or sc<best[0]: best=(sc,j)
            g2+= [' '.join(w[:best[1]]),' '.join(w[best[1]:])]
        else: g2.append(g)
    grp=g2
    tot=sum(syl(g) for g in grp); bounds=[ss]; acc=0
    inner=[(s+e)/2 for s,e in sil if s>ss+0.1 and e<se-0.1]
    for g in grp[:-1]:
        acc+=syl(g); x=ss+(se-ss)*acc/tot
        near=[m for m in inner if abs(m-x)<0.5]
        bounds.append(min(near,key=lambda m:abs(m-x)) if near else x)
    bounds.append(se)
    for i,g in enumerate(grp):
        d=disp(g).rstrip('.').rstrip(',')
        # split into 2 lines if long
        if len(d)>13:
            w=d.split(' '); best=None
            for j in range(1,len(w)):
                l1=' '.join(w[:j]); l2=' '.join(w[j:]); sc=abs(len(l1)-len(l2))-(5 if l1.endswith(',') else 0)
                if best is None or sc<best[0]: best=(sc,l1,l2)
            d=best[1]+'<br/>'+best[2]
        d=OVR.get(d,d)
        for h in sorted(HL,key=len,reverse=True):
            if h in d and '<b>' not in d: d=d.replace(h,'<b>'+h+'</b>',1)
        caps.append([round(bounds[i],3), round(bounds[i+1],3), d, k])
# fill gaps: keep each caption until next starts (max +0.4s)
for i in range(len(caps)-1):
    caps[i][1]=caps[i+1][0] if caps[i+1][0]-caps[i][1]<0.6 else caps[i][1]+0.3
t['caps']=caps
json.dump(t,open('tl.json','w'),ensure_ascii=False)
for c in caps: print(c)
