const {chromium}=require('playwright');
const assert=require('node:assert/strict');
const fs=require('node:fs/promises');
const path=require('node:path');
(async()=>{
  const browser=await chromium.launch({channel:process.env.PLAYWRIGHT_CHANNEL||'msedge',headless:true});
  const page=await browser.newPage({viewport:{width:1500,height:1050},reducedMotion:'reduce'});
  const errors=[];page.on('pageerror',e=>errors.push(e.message));
  try {
    await page.goto('http://127.0.0.1:5173/universe');
    await page.getByRole('heading',{name:'A universe to explore.',exact:true}).waitFor();
    await page.getByTestId('snapshot-date').waitFor({timeout:30000});
    await page.locator('.universe-loading').waitFor({state:'hidden',timeout:45000});
    await fs.mkdir(path.resolve(__dirname,'../tmp/universe'),{recursive:true});
    await page.screenshot({path:path.resolve(__dirname,'../tmp/universe/desktop-3d.png'),fullPage:true});
    await page.getByRole('button',{name:'Select Mars',exact:true}).click();
    await page.getByRole('heading',{name:'Mars',exact:true}).waitFor();
    await page.getByLabel('Date and time').fill('2025-01-01T12:00');
    await page.getByRole('button',{name:'Go to date',exact:true}).click();
    await page.getByTestId('snapshot-date').filter({hasText:'2025-01-01'}).waitFor();
    assert((await page.getByTestId('planet-facts').innerText()).includes('Retrograde'));
    const dateBeforeModelSwitch=await page.getByLabel('Date and time').inputValue();
    await page.getByLabel('Show Rahu & Ketu',{exact:false}).check();
    await page.getByRole('button',{name:'Select Rahu',exact:true}).click();
    await page.getByRole('heading',{name:'Rahu',exact:true}).waitFor();
    await page.getByLabel('Show Rahu & Ketu',{exact:false}).uncheck();
    assert.equal(await page.getByRole('button',{name:'Select Moon',exact:true}).getAttribute('aria-pressed'),'true');
    await page.getByRole('button',{name:'Select Mars',exact:true}).click();
    await page.getByRole('button',{name:'Modern astronomy',exact:true}).click();
    await page.getByTestId('snapshot-model').filter({hasText:'Modern'}).waitFor();
    assert.equal(await page.getByLabel('Date and time').inputValue(),dateBeforeModelSwitch);
    assert.equal(await page.getByRole('button',{name:'Select Mars',exact:true}).getAttribute('aria-pressed'),'true');
    await page.getByRole('button',{name:'Select Neptune',exact:true}).click();
    await page.getByRole('heading',{name:'Neptune',exact:true}).waitFor();
    await page.getByRole('button',{name:'Surya Siddhanta',exact:true}).click();
    await page.getByText('Neptune is outside the historical model.',{exact:false}).waitFor();
    await page.getByRole('button',{name:'Select Earth',exact:true}).click();
    await page.getByRole('button',{name:'2D map',exact:true}).click();
    await page.getByRole('img',{name:'Interactive universe map'}).waitFor();
    const original=await page.getByLabel('Date and time').inputValue();
    await page.getByRole('button',{name:'Mars moves backward',exact:false}).click();
    await page.getByRole('button',{name:'Next step',exact:true}).click();
    await page.getByRole('button',{name:'Replay tour',exact:true}).click();
    await page.getByRole('button',{name:'Exit tour',exact:true}).click();
    assert.equal(await page.getByLabel('Date and time').inputValue(),original);
    await page.getByRole('tab',{name:'Ask Surya',exact:true}).click();
    await page.route('**/api/chat',route=>route.fulfill({status:503,contentType:'application/json',body:JSON.stringify({detail:'Chat is not configured'})}));
    await page.getByLabel('Your question').fill('Why is Earth here?');
    await page.getByRole('button',{name:'Send question',exact:true}).click();
    await page.getByText('Chat is not configured',{exact:false}).waitFor();
    await page.unroute('**/api/chat');
    let chatPayload;
    await page.route('**/api/chat',route=>{
      chatPayload=route.request().postDataJSON();
      return route.fulfill({status:200,contentType:'application/json',body:JSON.stringify({
        session_id:'browser-scene-test',reply:'This is a sourced explanation.',tool_uses:[],
        sources:[{id:'SS.2.39',kind:'verse',chapter:2,verse:39,page:null,label:'SS 2.39',snippet:'Historical method'}],
        demonstrations:[{id:'retrograde',label:'Mars moves backward'},{id:'invented-command',label:'Unsupported action'}],
      })});
    });
    await page.getByRole('button',{name:'New conversation',exact:true}).click();
    await page.getByLabel('Your question').fill('Explain this world.');
    const dateBeforeAnswer=await page.getByLabel('Date and time').inputValue();
    await page.getByRole('button',{name:'Send question',exact:true}).click();
    await page.getByText('This is a sourced explanation.',{exact:true}).waitFor();
    assert.equal(chatPayload.explorer.body,'Earth');assert.equal(chatPayload.explorer.model,'historical');
    assert.notEqual(chatPayload.client_now,chatPayload.explorer.instant);
    assert.equal(await page.getByLabel('Date and time').inputValue(),dateBeforeAnswer,'answers cannot automatically change the scene');
    assert.equal(await page.getByRole('button',{name:'Show me: Unsupported action',exact:false}).count(),0);
    await page.getByRole('button',{name:'Select Mars',exact:true}).click();
    assert.equal(await page.getByRole('tab',{name:'Planet details',exact:true}).getAttribute('aria-selected'),'true','selecting a planet opens its facts');
    await page.getByRole('button',{name:'Select Earth',exact:true}).click();
    await page.getByRole('tab',{name:'Ask Surya',exact:true}).click();
    await page.getByText('Sources for this answer',{exact:true}).click();
    await page.getByRole('link',{name:'SS 2.39',exact:true}).waitFor();
    await page.getByRole('button',{name:'Show me: Mars moves backward',exact:false}).click();
    await page.getByRole('heading',{name:'Start before the reversal',exact:true}).waitFor();
    await page.getByRole('button',{name:'Exit tour',exact:true}).click();
    assert.equal(await page.getByLabel('Date and time').inputValue(),dateBeforeAnswer);
    await page.getByRole('tab',{name:'Planet details',exact:true}).click();
    await page.locator('.universe-loading').waitFor({state:'hidden',timeout:45000});
    for(const [width,height,label] of [[1500,1050,'desktop'],[390,844,'mobile']]) {
      await page.setViewportSize({width,height});
      assert(await page.evaluate(()=>document.documentElement.scrollWidth<=innerWidth+1));
      await fs.mkdir(path.resolve(__dirname,'../tmp/universe'),{recursive:true});
      await page.screenshot({path:path.resolve(__dirname,`../tmp/universe/${label}.png`),fullPage:true});
    }
    await page.emulateMedia({colorScheme:'dark'});
    await page.screenshot({path:path.resolve(__dirname,'../tmp/universe/dark.png'),fullPage:true});
    assert.deepEqual(errors,[]);
    console.log('PASS: real API, model/time preservation, retrograde facts, nodes, 2D, tour restoration, unavailable AI, scene-context payload, sourced stub answer, allowlisted user-activated demos, responsive layouts');
  } catch(error) {
    await fs.mkdir(path.resolve(__dirname,'../tmp/universe'),{recursive:true});
    await page.screenshot({path:path.resolve(__dirname,'../tmp/universe/failure.png'),fullPage:true});
    console.error((await page.locator('.universe-page').innerText()).slice(-3000));
    throw error;
  } finally {await browser.close()}
})().catch(e=>{console.error(e);process.exit(1)});
