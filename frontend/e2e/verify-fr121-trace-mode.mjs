/**
 * FR-121 verification -- the global "show data sources" switch, both states,
 * on the Draft board and a player card (CLAUDE.md's screenshot requirement).
 *
 * Usage: node e2e/verify-fr121-trace-mode.mjs [--url http://localhost:5199]
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

async function newPage() {
  const page = await browser.newPage({ viewport: { width: 1500, height: 950 } });
  page.on('console', (msg) => {
    if (msg.type() === 'error') console.log(`  console error: ${msg.text()}`);
  });
  return page;
}

async function shot(page, name) {
  const outPath = join(artifacts, name);
  await page.screenshot({ path: outPath, fullPage: false });
  console.log(`wrote ${outPath}`);
}

// networkidle never resolves against this dev server: Vite's HMR websocket
// stays open indefinitely, and the container can't reach fonts.googleapis.com
// (external host, blocked per docs/environment.md) so that request keeps
// retrying. domcontentloaded + an explicit selector wait is what actually
// works here.

// ---- 1. Draft board, default (switch OFF) ----
{
  const page = await newPage();
  await page.goto(url, { waitUntil: 'domcontentloaded' });
  await page.waitForSelector('text=/generated 20/', { timeout: 30_000 });
  await page.getByRole('button', { name: 'Draft', exact: true }).click();
  await page.waitForSelector('text=DRAFT LIVE', { timeout: 30_000 });
  // Expand the first board row's "why this rank" panel so a field-path caption
  // would be visible here if the switch were on.
  const expandHandle = page.getByTitle('Why this rank -- click to expand').first();
  if (await expandHandle.count()) await expandHandle.click();
  await page.waitForTimeout(200);
  const bodyOff = await page.textContent('body');
  console.log(`[draft board, off] contains 'board.json:players[': ${bodyOff.includes('board.json:players[')}`);
  console.log(`[draft board, off] contains 'DATA SOURCES SHOWN': ${bodyOff.includes('DATA SOURCES SHOWN')}`);
  await shot(page, 'fr121-draft-board-off.png');
  await page.close();
}

// ---- 2. Draft board, switch ON (Alt+T) ----
{
  const page = await newPage();
  await page.goto(url, { waitUntil: 'domcontentloaded' });
  await page.waitForSelector('text=/generated 20/', { timeout: 30_000 });
  await page.keyboard.down('Alt');
  await page.keyboard.press('KeyT');
  await page.keyboard.up('Alt');
  await page.waitForSelector('text=DATA SOURCES SHOWN', { timeout: 5_000 });
  await page.getByRole('button', { name: 'Draft', exact: true }).click();
  await page.waitForSelector('text=DRAFT LIVE', { timeout: 30_000 });
  const expandHandle = page.getByTitle('Why this rank -- click to expand').first();
  if (await expandHandle.count()) await expandHandle.click();
  await page.waitForTimeout(200);
  const bodyOn = await page.textContent('body');
  console.log(`[draft board, on] contains 'board.json:players[': ${bodyOn.includes('board.json:players[')}`);
  console.log(`[draft board, on] contains 'DATA SOURCES SHOWN': ${bodyOn.includes('DATA SOURCES SHOWN')}`);
  await shot(page, 'fr121-draft-board-on.png');
  await page.close();
}

// ---- 3. Player card, default (switch OFF) ----
{
  const page = await newPage();
  await page.goto(url, { waitUntil: 'domcontentloaded' });
  await page.waitForSelector('text=/generated 20/', { timeout: 30_000 });
  // Prep mode's Board -- click the first player row to open the detail sheet.
  await page.waitForSelector('table tbody tr, [role="row"]', { timeout: 15_000 }).catch(() => {});
  const firstRow = page.locator('div[style*="grid-template-columns"]').filter({ hasText: /^\d/ }).first();
  await firstRow.click({ timeout: 15_000 }).catch(async () => {
    // Fall back to clicking the first row-like clickable element under the board.
    await page.locator('text=RB1').first().click({ timeout: 15_000 });
  });
  await page.waitForSelector('text=PROJECTION', { timeout: 15_000 });
  const bodyOff = await page.textContent('body');
  console.log(`[player card, off] contains 'board.json:tier_label': ${bodyOff.includes('board.json:tier_label')}`);
  console.log(`[player card, off] contains 'SUPPRESS this row': ${bodyOff.includes('SUPPRESS this row')}`);
  await shot(page, 'fr121-player-card-off.png');
  await page.close();
}

// ---- 4. Player card, switch ON ----
{
  const page = await newPage();
  await page.goto(url, { waitUntil: 'domcontentloaded' });
  await page.waitForSelector('text=/generated 20/', { timeout: 30_000 });
  await page.keyboard.down('Alt');
  await page.keyboard.press('KeyT');
  await page.keyboard.up('Alt');
  await page.waitForSelector('text=DATA SOURCES SHOWN', { timeout: 5_000 });
  const firstRow = page.locator('div[style*="grid-template-columns"]').filter({ hasText: /^\d/ }).first();
  await firstRow.click({ timeout: 15_000 }).catch(async () => {
    await page.locator('text=RB1').first().click({ timeout: 15_000 });
  });
  await page.waitForSelector('text=PROJECTION', { timeout: 15_000 });
  const bodyOn = await page.textContent('body');
  console.log(`[player card, on] contains 'board.json:tier_label': ${bodyOn.includes('board.json:tier_label')}`);
  console.log(`[player card, on] contains 'SUPPRESS this row': ${bodyOn.includes('SUPPRESS this row')}`);
  await shot(page, 'fr121-player-card-on.png');
  await page.close();
}

// ---- 5. Settings panel showing the "Show data sources" checkbox ----
{
  const page = await newPage();
  await page.goto(url, { waitUntil: 'domcontentloaded' });
  await page.waitForSelector('text=/generated 20/', { timeout: 30_000 });
  await page.getByRole('button', { name: 'Settings' }).click();
  await page.waitForSelector('text=Show data sources', { timeout: 10_000 });
  await shot(page, 'fr121-settings-panel.png');
  await page.close();
}

await browser.close();
console.log('done');
