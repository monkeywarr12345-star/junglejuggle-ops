import json, re, subprocess
M='/home/claude/main/media/ai/2026-11-20-claude-plugins5'
t=json.load(open(M+'/timeline.json'))
src=open('/home/claude/main/ai/voice/2026-11-20-claude-plugins5/build.py',encoding='utf-8').read()
lines=dict((m[0],m[1]) for m in re.findall(r'\("(s\d)", "([^"]*[가-힣][^"]*)"',src))
out=subprocess.run(['ffmpeg','-nostdin','-i',M+'/narration.wav','-af','silencedetect=n=-38dB:d=0.08','-f','null','-'],capture_output=True,text=True).stderr
sil=list(zip([float(x) for x in re.findall(r'silence_start: ([0-9.]+)',out)],[float(x) for x in re.findall(r'silence_end: ([0-9.]+)',out)]))
DISP=[('다섯 개','5개'),('엘엘엠 에이피아이','LLM API'),('천삼백여 개','1,300여 개'),('이십일 에스티 엠씨피','21st MCP'),(' 만 개',' 1만 개'),('디엠','DM'),('댓글에 장착,',"댓글에 '장착'"),('클로드 멤','claude-mem'),('클로드 코드 셋업','Claude Code Setup'),('엘리펀트 골드피시','Elephant-Goldfish')]
HL=['5개','무료','기억','1,300여 개','앤트로픽 공식','구글','1만 개',"'장착'",'코끼리','금붕어']
OVR={}
def _pre():
    for k in lines:
        for a,b in DISP: lines[k]=lines[k].replace(a,b)
_pre()
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
            if best: d=best[1]+'<br/>'+best[2]
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
