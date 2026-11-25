import subprocess,json
D=json.load(open('ov/tl.json'))['dur']
fc=("[4:v]fps=30,setpts=PTS-STARTPTS[bgt];[0:v]fps=30,format=rgba[ov];[bgt][ov]overlay=0:0:shortest=1,format=yuv420p[v];"
"[1:a]aresample=48000,aformat=channel_layouts=mono,highpass=f=80,acompressor=threshold=0.2:ratio=2.2:attack=8:release=160,aformat=channel_layouts=stereo,asplit=2[nar][key];"
f"[2:a]atrim=start=0.2,asetpts=PTS-STARTPTS,atrim=0:{D},aresample=48000,aformat=channel_layouts=stereo,loudnorm=I=-26:TP=-2:LRA=7,aresample=48000,afade=t=out:st={D-1.5}:d=1.5[b0];[b0][key]sidechaincompress=threshold=0.05:ratio=2:attack=20:release=300[bgm];"
"[3:a]aresample=48000,aformat=channel_layouts=stereo,volume=0.3[sfx];"
"[nar][bgm][sfx]amix=inputs=3:normalize=0,loudnorm=I=-14:TP=-1.5:LRA=11,aresample=48000[a]")
cmd=['ffmpeg','-nostdin','-y','-loglevel','error','-framerate','30','-i','fr/f%05d.png','-i','v_fit.wav','-i','../g23/bgmPop.wav','-i','sfx.wav','-i','bgtrack.mp4','-filter_complex',fc,'-map','[v]','-map','[a]','-c:v','libx264','-preset','slow','-crf','16','-maxrate','20M','-bufsize','40M','-pix_fmt','yuv420p','-c:a','aac','-b:a','192k','-t',str(D),'-movflags','+faststart','app_final.mp4']
subprocess.run(cmd,check=True);print('ok')
