import { chromium } from 'playwright';

const EXEC = process.env.PLAYWRIGHT_CHROMIUM_PATH || '/opt/pw-browsers/chromium';
const URL = process.argv[2] || 'http://localhost:5199';
const OUT = 'e2e/artifacts';

const browser = await chromium.launch({ executablePath: EXEC });
const page = await browser.newPage({ viewport: { width: 1440, height: 900 } });

await page.goto(URL, { waitUntil: 'load', timeout: 15000 });
await page.waitForSelector('[data-testid="freshness-note"]:has-text("exported 20")', { timeout: 10000 });

const bodyText = await page.locator('body').innerText();
console.log('Contains "Refresh data" anywhere:', bodyText.includes('Refresh data'));

const noteCount = await page.locator('[data-testid="freshness-note"]').count();
console.log('freshness-note elements found:', noteCount);
if (noteCount > 0) {
  console.log('freshness-note text:', await page.locator('[data-testid="freshness-note"]').first().innerText());
}

await page.screenshot({ path: `${OUT}/topbar-no-refresh-button.png`, fullPage: false, clip: { x: 0, y: 0, width: 1440, height: 46 } });

// Also confirm in Draft mode
await page.getByRole('button', { name: 'Draft', exact: true }).click();
await page.waitForTimeout(1500);
const bodyText2 = await page.locator('body').innerText();
console.log('Draft mode -- contains "Refresh data":', bodyText2.includes('Refresh data'));
await page.screenshot({ path: `${OUT}/topbar-no-refresh-button-draft-mode.png`, fullPage: false, clip: { x: 0, y: 0, width: 1440, height: 46 } });

await browser.close();
