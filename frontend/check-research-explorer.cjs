const os = require('node:os');
const { chromium } = require(process.env.PLAYWRIGHT_MODULE || 'playwright');
const assert = require('node:assert/strict');
const fs = require('node:fs/promises');
const path = require('node:path');
const data = require('./src/pages/research/research-data.json');

(async () => {
  const browser = await chromium.launch({ channel: 'msedge', headless: true });
  const page = await browser.newPage({ viewport: { width: 1500, height: 1050 }, colorScheme: 'light' });
  const out = path.join(os.tmpdir(), "surya-siddhanta-checks", "research-explorer");
  await fs.mkdir(out, { recursive: true });
  const errors = [];
  page.on('pageerror', e => errors.push(e.message));
  try {
    await page.goto('http://127.0.0.1:5173/research');
    await page.getByRole('heading', { name: 'Measure the model.' }).waitFor();
    assert.equal(await page.locator('.research-matrix tbody button').count(), 88);
    for (const variant of ['naive', 'deltat']) {
      await page.getByRole('button', { name: variant === 'naive' ? 'Naïve time' : 'Time-aligned', exact: true }).click();
      for (const body of data.bodies) {
        await page.getByLabel('Body', { exact: true }).selectOption(body);
        await page.getByLabel('Window', { exact: true }).selectOption('1550');
        const w = data.series.find(s => s.body === body && s.variant === variant).windows[0];
        const cells = page.locator('.research-stats tbody tr').nth(variant === 'naive' ? 1 : 0).locator('td');
        assert.equal(await cells.first().innerText(), w.rms.toFixed(3) + '°');
        assert.equal(await page.locator('.research-matrix button[aria-pressed="true"]').count(), 1);
      }
    }
    await page.getByRole('button', { name: /^Moon, 1550 to 1649,/ }).click();
    await page.getByRole('heading', { name: 'Moon · 1550–1649' }).waitFor();
    const [download] = await Promise.all([page.waitForEvent('download'), page.getByRole('button', { name: 'Download evidence JSON' }).click()]);
    const evidence = JSON.parse(await fs.readFile(await download.path(), 'utf8'));
    assert.equal(evidence.body, 'Moon'); assert.equal(evidence.start, 1550);
    assert.equal(evidence.deltat.n, 3652); assert.equal(evidence.sources.naive.sha256.length, 64);
    const [csv] = await Promise.all([page.waitForEvent('download'), page.getByRole('button', { name: 'Download statistics CSV' }).click()]);
    const csvText = await fs.readFile(await csv.path(), 'utf8');
    assert.equal(csvText.trim().split('\n').length, 3);
    assert(csvText.includes(evidence.sources.naive.sha256));
    assert(csvText.includes(evidence.sources.deltat.sha256));
    assert(csvText.includes('time_convention,sample_step_days'));
    await page.locator('.research-explorer > section').first().screenshot({ path: path.join(out, 'research-matrix.png') });
    await page.locator('.research-detail').screenshot({ path: path.join(out, 'research-comparison.png') });
    await page.screenshot({ path: path.join(out, 'research-desktop.png'), fullPage: true });
    await page.evaluate(() => document.documentElement.dataset.theme = 'dark');
    await page.screenshot({ path: path.join(out, 'research-dark.png'), fullPage: true });
    await page.evaluate(() => document.documentElement.dataset.theme = 'light');
    await page.setViewportSize({ width: 390, height: 844 });
    await page.screenshot({ path: path.join(out, 'research-mobile.png'), fullPage: true });
    assert(await page.evaluate(() => document.documentElement.scrollWidth <= innerWidth));
    await page.getByLabel('Body', { exact: true }).focus(); await page.keyboard.press('ArrowDown');
    assert.notEqual(await page.getByLabel('Body', { exact: true }).inputValue(), 'Moon');
    await page.setViewportSize({ width: 1500, height: 1050 });
    await page.goto('http://127.0.0.1:5173/learn/mars');
    await page.getByText('Showing 2026-11-04 · Ujjain mean time', { exact: true }).waitFor();
    await page.locator('.lab-steps button').last().click();
    await page.locator('.lab-experiment').screenshot({ path: path.join(out, 'mars-learning-lab.png') });
    assert.deepEqual(errors, []);
    console.log('PASS: 88 matrix cells, 16 body/treatment selections, both exports, keyboard selection, mobile overflow and screenshots.');
  } finally { await browser.close(); }
})().catch(e => { console.error(e); process.exitCode = 1; });
