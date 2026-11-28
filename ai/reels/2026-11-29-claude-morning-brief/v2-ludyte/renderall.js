const { chromium } = require('playwright'); const fs=require('fs');
(async()=>{const srv=await require('./srv.js')(__dirname);const port=srv.address().port;const [out,a,b]=[process.argv[2],+process.argv[3],+process.argv[4]];fs.mkdirSync(out,{recursive:true});
const br=await chromium.launch();const p=await br.newPage({viewport:{width:1080,height:1920}});p.on('pageerror',e=>console.log('PAGEERR',e.message));
await p.goto(`http://127.0.0.1:${port}/index.html?tr`);await p.waitForFunction(()=>window.__ready,null,{timeout:60000});
for(let i=a;i<b;i++){await p.evaluate(x=>window.__timelines.main.seek(x),i/30);await p.screenshot({path:`${out}/f${String(i).padStart(5,"0")}.png`,omitBackground:true});}
await br.close();srv.close();})().catch(e=>{console.log('FAIL',e.message);process.exit(1)});
