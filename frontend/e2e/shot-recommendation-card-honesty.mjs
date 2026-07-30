/**
 * Screenshot recipe for thread
 * 2026-07-30-recommendation-card-states-a-rule-the-code-does-.
 *
 * Seeds picks 1-2 as fillers so overall pick 3 (this league's real
 * pick_sequence[0], user_draft_slot=3, teams=10) puts the user on the clock,
 * matching draft-room-recommendation.test.tsx's own seeding pattern, then
 * captures:
 *   - the RECOMMENDED / WHAT YOU GIVE UP card (items 1-2)
 *   - the board list header + a few rows, for the AVAIL column (item 3)
 * in both light and dark theme.
 *
 * Usage: node e2e/shot-recommendation-card-honesty.mjs --url http://localhost:5220 --tag before|after
 */
import { mkdirSync } from 'node:fs';
import { join, dirname } from 'node:path';
import { fileURLToPath } from 'node:url';
import { chromium } from 'playwright';

const root = join(dirname(fileURLToPath(import.meta.url)), '..');
const artifacts = join(root, 'e2e', 'artifacts');
mkdirSync(artifacts, { recursive: true });

const args = process.argv.slice(2);
const url = args.includes('--url') ? args[args.indexOf('--url') + 1] : 'http://localhost:5220';
const tag = args.includes('--tag') ? args[args.indexOf('--tag') + 1] : 'shot';

const browsersPath = process.env.PLAYWRIGHT_BROWSERS_PATH || '/opt/pw-browsers';
const executablePath = join(browsersPath, 'chromium');

function teamSlotAtPick(overallPick, teams) {
  const round = Math.ceil(overallPick / teams);
  const positionInRound = overallPick - (round - 1) * teams;
  return round % 2 === 1 ? positionInRound : teams - positionInRound + 1;
}

const LEAGUE_ID = 'primary';
const TEAMS = 10;

function seededDraftState() {
  const picks = [];
  for (let n = 1; n < 3; n++) {
    picks.push({
      overallPick: n,
      round: 1,
      teamSlot: teamSlotAtPick(n, TEAMS),
      playerId: null,
      playerName: `Filler ${n}`,
      timestamp: new Date().toISOString(),
      entryMode: 'typed',
    });
  }
  return { leagueId: LEAGUE_ID, mockId: 'shot-mock', picks, queue: [] };
}

async function shootTheme(browser, theme) {
  const context = await browser.newContext({ viewport: { width: 1440, height: 1000 } });
  const page = await context.newPage();
  await page.goto(url, { waitUntil: 'load' });
  await page.evaluate(
    ([state, t]) => {
      localStorage.setItem(`prep.draft.${state.leagueId}`, JSON.stringify(state));
      // ui/components/shell/useTheme.ts: 'prep.theme', dark is the default
      // with NO data-theme attribute -- only 'light' sets one.
      localStorage.setItem('prep.theme', t);
    },
    [seededDraftState(), theme],
  );
  await page.reload({ waitUntil: 'load' });
  await page.waitForSelector('text=/generated 20/', { timeout: 30_000 });

  await page.getByText('Draft', { exact: true }).first().click();
  await page.locator('input[placeholder^="Mark pick"]').waitFor({ state: 'visible', timeout: 15_000 });
  await page.waitForTimeout(400);

  // Board tab: header row + AVAIL column, no scroll needed (item 3).
  await page.screenshot({ path: join(artifacts, `rec-card-${tag}-${theme}-board.png`), fullPage: false });

  // Recommend pane: STRATEGY sits above RECOMMENDED / WHAT YOU GIVE UP inside
  // its own scrollable pane -- scroll the text into view before capturing.
  const recommendedLabel = page.getByText(/RECOMMENDED \(unvalidated/);
  await recommendedLabel.waitFor({ state: 'visible', timeout: 10_000 });
  await recommendedLabel.scrollIntoViewIfNeeded();
  await page.waitForTimeout(200);
  await page.screenshot({ path: join(artifacts, `rec-card-${tag}-${theme}-card.png`), fullPage: false });

  await context.close();
}

const browser = await chromium.launch({ executablePath });
await shootTheme(browser, 'dark');
await shootTheme(browser, 'light');
await browser.close();
console.log(`done: ${tag}`);
