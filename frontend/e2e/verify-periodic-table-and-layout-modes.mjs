/**
 * Screenshot verification for the 2026-07-31 design round's items 3 and 7,
 * built together because they share one mechanism:
 *   - docs/design/PERIODIC-TABLE-GRID.md -- the Grid pane tab + its Expand
 *     sheet (draft-order and position-by-team sort modes).
 *   - docs/design/PANE-LAYOUT-MODES.md -- Board/Balanced/Decide layout
 *     presets, one keystroke each (Alt+1/2/3), Alt+G for Expand.
 *
 * Cloud-container Chromium path per docs/frontend-cloud-runbook.md.
 * Usage: node e2e/verify-periodic-table-and-layout-modes.mjs [--url http://localhost:5199]
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
page.on('console', (msg) => {
  if (msg.type() === 'error') consoleErrors.push(msg.text());
});
page.on('pageerror', (err) => consoleErrors.push(String(err)));

await page.goto(url, { waitUntil: 'load' });
await page.waitForSelector('text=/generated 20/', { timeout: 60_000 });

const leagueId = 'primary';
const now = new Date().toISOString();

// Real user_draft_slot=3, pick_sequence 3, 18, 23, ... -- log real picks 1-2
// (opponents) so the user is off the clock, matching the other middle-pane
// verification script's own setup.
await page.evaluate(
  ({ leagueId, now }) => {
    function teamSlotAtPick(overallPick, teams) {
      const round = Math.ceil(overallPick / teams);
      const positionInRound = overallPick - (round - 1) * teams;
      return round % 2 === 1 ? positionInRound : teams - positionInRound + 1;
    }
    const teams = 10;
    const real = [
      { pick: 1, id: 1, name: 'Bijan Robinson' },
      { pick: 2, id: 2, name: "Ja'Marr Chase" },
    ];
    const picks = real.map((r) => ({
      overallPick: r.pick,
      round: 1,
      teamSlot: teamSlotAtPick(r.pick, teams),
      playerId: r.id,
      playerName: r.name,
      timestamp: now,
      entryMode: 'shortcut',
    }));
    localStorage.setItem(`prep.draft.${leagueId}`, JSON.stringify({ leagueId, mockId: 'grid-layout-verify', picks, queue: [] }));
  },
  { leagueId, now },
);
await page.reload({ waitUntil: 'load' });
await page.waitForSelector('text=/generated 20/', { timeout: 60_000 });
await page.getByText('Draft', { exact: true }).first().click();
await page.waitForSelector('text=/ON THE CLOCK/', { timeout: 15_000 });

// ---- 1. Grid tab (preview), inside the pane, alongside the four original tabs ----
await page.getByRole('button', { name: 'Grid' }).click();
await page.waitForSelector('text=/Expand/', { timeout: 10_000 });
const recommendStillThere = await page.getByRole('button', { name: 'Recommend' }).count();
const scarcityStillThere = await page.getByRole('button', { name: 'Scarcity' }).count();
const queueStillThere = await page.getByRole('button', { name: 'Queue' }).count();
const insightsStillThere = await page.getByRole('button', { name: 'Insights' }).count();
console.log(`additive check -- Recommend/Scarcity/Queue/Insights tabs still present: ${recommendStillThere}/${scarcityStillThere}/${queueStillThere}/${insightsStillThere} (all should be 1)`);
await page.screenshot({ path: join(artifacts, 'grid-1-pane-preview.png'), fullPage: false });

// ---- 2. Expand sheet, draft-order sort (default) ----
await page.getByRole('button', { name: /Expand/ }).click();
await page.waitForSelector('text="GRID"', { timeout: 10_000 });
const rosterRailVisible = await page.getByText('MY ROSTER').count();
console.log(`roster rail (MY ROSTER) still visible while expanded: ${rosterRailVisible} (should be 1)`);
await page.screenshot({ path: join(artifacts, 'grid-2-expanded-draft-order.png'), fullPage: false });

// ---- 3. Expand sheet, position-by-team sort ----
await page.getByRole('button', { name: 'Position × team' }).click();
await page.waitForSelector('[data-testid="grid-header-QB"]', { timeout: 10_000 });
await page.screenshot({ path: join(artifacts, 'grid-3-expanded-position-by-team.png'), fullPage: false });

// ---- 4. Esc closes the sheet ----
await page.keyboard.press('Escape');
await page.waitForSelector('text="GRID"', { state: 'detached', timeout: 10_000 }).catch(() => {});
const gridStillOpen = await page.getByText('GRID', { exact: true }).count();
console.log(`Esc closed the grid sheet: ${gridStillOpen === 0 ? 'yes' : 'NO -- still open'}`);

// ---- 5-7. Layout modes: Board / Balanced / Decide ----
await page.getByRole('button', { name: 'Board layout' }).click();
await page.waitForTimeout(150);
await page.screenshot({ path: join(artifacts, 'grid-4-layout-board.png'), fullPage: false });

await page.getByRole('button', { name: 'Balanced layout' }).click();
await page.waitForTimeout(150);
await page.screenshot({ path: join(artifacts, 'grid-5-layout-balanced.png'), fullPage: false });

await page.getByRole('button', { name: 'Decide layout' }).click();
await page.waitForTimeout(150);
await page.screenshot({ path: join(artifacts, 'grid-6-layout-decide.png'), fullPage: false });

// ---- 8. Alt+1/Alt+G work as keyboard shortcuts from anywhere on the screen ----
await page.keyboard.down('Alt');
await page.keyboard.press('Digit2'); // back to Balanced
await page.keyboard.up('Alt');
await page.waitForTimeout(150);
await page.keyboard.down('Alt');
await page.keyboard.press('KeyG');
await page.keyboard.up('Alt');
await page.waitForSelector('text="GRID"', { timeout: 10_000 });
console.log('Alt+G opened the grid sheet from a bare keypress: yes');
await page.screenshot({ path: join(artifacts, 'grid-7-altg-reopened.png'), fullPage: false });

console.log(`console errors: ${consoleErrors.length}`);
for (const e of consoleErrors) console.log(`  console error: ${e}`);

await browser.close();
