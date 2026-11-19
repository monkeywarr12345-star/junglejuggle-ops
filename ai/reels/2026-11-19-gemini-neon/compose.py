import subprocess, sys, json
# usage: compose.py src.mp4 out.mp4   (one continuous Ludyte cut, no re-ordering; last frame held to fill narration length)
src, out = sys.argv[1], sys.argv[2]
M = '/home/claude/main/media/ai/2026-11-19-gemini-neon'
T = json.load(open('tl.json')); DUR = T['dur']
has_a = bool(subprocess.run(['ffprobe', '-v', 'error', '-select_streams', 'a', '-show_entries', 'stream=index', '-of', 'csv=p=0', src], capture_output=True, text=True).stdout.strip())
fc = (f"[0:v]fps=30,scale=1080:1920:flags=lanczos:force_original_aspect_ratio=increase,crop=1080:1920,tpad=stop_mode=clone:stop_duration=3,"
      f"trim=duration={DUR},setpts=PTS-STARTPTS,eq=contrast=1.03:saturation=1.05[bg];[bg][1:v]overlay=0:0:format=auto,format=yuv420p[v];"
      "[2:a]aresample=48000,aformat=channel_layouts=stereo,highpass=f=80,acompressor=threshold=0.12:ratio=2.5:attack=8:release=120,volume=1.15[nar];"
      "[3:a]aresample=48000,aformat=channel_layouts=stereo,volume=0.55[sfx];")
if has_a:
    fc += (f"[0:a]atrim=0:{DUR},asetpts=PTS-STARTPTS,aresample=48000,aformat=channel_layouts=stereo,loudnorm=I=-24:TP=-2:LRA=8,aresample=48000,"
           f"equalizer=f=1800:width_type=o:width=2:g=-5,apad=whole_dur={DUR},afade=t=out:st={DUR-1.0}:d=1.0[amb];"
           "[nar][sfx][amb]amix=inputs=3:normalize=0,")
else:
    fc += "[nar][sfx]amix=inputs=2:normalize=0,"
fc += "loudnorm=I=-14:TP=-1.5:LRA=11,aresample=48000[a]"
subprocess.run(['ffmpeg', '-nostdin', '-y', '-loglevel', 'error', '-i', src, '-framerate', '30', '-i', 'fT/f%05d.png', '-i', f'{M}/narration.wav', '-i', f'{M}/sfx.wav',
                '-filter_complex', fc, '-map', '[v]', '-map', '[a]', '-c:v', 'libx264', '-preset', 'veryfast', '-crf', '18', '-c:a', 'aac', '-b:a', '192k',
                '-t', str(DUR), '-movflags', '+faststart', out], check=True)
print('ok', has_a)
