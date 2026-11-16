import subprocess, sys, json
# usage: compose.py src.mp4 frames_dir out_prefix "s0,s1,s2,s3,s4,s5"  (source start time for each narration section)
src, fr, out, starts = sys.argv[1], sys.argv[2], sys.argv[3], [tuple(map(float,(x+':1').split(':')[:2])) for x in sys.argv[4].split(',')]
M = '/home/claude/main/media/ai/2026-11-16-stock-ai3-60'
T = json.load(open('tl_60.json')); DUR = T['dur']
bounds = [T['s'][k] for k in sorted(T['s'])]; bounds[-1] = [bounds[-1][0], DUR]
fc = f"[0:v]fps=30,scale=1080:1920:flags=lanczos,split={len(bounds)}" + ''.join(f'[x{i}]' for i in range(len(bounds))) + ';'
cat = ''
for i, ((a, b), (s0, sp)) in enumerate(zip(bounds, starts)):
    n = round(b*30) - round(a*30)
    fc += f"[x{i}]trim=start={s0},setpts=(PTS-STARTPTS)/{sp},fps=30,trim=end_frame={n}[v{i}];"; cat += f'[v{i}]'
fc += f"{cat}concat=n={len(bounds)}:v=1:a=0,setpts=N/30/TB,eq=contrast=1.04:saturation=1.05[bg];[bg][1:v]overlay=0:0:format=auto,format=yuv420p[v];"
fc += (f"[2:a]aresample=48000,aformat=channel_layouts=stereo,asplit=2[nar][key];"
       f"[3:a]aresample=48000,aformat=channel_layouts=stereo,volume=0.55[sfx];"
       f"[0:a]atrim=0:{DUR},asetpts=PTS-STARTPTS,aresample=48000,loudnorm=I=-25:TP=-3:LRA=7,aresample=48000,afade=t=out:st={DUR-1.2}:d=1.2[mus];"
       f"[mus][key]sidechaincompress=threshold=0.05:ratio=4:attack=30:release=400[duck];")
def run(music, path):
    f = fc + ("[nar][sfx][duck]amix=inputs=3:normalize=0," if music else "[duck]anullsink;[nar][sfx]amix=inputs=2:normalize=0,") + "loudnorm=I=-15:TP=-1.5:LRA=11,aresample=48000[a]"
    subprocess.run(['ffmpeg','-nostdin','-y','-loglevel','error','-i',src,'-framerate','30','-i',f'{fr}/f%05d.png','-i',f'{M}/narration.wav','-i',f'{M}/sfx.wav',
        '-filter_complex',f,'-map','[v]','-map','[a]','-c:v','libx264','-preset','veryfast','-crf','18','-c:a','aac','-b:a','192k','-t',str(DUR),'-movflags','+faststart',path], check=True)
run(True, out + '_music.mp4'); run(False, out + '_nomusic.mp4'); print('ok')
