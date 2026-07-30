/**
 * Screenshot verification for docs/design/SUPPLIED-VALUES.md: the typed
 * opponent name (Prep > Opponents) and the TopBar SLOT override no longer
 * use --acc green -- a dotted underline plus a lowercase "typed"/"set by
 * you" marker instead.
 *
 * Cloud-container Chromium path per docs/frontend-cloud-runbook.md.
 * Usage: node e2e/verify-supplied-values.mjs [--url http://localhost:5199]
 */
import { mkdirSync } from 'node:fs';
import { join, dirname } from 'node:path';
import { fileURLToPath } from 'node:url';
import { chromium } from 'playwright';

const root = join(dirname(fileURLToPath(import.meta.url)), '..');
const artifacts = join(root, 'e2e', 'artifacts');
mkdirSync(artifacts, { recursive: true });

const args = process.argv.slice(2);
const url = args.includes('--url') ? args[args.indexOf('--url') + 1] : 'http://localhost:5199';

const browsersPath = process.env.PLAYWRIGHT_BROWSERS_PATH || '/opt/pw-browsers';
const executablePath = join(browsersPath, 'chromium');

const browser = await chromium.launch({ executablePath });
const page = await browser.newPage({ viewport: { width: 1600, height: 1000 } });

await page.goto(url, { waitUntil: 'networkidle' });
await page.waitForSelector('text=/generated 20/', { timeout: 30_000 });

// ---- 1. TopBar SLOT control, overridden ----
const slotSelect = page.locator('select[aria-label="Your draft slot"]');
await slotSelect.selectOption('7');
await page.waitForSelector('text=/set by you/', { timeout: 10_000 });
const slotBox = page.locator('text="SLOT"').first().locator('xpath=..');
await slotBox.screenshot({ path: join(artifacts, 'supplied-1-topbar-slot-overridden.png') });
console.log('captured topbar slot override');

// ---- 2. Opponents tab: typed name (Prep mode's own Opponents screen, not
// Draft mode's hub tab of the same name -- switch to Prep first) ----
await page.getByRole('button', { name: 'Prep', exact: true }).click();
await page.waitForSelector('text=/generated 20/', { timeout: 15_000 });
await page.getByRole('button', { name: 'Opponents', exact: true }).click();
await page.waitForSelector('text=/STILL NEEDS|roster/i', { timeout: 15_000 });
const editButtons = page.getByRole('button', { name: /edit team name/i });
const editCount = await editButtons.count();
console.log(`opponent edit buttons found: ${editCount}`);
if (editCount > 0) {
  await editButtons.first().click();
  const input = page.getByRole('textbox', { name: /team name for slot/i }).first();
  await input.fill('The Testers');
  await input.press('Enter');
  await page.waitForSelector('text="typed"', { timeout: 10_000 });
  await page.screenshot({ path: join(artifacts, 'supplied-2-opponents-typed-name.png'), fullPage: false });
  console.log('captured opponents typed name');
}

await browser.close();
