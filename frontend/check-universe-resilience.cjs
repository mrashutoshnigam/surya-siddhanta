const {chromium}=require('playwright');
const assert=require('node:assert/strict');
const fs=require('node:fs/promises');
const path=require('node:path');
(async()=>{
 const browser=await chromium.launch({channel:process.env.PLAYWRIGHT_CHANNEL||'msedge',headless:true});
 const page=await browser.newPage({viewport:{width:390,height:844},reducedMotion:'reduce'});
 const errors=[];page.on('pageerror',e=>errors.push(e.message));
 try {
  // Exercise the actual fallback selection, not just a manual switch.
  await page.addInitScript(()=>{
   const original=HTMLCanvasElement.prototype.getContext;
   HTMLCanvasElement.prototype.getContext=function(type,...rest){return /^webgl/.test(type)?null:original.call(this,type,...rest);};
  });
  let failures=0,fail=true;
  await page.route('**/api/explorer/trajectory',route=>{
   if(fail){failures++;return route.fulfill({status:503,contentType:'application/json',body:JSON.stringify({detail:'Temporary motion outage'})});}
   return route.continue();
  });
  await page.goto('http://127.0.0.1:5173/universe');
  await page.getByRole('img',{name:'Interactive universe map'}).waitFor();
  await page.getByText('Temporary motion outage',{exact:false}).waitFor();
  assert.equal(await page.getByRole('button',{name:'Play simulation'}).count(),1);
  const failuresAtAlert=failures; // StrictMode may cancel its first mount request.
  await page.waitForTimeout(1100);assert.equal(failures,failuresAtAlert,'failed requests must wait for user retry');
  fail=false;await page.getByRole('button',{name:'Retry motion'}).click();
  await page.locator('.universe-loading').waitFor({state:'hidden',timeout:45000});
  assert.equal(await page.getByRole('button',{name:'2D map',exact:true}).getAttribute('aria-pressed'),'true');
  const timeY=await page.locator('.universe-timeline').evaluate(e=>e.getBoundingClientRect().top);
  const panelY=await page.locator('.universe-side-panel').evaluate(e=>e.getBoundingClientRect().top);
  assert(timeY<panelY,'phone timeline stays beside the visual task');
  await page.getByRole('button',{name:'All tools',exact:false}).click();
  await page.getByRole('link',{name:'Planet Positions',exact:true}).waitFor();
  await page.getByRole('button',{name:'Close menu',exact:false}).click();
  await page.getByLabel('Date and time').fill('1500-01-01T12:00');
  await page.getByRole('button',{name:'Go to date',exact:true}).click();
  await page.getByText('Choose a valid date and time between 1550 and 2649 CE (UTC).',{exact:true}).waitFor();
  assert.equal(await page.getByLabel('Date and time').getAttribute('aria-describedby'),'universe-date-error');
  assert(await page.getByLabel('Date and time').evaluate(e=>document.activeElement===e));
  await page.getByLabel('Date and time').fill('1550-01-02T12:00');
  await page.getByRole('button',{name:'Go to date',exact:true}).click();
  await page.getByTestId('snapshot-date').filter({hasText:'1550-01-02'}).waitFor();
  await page.locator('.universe-loading').waitFor({state:'hidden',timeout:45000});
  await page.getByLabel('Speed',{exact:true}).selectOption('86400');
  await page.getByRole('button',{name:'Reverse',exact:true}).click();
  const before=Date.parse(await page.locator('.universe-time-heading time').getAttribute('datetime'));
  await page.getByRole('button',{name:'Play simulation'}).click();
  await page.waitForFunction(value=>Date.parse(document.querySelector('.universe-time-heading time').dateTime)<value-1000,before);
  await page.getByRole('button',{name:'Pause simulation'}).click();
  await page.getByRole('tab',{name:'Planet details',exact:true}).focus();
  await page.keyboard.press('ArrowRight');
  assert.equal(await page.getByRole('tab',{name:'Ask Surya',exact:true}).getAttribute('aria-selected'),'true');
  await page.keyboard.press('ArrowLeft');
  assert.equal(await page.getByRole('tab',{name:'Planet details',exact:true}).getAttribute('aria-selected'),'true');
  await fs.mkdir(path.resolve(__dirname,'../tmp/universe'),{recursive:true});
  await page.screenshot({path:path.resolve(__dirname,'../tmp/universe/fallback-mobile.png'),fullPage:true});
  assert.deepEqual(errors,[]);
  console.log('PASS: unavailable WebGL, reduced motion, failed-request recovery without retry storm, phone navigation, 1550 date, reverse playback, keyboard tabs');
 } finally {await browser.close()}
})().catch(e=>{console.error(e);process.exit(1)});
