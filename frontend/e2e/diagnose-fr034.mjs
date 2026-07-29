import { chromium } from 'playwright';

const EXEC = process.env.PLAYWRIGHT_CHROMIUM_PATH || '/opt/pw-browsers/chromium';
const URL = process.argv[2] || 'http://localhost:5199';

const browser = await chromium.launch({ executablePath: EXEC });
const page = await browser.newPage({ viewport: { width: 1440, height: 900 } });
const consoleErrors = [];
page.on('console', (msg) => {
  if (msg.type() === 'error') consoleErrors.push(msg.text());
});

await page.goto(URL, { waitUntil: 'networkidle' });
await page.waitForTimeout(800);

// Go to Predictions in the sidebar (prep mode default)
async function clickNav(label) {
  const el = page.locator(`text=${label}`).first();
  await el.click();
  await page.waitForTimeout(500);
}

await clickNav('Predictions');
await page.waitForTimeout(800);
await page.screenshot({ path: '/tmp/claude-0/-home-user-Fantasy-Football/1083ac0e-6d34-5aeb-95ad-29e9d3910c3f/scratchpad/predictions-before.png', fullPage: true });

const beforeText = await page.locator('body').innerText();
const beforeHeaderMatch = beforeText.match(/Live availability at pick \d+/);
console.log('BEFORE header line:', beforeHeaderMatch ? beforeHeaderMatch[0] : '(none found)');

// Find first few player names in the predictions table for comparison
const beforeRows = await page.locator('div[style*="grid-template-columns"]').allInnerTexts();
console.log('BEFORE first rows sample:', beforeRows.slice(1, 4));

// Now switch league via the top bar league switcher. Let's find the select/dropdown.
const selectHandle = await page.locator('select').first();
const selectCount = await page.locator('select').count();
console.log('select count on page:', selectCount);

if (selectCount > 0) {
  const options = await selectHandle.locator('option').allTextContents();
  console.log('league options:', options);
  // pick ethans_expert_league option if present
  const idx = options.findIndex((o) => /Ethan/i.test(o));
  console.log('ethan idx', idx, options[idx]);
  await selectHandle.selectOption({ label: options[idx] });
  await page.waitForTimeout(1200);
}

await page.screenshot({ path: '/tmp/claude-0/-home-user-Fantasy-Football/1083ac0e-6d34-5aeb-95ad-29e9d3910c3f/scratchpad/predictions-after-switch.png', fullPage: true });

const afterText = await page.locator('body').innerText();
const afterHeaderMatch = afterText.match(/Live availability at pick \d+/);
console.log('AFTER header line:', afterHeaderMatch ? afterHeaderMatch[0] : '(none found)');

const afterRows = await page.locator('div[style*="grid-template-columns"]').allInnerTexts();
console.log('AFTER first rows sample:', afterRows.slice(1, 4));

console.log('console errors:', consoleErrors);

await browser.close();
