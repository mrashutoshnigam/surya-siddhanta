const { chromium } = require('playwright');
const assert = require('node:assert/strict');
const fs = require('node:fs/promises');
const path = require('node:path');

(async () => {
  const browser = await chromium.launch({ channel: 'msedge', headless: true });
  const requests = [];
  let failNext = false;
  let releaseReply;
  try {
    const context = await browser.newContext({ viewport: { width: 1440, height: 1000 } });
    await context.addInitScript(() => localStorage.setItem('ss.project-introduction.dismissed', '1'));
    // Stub only the service boundary: exercise the real app, routing and UI.
    await context.route('**/api/**', async route => {
      const url = new URL(route.request().url());
      if (url.pathname === '/api/chat') {
        const body = route.request().postDataJSON();
        requests.push(body);
        if (body.message === 'Wait for me') await new Promise(resolve => { releaseReply = resolve; });
        if (failNext) {
          failNext = false;
          return route.fulfill({ status: 503, json: { detail: 'Chat temporarily unavailable' } });
        }
        return route.fulfill({ json: {
          session_id: 'panel-session',
          reply: body.message === 'Long answer' ? `A detailed answer\n\n\`\`\`text\n${'longitude'.repeat(80)}\n\`\`\`\n\n| Body | Value |\n| --- | --- |\n| Sun | ${'1234567890'.repeat(40)} |` : `Answer to ${body.message}`,
          tool_uses: body.message === 'Long answer' ? [{ tool: 'planet_position', input: { body: 'Sun' }, result: '1234567890'.repeat(100) }] : [],
          sources: [{ id: 'ch1', kind: 'verse', chapter: 1, verse: 1, page: null, label: 'Chapter 1, verse 1', snippet: 'A verse citation' }],
        } });
      }
      if (url.pathname.endsWith('/reset')) return route.fulfill({ json: {} });
      if (url.pathname === '/api/glossary') return route.fulfill({ json: { version: 1, terms: {}, routes: {} } });
      return route.fulfill({ status: 503, json: { detail: 'Offline in UI check' } });
    });
    const page = await context.newPage();
    page.setDefaultTimeout(10000);
    const errors = [];
    page.on('pageerror', error => errors.push(error.message));
    await page.goto('http://127.0.0.1:5173/learn');
    const trigger = page.getByRole('button', { name: 'Surya Siddhanta AI', exact: true });
    assert.equal(await trigger.count(), 1, 'Sidebar AI must be a button rather than a page link');
    await trigger.click();
    console.log('Checking persistent conversation and citations');
    assert(new URL(page.url()).pathname === '/learn', 'Opening chat must preserve the current page');
    const panel = page.getByRole('dialog', { name: 'Surya Siddhanta AI', exact: true });
    await panel.waitFor();
    const input = panel.getByRole('textbox', { name: 'Message' });
    await input.fill('What is a tithi?');
    await panel.getByRole('button', { name: 'Send', exact: true }).click();
    await panel.getByText('Answer to What is a tithi?', { exact: true }).waitFor();
    assert.equal(requests[0].latitude, 23.18);
    assert.equal(requests[0].longitude, 75.78);
    // Composition Enter must not send; Shift+Enter remains a newline.
    await input.fill('Still composing');
    await input.evaluate(el => el.dispatchEvent(new KeyboardEvent('keydown', { key: 'Enter', code: 'Enter', isComposing: true, bubbles: true })));
    assert.equal(requests.length, 1);
    await input.press('Shift+Enter');
    assert.equal(requests.length, 1);
    await input.fill('My unfinished question');
    await panel.getByRole('link', { name: 'Chapter 1, verse 1', exact: true }).click();
    assert(new URL(page.url()).pathname === '/book/1');
    assert.equal(await input.inputValue(), 'My unfinished question');
    await panel.getByRole('button', { name: 'Close chat', exact: true }).click();
    await panel.waitFor({ state: 'hidden' });
    assert(await trigger.evaluate(el => el === document.activeElement));
    await page.getByRole('link', { name: 'Learning Paths', exact: true }).click();
    await trigger.click();
    assert.equal(await input.inputValue(), 'My unfinished question');
    await input.fill('Wait for me');
    await panel.getByRole('button', { name: 'Send', exact: true }).click();
    await input.press('Enter');
    await page.waitForFunction(() => document.querySelector('.chat-content')?.getAttribute('aria-busy') === 'true');
    await panel.getByRole('button', { name: 'Terms', exact: true }).click();
    await page.getByRole('complementary', { name: 'Glossary', exact: true }).waitFor();
    await panel.waitFor({ state: 'hidden' });
    assert.equal(typeof releaseReply, 'function', 'The pending chat request must reach the service');
    releaseReply();
    await page.getByRole('button', { name: 'AI chat', exact: true }).click();
    await panel.getByText('Answer to Wait for me', { exact: true }).waitFor();
    assert.equal(requests[1].session_id, 'panel-session');
    assert.equal(requests.length, 2, 'A second Enter must not duplicate an in-flight request');
    console.log('Checking failed-request retry and glossary sharing');
    assert.equal(await page.getByRole('complementary', { name: 'Glossary', exact: true }).count(), 0);
    failNext = true;
    await input.fill('Please retry this question');
    await panel.getByRole('button', { name: 'Send', exact: true }).click();
    await panel.getByRole('alert').waitFor();
    await panel.getByRole('button', { name: 'Retry', exact: true }).click();
    await panel.getByText('Answer to Please retry this question', { exact: true }).waitFor();
    assert.equal(requests.at(-1).message, 'Please retry this question');
    assert.equal(await panel.getByText('Please retry this question', { exact: true }).count(), 1, 'Retry must not duplicate the user message');

    const output = path.resolve(__dirname, '../tmp/chat-panel');
    await fs.mkdir(output, { recursive: true });
    await page.screenshot({ path: path.join(output, 'desktop.png') });
    console.log('Checking desktop docking and mobile dialog');
    await page.setViewportSize({ width: 2000, height: 1100 });
    assert(await panel.evaluate(el => !el.matches(':modal')));
    const contentBox = await page.locator('main.content').boundingBox();
    const panelBox = await panel.boundingBox();
    assert(contentBox.x + contentBox.width <= panelBox.x + 1, 'Wide desktop panel must dock beside the page');
    await panel.getByRole('button', { name: 'New chat', exact: true }).focus();
    await page.keyboard.press('Tab');
    assert(!await panel.evaluate(el => el.contains(document.activeElement)), 'Desktop chat must allow focus back to the page');
    await page.setViewportSize({ width: 390, height: 844 });
    await page.emulateMedia({ reducedMotion: 'reduce' });
    await page.waitForFunction(() => document.querySelector('#chat-panel')?.matches(':modal'));
    assert(await panel.evaluate(el => el.scrollWidth <= el.clientWidth + 1));
    assert(await page.evaluate(() => document.documentElement.scrollWidth <= innerWidth + 1));
    for (let i = 0; i < 12; i++) {
      await page.keyboard.press('Tab');
      assert(await panel.evaluate(el => el.contains(document.activeElement)), 'Mobile focus must remain inside chat');
    }
    await input.fill('Draft on mobile');
    await page.screenshot({ path: path.join(output, 'mobile.png') });
    await page.keyboard.press('Escape');
    await panel.waitFor({ state: 'hidden' });
    assert.equal(await page.evaluate(() => document.body.style.overflow), '');
    await trigger.click();
    assert.equal(await input.inputValue(), 'Draft on mobile');
    await input.fill('Long answer');
    await panel.getByRole('button', { name: 'Send', exact: true }).click();
    await panel.getByText('A detailed answer', { exact: true }).waitFor();
    await panel.getByText('1 tool call(s)', { exact: true }).click();
    assert(await panel.locator('.chat-window').evaluate(el => el.scrollWidth <= el.clientWidth + 1), 'Long Markdown and tool results must scroll inside their own surfaces');
    await panel.getByRole('button', { name: 'Terms', exact: true }).click();
    await page.getByRole('button', { name: 'AI chat', exact: true }).click();
    assert(await panel.evaluate(el => el.matches(':modal')));
    await page.setViewportSize({ width: 390, height: 500 });
    const sendBox = await panel.getByRole('button', { name: 'Send', exact: true }).boundingBox();
    assert(sendBox && sendBox.y + sendBox.height <= 500, 'Composer must remain reachable on short mobile viewports');
    await panel.getByRole('button', { name: 'Close chat', exact: true }).click();
    assert.equal(await page.getByRole('complementary', { name: 'Glossary', exact: true }).count(), 0, 'Closing chat must not resurrect the previous glossary drawer');
    await page.setViewportSize({ width: 1440, height: 1000 });
    await page.getByRole('button', { name: 'Dark', exact: true }).click();
    await trigger.click();
    await page.getByRole('button', { name: 'Light', exact: true }).click();
    await page.getByRole('button', { name: 'Dark', exact: true }).click();
    await page.screenshot({ path: path.join(output, 'dark.png') });
    await panel.getByRole('button', { name: 'New chat', exact: true }).click();
    assert.equal(await panel.locator('.chat-msg').count(), 0);
    await input.fill('A fresh conversation');
    await panel.getByRole('button', { name: 'Send', exact: true }).click();
    await panel.getByText('Answer to A fresh conversation', { exact: true }).waitFor();
    assert.equal(requests.at(-1).session_id, undefined);
    await page.goto('http://127.0.0.1:5173/chat');
    await panel.waitFor();
    await page.waitForURL('**/positions');
    assert.deepEqual(errors, []);
    // Fresh legacy links can also show the first-visit introduction. Nested
    // native modals must close in order and restore document scrolling.
    const fresh = await browser.newContext({ viewport: { width: 390, height: 844 } });
    await fresh.route('**/api/**', route => route.fulfill({ status: 503, json: { detail: 'Offline in UI check' } }));
    const legacy = await fresh.newPage();
    await legacy.goto('http://127.0.0.1:5173/chat');
    const legacyChat = legacy.getByRole('dialog', { name: 'Surya Siddhanta AI', exact: true });
    await legacyChat.waitFor();
    await legacyChat.getByRole('button', { name: 'Close chat', exact: true }).click();
    await legacy.getByRole('button', { name: 'Close project introduction', exact: true }).click();
    await legacy.getByRole('dialog', { name: 'Computational Implementation of the Surya Siddhanta' }).waitFor({ state: 'detached' });
    await legacy.waitForFunction(() => document.body.style.overflow === '');
    assert.equal(await legacy.evaluate(() => document.body.style.overflow), '');
    await fresh.close();
    console.log('PASS: sidebar chat, route/draft/session preservation, hidden in-flight reply, citations, retry, glossary sharing, mobile modal/focus/Escape, desktop docking, themes, reset, legacy /chat');
  } finally {
    releaseReply?.();
    await browser.close();
  }
})().catch(error => { console.error(error); process.exitCode = 1; });
