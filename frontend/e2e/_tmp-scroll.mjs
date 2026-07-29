import { chromium } from 'playwright';
import { pathToFileURL } from 'node:url';
import { join } from 'node:path';

const htmlPath = join(process.cwd(), 'dist-standalone', 'board.html');
const browser = await chromium.launch({ executablePath: '/opt/pw-browsers/chromium' });
const page = await browser.newPage({ viewport: { width: 1440, height: 900 } });
await page.goto(pathToFileURL(htmlPath).href, { waitUntil: 'load' });
await page.waitForSelector('text=/generated 20/');
await page.locator('text=Bijan Robinson').first().click();
const heading = page.locator('text=WEEKLY FINISHES');
await heading.waitFor({ state: 'attached' });
await heading.scrollIntoViewIfNeeded();
await page.screenshot({ path: 'e2e/artifacts/standalone-player-detail-history.png' });
await browser.close();
