import subprocess,json,sys
F=json.load(open('fit.json'))
P=[('gC1.mp4',12.01,'hs1.mp4'),('gC2.mp4',10.74,'hs2.mp4'),('gC3.mp4',10.06,'hs3.mp4')]
for v,L,o in P:
    if sys.argv[1:] and o not in sys.argv[1:]: continue
    k,b=F[v]
    vf=f"setpts={k:.5f}*PTS+{b:.4f}/TB,scale=1080:1920:flags=lanczos,unsharp=5:5:0.35,fps=30,trim=0:{L},setpts=PTS-STARTPTS"
    subprocess.run(['ffmpeg','-nostdin','-y','-loglevel','error','-i',v,'-vf',vf,'-an','-c:v','libx264','-preset','medium','-crf','12',o],check=True);print('ok',o,k,b)
