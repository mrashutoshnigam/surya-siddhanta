// Diagnostic measurements under emulation, not a physical-device benchmark.
const {chromium}=require('playwright');
const fs=require('node:fs/promises');
(async()=>{
 const browser=await chromium.launch({channel:process.env.PLAYWRIGHT_CHANNEL||'msedge',headless:true});
 const page=await browser.newPage({viewport:{width:390,height:844},deviceScaleFactor:1,reducedMotion:'no-preference'});
 try {
  const session=await page.context().newCDPSession(page);
  await session.send('Emulation.setCPUThrottlingRate',{rate:4});
  await session.send('Network.enable');
  await session.send('Network.emulateNetworkConditions',{offline:false,latency:80,downloadThroughput:1_500_000,uploadThroughput:750_000});
  const start=Date.now();
  await page.goto(`${process.env.EXPLORER_URL||'http://127.0.0.1:5173'}/universe`);
  await page.getByTestId('snapshot-date').waitFor({timeout:60000});
  await page.locator('.universe-loading').waitFor({state:'hidden',timeout:60000});
  const readyMs=Date.now()-start;
  await page.getByLabel('Speed',{exact:true}).selectOption('86400');
  const frames=await page.evaluate(()=>new Promise(resolve=>{
   const deltas=[];let previous=performance.now(),start=previous;
   function frame(now){deltas.push(now-previous);previous=now;if(now-start<3000)requestAnimationFrame(frame);else resolve(deltas);}
   requestAnimationFrame(frame);
  }));
  const sorted=frames.slice().sort((a,b)=>a-b);
  const result={environment:'Headless desktop browser, 390x844 viewport, 4x CPU slowdown, 80ms network latency; real local astronomy API. Not a physical phone.',url:process.env.EXPLORER_URL||'http://127.0.0.1:5173',view:await page.locator('.universe-scene canvas').count()?'3D':'2D fallback',readyMs,frames:frames.length,meanFrameMs:frames.reduce((a,b)=>a+b,0)/frames.length,p95FrameMs:sorted[Math.floor(sorted.length*.95)],measuredAt:new Date().toISOString()};
  await fs.mkdir('../tmp/universe',{recursive:true});await fs.writeFile('../tmp/universe/performance.json',JSON.stringify(result,null,2));
  console.log(JSON.stringify(result,null,2));
 }finally{await browser.close();}
})().catch(e=>{console.error(e);process.exit(1)});
