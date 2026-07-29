/**
 * Verification script for this session's three jobs:
 *  1. Opponents/Predictions folded into the Draft-mode hub tabs (founder's
 *     direct ask, thread 049 item 1).
 *  2. ADP display on the prep board, draft screen, and player profile
 *     (FR-024, thread 082).
 *
 * Same executablePath workaround as cloud-board-screenshot.mjs -- see
 * docs/frontend-cloud-runbook.md.
 *
 * Usage: node e2e/verify-hub-and-adp.mjs --url http://localhost:5199
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
const consoleErrors = [];
page.on('console', (msg) => { if (msg.type() === 'error') consoleErrors.push(msg.text()); });
page.on('pageerror', (err) => consoleErrors.push('pageerror: ' + err.message));

async function shot(name) {
  const p = join(artifacts, name);
  await page.screenshot({ path: p, fullPage: false });
  console.log(`shot: ${p}`);
}

// ---- 1. Prep Board: ADP column ----
await page.goto(url, { waitUntil: 'networkidle' });
await page.waitForSelector('text=/generated 20/', { timeout: 30_000 });
console.log('== PREP BOARD ==');
console.log('has ADP (MFL) header:', await page.locator('text=/ADP \\(MFL\\)/').count());
await shot('01-prep-board.png');

// Find a row WITH an adp value (num) and one WITHOUT (em dash) for the null check.
const rowsText = await page.locator('.num').allTextContents();
console.log('sample numeric cell texts (first 20):', rowsText.slice(0, 20));

// ---- 2. Player profile: open a player with real ADP and one without ----
// Click first player name to open PlayerDetail.
const firstRow = page.locator('[role="row"], tr, .board-row').first();
await page.locator('text=Bijan Robinson').first().click({ timeout: 10_000 }).catch(() => {});
await page.waitForTimeout(500);
console.log('== PLAYER DETAIL (Bijan Robinson) ==');
console.log('has MARKET ADP block:', await page.locator('text=/MARKET ADP/').count());
await shot('02-player-detail-adp.png');
// close it
await page.keyboard.press('Escape').catch(() => {});
await page.waitForTimeout(300);

// ---- 3. Switch to Draft mode ----
console.log('== DRAFT MODE ==');
await page.locator('button', { hasText: 'Draft' }).first().click({ timeout: 10_000 }).catch(() => {});
await page.waitForTimeout(1000);
console.log('has Mark pick input:', await page.locator('[placeholder*="Mark pick"]').count());
console.log('has ADP column header in draft room:', await page.locator('text=/^ADP$/').count());
await shot('03-draft-room-board-tab.png');

// ---- 4. Draft mode -> Opponents tab ----
console.log('== DRAFT MODE: OPPONENTS TAB ==');
await page.locator('button', { hasText: 'Opponents' }).first().click({ timeout: 10_000 }).catch(() => {});
await page.waitForTimeout(500);
console.log('has Opponents heading:', await page.locator('h2:has-text("Opponents")').count());
console.log('has live-vs-static caveat:', await page.locator('text=/does not move the cards below/').count());
console.log('has "not wired in" placeholder (should be 0):', await page.locator('text=/not wired into Draft mode yet/').count());
await shot('04-draft-room-opponents-tab.png');

// ---- 5. Draft mode -> Predictions tab ----
console.log('== DRAFT MODE: PREDICTIONS TAB ==');
await page.locator('button', { hasText: 'Predictions' }).first().click({ timeout: 10_000 }).catch(() => {});
await page.waitForTimeout(500);
console.log('has Predictions heading:', await page.locator('h2:has-text("Predictions")').count());
console.log('has calibration caveat:', await page.locator('text=/currently not calibrated/').count());
await shot('05-draft-room-predictions-tab.png');

// ---- 6. Back to Board tab, look at a row without ADP ----
console.log('== DRAFT MODE: BOARD TAB, ADP null check ==');
await page.locator('button', { hasText: 'Board' }).first().click({ timeout: 10_000 }).catch(() => {});
await page.waitForTimeout(500);
await shot('06-draft-room-board-tab-2.png');

console.log(`console errors: ${consoleErrors.length}`);
for (const e of consoleErrors) console.log(`  console error: ${e}`);

await browser.close();
