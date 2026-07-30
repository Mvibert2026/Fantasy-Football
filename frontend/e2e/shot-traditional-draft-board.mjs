/**
 * Screenshot verification for FR-135 -- the traditional draft board
 * (`ui/components/TraditionalDraftBoard.tsx`, wired into DraftRoom.tsx as the
 * new "Draft Board" hub tab). Built to
 * `docs/design/research/draft-board/FINDINGS.md` §4.
 *
 * Captures the empty board (before any pick), a mid-draft partially-filled
 * board, both views (pick-order / roster-slot), both themes, at a wide width
 * and at 1180px (this project's own standing narrow reference width), plus
 * the mobile breakpoint switch.
 *
 * Cloud-container Chromium path per docs/frontend-cloud-runbook.md.
 * Usage: node e2e/shot-traditional-draft-board.mjs [--url http://localhost:5199]
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

// board.json player ids are real, dense small integers starting at 1, in
// overall-rank order (verified directly against public/data/board.json:
// id 1 = Bijan Robinson/rank 1, id 2 = Ja'Marr Chase/rank 2, ...) -- so
// `playerId: overall` below is a real board player, not a synthetic one; the
// app itself never assumes this mapping, it just looks up whatever id the
// pick record carries.
async function seedMidDraft(page, leagueId) {
  const now = new Date().toISOString();
  await page.evaluate(
    ({ leagueId, now }) => {
      const teams = 10;
      function teamSlotAtPick(overallPick) {
        const round = Math.ceil(overallPick / teams);
        const positionInRound = overallPick - (round - 1) * teams;
        return round % 2 === 1 ? positionInRound : teams - positionInRound + 1;
      }
      const picks = [];
      for (let overall = 1; overall <= 25; overall++) {
        const round = Math.ceil(overall / teams);
        const teamSlot = teamSlotAtPick(overall);
        if (overall === 13) {
          picks.push({ overallPick: overall, round, teamSlot, playerId: null, playerName: 'Local Waiver Pickup', timestamp: now, entryMode: 'typed' });
        } else if (overall === 24) {
          picks.push({ overallPick: overall, round, teamSlot, playerId: null, playerName: '(auto-filled — unknown pick)', timestamp: now, entryMode: null });
        } else {
          picks.push({ overallPick: overall, round, teamSlot, playerId: overall, playerName: `Board Player ${overall}`, timestamp: now, entryMode: 'shortcut' });
        }
      }
      localStorage.setItem(`prep.draft.${leagueId}`, JSON.stringify({ leagueId, mockId: 'tdb-shot', picks, queue: [] }));
    },
    { leagueId, now },
  );
}

const browser = await chromium.launch({ executablePath });
const leagueId = 'primary';

async function newPage(theme, viewport) {
  const page = await browser.newPage({ viewport });
  await page.addInitScript((t) => {
    try {
      localStorage.setItem('prep.theme', t);
    } catch {
      /* ignore */
    }
  }, theme);
  return page;
}

async function gotoDraftBoard(page) {
  await page.goto(url, { waitUntil: 'load', timeout: 40000 });
  await page.waitForSelector('text=/generated 20/', { timeout: 40_000 });
  await page.getByText('Draft', { exact: true }).first().click();
  await page.waitForSelector('[data-testid="tdb-onclock-bar"]', { timeout: 15_000 }).catch(async () => {
    await page.getByRole('button', { name: 'Draft Board' }).click();
    await page.waitForSelector('[data-testid="tdb-onclock-bar"]', { timeout: 15_000 });
  });
  await page.getByRole('button', { name: 'Draft Board' }).click();
  await page.waitForSelector('[data-testid="tdb-onclock-bar"]', { timeout: 15_000 });
}

let n = 0;
function shotName(label) {
  n += 1;
  return `tdb-${String(n).padStart(2, '0')}-${label}.png`;
}

// ---- 1. Empty board, pick-order, wide, dark ----
{
  const page = await newPage('dark', { width: 1700, height: 1100 });
  await gotoDraftBoard(page);
  const file = shotName('empty-pickorder-wide-dark');
  await page.screenshot({ path: join(artifacts, file), fullPage: false });
  console.log('wrote', file);
  await page.close();
}

// ---- 2. Empty board, pick-order, 1180w, dark ----
{
  const page = await newPage('dark', { width: 1180, height: 1000 });
  await gotoDraftBoard(page);
  await page.screenshot({ path: join(artifacts, shotName('empty-pickorder-1180-dark')), fullPage: false });
  await page.close();
}

// ---- 3. Empty board, roster-slot, wide, dark ----
{
  const page = await newPage('dark', { width: 1700, height: 1100 });
  await gotoDraftBoard(page);
  await page.getByTestId('tdb-view-toggle-roster-slot').click();
  await page.waitForSelector('[data-testid="tdb-roster-slot-grid"]', { timeout: 10_000 });
  await page.screenshot({ path: join(artifacts, shotName('empty-rosterslot-wide-dark')), fullPage: false });
  await page.close();
}

// ---- 4. Empty board, pick-order, wide, light ----
{
  const page = await newPage('light', { width: 1700, height: 1100 });
  await gotoDraftBoard(page);
  await page.screenshot({ path: join(artifacts, shotName('empty-pickorder-wide-light')), fullPage: false });
  await page.close();
}

// ---- 5. Mid-draft, pick-order, wide, dark ----
{
  const page = await newPage('dark', { width: 1700, height: 1100 });
  await gotoDraftBoard(page);
  await seedMidDraft(page, leagueId);
  await page.reload({ waitUntil: 'load' });
  await page.waitForSelector('text=/generated 20/', { timeout: 40_000 });
  await page.getByText('Draft', { exact: true }).first().click();
  await page.getByRole('button', { name: 'Draft Board' }).click();
  await page.waitForSelector('[data-testid="tdb-onclock-bar"]', { timeout: 15_000 });
  await page.waitForSelector('text=/ON THE CLOCK/', { timeout: 15_000 });
  await page.screenshot({ path: join(artifacts, shotName('mid-pickorder-wide-dark')), fullPage: false });
  await page.close();
}

// ---- 6. Mid-draft, pick-order, 1180w, dark ----
{
  const page = await newPage('dark', { width: 1180, height: 1000 });
  await gotoDraftBoard(page);
  await seedMidDraft(page, leagueId);
  await page.reload({ waitUntil: 'load' });
  await page.waitForSelector('text=/generated 20/', { timeout: 40_000 });
  await page.getByText('Draft', { exact: true }).first().click();
  await page.getByRole('button', { name: 'Draft Board' }).click();
  await page.waitForSelector('[data-testid="tdb-onclock-bar"]', { timeout: 15_000 });
  await page.screenshot({ path: join(artifacts, shotName('mid-pickorder-1180-dark')), fullPage: false });
  await page.close();
}

// ---- 7. Mid-draft, roster-slot, wide, dark ----
{
  const page = await newPage('dark', { width: 1700, height: 1100 });
  await gotoDraftBoard(page);
  await seedMidDraft(page, leagueId);
  await page.reload({ waitUntil: 'load' });
  await page.waitForSelector('text=/generated 20/', { timeout: 40_000 });
  await page.getByText('Draft', { exact: true }).first().click();
  await page.getByRole('button', { name: 'Draft Board' }).click();
  await page.waitForSelector('[data-testid="tdb-onclock-bar"]', { timeout: 15_000 });
  await page.getByTestId('tdb-view-toggle-roster-slot').click();
  await page.waitForSelector('[data-testid="tdb-roster-slot-grid"]', { timeout: 10_000 });
  await page.screenshot({ path: join(artifacts, shotName('mid-rosterslot-wide-dark')), fullPage: false });
  await page.close();
}

// ---- 8. Mid-draft, roster-slot, 1180w, dark ----
{
  const page = await newPage('dark', { width: 1180, height: 1000 });
  await gotoDraftBoard(page);
  await seedMidDraft(page, leagueId);
  await page.reload({ waitUntil: 'load' });
  await page.waitForSelector('text=/generated 20/', { timeout: 40_000 });
  await page.getByText('Draft', { exact: true }).first().click();
  await page.getByRole('button', { name: 'Draft Board' }).click();
  await page.waitForSelector('[data-testid="tdb-onclock-bar"]', { timeout: 15_000 });
  await page.getByTestId('tdb-view-toggle-roster-slot').click();
  await page.waitForSelector('[data-testid="tdb-roster-slot-grid"]', { timeout: 10_000 });
  await page.screenshot({ path: join(artifacts, shotName('mid-rosterslot-1180-dark')), fullPage: false });
  await page.close();
}

// ---- 9. Mid-draft, pick-order, wide, light ----
{
  const page = await newPage('light', { width: 1700, height: 1100 });
  await gotoDraftBoard(page);
  await seedMidDraft(page, leagueId);
  await page.reload({ waitUntil: 'load' });
  await page.waitForSelector('text=/generated 20/', { timeout: 40_000 });
  await page.getByText('Draft', { exact: true }).first().click();
  await page.getByRole('button', { name: 'Draft Board' }).click();
  await page.waitForSelector('[data-testid="tdb-onclock-bar"]', { timeout: 15_000 });
  await page.screenshot({ path: join(artifacts, shotName('mid-pickorder-wide-light')), fullPage: false });
  await page.close();
}

// ---- 10. Mid-draft, pick-order, 1180w, light ----
{
  const page = await newPage('light', { width: 1180, height: 1000 });
  await gotoDraftBoard(page);
  await seedMidDraft(page, leagueId);
  await page.reload({ waitUntil: 'load' });
  await page.waitForSelector('text=/generated 20/', { timeout: 40_000 });
  await page.getByText('Draft', { exact: true }).first().click();
  await page.getByRole('button', { name: 'Draft Board' }).click();
  await page.waitForSelector('[data-testid="tdb-onclock-bar"]', { timeout: 15_000 });
  await page.screenshot({ path: join(artifacts, shotName('mid-pickorder-1180-light')), fullPage: false });
  await page.close();
}

// ---- 11. Mid-draft, roster-slot, wide, light ----
{
  const page = await newPage('light', { width: 1700, height: 1100 });
  await gotoDraftBoard(page);
  await seedMidDraft(page, leagueId);
  await page.reload({ waitUntil: 'load' });
  await page.waitForSelector('text=/generated 20/', { timeout: 40_000 });
  await page.getByText('Draft', { exact: true }).first().click();
  await page.getByRole('button', { name: 'Draft Board' }).click();
  await page.waitForSelector('[data-testid="tdb-onclock-bar"]', { timeout: 15_000 });
  await page.getByTestId('tdb-view-toggle-roster-slot').click();
  await page.waitForSelector('[data-testid="tdb-roster-slot-grid"]', { timeout: 10_000 });
  await page.screenshot({ path: join(artifacts, shotName('mid-rosterslot-wide-light')), fullPage: false });
  await page.close();
}

// ---- 12. Mobile breakpoint switch, pick-order, dark ----
{
  const page = await newPage('dark', { width: 420, height: 850 });
  await gotoDraftBoard(page);
  await seedMidDraft(page, leagueId);
  await page.reload({ waitUntil: 'load' });
  await page.waitForSelector('text=/generated 20/', { timeout: 40_000 });
  await page.getByText('Draft', { exact: true }).first().click();
  await page.getByRole('button', { name: 'Draft Board' }).click();
  await page.waitForSelector('[data-testid="tdb-mobile-round"]', { timeout: 15_000 });
  await page.screenshot({ path: join(artifacts, shotName('mobile-pickorder-dark')), fullPage: false });
  await page.close();
}

// ---- 13. Mobile breakpoint switch, roster-slot, dark ----
{
  const page = await newPage('dark', { width: 420, height: 850 });
  await gotoDraftBoard(page);
  await seedMidDraft(page, leagueId);
  await page.reload({ waitUntil: 'load' });
  await page.waitForSelector('text=/generated 20/', { timeout: 40_000 });
  await page.getByText('Draft', { exact: true }).first().click();
  await page.getByRole('button', { name: 'Draft Board' }).click();
  await page.waitForSelector('[data-testid="tdb-mobile-round"]', { timeout: 15_000 });
  await page.getByTestId('tdb-view-toggle-roster-slot').click();
  await page.waitForSelector('[data-testid="tdb-mobile-teams"]', { timeout: 10_000 });
  await page.screenshot({ path: join(artifacts, shotName('mobile-rosterslot-dark')), fullPage: false });
  await page.close();
}

console.log(`wrote ${n} screenshots to ${artifacts}`);
await browser.close();
