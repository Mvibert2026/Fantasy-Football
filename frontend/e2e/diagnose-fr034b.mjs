import { chromium } from 'playwright';

const EXEC = process.env.PLAYWRIGHT_CHROMIUM_PATH || '/opt/pw-browsers/chromium';
const browser = await chromium.launch({ executablePath: EXEC });
const page = await browser.newPage({ viewport: { width: 1440, height: 900 } });

await page.goto('http://localhost:5199', { waitUntil: 'networkidle' });
await page.waitForTimeout(600);
await page.locator('text=Predictions').first().click();
await page.waitForTimeout(600);

const beforeText = await page.locator('body').innerText();
console.log('=== BEFORE (Westwood) ===');
console.log(beforeText.slice(0, 900));

const selectHandle = page.locator('select').first();
await selectHandle.selectOption({ label: "Ethan's Expert League (Yahoo 834236)" });
await page.waitForTimeout(3000);

await page.screenshot({ path: 'e2e/artifacts/predictions-after-switch.png', fullPage: true });
const afterText = await page.locator('body').innerText();
console.log('=== AFTER (Ethan switch) ===');
console.log(afterText.slice(0, 900));
await browser.close();
