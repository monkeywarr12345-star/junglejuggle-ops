import json,subprocess,sys
T=json.load(open('tl_60c.json'));DUR=T['dur']
b=[T['s'][k] for k in sorted(T['s'])];b[-1]=[b[-1][0],DUR]
st=[0.0,3.583,5.022,9.557,16.305,22.423,30.84,40.426,48.038,55.0]
mus=sys.argv[1]; out=sys.argv[2]; ML=float(sys.argv[3]) if len(sys.argv)>3 else -20
fc="[1:a]aresample=48000,aformat=channel_layouts=stereo,asplit=%d"%len(b)+''.join(f'[l{i}]' for i in range(len(b)))+';'
cat=''
for i,((a,e),s) in enumerate(zip(b,st)):
    d=e-a
    fc+=f"[l{i}]atrim=start={s}:duration={d:.4f},asetpts=PTS-STARTPTS,afade=t=in:d=0.015,afade=t=out:st={d-0.015:.4f}:d=0.015[g{i}];";cat+=f'[g{i}]'
fc+=f"{cat}concat=n={len(b)}:v=0:a=1,loudnorm=I=-24:TP=-2:LRA=8,aresample=48000,equalizer=f=1800:width_type=o:width=2:g=-5[lud];"
fc+="[0:a]aresample=48000,aformat=channel_layouts=stereo,asplit[v][key];"
fc+=f"[2:a]atrim=0:{DUR},asetpts=PTS-STARTPTS,aresample=48000,aformat=channel_layouts=stereo,loudnorm=I={ML}:TP=-2:LRA=7,aresample=48000,equalizer=f=1800:width_type=o:width=2:g=-4,equalizer=f=3000:width_type=o:width=1:g=-2,afade=t=in:d=0.3,afade=t=out:st={DUR-1.5}:d=1.5[m];"
fc+="[lud][m]amix=inputs=2:normalize=0[bed];[bed][key]sidechaincompress=threshold=0.08:ratio=2:attack=40:release=450[duck];"
fc+="[v][duck]amix=inputs=2:normalize=0,loudnorm=I=-14:TP=-1.5:LRA=11,aresample=48000[a]"
subprocess.run(['ffmpeg','-y','-v','error','-i','out60c_nomusic.mp4','-i','src/p12.mp4','-i',mus,'-filter_complex',fc,'-map','0:v','-map','[a]','-c:v','copy','-c:a','aac','-b:a','192k','-t',str(DUR),'-movflags','+faststart',out],check=True)
print('ok',DUR)
