const os = require('node:os');
const { chromium } = require(process.env.PLAYWRIGHT_MODULE || 'playwright');
const assert = require('node:assert/strict');
const fs = require('node:fs/promises');
const path=require('node:path');
const bodies = (process.env.LESSON_BODIES || 'Sun,Moon,Mars,Mercury,Venus,Jupiter,Saturn').split(',');
(async () => {
 const browser = await chromium.launch({channel:'msedge',headless:true});
 const page = await browser.newPage({viewport:{width:1500,height:1100}});
 page.setDefaultTimeout(6000);
 const errors=[]; page.on('pageerror', e=>errors.push(e.message));
 try {
  await page.goto('http://127.0.0.1:5173/learn');
  await page.getByRole('heading',{name:'Choose your learning path',exact:true}).waitFor({timeout:5000});
  assert.equal(await page.locator('.path-list a').count(),8);
  for (const body of bodies) {
   await page.goto(`http://127.0.0.1:5173/learn/${body.toLowerCase()}`);
   await page.getByText('Showing 2026-11-04 · Ujjain mean time',{exact:true}).waitFor();
   const response=await page.request.post('http://127.0.0.1:8000/book/chapter/2',{data:{year:2026,month:11,day:4}});
   const payload=await response.json();
   const row=payload.cards['ii.43-45'].rows.find(r=>r.body===body);
   assert.equal(await page.locator('.lab-steps button').count(),row.stages.length);
   for(let i=0;i<row.stages.length;i++) {
    const button=page.locator('.lab-steps button').nth(i);
    assert((await button.innerText()).includes(row.stages[i].longitude.toFixed(4)));
    await button.click();
    assert((await page.locator('.lab-dial title').first().textContent()).includes(row.stages[i].longitude.toFixed(4)));
   }
   const [download]=await Promise.all([page.waitForEvent('download'),page.getByRole('button',{name:'Download this calculation'}).click()]);
   const data=JSON.parse(await fs.readFile(await download.path(),'utf8'));
   assert.equal(data.body,body); assert.equal(data.true_longitude,row.true_longitude);
   if(body==='Sun') {
    const day=payload.cards['ii.60-63'];
    assert.equal(data.lesson_context.day_ghatis,day.day_ghatis);
    assert((await page.locator('.lesson-context').innerText()).includes(day.day_ghatis.toFixed(3)));
   }
   if(body==='Moon') {
    const t=payload.cards['ii.66'];
    assert.equal(data.lesson_context.number,t.number);
    assert((await page.locator('.lesson-context').innerText()).includes(t.elongation.toFixed(4)));
    assert((await page.locator('.lesson-context').innerText()).includes(`Tithi ${t.number}`));
   }
   if(['Mercury','Venus','Jupiter','Saturn'].includes(body)) {
    assert.equal(data.lesson_context.sun_longitude,payload.cards['ii.66'].sun);
    const other={Mercury:'Venus',Venus:'Mercury',Jupiter:'Saturn',Saturn:'Jupiter'}[body];
    const comparison=payload.cards['ii.43-45'].rows.find(r=>r.body===other);
    assert((await page.locator('.lesson-context').innerText()).includes(comparison.true_longitude.toFixed(4)));
   }
   await page.setViewportSize({width:390,height:844});
   assert(await page.evaluate(()=>document.documentElement.scrollWidth<=innerWidth+1));
   await fs.mkdir(path.join(os.tmpdir(), "surya-siddhanta-checks", 'learning-paths'),{recursive:true});
   await page.screenshot({path:path.join(os.tmpdir(), "surya-siddhanta-checks", `learning-paths/${body.toLowerCase()}.png`),fullPage:true});
   await page.setViewportSize({width:1500,height:1100});
   if(body==='Mercury') {
    await page.getByLabel('Day',{exact:true}).fill('6');
    await page.getByText('Showing 2026-11-06 · Ujjain mean time',{exact:true}).waitFor();
    await page.getByRole('link',{name:'Explore Venus',exact:false}).click();
    await page.getByText('Showing 2026-11-06 · Ujjain mean time',{exact:true}).waitFor();
   }
  }
  assert.deepEqual(errors,[]); console.log(`PASS: learning directory and real API stages/exports/mobile for ${bodies.join(', ')}`);
 } finally { await browser.close(); }
})().catch(e=>{console.error(e);process.exit(1)});
