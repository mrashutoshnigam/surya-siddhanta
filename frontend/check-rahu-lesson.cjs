const os = require('node:os');
const {chromium}=require(process.env.PLAYWRIGHT_MODULE || 'playwright');
const assert=require('node:assert/strict');
const fs=require('node:fs/promises');
const path=require('node:path');
(async()=>{
 const browser=await chromium.launch({channel:'msedge',headless:true});
 const page=await browser.newPage({viewport:{width:1500,height:1100}});page.setDefaultTimeout(6000);
 try {
  await page.goto('http://127.0.0.1:5173/learn/rahu');
  await page.getByText('Showing 2026-11-04 · Ujjain mean time',{exact:true}).waitFor();
  const response=await page.request.post('http://127.0.0.1:8000/book/chapter/1',{data:{year:2026,month:11,day:4}});
  const node=(await response.json()).cards['i.43-44'].rows.find(r=>r.planet==='Moon');
  assert((await page.locator('.node-values').innerText()).includes(node.longitude.toFixed(4)));
  assert((await page.locator('.node-values').innerText()).includes(((node.longitude+180)%360).toFixed(4)));
  await page.getByRole('button',{name:'Phase and node alignment'}).click();
  await page.getByRole('button',{name:'Check my answer'}).click();
  assert((await page.locator('.lab-feedback').innerText()).includes('Correct.'));
  const [download]=await Promise.all([page.waitForEvent('download'),page.getByRole('button',{name:'Download this calculation'}).click()]);
  const data=JSON.parse(await fs.readFile(await download.path(),'utf8'));
  assert.equal(data.ascending_node,node.longitude);assert.equal(data.event_prediction,false);
  await page.getByLabel('Month',{exact:true}).fill('2');await page.getByLabel('Day',{exact:true}).fill('31');
  assert(await page.getByRole('button',{name:'Download this calculation'}).isDisabled());
  await page.getByRole('button',{name:'Reset demo'}).click();
  await page.getByText('Showing 2026-11-04 · Ujjain mean time',{exact:true}).waitFor();
  await page.route('**/api/book/chapter/1',r=>r.abort());
  await page.getByLabel('Day',{exact:true}).fill('5');
  await page.getByRole('button',{name:'Retry calculation'}).waitFor();
  assert(await page.getByRole('button',{name:'Download this calculation'}).isDisabled());
  await page.unroute('**/api/book/chapter/1');
  await page.getByRole('button',{name:'Retry calculation'}).click();
  await page.getByText('Showing 2026-11-05 · Ujjain mean time',{exact:true}).waitFor();
  await page.setViewportSize({width:390,height:844});
  assert(await page.evaluate(()=>document.documentElement.scrollWidth<=innerWidth+1));
  await fs.mkdir(path.join(os.tmpdir(), "surya-siddhanta-checks", 'learning-paths'),{recursive:true});
  await page.screenshot({path:path.join(os.tmpdir(), "surya-siddhanta-checks", 'learning-paths/rahu.png'),fullPage:true});
  console.log('PASS: Rahu node values, opposite node, concept quiz, export, invalid date, failure/retry and mobile');
 }finally{await browser.close()}
})().catch(e=>{console.error(e);process.exit(1)});
