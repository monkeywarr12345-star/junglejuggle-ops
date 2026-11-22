import subprocess,re,sys,numpy as np
# per-clip: fit time scale between clip audio pauses and original part pauses, slow video to match, trim to segment length
def pauses(f):
    e=subprocess.run(['ffmpeg','-nostdin','-i',f,'-af','silencedetect=n=-38dB:d=0.2','-f','null','-'],capture_output=True,text=True).stderr
    return [float(x) for x in re.findall(r'silence_(?:start|end): ([0-9.]+)',e)]
parts=[('elC1.mp4','el_p1.wav',12.1),('elC2.mp4','el_p2.wav',8.35),('elC3.mp4','el_p3.wav',10.557)]
outs=[]
for i,(v,a,L) in enumerate(parts):
    pc=[p for p in pauses(v) if 0.1<p];po=[p for p in pauses(a) if 0.1<p]
    n=min(len(pc),len(po));pc=np.array(pc[:n]);po=np.array(po[:n])
    keep=po<L-.05; pc,po=pc[keep],po[keep]
    k,b=np.polyfit(pc,po,1);res=np.abs(po-(k*pc+b)).max()
    print(v,'scale %.4f off %.3f maxres %.3f n=%d'%(k,b,res,len(pc)))
    o=f'hs{i+1}.mp4';outs.append(o)
    # video time t_v maps to original time k*t_v+b  -> new pts = k*pts + b ; then trim 0..L
    vf=f"setpts={k:.5f}*PTS+{b:.4f}/TB,fps=30,trim=0:{L},setpts=PTS-STARTPTS"
    subprocess.run(['ffmpeg','-nostdin','-y','-loglevel','error','-i',v,'-vf',vf,'-an','-c:v','libx264','-preset','medium','-crf','12',o],check=True)
open('hs.txt','w').write(''.join(f"file '{o}'\n" for o in outs))
subprocess.run(['ffmpeg','-nostdin','-y','-loglevel','error','-f','concat','-safe','0','-i','hs.txt','-c','copy','host_el.mp4'],check=True)
print(subprocess.run(['ffprobe','-v','error','-show_entries','format=duration','-of','csv=p=0','host_el.mp4'],capture_output=True,text=True).stdout)
