import subprocess, sys, json
# compose3.py host.mp4 frames scale:crop out.mp4 broll1..4
src, fr, sc, out = sys.argv[1:5]; BR = sys.argv[5:9]
SC, cy = float(sc.split(':')[0]), int(sc.split(':')[1]); FW = int(round(1080*SC/2))*2
BGM = '/home/claude/main/media/ai/2026-11-21-free-opensource-swap/src/bgm_ludyte.wav'
T = json.load(open(fr + '.tl.json')); DUR = T['dur']; C = lambda i: T['caps'][i][:2]
WIN = [C(1), C(2), C(6), [C(9)[0], C(10)[1]]]
fc = (f"[0:v]fps=30,scale=1080:1920,split=2[h0][h1];[h0]crop=1080:960:0:{min(960,int(cy/SC))},boxblur=28:2,eq=brightness=-0.06[hb];"
      f"[h1]scale={FW}:-2:flags=lanczos,crop={FW}:960:0:{cy}[hf];[hb][hf]overlay=(W-w)/2:0,eq=contrast=1.03:saturation=1.04,pad=1080:1920:0:960:black,trim=duration={DUR},setpts=PTS-STARTPTS[b0];")
last = 'b0'
OFF = [0.2, 1.2, 0.3, 0.8]
for k, (a, b) in enumerate(WIN):
    i = 4 + k
    fc += (f"[{i}:v]trim=start={OFF[k]},setpts=PTS-STARTPTS,tpad=stop_mode=clone:stop_duration=2,fps=30,scale=1188:2112:flags=lanczos,crop=1080:1920:54:96,eq=contrast=1.05:saturation=1.08,trim=duration={b-a+0.05},setpts=PTS-STARTPTS+{a}/TB[r{k}];"
           f"[{last}][r{k}]overlay=0:0:enable='between(t,{a},{b})':eof_action=pass[m{k}];")
    last = f"m{k}"
fc += (f"[{last}][1:v]overlay=0:0:format=auto,format=yuv420p[v];"
       "[0:a]aresample=48000,aformat=channel_layouts=stereo,highpass=f=70,acompressor=threshold=0.15:ratio=2.2:attack=8:release=150,asplit=2[nar][key];"
       f"[2:a]atrim=start=0.45,asetpts=PTS-STARTPTS,atrim=0:{DUR},aresample=48000,aformat=channel_layouts=stereo,loudnorm=I=-20:TP=-2:LRA=7,aresample=48000,"
       f"equalizer=f=1800:width_type=o:width=2:g=-4,afade=t=out:st={DUR-1.4}:d=1.4[bgm0];[bgm0][key]sidechaincompress=threshold=0.05:ratio=2:attack=20:release=300[bgm];"
       "[3:a]aresample=48000,volume=0.32[sfx];"
       f"[nar][bgm][sfx]amix=inputs=3:normalize=0,loudnorm=I=-14:TP=-1.5:LRA=11,aresample=48000[a]")
cmd = ['ffmpeg', '-nostdin', '-y', '-loglevel', 'error', '-i', src, '-framerate', '30', '-i', fr + '/f%05d.png', '-i', BGM, '-i', 'sfx3.wav'] + sum([['-i', b] for b in BR], [])
cmd += ['-filter_complex', fc, '-map', '[v]', '-map', '[a]', '-c:v', 'libx264', '-preset', 'veryfast', '-crf', '18', '-c:a', 'aac', '-b:a', '192k', '-t', str(DUR), '-movflags', '+faststart', out]
subprocess.run(cmd, check=True); print('ok', out)
