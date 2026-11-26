const { chromium } = require('playwright'); const fs=require('fs');
(async()=>{const [port,out,list,q]=[process.argv[2],process.argv[3],process.argv[4],process.argv[5]||'preview'];fs.mkdirSync(out,{recursive:true});
const b=await chromium.launch({args:['--use-angle=swiftshader','--enable-unsafe-swiftshader','--ignore-gpu-blocklist']});
const p=await b.newPage({viewport:{width:1080,height:1920}});
p.on('console',m=>{if(m.type()==='error')console.log('ERR',m.text())});p.on('pageerror',e=>console.log('PAGEERR',e.message));
await p.goto(`http://127.0.0.1:${port}/ov/index.html?${q}`);await p.waitForFunction(()=>window.__ready,null,{timeout:60000});
for(const t of list.split(',').map(Number)){await p.evaluate(x=>window.__timelines.main.seek(x),t);await p.screenshot({path:`${out}/t${String(t.toFixed(2)).padStart(5,'0')}.png`,omitBackground:!q.includes('preview')});}
await b.close();})().catch(e=>{console.log('FAIL',e.message);process.exit(1)});
