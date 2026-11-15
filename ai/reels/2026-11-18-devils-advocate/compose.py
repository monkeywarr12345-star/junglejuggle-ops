import subprocess, sys
# usage: compose.py A|B video_src frames_dir out_prefix
V, src, fr, out = sys.argv[1:5]
M = '/home/claude/main/media/ai/2026-11-18-devils-advocate'
DUR, CUT = 20.48, 15.852
TAIL = {'A': 21.3, 'B': 22.6}[V]          # where the closing shot starts in the source
nC = round(CUT*30); nT = round(DUR*30) - nC
if V == 'A':
    pre = "scale=1080:1920:flags=lanczos,unsharp=5:5:0.4"
    place = "[bg]null[base]"
else:
    pre = "scale=1080:608:flags=lanczos,unsharp=5:5:0.3"
    place = "color=c=0x0a0a0b:s=1080x1920:r=30[blk];[blk][bg]overlay=0:500:shortest=1[base]"
fc = (f"[0:v]fps=30,{pre},split=2[x1][x2];"
      f"[x1]trim=start=0:end_frame={nC},setpts=PTS-STARTPTS[a1];"
      f"[x2]trim=start={TAIL},setpts=PTS-STARTPTS,trim=end_frame={nT}[a2];"
      f"[a1][a2]concat=n=2:v=1:a=0,setpts=N/30/TB,eq=contrast=1.04:saturation=1.03[bg];{place};"
      f"[base][1:v]overlay=0:0:format=auto,format=yuv420p[v];"
      # audio: narration (2), sfx (3), ludyte music (0)
      f"[2:a]aresample=48000,aformat=channel_layouts=stereo,volume=1.0,asplit=2[nar][key];"
      f"[3:a]aresample=48000,aformat=channel_layouts=stereo,volume=0.55[sfx];"
      f"[0:a]atrim=0:{DUR},asetpts=PTS-STARTPTS,aresample=48000,loudnorm=I=-25:TP=-3:LRA=7,aresample=48000,afade=t=out:st={DUR-1.2}:d=1.2[mus];"
      f"[mus][key]sidechaincompress=threshold=0.05:ratio=4:attack=30:release=400[duck];")
def run(music, path):
    f = fc.replace('{mv}', '0.55' if V=='B' else '0.8')
    if music:
        f += "[nar][sfx][duck]amix=inputs=3:normalize=0,loudnorm=I=-15:TP=-1.5:LRA=11,aresample=48000[a]"
    else:
        f += "[duck]anullsink;[nar][sfx]amix=inputs=2:normalize=0,loudnorm=I=-15:TP=-1.5:LRA=11,aresample=48000[a]"
    cmd = ['ffmpeg','-nostdin','-y','-loglevel','error','-i',src,'-framerate','30','-i',f'{fr}/f%05d.png',
           '-i',f'{M}/narration.wav','-i',f'{M}/sfx.wav','-filter_complex',f,'-map','[v]','-map','[a]',
           '-c:v','libx264','-preset','veryfast','-crf','18','-c:a','aac','-b:a','192k','-t',str(DUR),'-movflags','+faststart',path]
    subprocess.run(cmd, check=True)
run(True, out + '_music.mp4'); run(False, out + '_nomusic.mp4'); print('ok')
