import subprocess, sys, json
# compose_split.py host.mp4(1080x1920, 31s, synced) voice.wav frames bgm.wav sfx.wav out.mp4
# layout: black canvas, host top-half crop placed at y=960 (bottom half), overlay on top (stage + full scenes + captions)
src, voice, fr, bgm, sfx, out = sys.argv[1:7]
DUR = json.load(open(fr + '.tl.json'))['dur']
fc = (
    f"[0:v]fps=30,scale=1080:1920:flags=lanczos,crop=1080:960:0:40,eq=contrast=1.03:saturation=1.03,unsharp=5:5:0.35,trim=duration={DUR},setpts=PTS-STARTPTS[h];"
    f"color=c=black:s=1080x1920:r=30:d={DUR}[bg];[bg][h]overlay=0:960[b0];"
    "[b0][2:v]overlay=0:0:format=auto,format=yuv420p[v];"
    # voice: sit it in the room (no 'floating' dry studio feel): HPF, gentle LPF, short early reflections, light comp
    "[1:a]aresample=48000,aformat=channel_layouts=mono,highpass=f=85,lowpass=f=11500,"
    "equalizer=f=220:width_type=o:width=1.2:g=1.5,equalizer=f=3200:width_type=o:width=1.5:g=-1.5,"
    "acompressor=threshold=0.18:ratio=2.2:attack=8:release=160,asplit=2[vd][vr];"
    "[vr]aecho=0.8:0.55:23|37|51:0.14|0.10|0.06,lowpass=f=6000,volume=0.85[vw];"
    "[vd][vw]amix=inputs=2:normalize=0,aformat=channel_layouts=stereo,asplit=2[nar][key];"
    f"anoisesrc=color=pink:amplitude=0.0035:d={DUR},lowpass=f=2500,aformat=channel_layouts=stereo[room];"
    f"[3:a]atrim=start=0.3,asetpts=PTS-STARTPTS,atrim=0:{DUR},aresample=48000,aformat=channel_layouts=stereo,loudnorm=I=-26:TP=-2:LRA=7,aresample=48000,"
    f"equalizer=f=1800:width_type=o:width=2:g=-4,afade=t=out:st={DUR-1.4}:d=1.4[bgm0];[bgm0][key]sidechaincompress=threshold=0.05:ratio=2:attack=20:release=300[bgm];"
    "[4:a]aresample=48000,aformat=channel_layouts=stereo,volume=0.3[sfx];"
    "[nar][room][bgm][sfx]amix=inputs=4:normalize=0,loudnorm=I=-14:TP=-1.5:LRA=11,aresample=48000[a]")
cmd = ['ffmpeg', '-nostdin', '-y', '-loglevel', 'error', '-i', src, '-i', voice, '-framerate', '30', '-i', fr + '/f%05d.png', '-i', bgm, '-i', sfx,
       '-filter_complex', fc, '-map', '[v]', '-map', '[a]', '-c:v', 'libx264', '-preset', 'slow', '-crf', '15', '-maxrate', '20M', '-bufsize', '40M',
       '-profile:v', 'high', '-pix_fmt', 'yuv420p', '-c:a', 'aac', '-b:a', '192k', '-t', str(DUR), '-movflags', '+faststart', out]
subprocess.run(cmd, check=True); print('ok', out)
