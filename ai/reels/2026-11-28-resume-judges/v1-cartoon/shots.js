const { chromium } = require('playwright');
(async()=>{const srv=await require('./srv.js')(__dirname);const port=srv.address().port;const [out,list]=[process.argv[2],process.argv[3]];require('fs').mkdirSync(out,{recursive:true});
const b=await chromium.launch();const p=await b.newPage({viewport:{width:1080,height:1920}});p.on('pageerror',e=>console.log('PAGEERR',e.message));
for(const h of ['','?cover']){await p.goto(`http://127.0.0.1:${port}/index.html${h}`);await p.waitForFunction(()=>window.__ready);
 const L=h?[3.2]:list.split(',').map(Number);for(const t of L){await p.evaluate(x=>window.__timelines.main.seek(x),t);await p.screenshot({path:`${out}/${h?'cover':'t'+t.toFixed(2).padStart(5,'0')}.jpg`,type:'jpeg',quality:90});}}
await b.close();srv.close();})();
