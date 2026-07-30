/**
 * Screenshot verification for the 2026-07-31 design round item 6
 * (docs/design/RANKINGS-PANE.md item 1) plus FR-122 and the light-theme row
 * parity item bundled with it:
 *
 *   A. PLAYER column never drops, at 1180w and a wide width.
 *   B. FR-122: typing in the pick-entry field narrows the visible row list.
 *   C. Light-theme alternating row tint, matching Board.tsx's already-shipped
 *      treatment (LIGHT-THEME-SHADING.md).
 *
 * Cloud-container Chromium path per docs/frontend-cloud-runbook.md.
 * Usage: node e2e/verify-rankings-pane.mjs [--url http://localhost:5199]
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

const leagueId = 'primary';
const now = new Date().toISOString();

/** Opens Draft mode with two real opponent picks logged (so the user's own
 *  slot, 3, is genuinely on the clock at pick 3 -- same seed the middle-pane
 *  verification script uses) and optionally forces the light theme first. */
async function openDraftRoom(page, { theme } = {}) {
  if (theme === 'light') {
    await page.addInitScript(() => {
      try {
        localStorage.setItem('prep.theme', 'light');
      } catch {
        /* ignore */
      }
    });
  }
  await page.goto(url, { waitUntil: 'load', timeout: 90000 });
  await page.waitForSelector('text=/generated 20/', { timeout: 90_000 });
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
      localStorage.setItem(`prep.draft.${leagueId}`, JSON.stringify({ leagueId, mockId: 'rankings-pane-verify', picks, queue: [] }));
    },
    { leagueId, now },
  );
  await page.reload({ waitUntil: 'load', timeout: 90000 });
  await page.waitForSelector('text=/generated 20/', { timeout: 90_000 });
  await page.getByText('Draft', { exact: true }).first().click();
  await page.waitForSelector('text=/ON THE CLOCK/', { timeout: 30_000 });
  await page.waitForSelector('[data-testid="rankings-pane-list"]', { timeout: 30_000 });
}

const results = {};

// ---- A. PLAYER column at a wide width, dark (default) ----
{
  const page = await browser.newPage({ viewport: { width: 1600, height: 1000 } });
  await openDraftRoom(page);
  const headerHasPlayer = await page.getByTestId('rankings-pane-header-row').getByText('PLAYER').count();
  results['wide dark: PLAYER header present'] = headerHasPlayer;
  await page.screenshot({ path: join(artifacts, 'rankings-pane-01-wide-dark.png'), fullPage: false });
  await page.close();
}

// ---- A. PLAYER column at 1180w, dark -- the exact defect width ----
{
  const page = await browser.newPage({ viewport: { width: 1180, height: 900 } });
  await openDraftRoom(page);
  const headerHasPlayer = await page.getByTestId('rankings-pane-header-row').getByText('PLAYER').count();
  results['1180w dark: PLAYER header present'] = headerHasPlayer;
  // Also confirm a real row's name text is present, not just the header word.
  const firstRowText = await page.getByTestId('rankings-pane-list').innerText();
  results['1180w dark: row list contains "Bijan"'] = firstRowText.includes('Bijan');
  await page.screenshot({ path: join(artifacts, 'rankings-pane-02-1180w-dark.png'), fullPage: false });
  await page.close();
}

// ---- C. Wide width, light theme -- row shading parity ----
{
  const page = await browser.newPage({ viewport: { width: 1600, height: 1000 } });
  await openDraftRoom(page, { theme: 'light' });
  const themeAttr = await page.evaluate(() => document.documentElement.getAttribute('data-theme'));
  results['light page data-theme attribute'] = themeAttr;
  await page.screenshot({ path: join(artifacts, 'rankings-pane-03-wide-light.png'), fullPage: false });
  await page.close();
}

// ---- A + C. 1180w, light theme -- both fixes together, the hardest combination ----
{
  const page = await browser.newPage({ viewport: { width: 1180, height: 900 } });
  await openDraftRoom(page, { theme: 'light' });
  const headerHasPlayer = await page.getByTestId('rankings-pane-header-row').getByText('PLAYER').count();
  results['1180w light: PLAYER header present'] = headerHasPlayer;
  await page.screenshot({ path: join(artifacts, 'rankings-pane-04-1180w-light.png'), fullPage: false });
  await page.close();
}

// ---- B. FR-122 search filter, wide dark: before/after typing ----
{
  const page = await browser.newPage({ viewport: { width: 1600, height: 1000 } });
  await openDraftRoom(page);
  const rowCountBefore = await page.getByTestId('rankings-pane-list').locator('[data-testid^="rankings-pane-row-"]').count();
  results['FR-122: row count before search'] = rowCountBefore;
  await page.screenshot({ path: join(artifacts, 'rankings-pane-05-search-before.png'), fullPage: false });

  const input = page.getByPlaceholder(/Mark pick/);
  await input.fill('RB1');
  await page.waitForTimeout(800);
  const rowCountAfter = await page.getByTestId('rankings-pane-list').locator('[data-testid^="rankings-pane-row-"]').count();
  results['FR-122: row count after typing "RB1"'] = rowCountAfter;
  const listText = await page.getByTestId('rankings-pane-list').innerText();
  results['FR-122: filtered list still shows an RB10-range player'] = /RB1\d/.test(listText) || listText.includes('RB1');
  await page.screenshot({ path: join(artifacts, 'rankings-pane-06-search-after-RB1.png'), fullPage: false });

  await input.fill('zzz-no-such-player-zzz');
  await page.waitForTimeout(800);
  const noMatchText = await page.getByText(/No still-available player matches/).count();
  results['FR-122: honest empty state on a query with no matches'] = noMatchText;
  await page.screenshot({ path: join(artifacts, 'rankings-pane-07-search-no-match.png'), fullPage: false });

  await page.close();
}

console.log(JSON.stringify(results, null, 2));
await browser.close();
