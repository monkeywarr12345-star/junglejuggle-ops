import subprocess, sys, json
# usage: compose.py out.mp4  (sources src/A.mp4 + src/B.mp4 concatenated: B starts at 30.0)
out=sys.argv[1]
M='/home/claude/main/media/ai/2026-11-16-trader45'
T=json.load(open('tl.json')); DUR=T['dur']
keys=sorted(T['s'],key=lambda x:int(x[1:])); b=[T['s'][k] for k in keys]; b[-1]=[b[-1][0],DUR]
ST=[0.0,11.184,13.282,18.684,21.091,25.568,30.0,36.857,42.239,45.469,53.603]
fc="[0:v][0:a][1:v][1:a]concat=n=2:v=1:a=1[pv][pa];"
fc+=f"[pv]fps=30,scale=1080:1920:flags=lanczos,split={len(b)}"+''.join(f'[x{i}]' for i in range(len(b)))+';'
fc+=f"[pa]aresample=48000,aformat=channel_layouts=stereo,asplit={len(b)}"+''.join(f'[y{i}]' for i in range(len(b)))+';'
cv='';ca=''
for i,((a,e),s) in enumerate(zip(b,ST)):
    n=round(e*30)-round(a*30); d=n/30
    fc+=f"[x{i}]trim=start={s},setpts=PTS-STARTPTS,trim=end_frame={n}[v{i}];"; cv+=f'[v{i}]'
    fc+=f"[y{i}]atrim=start={s}:duration={d:.4f},asetpts=PTS-STARTPTS,afade=t=in:d=0.04,afade=t=out:st={d-0.04:.4f}:d=0.04[g{i}];"; ca+=f'[g{i}]'
fc+=f"{cv}concat=n={len(b)}:v=1:a=0,setpts=N/30/TB,eq=contrast=1.03:saturation=1.05[bg];[bg][2:v]overlay=0:0:format=auto,format=yuv420p[v];"
fc+=f"{ca}concat=n={len(b)}:v=0:a=1,loudnorm=I=-20:TP=-2:LRA=8,aresample=48000,equalizer=f=1800:width_type=o:width=2:g=-4,equalizer=f=3000:width_type=o:width=1:g=-2,afade=t=out:st={DUR-1.2}:d=1.2[bed];"
fc+="[3:a]aresample=48000,aformat=channel_layouts=stereo,highpass=f=80,acompressor=threshold=0.12:ratio=2.5:attack=8:release=120,volume=1.15,asplit[nar][key];"
fc+="[4:a]aresample=48000,aformat=channel_layouts=stereo,volume=0.4[sfx];"
fc+="[bed][key]sidechaincompress=threshold=0.04:ratio=5:attack=30:release=450:makeup=1[duck];"
fc+="[nar][sfx][duck]amix=inputs=3:normalize=0,loudnorm=I=-14:TP=-1.5:LRA=11,aresample=48000[a]"
subprocess.run(['ffmpeg','-nostdin','-y','-loglevel','error','-i','src/A.mp4','-i','src/B.mp4','-framerate','30','-i','fT/f%05d.png','-i',f'{M}/narration.wav','-i',f'{M}/sfx.wav',
 '-filter_complex',fc,'-map','[v]','-map','[a]','-c:v','libx264','-preset','veryfast','-crf','18','-c:a','aac','-b:a','192k','-t',str(DUR),'-movflags','+faststart',out],check=True)
print('ok')
