const os = require('node:os');
const { chromium } = require('playwright');
const assert = require('node:assert/strict');
const path = require('node:path');
const fs = require('node:fs/promises');

(async () => {
  const browser = await chromium.launch({ channel: 'msedge', headless: true });
  const context = await browser.newContext({ viewport: { width: 1440, height: 1000 } });
  const page = await context.newPage();
  const errors = [];
  page.on('pageerror', error => errors.push(error.message));
  const dialog = page.getByRole('dialog', { name: 'Computational Implementation of the Surya Siddhanta' });
  try {
    await page.goto('http://127.0.0.1:5173/');
    await dialog.waitFor({ timeout: 6000 });
    for (const text of ['Ashutosh Nigam', 'M25AI2006', 'M.Tech.', 'Indian Institute of Technology Jodhpur', 'Department of Computer Science and Engineering']) {
      assert((await dialog.innerText()).includes(text));
    }
    assert.equal(await dialog.getByRole('link').count(), 5);
    assert(await dialog.getByRole('img', { name: 'IIT Jodhpur logo' }).evaluate(img => img.complete && img.naturalWidth > 0));
    for (const title of ['Project report', 'Computational edition paper', 'JPL DE440 comparison paper']) {
      const href = await dialog.getByRole('link', { name: new RegExp(title) }).getAttribute('href');
      const url = new URL(href);
      assert.equal(url.origin, 'https://github.com');
      assert(url.pathname.startsWith('/mrashutoshnigam/Surya_Siddhanta/blob/'));
      assert(url.pathname.endsWith('.pdf'));
    }
    // Keyboard focus stays inside the modal, including backward traversal.
    for (let i = 0; i < 10; i++) {
      await page.keyboard.press('Tab');
      assert(await dialog.evaluate(el => el.contains(document.activeElement)));
    }
    await page.keyboard.press('Shift+Tab');
    assert(await dialog.evaluate(el => el.contains(document.activeElement)));
    const output = path.join(os.tmpdir(), "surya-siddhanta-checks", 'project-welcome');
    await fs.mkdir(output, { recursive: true });
    await dialog.getByRole('heading', { level: 2 }).focus();
    await page.screenshot({ path: path.join(output, 'desktop.png') });
    await page.keyboard.press('Escape');
    await dialog.waitFor({ state: 'detached' });
    await page.reload();
    await page.getByRole('heading', { name: 'Planet Positions', exact: true }).waitFor();
    assert.equal(await dialog.count(), 0, 'dismissal survives reload');
    await page.getByRole('button', { name: 'About this project', exact: true }).click();
    await dialog.waitFor();
    await dialog.getByRole('button', { name: 'Explore the project' }).click();
    await dialog.waitFor({ state: 'detached' });
    assert(await page.getByRole('button', { name: 'About this project', exact: true }).evaluate(button => button === document.activeElement));
    // Direct links do not interrupt someone with an introduction.
    const fresh = await browser.newContext();
    const direct = await fresh.newPage();
    await direct.goto('http://127.0.0.1:5173/learn');
    await direct.getByRole('heading', { name: 'Choose your learning path', exact: true }).waitFor();
    assert.equal(await direct.getByRole('dialog').count(), 0);
    await direct.goto('http://127.0.0.1:5173/positions');
    await direct.getByRole('dialog').waitFor();
    await direct.getByRole('button', { name: 'Close project introduction' }).click();
    await direct.getByRole('dialog').waitFor({ state: 'detached' });
    await fresh.close();
    await page.setViewportSize({ width: 390, height: 844 });
    await page.emulateMedia({ reducedMotion: 'reduce' });
    await page.getByRole('button', { name: 'About this project', exact: true }).click();
    await dialog.waitFor();
    assert(await page.evaluate(() => document.documentElement.scrollWidth <= innerWidth + 1));
    assert(await dialog.evaluate(el => el.scrollWidth <= el.clientWidth + 1));
    await page.screenshot({ path: path.join(output, 'mobile.png') });
    await dialog.getByRole('link', { name: /Docker Hub/ }).scrollIntoViewIfNeeded();
    await dialog.getByRole('button', { name: 'Explore the project' }).click();
    await page.setViewportSize({ width: 1440, height: 1000 });
    await page.getByRole('button', { name: 'Dark', exact: true }).click();
    await page.getByRole('button', { name: 'About this project', exact: true }).click();
    await dialog.waitFor();
    await page.screenshot({ path: path.join(output, 'dark.png') });
    await page.mouse.click(4, 4);
    await dialog.waitFor({ state: 'detached' });
    const blocked = await browser.newContext();
    await blocked.addInitScript(() => {
      Storage.prototype.getItem = () => { throw new Error('Storage unavailable'); };
      Storage.prototype.setItem = () => { throw new Error('Storage unavailable'); };
    });
    const noStorage = await blocked.newPage();
    await noStorage.goto('http://127.0.0.1:5173/');
    await noStorage.getByRole('dialog').waitFor();
    await noStorage.getByRole('button', { name: 'Explore the project' }).click();
    await noStorage.getByRole('dialog').waitFor({ state: 'detached' });
    await noStorage.getByRole('button', { name: 'About this project', exact: true }).click();
    await noStorage.getByRole('dialog').waitFor();
    await blocked.close();
    assert.deepEqual(errors, []);
    console.log('PASS: first visit, content/logo/external PDF links, keyboard trap, Escape, persistence, reopen/focus restoration, fresh direct route, close/backdrop, blocked storage, mobile, dark theme');
  } finally {
    await browser.close();
  }
})().catch(error => { console.error(error); process.exit(1); });
