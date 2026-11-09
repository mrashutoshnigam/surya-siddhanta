const os = require('node:os');
// Run after starting Vite on :5173 and the API on :8000.
// PLAYWRIGHT_MODULE may point at a host-provided Playwright package.
const { chromium } = require(process.env.PLAYWRIGHT_MODULE || "playwright");
const assert = require("node:assert/strict");
const fs = require("node:fs/promises");
const path = require("node:path");

(async () => {
  const browser = await chromium.launch({ channel: "msedge", headless: true });
  const out = path.join(os.tmpdir(), "surya-siddhanta-checks", 'learning-lab');
  await fs.mkdir(out, { recursive: true });
  const page = await browser.newPage({ viewport: { width: 1500, height: 1100 }, colorScheme: "light" });
  const errors = [];
  page.on("pageerror", e => errors.push(e.message));
  try {
    // A missing external corpus must not prevent the numerical lesson.
    await page.route("**/api/corpus/verses/2", route => route.abort());
    await page.goto("http://127.0.0.1:5173/learn/mars");
    await page.getByText("Showing 2026-11-04 · Ujjain mean time", { exact: true }).waitFor();
    await page.getByLabel("Day", { exact: true }).focus();
    await page.keyboard.press("ArrowUp");
    assert.equal(await page.getByLabel("Day", { exact: true }).inputValue(), "5");
    await page.getByRole("button", { name: "Reset demo" }).click();
    await page.getByText("Showing 2026-11-04 · Ujjain mean time", { exact: true }).waitFor();
    const response = await page.request.post("http://127.0.0.1:8000/book/chapter/2", { data: { year: 2026, month: 11, day: 4 } });
    assert(response.ok());
    const row = (await response.json()).cards["ii.43-45"].rows.find(r => r.body === "Mars");
    for (let i = 0; i < row.stages.length; i++) {
      const button = page.locator(".lab-steps button").nth(i);
      assert((await button.innerText()).includes(row.stages[i].longitude.toFixed(4)));
      await button.click();
      assert.equal(await button.getAttribute("aria-pressed"), "true");
      assert((await page.locator(".lab-dial title").textContent()).includes(row.stages[i].longitude.toFixed(4)));
    }
    await page.getByRole("button", { name: "Ahead", exact: true }).click();
    await page.getByRole("button", { name: "Check my answer" }).click();
    await page.locator(".lab-feedback").waitFor();
    const [download] = await Promise.all([
      page.waitForEvent("download"), page.getByRole("button", { name: "Download this calculation" }).click(),
    ]);
    const downloaded = JSON.parse(await fs.readFile(await download.path(), "utf8"));
    assert.equal(downloaded.true_longitude, row.true_longitude);
    assert.equal(downloaded.time_basis, "Ujjain mean time");
    await page.getByLabel("Evaluation window").selectOption("2550");
    assert((await page.locator(".lab-research-figure title").textContent()).includes("2550 to 2649"));
    const [researchDownload] = await Promise.all([
      page.waitForEvent("download"), page.getByRole("button", { name: "Download this window" }).click(),
    ]);
    const research = JSON.parse(await fs.readFile(await researchDownload.path(), "utf8"));
    assert.equal(research.windows[0].start, 2550);
    assert.equal(research.source_sha256.length, 64);

    await page.getByRole("button", { name: "Reset demo" }).click();
    await page.getByText("Showing 2026-11-04 · Ujjain mean time", { exact: true }).waitFor();
    await page.getByLabel("Month", { exact: true }).fill("2");
    await page.getByLabel("Day", { exact: true }).fill("31");
    await page.getByText("Enter a valid calendar date using a whole day.", { exact: true }).waitFor();
    assert(await page.getByRole("button", { name: "Download this calculation" }).isDisabled());
    await page.getByRole("button", { name: "Reset demo" }).click();
    await page.getByText("Showing 2026-11-04 · Ujjain mean time", { exact: true }).waitFor();

    // Slow earlier response must never overwrite the latest date selection.
    await page.route("**/api/book/chapter/2", async route => {
      const body = route.request().postDataJSON();
      const result = await route.fetch();
      if (body.day === 5) await new Promise(resolve => setTimeout(resolve, 1200));
      await route.fulfill({ response: result });
    });
    await page.getByLabel("Day", { exact: true }).fill("5");
    await page.waitForTimeout(350);
    await page.getByLabel("Day", { exact: true }).fill("6");
    await page.getByText("Showing 2026-11-06 · Ujjain mean time", { exact: true }).waitFor();
    await page.waitForTimeout(1500);
    assert((await page.locator(".lab-status").innerText()).includes("2026-11-06"));
    await page.unroute("**/api/book/chapter/2");

    await page.route("**/api/book/chapter/2", route => route.fulfill({ status: 503, contentType: "application/json", body: JSON.stringify({ detail: "Test backend unavailable" }) }));
    await page.getByLabel("Day", { exact: true }).fill("7");
    await page.getByRole("button", { name: "Retry calculation" }).waitFor();
    assert(await page.getByRole("button", { name: "Download this calculation" }).isDisabled());
    await page.unroute("**/api/book/chapter/2");
    await page.getByRole("button", { name: "Retry calculation" }).click();
    await page.getByText("Showing 2026-11-07 · Ujjain mean time", { exact: true }).waitFor();
    await page.getByRole("link", { name: "Inspect the calculation in the book" }).click();
    await page.waitForURL("**/book/1?year=2026&month=11&day=7#i.52-54");
    assert.equal(await page.getByLabel("Day", { exact: true }).inputValue(), "7");
    await page.goto("http://127.0.0.1:5173/learn/mars");
    await page.getByText("Showing 2026-11-04 · Ujjain mean time", { exact: true }).waitFor();
    await page.getByLabel("Day", { exact: true }).fill("8");
    await page.getByText("Showing 2026-11-08 · Ujjain mean time", { exact: true }).waitFor();
    await page.locator(".lab-steps button").last().click();
    await page.getByRole("link", { name: "Inspect the calculation in the book" }).click();
    await page.waitForURL("**/book/2?year=2026&month=11&day=8#ii.43-45");
    assert.equal(await page.getByLabel("Day", { exact: true }).inputValue(), "8");
    await page.goto("http://127.0.0.1:5173/learn/mars");
    await page.getByText("Showing 2026-11-04 · Ujjain mean time", { exact: true }).waitFor();
    await page.getByRole("button", { name: "Reset demo" }).click();
    await page.getByText("Showing 2026-11-04 · Ujjain mean time", { exact: true }).waitFor();
    await page.locator(".lab-steps button").last().click();
    await page.evaluate(() => window.scrollTo(0, 0));
    await page.screenshot({ path: path.join(out, "desktop-light.png"), fullPage: true });
    await page.evaluate(() => document.documentElement.dataset.theme = "dark");
    await page.screenshot({ path: path.join(out, "desktop-dark.png"), fullPage: true });
    await page.evaluate(() => document.documentElement.dataset.theme = "light");
    await page.setViewportSize({ width: 390, height: 844 });
    await page.screenshot({ path: path.join(out, "mobile.png"), fullPage: true });
    assert(await page.evaluate(() => document.documentElement.scrollWidth <= innerWidth));
    await page.getByRole("button", { name: "Reset demo" }).focus();
    await page.keyboard.press("Tab");
    assert.equal(await page.evaluate(() => document.activeElement.tagName), "INPUT");
    assert.deepEqual(errors, []);
    console.log("PASS: real API values, stages, quiz, exports, invalid dates, stale responses, retry, missing corpus, mobile overflow, keyboard focus and screenshots.");
  } finally { await browser.close(); }
})().catch(error => { console.error(error); process.exitCode = 1; });
