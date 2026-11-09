// Controlled response ordering exercises the real hook through its UI, without
// relying on network timing or the expensive astronomy trajectory calculation.
const {chromium}=require('playwright');
const assert=require('node:assert/strict');
const DAY=86400;
function windowResponse(request) {
 const start=Date.parse(request.start)/1000,end=start+request.days*DAY;
 const positions={Earth:[0,0,0],Sun:[1,0,0],Moon:[0,1,0]};
 const velocities=Object.fromEntries(Object.keys(positions).map(body=>[body,[0,0,0]]));
 return {model:request.model,origin:'Earth',frame:'SS sidereal ecliptic',units:'yojanas',velocity_units:'yojanas/day',
  time_scale:'Ujjain mean time',provenance:'Deterministic browser fixture',start:request.start,end:new Date(end*1000).toISOString(),
  angular_tolerance_arcsec:1,samples:[{timestamp:start,positions,velocities},{timestamp:end,positions,velocities}]};
}
(async()=>{
 const browser=await chromium.launch({channel:process.env.PLAYWRIGHT_CHANNEL||'msedge',headless:true});
 const page=await browser.newPage({viewport:{width:1200,height:1000},reducedMotion:'reduce'});
 page.setDefaultTimeout(10000);
 const errors=[];page.on('pageerror',error=>errors.push(error.message));
 try {
  await page.addInitScript(()=>{
   Date.now=()=>Date.parse('2026-11-06T12:00:00Z');
   const original=HTMLCanvasElement.prototype.getContext;
   HTMLCanvasElement.prototype.getContext=function(type,...rest){return /^webgl/.test(type)?null:original.call(this,type,...rest);};
  });
  let initialSeen;
  const initialRequest=new Promise(resolve=>{initialSeen=resolve;});
  const pending=[];let initialReleased=false,futureFailures=0;
  await page.route('**/api/explorer/trajectory',route=>{
   const request=route.request().postDataJSON();
   if(request.start.startsWith('2026-')&&!initialReleased){pending.push(route);initialSeen();return;}
   if(request.start.startsWith('2025-01-14')) {
    futureFailures++;
    return route.fulfill({status:503,contentType:'application/json',body:JSON.stringify({detail:'Prefetched window failed'})});
   }
   return route.fulfill({status:200,contentType:'application/json',body:JSON.stringify(windowResponse(request))});
  });
  await page.goto('http://127.0.0.1:5173/universe');
  await initialRequest;
  await page.getByLabel('Timezone',{exact:true}).selectOption('0');
  await page.getByLabel('Date and time').fill('2025-01-01T12:00');
  await page.getByRole('button',{name:'Go to date',exact:true}).click();
  await page.locator('.universe-loading').waitFor({state:'hidden'});
  await page.getByRole('button',{name:'Play simulation'}).click();
  const delayedFailure=page.waitForResponse(response=>response.url().endsWith('/explorer/trajectory')&&response.status()===503&&response.request().postDataJSON().start.startsWith('2026-'));
  initialReleased=true;
  for(const route of pending)await route.fulfill({status:503,contentType:'application/json',body:JSON.stringify({detail:'Delayed old-date failure'})}).catch(error=>{
   if(!route.request().failure())throw error; // StrictMode's cancelled first request is harmless.
  });
  await delayedFailure;
  await page.waitForTimeout(300);
  assert.equal(await page.getByText('Delayed old-date failure',{exact:false}).count(),0,'an irrelevant late failure must not show a global error');
  assert.equal(await page.getByRole('button',{name:'Pause simulation'}).count(),1,'an irrelevant late failure must not pause the active date');
  await page.getByRole('button',{name:'Pause simulation'}).click();

  // Returning to a cached failed window must expose its error and a usable retry.
  await page.getByLabel('Date and time').fill('2026-11-06T12:00');
  await page.getByRole('button',{name:'Go to date',exact:true}).click();
  await page.getByText('Delayed old-date failure',{exact:false}).waitFor();
  await page.getByRole('button',{name:'Retry motion',exact:true}).click();
  await page.locator('.universe-loading').waitFor({state:'hidden'});

  // A failed prefetch is irrelevant until playback needs that window.
  await page.getByLabel('Date and time').fill('2025-01-13T12:00');
  await page.getByRole('button',{name:'Go to date',exact:true}).click();
  await page.locator('.universe-loading').waitFor({state:'hidden'});
  await page.getByLabel('Speed',{exact:true}).selectOption('3600');
  const prefetchFailure=page.waitForResponse(response=>response.url().endsWith('/explorer/trajectory')&&response.status()===503&&response.request().postDataJSON().start.startsWith('2025-01-14'));
  await page.getByRole('button',{name:'Play simulation'}).click();
  await prefetchFailure;
  await page.waitForTimeout(200);
  assert.equal(futureFailures,1);
  assert.equal(await page.getByText('Prefetched window failed',{exact:false}).count(),0,'unused prefetch errors must not interrupt playback');
  assert.equal(await page.getByRole('button',{name:'Pause simulation'}).count(),1);
  await page.getByLabel('Speed',{exact:true}).selectOption(String(30*DAY));
  await page.getByText('Prefetched window failed',{exact:false}).waitFor();
  assert(await page.getByRole('button',{name:'Play simulation'}).isDisabled(),'a needed failed window must provide recovery');

  // A jump to a successful cached window must clear the old error immediately.
  await page.getByLabel('Date and time').fill('2025-01-01T12:00');
  await page.getByRole('button',{name:'Go to date',exact:true}).click();
  await page.locator('.universe-loading').waitFor({state:'hidden'});
  assert(await page.getByRole('button',{name:'Play simulation'}).isEnabled());
  assert.equal(await page.getByText('Prefetched window failed',{exact:false}).count(),0);
  assert.deepEqual(errors,[]);
  console.log('PASS: late irrelevant failure, failed-window revisit/retry, prefetch failure isolation, needed-window failure, cached-date recovery');
 } finally {await browser.close();}
})().catch(error=>{console.error(error);process.exit(1);});
