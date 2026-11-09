const os = require('node:os');
const { chromium } = require(process.env.PLAYWRIGHT_MODULE || 'playwright');
const assert = require('node:assert/strict');
const fs = require('node:fs/promises');
const path = require('node:path');

(async () => {
  const browser = await chromium.launch({ channel: 'msedge', headless: true });
  const page = await browser.newPage({ viewport: { width: 1280, height: 900 }, timezoneId: 'Asia/Kolkata' });
  await page.clock.setFixedTime(new Date('2026-11-09T07:04:00Z'));
  page.setDefaultTimeout(6000);
  const glossary = await fs.readFile(path.join(__dirname, '../src/suryasiddhanta/data/glossary.json'), 'utf8');
  await page.route('**/api/glossary', route => route.fulfill({ contentType: 'application/json', body: glossary }));
  let tithi;
  const requests = [];
  let holdNext = false;
  let heldRequest;
  await page.route('**/api/calc/panchanga', async route => {
    const request = route.request().postDataJSON();
    requests.push(request);
    const held = holdNext;
    holdNext = false;
    if (held) await new Promise(resolve => { heldRequest = resolve; });
    const minute = Math.round((request.day - Math.floor(request.day)) * 1440);
    const zoneMinutes = Math.round(Math.abs(request.utc_offset) * 60);
    const at = `${request.year}-${String(request.month).padStart(2, '0')}-${String(Math.floor(request.day)).padStart(2, '0')} ${String(Math.floor(minute / 60)).padStart(2, '0')}:${String(minute % 60).padStart(2, '0')} (UTC${request.utc_offset < 0 ? '-' : '+'}${String(Math.floor(zoneMinutes / 60)).padStart(2, '0')}:${String(zoneMinutes % 60).padStart(2, '0')})`;
    return route.fulfill({
    contentType: 'application/json',
    body: JSON.stringify({
      tithi,
      at: held ? 'Earlier request' : at,
      vara: { number: 0, name: 'Ravivara' },
      nakshatra: { number: 14, name: 'Chitra', pada: 4 },
      yoga: { number: 3, name: 'Ayushman' }, karana: { number: 60, name: 'Chatushpada', type: 'fixed' },
      masa: { number: 7, name: 'Kartika' },
      ritu: { number: 4, name: 'Sharad' },
      samvatsara: { number: 53, name: 'Raudra' },
      sun_longitude: 200, moon_longitude: 164.06, ayanamsha: 22.913,
      summary: '',
    }),
    });
  });
  try {
    for (const [number, name, paksha] of [
      [28, 'Trayodashi', 'Krishna'], [13, 'Trayodashi', 'Shukla'],
      [15, 'Purnima', 'Shukla'], [30, 'Amavasya', 'Krishna'],
    ]) {
      tithi = { number, name, paksha, fraction: 0.005 };
      await page.goto('http://127.0.0.1:5173/panchanga');
      const row = page.locator('tr').filter({ has: page.getByRole('rowheader', { name: 'Tithi', exact: true }) });
      await row.waitFor();
      assert.equal(requests.at(-1).year, 2026);
      assert.equal(requests.at(-1).month, 11);
      assert(Math.abs(requests.at(-1).day - (9 + (12 * 60 + 34) / 1440)) < 1e-9, 'Opening Panchanga must use the current time, not midnight');
      assert.equal(requests.at(-1).utc_offset, 5.5);
      assert.equal(await page.getByLabel('Time', { exact: true }).inputValue(), '12:34');
      await page.getByRole('heading', { name: 'Panchanga — 2026-11-09 12:34 (UTC+05:30)', exact: true }).waitFor();
      assert.equal(await row.locator('td').innerText(), `${name} (${paksha} paksha) — #${number} (0.5% elapsed)`);
      for (const [label, expected] of [['Yoga', 'Ayushman'], ['Karana', 'Chatushpada']]) {
        const namedRow = page.locator('tr').filter({ has: page.getByRole('rowheader', { name: label, exact: true }) });
        assert.equal(await namedRow.locator('td').innerText(), expected);
      }
    }
    let before = requests.length;
    await Promise.all([
      page.waitForResponse(response => response.url().endsWith('/api/calc/panchanga')),
      page.getByLabel('Time', { exact: true }).fill('18:45'),
    ]);
    assert(requests.length > before);
    assert(Math.abs(requests.at(-1).day - (9 + 18.75 / 24)) < 1e-9);
    before = requests.length;
    const changedZone = page.waitForResponse(response => response.url().endsWith('/api/calc/panchanga'));
    await page.getByLabel('Time zone (hours from UTC; IST = 5.5)', { exact: true }).fill('0');
    await changedZone;
    assert(requests.length > before, 'Timezone changes must recalculate');
    assert.equal(requests.at(-1).utc_offset, 0);
    // An earlier response arriving last must never replace the current result.
    holdNext = true;
    await Promise.all([
      page.waitForRequest(request => request.url().endsWith('/api/calc/panchanga')),
      page.getByLabel('Time', { exact: true }).fill('19:00'),
    ]);
    await page.getByLabel('Time', { exact: true }).fill('20:00');
    await page.getByRole('heading', { name: 'Panchanga — 2026-11-09 20:00 (UTC+00:00)', exact: true }).waitFor();
    assert.equal(typeof heldRequest, 'function');
    const oldResponse = page.waitForResponse(response => response.url().endsWith('/api/calc/panchanga'));
    heldRequest();
    await oldResponse;
    await page.evaluate(() => new Promise(resolve => requestAnimationFrame(() => requestAnimationFrame(resolve))));
    assert.equal(await page.getByRole('heading', { name: 'Panchanga — Earlier request', exact: true }).count(), 0);
    await page.clock.setFixedTime(new Date('2026-11-09T18:45:00Z'));
    const nowResponse = page.waitForResponse(response => response.url().endsWith('/api/calc/panchanga'));
    await page.getByRole('button', { name: 'Now', exact: true }).click();
    await nowResponse;
    assert.equal(await page.getByLabel('Day', { exact: true }).inputValue(), '10');
    assert.equal(await page.getByLabel('Time', { exact: true }).inputValue(), '00:15');
    assert.equal(requests.at(-1).utc_offset, 5.5);
    assert(Math.abs(requests.at(-1).day - (10 + 15 / 1440)) < 1e-9, 'Now must restore the current local date, time and timezone across midnight');
    await page.getByRole('heading', { name: 'Panchanga — 2026-11-10 00:15 (UTC+05:30)', exact: true }).waitFor();
    await page.setViewportSize({ width: 390, height: 844 });
    assert(await page.evaluate(() => document.documentElement.scrollWidth <= innerWidth + 1));
    await fs.mkdir(path.join(os.tmpdir(), 'surya-siddhanta-checks', 'panchanga'), { recursive: true });
    await page.screenshot({ path: path.join(os.tmpdir(), 'surya-siddhanta-checks', 'panchanga/tithi-mobile.png'), fullPage: true });
    console.log('PASS: current local date/time, editable time, timezone recalculation, server timestamp, stale-response protection, Now across midnight, named yoga/karana/tithis, mobile layout');
  } finally {
    await browser.close();
  }
})().catch(error => { console.error(error); process.exit(1); });
