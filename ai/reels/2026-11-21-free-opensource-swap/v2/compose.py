import subprocess, sys, json
# usage: compose.py src.mp4 out.mp4 [music]
# one continuous Ludyte cut (no re-ordering); last frame held to fill narration length.
# music mode: Ludyte Music Studio BGM (-20 LUFS, 1.8kHz -4dB, sidechain ducked under voice, ratio 2)
src, out = sys.argv[1], sys.argv[2]
MUSIC = len(sys.argv) > 3 and sys.argv[3] == 'music'
M = '/home/claude/main/media/ai/2026-11-21-free-opensource-swap'
BGM = M + '/src/bgm_ludyte.wav'
T = json.load(open('tl.json')); DUR = T['dur']
has_a = bool(subprocess.run(['ffprobe', '-v', 'error', '-select_streams', 'a', '-show_entries', 'stream=index', '-of', 'csv=p=0', src], capture_output=True, text=True).stdout.strip())
fc = (f"[0:v]fps=30,scale=1080:1920:flags=lanczos:force_original_aspect_ratio=increase,crop=1080:1920,tpad=stop_mode=clone:stop_duration=4,"
      f"trim=duration={DUR},setpts=PTS-STARTPTS,eq=contrast=1.03:saturation=1.05[b0];[b0][1:v]overlay=0:0:format=auto,format=yuv420p[v];"
      "[2:a]aresample=48000,aformat=channel_layouts=stereo,highpass=f=80,acompressor=threshold=0.12:ratio=2.5:attack=8:release=120,volume=1.15,asplit=2[nar][key];"
      "[3:a]aresample=48000,aformat=channel_layouts=stereo,volume=0.55[sfx];")
mix = ['[nar]', '[sfx]']
amb_lufs = -28 if MUSIC else -24
if has_a:
    fc += (f"[0:a]atrim=0:{DUR},asetpts=PTS-STARTPTS,aresample=48000,aformat=channel_layouts=stereo,loudnorm=I={amb_lufs}:TP=-2:LRA=8,aresample=48000,"
           f"equalizer=f=1800:width_type=o:width=2:g=-5,apad=whole_dur={DUR},afade=t=out:st={DUR-1.0}:d=1.0[amb];")
    mix.append('[amb]')
if MUSIC:
    fc += (f"[4:a]atrim=start=0.45,asetpts=PTS-STARTPTS,atrim=0:{DUR},aresample=48000,aformat=channel_layouts=stereo,loudnorm=I=-20:TP=-2:LRA=7,aresample=48000,"
           f"equalizer=f=1800:width_type=o:width=2:g=-4,afade=t=out:st={DUR-1.6}:d=1.6[bgm0];"
           "[bgm0][key]sidechaincompress=threshold=0.05:ratio=2:attack=20:release=300[bgm];")
    mix.append('[bgm]')
else:
    fc += "[key]anullsink;"
fc += ''.join(mix) + f"amix=inputs={len(mix)}:normalize=0,loudnorm=I=-14:TP=-1.5:LRA=11,aresample=48000[a]"
cmd = ['ffmpeg', '-nostdin', '-y', '-loglevel', 'error', '-i', src, '-framerate', '30', '-i', 'fT/f%05d.png', '-i', f'{M}/narration.wav', '-i', f'{M}/sfx.wav']
if MUSIC:
    cmd += ['-i', BGM]
cmd += ['-filter_complex', fc, '-map', '[v]', '-map', '[a]', '-c:v', 'libx264', '-preset', 'veryfast', '-crf', '18', '-c:a', 'aac', '-b:a', '192k',
        '-t', str(DUR), '-movflags', '+faststart', out]
subprocess.run(cmd, check=True)
print('ok', has_a, 'music' if MUSIC else 'nomusic')
