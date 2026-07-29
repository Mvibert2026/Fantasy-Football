import { chromium } from 'playwright';
const EXEC = '/opt/pw-browsers/chromium';
const browser = await chromium.launch({ executablePath: EXEC });
const page = await browser.newPage({ viewport: { width: 1440, height: 900 } });
await page.goto('http://localhost:5199', { waitUntil: 'load', timeout: 15000 });
await page.waitForTimeout(1000);

const select = page.locator('select[aria-label="Select league"]');
await select.selectOption({ label: "Ethan's Expert League (Yahoo 834236)" });
await page.waitForTimeout(1500);

await page.locator('text=Opponents').first().click();
await page.waitForTimeout(500);

const editButtons = page.locator('button[aria-label^="Edit team name"]');
await editButtons.first().click();
await page.waitForTimeout(200);
const input = page.locator('input[aria-label^="Team name for slot"]').first();
await input.fill('The Testers');
await input.press('Enter');
await page.waitForTimeout(400);

const ls = await page.evaluate(() => JSON.stringify(Object.fromEntries(Object.entries(localStorage))));
console.log('localStorage after typing (pre-reload):', ls);

await page.reload({ waitUntil: 'load', timeout: 15000 });
await page.waitForTimeout(1500);

const ls2 = await page.evaluate(() => JSON.stringify(Object.fromEntries(Object.entries(localStorage))));
console.log('localStorage after reload:', ls2);

const select2 = page.locator('select[aria-label="Select league"]');
await select2.waitFor({ state: 'attached' });
const opts = await select2.locator('option').allTextContents();
console.log('league options after reload:', opts);
await select2.selectOption({ label: "Ethan's Expert League (Yahoo 834236)" });
await page.waitForTimeout(2000);

const currentLeagueVal = await select2.inputValue();
console.log('select value after re-selecting:', currentLeagueVal);

await page.locator('text=Opponents').first().click();
await page.waitForTimeout(600);
const text = await page.locator('body').innerText();
console.log('Contains "The Testers":', text.includes('The Testers'));
console.log('Body snippet:', text.slice(0, 600));

await browser.close();
