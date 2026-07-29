import { chromium } from 'playwright';
import { pathToFileURL } from 'node:url';
import { join } from 'node:path';

const htmlPath = join(process.cwd(), 'dist-standalone', 'board.html');
const browser = await chromium.launch({ executablePath: '/opt/pw-browsers/chromium' });
const page = await browser.newPage({ viewport: { width: 1440, height: 1400 } });
await page.goto(pathToFileURL(htmlPath).href, { waitUntil: 'load' });
await page.waitForSelector('text=/generated 20/');
await page.locator('text=Bijan Robinson').first().click();
await page.waitForSelector('text=WEEKLY FINISHES');
const body = await page.textContent('body');
console.log('contains "not included in this static snapshot":', body.includes('not included in this static snapshot'));
console.log('contains "Could not load weekly_finishes.json":', body.includes('Could not load weekly_finishes.json'));
console.log('contains "Could not load season_stats.json":', body.includes('Could not load season_stats.json'));
await page.screenshot({ path: 'e2e/artifacts/standalone-player-detail-scrolled.png' });
await browser.close();
