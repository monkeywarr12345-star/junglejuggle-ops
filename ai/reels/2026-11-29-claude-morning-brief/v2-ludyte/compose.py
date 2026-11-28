import subprocess,json,sys
D=37.0; SW=4.97
CL=json.load(open('clips.json'))
ins=['-f','lavfi','-i',f'color=c=white:s=1080x1920:r=30:d={D},format=rgb24']
fc=[];last='[0:v]'
for k,c in enumerate(CL):
    ins+=['-i',c['f']]; i=k+1; sp=c.get('sp',1)
    if c.get('full'):
        chain=f"[{i}:v]fps=30,trim=start={c['ss']}:duration={c['dur']*sp},setpts=(PTS-STARTPTS)/{sp},scale=1080:1920,format=rgb24,tpad=start_duration={c['t0']}:color=white:stop_mode=clone:stop_duration=1[c{k}]"
        pos="0:0"
    else:
        x,y,w,h=c.get('rect',[230,630,620,620]); cx,cy,cw,ch=c.get('crop',[60,60,960,960])
        chain=(f"[{i}:v]fps=30,trim=start={c['ss']}:duration={c['dur']*sp},setpts=(PTS-STARTPTS)/{sp},scale=1080:1080,crop={cw}:{ch}:{cx}:{cy},scale={w}:{h}:flags=lanczos,"
               f"hue=s=0,format=rgb24,curves=all='0/0 0.06/0 0.82/1 1/1',format=rgb24,tpad=start_duration={c['t0']}:color=white:stop_mode=clone:stop_duration=1[c{k}]")
        pos=f"{x}:{y}"
    fc.append(chain)
    fc.append(f"{last}[c{k}]overlay={pos}:format=rgb:enable='between(t,{c['t0']},{c['t0']+c['dur']})':eof_action=pass[b{k}]"); last=f'[b{k}]'
n=len(CL)+1
ins+=['-framerate','30','-i','fr/f%05d.png']
fc.append(f"[{n}:v]format=rgba[ov];{last}[ov]overlay=0:0:shortest=1:format=rgb,format=gbrp,scale=out_color_matrix=bt709:out_range=tv,format=yuv420p[v]")
subprocess.run(['ffmpeg','-nostdin','-y','-loglevel','error']+ins+['-filter_complex',';'.join(fc),'-map','[v]','-c:v','libx264','-preset','slow','-crf','16','-pix_fmt','yuv420p','-colorspace','bt709','-color_primaries','bt709','-color_trc','bt709','-color_range','tv','-t',str(D),'vtmp.mp4'],check=True)
A=("[1:a]aresample=48000,aformat=channel_layouts=mono,highpass=f=80,acompressor=threshold=0.2:ratio=2.2:attack=8:release=160,aformat=channel_layouts=stereo,adelay=5000|5000,asplit=2[nar][key];"
f"[2:a]atrim=start=20,asetpts=PTS-STARTPTS,atrim=0:{D-SW},aresample=48000,aformat=channel_layouts=stereo,loudnorm=I=-26:TP=-2:LRA=7,aresample=48000,afade=t=in:d=0.15,afade=t=out:st={D-SW-1.5}:d=1.5,adelay={int(SW*1000)}|{int(SW*1000)}[b0a];"
"[b0a][key]sidechaincompress=threshold=0.05:ratio=2:attack=20:release=300[bgm];"
f"[4:a]atrim=start=0.4,asetpts=PTS-STARTPTS,atrim=0:{SW},aresample=48000,aformat=channel_layouts=stereo,loudnorm=I=-19:TP=-2:LRA=7,aresample=48000,afade=t=in:d=0.08,afade=t=out:st={SW-0.05}:d=0.05[hk];"
"[3:a]aresample=48000,aformat=channel_layouts=stereo,volume=0.3[sfx];"
f"[nar][bgm][sfx][hk]amix=inputs=4:normalize=0:duration=longest,loudnorm=I=-14:TP=-1.5:LRA=11,aresample=48000,apad,atrim=0:{D}[a]")
subprocess.run(['ffmpeg','-nostdin','-y','-loglevel','error','-i','vtmp.mp4','-i','v_fit.wav','-i','/home/claude/work/g23/bgmPop.wav','-i','sfx.wav','-i','lud/strings.m4a','-filter_complex',A,'-map','0:v','-map','[a]','-c:v','copy','-c:a','aac','-b:a','192k','-t',str(D),'-movflags','+faststart',sys.argv[1] if len(sys.argv)>1 else 'mb_final.mp4'],check=True)
print('ok')
