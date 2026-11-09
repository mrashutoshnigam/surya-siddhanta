// Run against a built container: APP_URL=http://127.0.0.1:18080 node check-docker-assets.cjs
const { chromium } = require('playwright');
const assert = require('node:assert/strict');
const fs = require('node:fs/promises');
const path = require('node:path');
const base = process.env.APP_URL || 'http://127.0.0.1:18080';

async function checkFiles(request, directory, prefix = '') {
  for (const entry of await fs.readdir(directory, { withFileTypes: true })) {
    const relative = `${prefix}${entry.name}`;
    const source = path.join(directory, entry.name);
    if (entry.isDirectory()) {
      await checkFiles(request, source, `${relative}/`);
      continue;
    }
    const response = await request.get(new URL(relative, `${base}/`).href, { timeout: 10000 });
    assert.equal(response.status(), 200, `Missing deployed asset: ${relative}`);
    assert.ok((await response.body()).equals(await fs.readFile(source)), `Incorrect deployed asset: ${relative}`);
    console.log(`PASS: ${relative}`);
  }
}

(async () => {
  const browser = await chromium.launch({ channel: 'msedge', headless: true });
  try {
    const page = await browser.newPage({ viewport: { width: 1440, height: 1000 } });
    await checkFiles(page.request, path.join(__dirname, 'public'));
    await page.goto(base);
    const dialog = page.getByRole('dialog', { name: 'Computational Implementation of the Surya Siddhanta' });
    await dialog.waitFor();
    const logo = dialog.getByRole('img', { name: 'IIT Jodhpur logo' });
    await logo.evaluate(image => image.decode());
    assert(await logo.evaluate(image => image.complete && image.naturalWidth > 0));
    const output = path.join(__dirname, '../tmp/project-welcome/docker.png');
    await fs.mkdir(path.dirname(output), { recursive: true });
    await page.screenshot({ path: output });
    console.log('PASS: IIT Jodhpur logo renders in the deployed pop-up');
  } finally {
    await browser.close();
  }
})().catch(error => { console.error(error); process.exit(1); });
