const { chromium } = require('playwright'); const path=require('path'), fs=require('fs');
(async()=>{const [port,out,fps,list]=[process.argv[2],process.argv[3],+process.argv[4]||30,process.argv[5]];fs.mkdirSync(out,{recursive:true});
const dur=JSON.parse(fs.readFileSync('tl.json')).dur;
const b=await chromium.launch();const p=await b.newPage({viewport:{width:1080,height:1920}});
await p.goto(`http://127.0.0.1:${port}/index.html`);
const ts=list?list.split(',').map(Number):Array.from({length:Math.round(dur*fps)},(_,i)=>i/fps);
for(let i=0;i<ts.length;i++){await p.evaluate((x)=>{window.__timelines.main.seek(x,false);return 1},Math.max(ts[i],0.02));await p.screenshot({path:path.join(out,(list?'t'+ts[i]:'f'+String(i).padStart(5,'0'))+'.png'),omitBackground:true});}
await b.close();fs.writeFileSync(out+'.done',String(ts.length));})().catch(e=>{fs.writeFileSync(process.argv[3]+'.err',e.message);process.exit(1)});
