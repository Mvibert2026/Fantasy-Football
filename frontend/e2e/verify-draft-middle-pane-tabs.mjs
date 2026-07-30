/**
 * Screenshot verification for docs/design/DRAFT-MIDDLE-PANE.md: the middle
 * pane's fixed stack becomes one tab set (Recommend / Scarcity / Queue /
 * Insights), NEXT DECISION as a persistent footer, FR-049's look-ahead
 * toggle, FR-051's next-pick reference point, and FR-045's pace suppression.
 *
 * Cloud-container Chromium path per docs/frontend-cloud-runbook.md.
 * Usage: node e2e/verify-draft-middle-pane-tabs.mjs [--url http://localhost:5199]
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

await page.goto(url, { waitUntil: 'networkidle' });
await page.waitForSelector('text=/generated 20/', { timeout: 30_000 });

const leagueId = 'primary';
const now = new Date().toISOString();

// Real user_draft_slot=3, pick_sequence 3, 18, 23, ... -- log real picks 1-2
// (opponents) so the user is on the clock at their own real pick 3.
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
    localStorage.setItem(`prep.draft.${leagueId}`, JSON.stringify({ leagueId, mockId: 'middle-pane-verify', picks, queue: [] }));
  },
  { leagueId, now },
);
await page.reload({ waitUntil: 'networkidle' });
await page.waitForSelector('text=/generated 20/', { timeout: 30_000 });
await page.getByText('Draft', { exact: true }).first().click();
await page.waitForSelector('text=/ON THE CLOCK/', { timeout: 15_000 });

// ---- 1. Recommend tab, default "this pick" state, with the FR-051 reference point ----
await page.waitForSelector('text="RECOMMENDED (unvalidated stopgap score, not a backtested model)"', { timeout: 10_000 });
const refPointPresent = await page.getByText(/LIKELY BEST AVAILABLE AT YOUR PICK/).count();
console.log(`FR-051 reference point present (on-clock, this-pick): ${refPointPresent}`);
await page.screenshot({ path: join(artifacts, 'middle-pane-1-recommend-this-pick.png'), fullPage: false });

// ---- 2. Recommend tab, look-ahead toggled ----
const lookAheadBtn = page.getByRole('button', { name: /Look ahead/ });
const lookAheadCount = await lookAheadBtn.count();
console.log(`look-ahead toggle present: ${lookAheadCount}`);
if (lookAheadCount > 0) {
  await lookAheadBtn.first().click();
  await page.waitForSelector('text=/LOOKING AHEAD/', { timeout: 10_000 });
  const refPointGone = await page.getByText(/LIKELY BEST AVAILABLE AT YOUR PICK/).count();
  console.log(`FR-051 reference point present (look-ahead, should be 0): ${refPointGone}`);
  await page.screenshot({ path: join(artifacts, 'middle-pane-2-recommend-look-ahead.png'), fullPage: false });
  // toggle back for the remaining captures
  await page.getByRole('button', { name: 'This pick' }).click();
}

// ---- 3. Scarcity tab ----
await page.getByRole('button', { name: 'Scarcity' }).click();
await page.waitForSelector('text="POSITION SCARCITY"', { timeout: 10_000 });
await page.screenshot({ path: join(artifacts, 'middle-pane-3-scarcity.png'), fullPage: false });

// ---- 4. Scarcity tab with FR-045 pace suppression, after Auto-fill ----
await page.getByRole('button', { name: 'Recommend' }).click();
await page.evaluate(
  ({ leagueId, now }) => {
    function teamSlotAtPick(overallPick, teams) {
      const round = Math.ceil(overallPick / teams);
      const positionInRound = overallPick - (round - 1) * teams;
      return round % 2 === 1 ? positionInRound : teams - positionInRound + 1;
    }
    const teams = 10;
    const picks = [
      { overallPick: 1, round: 1, teamSlot: teamSlotAtPick(1, teams), playerId: null, playerName: 'Filler 1', timestamp: now, entryMode: 'typed' },
    ];
    localStorage.setItem(`prep.draft.${leagueId}`, JSON.stringify({ leagueId, mockId: 'middle-pane-verify-2', picks, queue: [] }));
  },
  { leagueId, now },
);
await page.reload({ waitUntil: 'networkidle' });
await page.waitForSelector('text=/generated 20/', { timeout: 30_000 });
await page.getByText('Draft', { exact: true }).first().click();
await page.waitForSelector('text=/NOT ON THE CLOCK|ON THE CLOCK/', { timeout: 15_000 });
await page.getByRole('button', { name: 'Auto-fill to my pick' }).click();
await page.getByRole('button', { name: 'Scarcity' }).click();
await page.waitForSelector('text="POSITION SCARCITY"', { timeout: 10_000 });
const suppressedCount = await page.getByText(/auto-filled picks stand in for unknown opponents/).count();
console.log(`FR-045 pace-suppression text count (should be > 0): ${suppressedCount}`);
const paceCount = await page.getByText(/ahead of pace|behind of pace/).count();
console.log(`stale pace phrases still present (should be 0): ${paceCount}`);
await page.screenshot({ path: join(artifacts, 'middle-pane-4-scarcity-pace-suppressed.png'), fullPage: false });

// ---- 5. Queue tab ----
await page.getByRole('button', { name: 'Queue' }).click();
await page.waitForSelector('text=/^Queue \\(/', { timeout: 10_000 });
await page.screenshot({ path: join(artifacts, 'middle-pane-5-queue.png'), fullPage: false });

// ---- 6. Insights tab, honest not-built state ----
await page.getByRole('button', { name: 'Insights' }).click();
await page.waitForSelector('text="Not built yet."', { timeout: 10_000 });
await page.screenshot({ path: join(artifacts, 'middle-pane-6-insights.png'), fullPage: false });

console.log(`console errors: ${consoleErrors.length}`);
for (const e of consoleErrors) console.log(`  console error: ${e}`);

await browser.close();
