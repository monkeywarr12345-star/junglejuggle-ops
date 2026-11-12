const {chromium}=require('playwright');(async()=>{const b=await chromium.launch();const p=await b.newPage({viewport:{width:1080,height:1920}});
await p.goto('file://'+process.argv[2]);const T=await p.evaluate('TOTAL');const fps=30;const n=Math.round(T*fps);
for(let i=0;i<n;i++){await p.evaluate(t=>seek(t),i/fps);await p.screenshot({path:`${process.argv[3]}/${String(i).padStart(4,'0')}.jpg`,type:'jpeg',quality:88});}
console.log(n,T);await b.close()})()
