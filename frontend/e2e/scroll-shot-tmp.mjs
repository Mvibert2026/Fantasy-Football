import { chromium } from 'playwright';
import { join } from 'node:path';

const url = 'http://localhost:5211';
const browsersPath = process.env.PLAYWRIGHT_BROWSERS_PATH || '/opt/pw-browsers';
const executablePath = join(browsersPath, 'chromium');
const browser = await chromium.launch({ executablePath });
const page = await browser.newPage({ viewport: { width: 1600, height: 1200 } });
await page.goto(url, { waitUntil: 'networkidle' });
await page.waitForSelector('text=/generated 20/', { timeout: 30000 });
await page.locator('[role="button"]', { hasText: 'Methodology' }).first().click();
await page.waitForTimeout(500);
const h3 = page.locator('h3', { hasText: 'ADP' }).first();
await h3.scrollIntoViewIfNeeded();
await page.waitForTimeout(300);
await page.screenshot({ path: 'e2e/artifacts/adp-methodology-scrolled-2026-07-29.png' });
console.log('done');
await browser.close();
