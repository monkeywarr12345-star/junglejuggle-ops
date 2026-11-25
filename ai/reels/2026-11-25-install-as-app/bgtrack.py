import json, subprocess, os
T = json.load(open('ov/tl.json')); D = T['dur']
os.makedirs('bgseg', exist_ok=True)
def run(c): subprocess.run(c, check=True)
# 1) bg ping-pong loop (seamless) long enough for whole reel
if not os.path.exists('hv/bgloop.mp4'):
    run(['ffmpeg','-nostdin','-v','error','-y','-i','hv/bg.mp4','-filter_complex',
         '[0:v]fps=30,scale=1080:1920:force_original_aspect_ratio=increase,crop=1080:1920,setsar=1,split[a][b];[b]reverse[r];[a][r]concat=n=2:v=1[o]',
         '-map','[o]','-c:v','libx264','-crf','14','-preset','fast','-pix_fmt','yuv420p','hv/bgpp.mp4'])
    run(['ffmpeg','-nostdin','-v','error','-y','-stream_loop','3','-i','hv/bgpp.mp4','-c','copy','hv/bgloop.mp4'])
# 2) segments: (start, end, source, source_offset, dy, scale)
SEG = [
    (0.0, 3.45, 'hook', 0.0, 0, 1.0, 1.7),
    (3.45, 29.12, 'bgloop', 3.45, 0, 1.0),
    (29.12, 36.4, 'gate', 0.0, -250, 1.0),
    (36.4, 42.6, 'warn', 0.0, 0, 1.0),
    (42.6, 46.55, 'vs', 0.0, -380, 1.0),
    (46.55, D, 'cta', 0.0, 0, 1.0),
]
if os.path.exists('bgseg.json'): SEG = json.load(open('bgseg.json'))
lst = []
for k, sg in enumerate(SEG):
    a, b, src, off, dy, sc = sg[:6]; sp = sg[6] if len(sg) > 6 else 1.0
    dur = b - a; out = f'bgseg/s{k:02d}.mp4'
    sc = max(sc, 1 + 2 * abs(dy) / 1920 + 0.004)
    W, H = int(1080 * sc) // 2 * 2, int(1920 * sc) // 2 * 2
    cy = min(max((H - 1920) // 2 - dy, 0), H - 1920)
    vf = (f'setpts=PTS/{sp},fps=30,scale={W}:{H}:force_original_aspect_ratio=increase,crop={W}:{H},'
          f'crop=1080:1920:{(W-1080)//2}:{cy},'
          f'tpad=stop_mode=clone:stop_duration=10,trim=0:{dur:.4f},setpts=PTS-STARTPTS,setsar=1')
    key=json.dumps(sg)
    if os.path.exists(out) and os.path.exists(out+'.key') and open(out+'.key').read()==key:
        lst.append(f"file '{os.path.abspath(out)}'"); continue
    run(['ffmpeg','-nostdin','-v','error','-y','-ss',f'{off:.3f}','-i',f'hv/{src}.mp4','-vf',vf,'-an',
         '-c:v','libx264','-crf','14','-preset','fast','-pix_fmt','yuv420p','-r','30',out])
    open(out+'.key','w').write(key)
    lst.append(f"file '{os.path.abspath(out)}'")
open('bgseg/list.txt','w').write('\n'.join(lst))
# 3) concat + unified grade + grain
run(['ffmpeg','-nostdin','-v','error','-y','-f','concat','-safe','0','-i','bgseg/list.txt',
     '-vf','eq=contrast=1.04:saturation=0.92,format=yuv420p','-t',f'{D:.3f}',
     '-c:v','libx264','-crf','16','-preset','fast','-r','30','bgtrack.mp4'])
print('ok')
