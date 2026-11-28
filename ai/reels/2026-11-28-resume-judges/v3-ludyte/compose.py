import subprocess,json,sys
D=38.0
# (file, scene_start, src_start, dur, speed)
CL=json.load(open('clips.json'))
ins=['-f','lavfi','-i',f'color=c=white:s=1080x1920:r=30:d={D},format=rgb24']
fc=[];last='[0:v]'
for k,c in enumerate(CL):
    ins+=['-i',c['f']]; i=k+1
    y0=c.get('y0',140); h=c.get('h',632)
    fc.append(f"[{i}:v]fps=30,trim=start={c['ss']}:duration={c['dur']*c.get('sp',1)},setpts=(PTS-STARTPTS)/{c.get('sp',1)},scale=1080:1080,crop=1080:{h}:0:{y0},scale=888:520:flags=lanczos,hue=s=0,format=rgb24,curves=all='0/0 0.06/0 0.82/1 1/1',format=rgb24,tpad=start_duration={c['t0']}:color=white:stop_mode=clone:stop_duration=1[c{k}]")
    fc.append(f"{last}[c{k}]overlay=96:636:format=rgb:enable='between(t,{c['t0']},{c['t0']+c['dur']})':eof_action=pass[b{k}]"); last=f'[b{k}]'
n=len(CL)+1
ins+=['-framerate','30','-i','fr/f%05d.png','-i','v_fit.wav','-i','/home/claude/work/g23/bgmPop.wav','-i','sfx.wav']
fc.append(f"[{n}:v]format=rgba[ov];{last}[ov]overlay=0:0:shortest=1:format=rgb,format=gbrp,scale=out_color_matrix=bt709:out_range=tv,format=yuv420p[v]")
fc.append(f"[{n+1}:a]aresample=48000,aformat=channel_layouts=mono,highpass=f=80,acompressor=threshold=0.2:ratio=2.2:attack=8:release=160,aformat=channel_layouts=stereo,asplit=2[nar][key];[{n+2}:a]atrim=start=20,asetpts=PTS-STARTPTS,atrim=0:{D},aresample=48000,aformat=channel_layouts=stereo,loudnorm=I=-26:TP=-2:LRA=7,aresample=48000,afade=t=in:d=0.3,afade=t=out:st=36.5:d=1.5[b0a];[b0a][key]sidechaincompress=threshold=0.05:ratio=2:attack=20:release=300[bgm];[{n+3}:a]aresample=48000,aformat=channel_layouts=stereo,volume=0.3[sfx];[nar][bgm][sfx]amix=inputs=3:normalize=0,loudnorm=I=-14:TP=-1.5:LRA=11,aresample=48000[a]")
cmd=['ffmpeg','-nostdin','-y','-loglevel','error']+ins+['-filter_complex',';'.join(fc),'-map','[v]','-map','[a]','-c:v','libx264','-preset','slow','-crf','16','-pix_fmt','yuv420p','-colorspace','bt709','-color_primaries','bt709','-color_trc','bt709','-color_range','tv','-c:a','aac','-b:a','192k','-t',str(D),'-movflags','+faststart',sys.argv[1] if len(sys.argv)>1 else 'rj_final.mp4']
subprocess.run(cmd,check=True);print('ok')
