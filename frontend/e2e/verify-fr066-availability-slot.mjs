import { chromium } from 'playwright';

/**
 * FR-066 ("When slot selection happens on the availability, it doesn't change the
 * picks shown"). Screenshot proof, not just a passing test suite -- per this
 * project's evidence standards, a UI fix is not verified without a screenshot a
 * human has looked at.
 *
 * Captures the Availability Explorer at the sourced slot, then again after
 * overriding the slot via the top bar's SLOT control -- the pick-selector row
 * changes, and the honest "not recomputed for your selection" banner appears.
 */

const EXEC = process.env.PLAYWRIGHT_CHROMIUM_PATH || '/opt/pw-browsers/chromium';
const URL = process.argv[2] || 'http://localhost:5199';
const OUT_DIR = '/home/user/Fantasy-Football/.claude/worktrees/agent-a6aa496d85bd1b2b9/frontend/e2e/artifacts';

const browser = await chromium.launch({ executablePath: EXEC });
const page = await browser.newPage({ viewport: { width: 1440, height: 900 } });
const consoleErrors = [];
page.on('console', (msg) => {
  if (msg.type() === 'error') consoleErrors.push(msg.text());
});

await page.goto(URL, { waitUntil: 'networkidle' });
await page.waitForTimeout(600);

async function clickNav(label) {
  await page.locator(`text=${label}`).first().click();
  await page.waitForTimeout(400);
}

await clickNav('Availability');
await page.waitForTimeout(600);

const picksGroupSel = '[aria-label="Your picks"]';
const beforePicks = await page.locator(`${picksGroupSel} button`).allInnerTexts();
console.log('BEFORE slot override -- YOUR PICKS buttons:', beforePicks);
const beforeSlotLabel = await page.getByLabel('Your draft slot').inputValue();
console.log('BEFORE slot select value:', beforeSlotLabel);

await page.screenshot({ path: `${OUT_DIR}/fr066-availability-before-override.png`, fullPage: true });

// Pick a different slot from the top bar's SLOT select -- whatever the current
// value isn't, deterministically the first differing option.
const slotSelect = page.getByLabel('Your draft slot');
const options = await slotSelect.locator('option').allTextContents();
const target = options.find((o) => o !== beforeSlotLabel);
console.log('overriding to slot:', target);
await slotSelect.selectOption(target);
await page.waitForTimeout(500);

const afterPicks = await page.locator(`${picksGroupSel} button`).allInnerTexts();
console.log('AFTER slot override -- YOUR PICKS buttons:', afterPicks);

const bannerVisible = await page.getByText(/has not been recomputed for your selection/i).isVisible();
console.log('override banner visible:', bannerVisible);

await page.screenshot({ path: `${OUT_DIR}/fr066-availability-after-override.png`, fullPage: true });

// A second, different slot -- side-by-side proof this isn't a one-off toggle.
const target2 = options.find((o) => o !== beforeSlotLabel && o !== target);
if (target2) {
  await slotSelect.selectOption(target2);
  await page.waitForTimeout(500);
  const afterPicks2 = await page.locator(`${picksGroupSel} button`).allInnerTexts();
  console.log('AFTER SECOND slot override -- YOUR PICKS buttons:', afterPicks2);
  await page.screenshot({ path: `${OUT_DIR}/fr066-availability-after-override-2.png`, fullPage: true });
}

// Clear the override -- confirm it reverts.
const clearBtn = page.getByLabel('Clear draft slot override');
if (await clearBtn.isVisible()) {
  await clearBtn.click();
  await page.waitForTimeout(500);
  const clearedPicks = await page.locator(`${picksGroupSel} button`).allInnerTexts();
  console.log('AFTER clearing override -- YOUR PICKS buttons:', clearedPicks);
  console.log('matches original?', JSON.stringify(clearedPicks) === JSON.stringify(beforePicks));
  await page.screenshot({ path: `${OUT_DIR}/fr066-availability-after-clear.png`, fullPage: true });
}

console.log('console errors:', consoleErrors);
await browser.close();
