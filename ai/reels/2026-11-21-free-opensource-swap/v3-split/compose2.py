import subprocess, sys, json
# usage: compose2.py host.mp4 frames_dir scale:crop_y out.mp4 [music]
src, fr, sc, out = sys.argv[1], sys.argv[2], sys.argv[3], sys.argv[4]
SC, cy = float(sc.split(':')[0]), int(sc.split(':')[1])
FW = int(round(1080*SC/2))*2
MUSIC = len(sys.argv) > 5 and sys.argv[5] == 'music'
BGM = '/home/claude/main/media/ai/2026-11-21-free-opensource-swap/src/bgm_ludyte.wav'
DUR = json.load(open(fr + '.tl.json'))['dur']
fc = (f"[0:v]fps=30,scale=1080:1920,split=2[h0][h1];[h0]crop=1080:960:0:{min(960,int(cy/SC))},boxblur=28:2,eq=brightness=-0.06[hb];[h1]scale={FW}:-2:flags=lanczos,crop={FW}:960:0:{cy}[hf];[hb][hf]overlay=(W-w)/2:0,eq=contrast=1.03:saturation=1.04,pad=1080:1920:0:960:black,"
      f"trim=duration={DUR},setpts=PTS-STARTPTS[b0];[b0][1:v]overlay=0:0:format=auto,format=yuv420p[v];"
      "[0:a]aresample=48000,aformat=channel_layouts=stereo,highpass=f=70,acompressor=threshold=0.15:ratio=2.2:attack=8:release=150,asplit=2[nar][key];")
mix = ['[nar]']
if MUSIC:
    fc += (f"[2:a]atrim=start=0.45,asetpts=PTS-STARTPTS,atrim=0:{DUR},aresample=48000,aformat=channel_layouts=stereo,loudnorm=I=-21:TP=-2:LRA=7,aresample=48000,"
           f"equalizer=f=1800:width_type=o:width=2:g=-4,afade=t=out:st={DUR-1.4}:d=1.4[bgm0];[bgm0][key]sidechaincompress=threshold=0.05:ratio=2:attack=20:release=300[bgm];")
    mix.append('[bgm]')
else:
    fc += "[key]anullsink;"
fc += ''.join(mix) + f"amix=inputs={len(mix)}:normalize=0,loudnorm=I=-14:TP=-1.5:LRA=11,aresample=48000[a]"
cmd = ['ffmpeg', '-nostdin', '-y', '-loglevel', 'error', '-i', src, '-framerate', '30', '-i', fr + '/f%05d.png']
if MUSIC: cmd += ['-i', BGM]
cmd += ['-filter_complex', fc, '-map', '[v]', '-map', '[a]', '-c:v', 'libx264', '-preset', 'veryfast', '-crf', '18', '-c:a', 'aac', '-b:a', '192k',
        '-t', str(DUR), '-movflags', '+faststart', out]
subprocess.run(cmd, check=True); print('ok', out)
