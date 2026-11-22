import subprocess, sys, json
# compose4.py host.mp4 frames bgm.wav sfx.wav out.mp4  (B format: full-screen mascot + overlay + inserts drawn in overlay)
src, fr, bgm, sfx, out = sys.argv[1:6]
T = json.load(open(fr + '.tl.json')); DUR = T['dur']
fc = (f"[0:v]fps=30,scale=1080:1920:flags=lanczos,eq=contrast=1.04:saturation=1.06,trim=duration={DUR},setpts=PTS-STARTPTS[b0];"
      "[b0][1:v]overlay=0:0:format=auto,format=yuv420p[v];"
      "[0:a]aresample=48000,aformat=channel_layouts=stereo,highpass=f=70,acompressor=threshold=0.15:ratio=2.2:attack=8:release=150,asplit=2[nar][key];"
      f"[2:a]atrim=start=0.3,asetpts=PTS-STARTPTS,atrim=0:{DUR},aresample=48000,aformat=channel_layouts=stereo,loudnorm=I=-26:TP=-2:LRA=7,aresample=48000,"
      f"equalizer=f=1800:width_type=o:width=2:g=-4,afade=t=out:st={DUR-1.4}:d=1.4[bgm0];[bgm0][key]sidechaincompress=threshold=0.05:ratio=2:attack=20:release=300[bgm];"
      "[3:a]aresample=48000,volume=0.32[sfx];"
      "[nar][bgm][sfx]amix=inputs=3:normalize=0,loudnorm=I=-14:TP=-1.5:LRA=11,aresample=48000[a]")
cmd = ['ffmpeg', '-nostdin', '-y', '-loglevel', 'error', '-i', src, '-framerate', '30', '-i', fr + '/f%05d.png', '-i', bgm, '-i', sfx,
       '-filter_complex', fc, '-map', '[v]', '-map', '[a]', '-c:v', 'libx264', '-preset', 'slow', '-crf', '15', '-maxrate', '20M', '-bufsize', '40M', '-profile:v', 'high', '-pix_fmt', 'yuv420p',
       '-c:a', 'aac', '-b:a', '192k', '-t', str(DUR), '-movflags', '+faststart', out]
subprocess.run(cmd, check=True); print('ok', out)
