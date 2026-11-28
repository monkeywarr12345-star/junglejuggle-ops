const { chromium } = require('playwright');
(async()=>{const srv=await require('./srv.js')(__dirname);const port=srv.address().port;const [out,list,q]=[process.argv[2],process.argv[3],process.argv[4]||'still'];require('fs').mkdirSync(out,{recursive:true});
const b=await chromium.launch();const p=await b.newPage({viewport:{width:1080,height:1920}});p.on('pageerror',e=>console.log('PAGEERR',e.message));
await p.goto(`http://127.0.0.1:${port}/index.html?${q}`);await p.waitForFunction(()=>window.__ready);
for(const t of list.split(',').map(Number)){await p.evaluate(x=>window.__timelines.main.seek(x),t);await p.screenshot({path:`${out}/${q}_${t.toFixed(2).padStart(5,'0')}.png`,omitBackground:q.includes('tr')});}
await b.close();srv.close();})();
