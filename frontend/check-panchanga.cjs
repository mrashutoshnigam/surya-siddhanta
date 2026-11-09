const os = require('node:os');
const { chromium } = require(process.env.PLAYWRIGHT_MODULE || 'playwright');
const assert = require('node:assert/strict');
const fs = require('node:fs/promises');
const path = require('node:path');

(async () => {
  const browser = await chromium.launch({ channel: 'msedge', headless: true });
  const page = await browser.newPage({ viewport: { width: 1280, height: 900 } });
  page.setDefaultTimeout(6000);
  const glossary = await fs.readFile(path.join(__dirname, '../src/suryasiddhanta/data/glossary.json'), 'utf8');
  await page.route('**/api/glossary', route => route.fulfill({ contentType: 'application/json', body: glossary }));
  let tithi;
  await page.route('**/api/calc/panchanga', route => route.fulfill({
    contentType: 'application/json',
    body: JSON.stringify({
      tithi,
      vara: { number: 0, name: 'Ravivara' },
      nakshatra: { number: 14, name: 'Chitra', pada: 4 },
      yoga: { number: 2 }, karana: { number: 56 },
      masa: { number: 7, name: 'Kartika' },
      ritu: { number: 4, name: 'Sharad' },
      samvatsara: { number: 53, name: 'Raudra' },
      sun_longitude: 200, moon_longitude: 164.06, ayanamsha: 22.913,
      summary: '',
    }),
  }));
  try {
    for (const [number, name, paksha] of [
      [28, 'Trayodashi', 'Krishna'], [13, 'Trayodashi', 'Shukla'],
      [15, 'Purnima', 'Shukla'], [30, 'Amavasya', 'Krishna'],
    ]) {
      tithi = { number, name, paksha, fraction: 0.005 };
      await page.goto('http://127.0.0.1:5173/panchanga');
      const row = page.locator('tr').filter({ has: page.getByRole('rowheader', { name: 'Tithi', exact: true }) });
      await row.waitFor();
      assert.equal(await row.locator('td').innerText(), `${name} (${paksha} paksha) — #${number} (0.5% elapsed)`);
    }
    await page.setViewportSize({ width: 390, height: 844 });
    assert(await page.evaluate(() => document.documentElement.scrollWidth <= innerWidth + 1));
    await fs.mkdir(path.join(os.tmpdir(), "surya-siddhanta-checks", 'panchanga'), { recursive: true });
    await page.screenshot({ path: path.join(os.tmpdir(), "surya-siddhanta-checks", 'panchanga/tithi-mobile.png'), fullPage: true });
    console.log('PASS: named tithis, both pakshas, full/new moon, elapsed percentage, mobile layout');
  } finally {
    await browser.close();
  }
})().catch(error => { console.error(error); process.exit(1); });
