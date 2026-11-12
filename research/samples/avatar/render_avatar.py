import sys,json,wave,struct,math,subprocess,os
from playwright.sync_api import sync_playwright
wav,html,out=sys.argv[1:4]
w=wave.open(wav);sr=w.getframerate();n=w.getnframes();ch=w.getnchannels();sw=w.getsampwidth()
raw=w.readframes(n);w.close()
fmt={2:'h',4:'i'}[sw];vals=struct.unpack('<'+fmt*(len(raw)//sw),raw)[::ch];peak=float(2**(8*sw-1))
FPS=30;step=sr//FPS;env=[]
for i in range(0,len(vals),step):
    seg=vals[i:i+step];env.append(math.sqrt(sum((v/peak)**2 for v in seg)/max(len(seg),1)))
m=max(env) or 1;env=[min(1,e/m*1.3) for e in env];dur=len(vals)/sr
os.makedirs('frames',exist_ok=True)
with sync_playwright() as p:
    b=p.chromium.launch();pg=b.new_page(viewport={'width':1080,'height':1920})
    pg.add_init_script('window.ENV='+json.dumps(env));pg.goto('file://'+os.path.abspath(html))
    N=int(dur*FPS)
    for i in range(N):
        pg.evaluate(f'seek({i/FPS})');pg.screenshot(path=f'frames/{i:05d}.jpg',type='jpeg',quality=88)
    b.close()
subprocess.run(['ffmpeg','-loglevel','error','-y','-framerate',str(FPS),'-i','frames/%05d.jpg','-i',wav,'-c:v','libx264','-pix_fmt','yuv420p','-crf','20','-c:a','aac','-shortest',out],check=True)
print('dur',dur,'frames',N)
