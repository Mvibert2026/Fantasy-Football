import { chromium } from 'playwright';

const url = process.argv[2] || 'http://localhost:5200';
const outDir = new URL('./artifacts/', import.meta.url).pathname;

const browser = await chromium.launch({ executablePath: process.env.PLAYWRIGHT_CHROMIUM_PATH || '/opt/pw-browsers/chromium' });
const page = await browser.newPage({ viewport: { width: 1500, height: 950 } });
await page.goto(url, { waitUntil: 'networkidle' });
await page.waitForTimeout(600);
await page.screenshot({ path: `${outDir}topbar-prod-2026-07-29.png`, clip: { x: 0, y: 0, width: 1500, height: 60 } });
console.log('captured prod topbar');
await browser.close();
