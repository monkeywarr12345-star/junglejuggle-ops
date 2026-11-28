const { chromium } = require('playwright');
(async()=>{const srv=await require('./srv.js')(__dirname);const port=srv.address().port;
const b=await chromium.launch();const p=await b.newPage({viewport:{width:1080,height:1920}});p.on('pageerror',e=>console.log('PAGEERR',e.message));
await p.goto(`http://127.0.0.1:${port}/index.html?cover`);await p.waitForFunction(()=>window.__ready);await p.waitForTimeout(300);
await p.screenshot({path:'cover.png'});await b.close();srv.close();})();
