/**
 * Screenshot recipe for thread 082 / FR-024 (ADP display on Board, Draft
 * Room, Player Detail). Follows docs/frontend-cloud-runbook.md's cloud
 * Chromium recipe verbatim (explicit executablePath against the
 * pre-installed 1194 binary, not the pinned 1234 `playwright install` would
 * try to fetch).
 *
 * Usage: node e2e/cloud-adp-screenshot.mjs [--url http://localhost:5199]
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
const page = await browser.newPage({ viewport: { width: 1440, height: 900 } });
page.on('console', (msg) => {
  if (msg.type() === 'error') console.log(`console error: ${msg.text()}`);
});

await page.goto(url, { waitUntil: 'networkidle' });
await page.waitForSelector('text=/generated 20/', { timeout: 30_000 });

// ---- 1. Board (prep) table with the new ADP column -----------------------
await page.screenshot({ path: join(artifacts, 'adp-board-2026-07-29.png'), fullPage: false });
console.log('wrote adp-board-2026-07-29.png');

// ---- 1b. Scroll to a null-ADP row (Jeremiyah Love, overall_rank 33) so the
// board table's own honest-null "—" rendering is visible, not just present
// values in the top-16 rows.
await page.getByText('Jeremiyah Love', { exact: true }).first().scrollIntoViewIfNeeded();
await page.waitForTimeout(150);
await page.screenshot({ path: join(artifacts, 'adp-board-null-row-2026-07-29.png'), fullPage: false });
console.log('wrote adp-board-null-row-2026-07-29.png');

// ---- 2. Board row with a REAL ADP value -> Player Detail ------------------
// Bijan Robinson, overall_rank 1, adp 3.29 -- present in the live export.
await page.getByText('Bijan Robinson', { exact: true }).first().click();
const marketAdpPresent = page.getByText('MARKET ADP', { exact: false }).first();
await marketAdpPresent.waitFor({ timeout: 10_000 });
await marketAdpPresent.scrollIntoViewIfNeeded();
await page.waitForTimeout(150);
await page.screenshot({ path: join(artifacts, 'adp-player-detail-present.png'), fullPage: false });
console.log('wrote adp-player-detail-present.png (Bijan Robinson, ADP present)');
await page.keyboard.press('Escape');
await page.waitForTimeout(200);

// ---- 3. Board row with NO ADP value (honest null) -> Player Detail -------
// Jeremiyah Love, overall_rank 33 -- a real 2026 rookie ranked in our top 40
// with no MFL opinion at all (MFL only covers roughly the top ~230 picks).
await page.getByText('Jeremiyah Love', { exact: true }).first().click();
const marketAdpNull = page.getByText('MARKET ADP', { exact: false }).first();
await marketAdpNull.waitFor({ timeout: 10_000 });
await marketAdpNull.scrollIntoViewIfNeeded();
await page.waitForTimeout(150);
await page.screenshot({ path: join(artifacts, 'adp-player-detail-null.png'), fullPage: false });
console.log('wrote adp-player-detail-null.png (Jeremiyah Love, ADP null)');
await page.keyboard.press('Escape');
await page.waitForTimeout(200);

// ---- 4. Draft Room board list with the compact ADP figure -----------------
await page.getByText('Draft', { exact: true }).first().click();
await page.waitForTimeout(800);
await page.screenshot({ path: join(artifacts, 'adp-draft-room-2026-07-29.png'), fullPage: false });
console.log('wrote adp-draft-room-2026-07-29.png');

// ---- 4b. Scroll the draft-room board list to the same null-ADP player. ----
await page.getByText('Jeremiyah Love', { exact: true }).first().scrollIntoViewIfNeeded();
await page.waitForTimeout(150);
await page.screenshot({ path: join(artifacts, 'adp-draft-room-null-row-2026-07-29.png'), fullPage: false });
console.log('wrote adp-draft-room-null-row-2026-07-29.png');

await browser.close();
