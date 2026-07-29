/**
 * Threads 069/073 visual verification (one-off, kept for provenance).
 *
 * Captures, against a RUNNING dev server (default http://localhost:5190):
 *   1. board-069-scoring-format.png -- the Board header, which must read
 *      "<consensus_source> · half ppr · ..." (thread 069's done-looks-like).
 *   2. player-detail-073-no-suspension.png -- the first player's detail sheet.
 *      Every live row is suspension_flag: false today (ADR-053's curated list
 *      is verified-empty), so the CORRECT live state is no suspension block;
 *      the states that do render are unit-tested on synthetic rows
 *      (ui/__tests__/suspension-and-scoring-format.test.tsx).
 *
 * Usage: node e2e/verify-069-073.mjs [--url http://localhost:5190]
 */

import { mkdirSync } from 'node:fs';
import { join, dirname } from 'node:path';
import { fileURLToPath } from 'node:url';
import { chromium } from 'playwright';

const root = join(dirname(fileURLToPath(import.meta.url)), '..');
const artifacts = join(root, 'e2e', 'artifacts');
mkdirSync(artifacts, { recursive: true });

const args = process.argv.slice(2);
const url = args.includes('--url') ? args[args.indexOf('--url') + 1] : 'http://localhost:5190';

const browser = await chromium.launch();
const page = await browser.newPage({ viewport: { width: 1440, height: 900 } });
await page.goto(url, { waitUntil: 'networkidle' });

// Board is the landing view; wait for the provenance line to be real data.
await page.waitForSelector('text=/generated 20/', { timeout: 30_000 });

const provenance = await page.locator('text=/generated 20/').first().innerText();
console.log(`provenance line: ${provenance}`);
if (!/half ppr/.test(provenance)) {
  console.error('FAIL: provenance line does not carry the scoring format');
  process.exitCode = 1;
}

await page.screenshot({ path: join(artifacts, 'board-069-scoring-format.png') });

// Open the first player row's detail sheet; today's honest state has no
// suspension block anywhere.
await page.locator('text=Bijan Robinson').first().click();
await page.waitForSelector('text=PROJECTION', { timeout: 15_000 });
const suspCount = await page.locator('[data-testid="suspension-note"]').count();
console.log(`suspension-note blocks on live data: ${suspCount} (expected 0 while the curated list is empty)`);
if (suspCount !== 0) {
  console.error('FAIL: a suspension block rendered from live data whose flags are all false');
  process.exitCode = 1;
}
await page.screenshot({ path: join(artifacts, 'player-detail-073-no-suspension.png') });

await browser.close();
console.log(`screenshots written to ${artifacts}`);
