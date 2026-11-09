const {chromium}=require('playwright');
const assert=require('node:assert/strict');
const fs=require('node:fs/promises');
(async()=>{
  const browser=await chromium.launch({...(process.env.PLAYWRIGHT_CHANNEL?{channel:process.env.PLAYWRIGHT_CHANNEL}:{channel:'msedge'}),headless:true});
  const page=await browser.newPage({viewport:{width:1500,height:1050},reducedMotion:'reduce'});
  const errors=[];page.on('pageerror',e=>errors.push(e.message));
  try {
    await page.goto('http://127.0.0.1:5173/universe');
    await page.getByLabel('Surface spin', {exact:true}).waitFor({timeout:5000});
    await page.getByTestId('snapshot-date').waitFor({state:'attached',timeout:30000});
    await page.locator('.universe-loading').waitFor({state:'hidden',timeout:45000});
    await page.getByRole('button',{name:'Play simulation',exact:true}).click();
    await page.getByRole('button',{name:'Now',exact:true}).click();
    assert.equal(await page.getByRole('button',{name:'Play simulation',exact:true}).count(),1,'Now is an explicit jump and must pause');
    const canvas=page.locator('.universe-scene canvas');
    if(await canvas.count()){
      const box=await canvas.boundingBox();
      await page.mouse.move(box.x+box.width*.55,box.y+box.height*.55);
      await page.mouse.down();await page.mouse.move(box.x+box.width*.7,box.y+box.height*.65,{steps:12});await page.mouse.up();
      await page.mouse.wheel(0,-150);await page.waitForTimeout(900);
      const labelPositions=()=>page.locator('.universe-scene').evaluate(el=>{
        const canvas=el.querySelector('canvas').getBoundingClientRect();
        return Object.fromEntries([...el.querySelectorAll('.universe-planet-label')].filter(label=>getComputedStyle(label).visibility==='visible').map(label=>{const r=label.getBoundingClientRect();return [label.textContent,[r.x-canvas.x,r.y-canvas.y]];}));
      });
      const poseBefore=await labelPositions();
      await page.getByRole('button',{name:'A spin and a journey',exact:false}).click();
      await page.getByRole('heading',{name:'A globe can turn in place',exact:true}).waitFor();
      await page.waitForTimeout(400);
      await page.getByRole('button',{name:'Exit tour',exact:true}).click();await page.waitForTimeout(900);
      const poseAfter=await labelPositions();
      for(const [id,point] of Object.entries(poseBefore))if(poseAfter[id])assert(Math.hypot(point[0]-poseAfter[id][0],point[1]-poseAfter[id][1])<3,`${id}: tour must restore the camera angle and zoom`);
    }
    await page.getByRole('button',{name:'2D map',exact:true}).click();
    await page.getByLabel('Surface spin',{exact:true}).uncheck();
    await page.getByLabel('Orbital motion',{exact:true}).uncheck();
    await page.getByRole('button',{name:'Play simulation',exact:true}).click();
    const frozen=await page.getByLabel('Date and time',{exact:true}).inputValue();
    await page.waitForTimeout(400);
    assert.equal(await page.getByLabel('Date and time',{exact:true}).inputValue(),frozen);
    await page.getByRole('button',{name:'Pause simulation',exact:true}).click();
    await page.getByRole('button',{name:'Step forward one day',exact:true}).click();
    assert.notEqual(await page.getByLabel('Date and time',{exact:true}).inputValue(),frozen);
    const before=await page.getByLabel('Date and time',{exact:true}).inputValue();
    await page.getByRole('button',{name:'Mars moves backward',exact:false}).click();
    const lesson=page.getByRole('region',{name:'Active guided tour',exact:true});
    await lesson.getByRole('heading',{name:'Start before the reversal',exact:true}).waitFor();
    assert(await lesson.evaluate(el=>el.closest('.universe-observatory')!==null));
    await page.getByRole('img',{name:'Mars longitude from October 2024 to April 2025',exact:true}).waitFor({timeout:30000});
    await page.getByRole('button',{name:'Next step',exact:true}).click();
    await page.getByText('Backward in longitude',{exact:true}).waitFor();
    await page.getByLabel('Explore tour date',{exact:true}).focus();
    await page.keyboard.press('ArrowRight');
    assert.equal(await page.getByRole('button',{name:'Play simulation',exact:true}).count(),1);
    await page.getByRole('button',{name:'Exit tour',exact:true}).click();
    assert.equal(await page.getByLabel('Date and time',{exact:true}).inputValue(),before);
    assert.equal(await page.getByLabel('Surface spin',{exact:true}).isChecked(),false);
    assert.equal(await page.getByLabel('Orbital motion',{exact:true}).isChecked(),false);
    await page.getByRole('button',{name:'Select Mars',exact:true}).click();
    await page.getByRole('heading',{name:'What should I watch?',exact:true}).waitFor();
    await page.getByRole('tab',{name:'Ask Surya',exact:true}).click();
    await page.route('**/api/chat',route=>route.fulfill({status:200,contentType:'application/json',body:JSON.stringify({session_id:'lesson-context',reply:'Look at the selected motion.',sources:[],demonstrations:[],tool_uses:[]})}));
    await page.getByRole('button',{name:'Explain this motion',exact:true}).click();
    await page.getByText('Look at the selected motion.',{exact:true}).waitFor();
    const answer=await page.locator('.is-assistant .universe-message-context').innerText();
    assert(answer.includes('Mars')&&answer.includes('Surya Siddhanta'));
    await page.getByRole('button',{name:'Select Earth',exact:true}).click();
    await page.getByRole('button',{name:'Step forward one day',exact:true}).click();
    await page.getByRole('tab',{name:'Ask Surya',exact:true}).click();
    assert.equal(await page.locator('.is-assistant .universe-message-context').innerText(),answer);
    for(const [width,height,label] of [[1500,1050,'desktop-learning'],[390,844,'mobile-learning']]){
      await page.setViewportSize({width,height});
      await page.getByRole('button',{name:'Mars moves backward',exact:false}).click();
      await lesson.waitFor();
      const headingBox=await lesson.locator('h2').boundingBox(),themeBox=await page.locator('.theme-toggle').boundingBox();
      assert(headingBox.y>=themeBox.y+themeBox.height||headingBox.x+headingBox.width<=themeBox.x,'fixed theme controls must not obscure a focused tour heading');
      await page.locator('.universe-loading').waitFor({state:'hidden',timeout:45000});
      const headingColors=await lesson.locator('h2').evaluate(el=>({text:getComputedStyle(el).color,background:getComputedStyle(el.closest('section')).backgroundColor}));
      assert.notEqual(headingColors.text,'rgb(10, 11, 13)','tour headings must remain readable on the space surface');
      assert(await page.evaluate(()=>document.documentElement.scrollWidth<=innerWidth+1));
      await page.evaluate(()=>window.scrollTo(0,0));
      await fs.mkdir('../tmp/universe',{recursive:true});
      await page.screenshot({path:`../tmp/universe/${label}.png`,fullPage:true});
      await page.getByRole('button',{name:'Exit tour',exact:true}).click();
    }
    assert.deepEqual(errors,[]);
    console.log('PASS: independent motion, day stepping, scene-attached tour, exact Mars chart, keyboard scrub, restoration, beginner facts, immutable chat context, responsive layout');
  }finally{await browser.close();}
})().catch(e=>{console.error(e);process.exit(1)});
