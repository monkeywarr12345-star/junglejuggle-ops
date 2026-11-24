import json,numpy as np
m=json.load(open('marks_fit.json'));e=np.load('env.npy')
def dip(i,lo=.3,hi=.75):
    a,b=m[i]['t0'],m[i]['t1'];A,B=int((a+(b-a)*lo)*100),int((a+(b-a)*hi)*100)
    seg=e[A:B];k=np.convolve(seg,np.ones(3)/3,'same');return round((A+int(np.argmin(k)))/100,2)
T=lambda i:m[i]['t0']
mid=lambda i:round((m[i]['t1']+m[i+1]['t0'])/2,2)
D=round(m[-1]['t1']+0.45,2)
d1,d2,d4,d5,d8,d11,d12,d16,d20=dip(1,.2,.45),dip(2,.42,.68),dip(4,.25,.5),dip(5,.55,.8),dip(8,.5,.72),dip(11,.3,.6),dip(12,.3,.58),dip(16,.2,.5),dip(20,.35,.65)
f50=d8
sc=[['hook',0,mid(1),'split','#3B0A16'],['burst',mid(1),mid(2),'full','#0A2163'],['rename',mid(2),mid(4),'split','#14203F'],
['zero',mid(4),mid(5),'full','#04402F'],['src',mid(5),round(f50-0.05,2),'split','#0A2163'],['fifty',round(f50-0.05,2),mid(8),'full','#0A2163'],
['quizArch',mid(8),mid(10),'full','#2B1670'],['quiz',mid(10),mid(11),'split','#2B1670'],['cite',mid(11),mid(12),'split','#2B1670'],
['flash',mid(12),mid(15),'full','#4B0F42'],['audio',mid(15),mid(16),'split','#4B0F42'],['host',mid(16),mid(17),'host','#1A1C22'],
['save',mid(17),mid(18),'split','#1A1C22'],['dm',mid(18),D,'full','#1A1C22']]
L=lambda x:round(x-0.05,2)
caps=[[0,'시험공부, 요약 노트','이제 안 만들어도 돼요',d1],[L(T(2)),'강의 PDF 하나 넣으면','퀴즈가 쏟아지거든요',d2],[L(T(3)),'구글 제미나이 노트북이에요',''],
[L(T(4)),'옛 이름은','노트북LM이고요',d4],[L(T(5)),'구글 계정만 있으면','0원이에요',d5],[L(T(6)),'첫 번째, 자료 넣기',''],[L(T(8)),'PDF랑 유튜브 링크까지',''],
[L(d8),'한 번에','50개 돼요',d8+0.15],[L(T(9)),'두 번째, 퀴즈 버튼',''],[L(T(11)),'내 자료로만','문제를 내 줘요',d11],[L(T(12)),'틀린 건 물어보면','근거를 짚어서 답해요',d12],
[L(T(13)),'세 번째, 플래시카드',''],[L(T(15)),'저는 이걸로 외우고',''],[L(T(16)),'출근길엔','오디오로 들어요',d16],[L(T(17)),'시험 전날 꺼내 봐요',''],
[L(T(18)),'저장해 두세요',''],[L(T(19)),"댓글에 '공부' 남기면",''],[L(T(20)),'공부 프롬프트','DM 드려요',d20]]
ev={'strike':d1-0.45,'zeroSlam':d5,'scramble':d4,'dmArrive':T(20),'typing':T(19)+0.5}
json.dump({'dur':D,'scenes':sc,'caps':caps,'ev':ev},open('ov/tl.json','w'),ensure_ascii=False)
for s in sc: print(s[0],s[1],s[2],round(s[2]-s[1],2),s[3])
print(ev,D)
