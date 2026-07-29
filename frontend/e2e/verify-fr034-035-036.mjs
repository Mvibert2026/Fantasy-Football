import { chromium } from 'playwright';

const EXEC = process.env.PLAYWRIGHT_CHROMIUM_PATH || '/opt/pw-browsers/chromium';
const URL = process.argv[2] || 'http://localhost:5199';
const OUT = 'e2e/artifacts';

const browser = await chromium.launch({ executablePath: EXEC });
const page = await browser.newPage({ viewport: { width: 1440, height: 900 } });
const consoleErrors = [];
page.on('console', (msg) => {
  if (msg.type() === 'error') consoleErrors.push(msg.text());
});

async function click(text) {
  await page.locator(`text=${text}`).first().click();
  await page.waitForTimeout(400);
}

await page.goto(URL, { waitUntil: 'load', timeout: 15000 });
await page.waitForTimeout(1000);

// ---------- FR-035: Predictions, Westwood (default) ----------
await click('Predictions');
await page.waitForTimeout(500);
await page.screenshot({ path: `${OUT}/fr035-predictions-westwood.png`, fullPage: false });
const t1 = await page.locator('body').innerText();
const predictLine1 = t1.split('\n').find((l) => l.startsWith('Predicting for'));
console.log('FR-035 Westwood context line:', predictLine1);

// Switch league to Ethan's
const select = page.locator('select[aria-label="Select league"]');
await select.selectOption({ label: "Ethan's Expert League (Yahoo 834236)" });
await page.waitForTimeout(2500);
await page.screenshot({ path: `${OUT}/fr035-predictions-ethans.png`, fullPage: false });
const t2 = await page.locator('body').innerText();
const predictLine2 = t2.split('\n').find((l) => l.startsWith('Predicting for'));
console.log('FR-035 Ethans context line:', predictLine2);

// ---------- FR-034: draft slot selector visible in Prep, override it ----------
await page.screenshot({ path: `${OUT}/fr034-slot-selector-prep-before.png`, fullPage: false, clip: { x: 0, y: 0, width: 1440, height: 46 } });

const slotSelect = page.locator('select[aria-label="Your draft slot"]');
const slotOptions = await slotSelect.locator('option').allTextContents();
console.log('FR-034 slot options (Ethans, should be 1..10):', slotOptions);
await slotSelect.selectOption('5');
await page.waitForTimeout(600);
await page.screenshot({ path: `${OUT}/fr034-slot-selector-prep-overridden.png`, fullPage: false, clip: { x: 0, y: 0, width: 1440, height: 46 } });
const t3 = await page.locator('body').innerText();
console.log('FR-035 predicting line after slot override:', t3.split('\n').find((l) => l.startsWith('Predicting for')));

// ---------- FR-036: Opponents, Prep mode ----------
await click('Opponents');
await page.waitForTimeout(500);
await page.screenshot({ path: `${OUT}/fr036-opponents-prep-before.png`, fullPage: true });

// Find an edit button for an unnamed slot and type a name
const editButtons = page.locator('button[aria-label^="Edit team name"]');
const editCount = await editButtons.count();
console.log('FR-036 edit buttons found:', editCount);
await editButtons.first().click();
await page.waitForTimeout(200);
const input = page.locator('input[aria-label^="Team name for slot"]').first();
await input.fill('The Testers');
await input.press('Enter');
await page.waitForTimeout(400);
await page.screenshot({ path: `${OUT}/fr036-opponents-prep-typed.png`, fullPage: true });

// Reload the page to prove localStorage persistence survives a reload. leagueId
// itself is not persisted across reload (pre-existing app behaviour, unrelated to
// FR-036) -- default league loads first, so re-select Ethan's before checking.
await page.reload({ waitUntil: 'load', timeout: 15000 });
await page.waitForTimeout(1200);
await select.selectOption({ label: "Ethan's Expert League (Yahoo 834236)" });
await page.waitForTimeout(1500);
await click('Opponents');
await page.waitForTimeout(500);
const t4 = await page.locator('body').innerText();
console.log('FR-036 "The Testers" present after reload (same league re-selected):', t4.includes('The Testers'));
await page.screenshot({ path: `${OUT}/fr036-opponents-prep-after-reload.png`, fullPage: true });

// ---------- FR-034: switch to Draft mode, confirm slot selector still there ----------
await click('Draft');
await page.waitForTimeout(1200);
await page.screenshot({ path: `${OUT}/fr034-slot-selector-draft-mode.png`, fullPage: false, clip: { x: 0, y: 0, width: 1440, height: 46 } });
const t5 = await page.locator('body').innerText();
console.log('Draft mode top bar snippet:', t5.slice(0, 200));

// ---------- FR-036: Opponents tab inside Draft mode (AdaptedOpponentsPane) ----------
const draftOpponentsTab = page.locator('button:has-text("Opponents")').first();
if (await draftOpponentsTab.count() > 0) {
  await draftOpponentsTab.click();
  await page.waitForTimeout(600);
  await page.screenshot({ path: `${OUT}/fr036-opponents-draft-mode.png`, fullPage: true });
  const t6 = await page.locator('body').innerText();
  console.log('FR-036 "The Testers" visible inside Draft mode tab:', t6.includes('The Testers'));
} else {
  console.log('No Opponents tab found inside Draft mode');
}

console.log('console errors seen:', consoleErrors.filter((e) => !e.includes('ERR_CONNECTION_RESET') && !e.includes('404')));

await browser.close();
