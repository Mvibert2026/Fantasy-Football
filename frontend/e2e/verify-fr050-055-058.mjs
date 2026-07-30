/**
 * Screenshot verification for FR-055 (draft-room column headers), FR-050
 * (VBD in the draft player list), and FR-058 (recommendation panel explains
 * a VBD override) -- built together, same component, same session.
 *
 * Cloud-container Chromium path per docs/frontend-cloud-runbook.md
 * (executablePath against the pre-installed binary; do not `playwright install`).
 *
 * Usage: node e2e/verify-fr050-055-058.mjs [--url http://localhost:5199]
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

// ---- Seed a draft state that produces a real FR-058 departure -----------
// Real board.json (2026-07-29, contract 1.14.0), top VBD players:
//   1 Bijan Robinson RB  vbd 172.17   2 Ja'Marr Chase WR  vbd 152.02
//   3 Jahmyr Gibbs RB    vbd 137.08   4 Puka Nacua WR     vbd 123.46
//   5 Christian McCaffrey RB vbd 116.56
// This league's real user_draft_slot is 3 (pick_sequence 3, 18, 23, ...),
// so pick 3 is the user's own turn. Picks 1-5 are logged so the top five
// VBD players are all off the board -- 1/2/4/5 as opponent picks, 3 as the
// user's own real pick (Gibbs) so MY ROSTER also shows something real.
// Picks 6-17 are honest off-board fillers (playerId null, per
// AUTO_FILL_PLACEHOLDER's own convention in DraftRoom.tsx) so no other real
// player is marked taken. That leaves Josh Allen (QB, rank 6, vbd 113.71) as
// the actual highest-VBD player still on the board once the user is on the
// clock again at pick 18 (round 2) -- but round 2 < 6 triggers the
// unbacktested early-QB penalty (-25), and Jaxon Smith-Njigba (WR, vbd
// 106.75) gets the unfilled-need bonus (+8, WR still open), so the
// recommendation's #1 pick becomes JSN, not the higher-VBD Josh Allen. That
// is a real, reproducible FR-058 departure, not a contrived score.
const leagueId = 'primary';
const now = new Date().toISOString();
const draftState = await page.evaluate(
  ({ leagueId, now }) => {
    function teamSlotAtPick(overallPick, teams) {
      const round = Math.ceil(overallPick / teams);
      const positionInRound = overallPick - (round - 1) * teams;
      return round % 2 === 1 ? positionInRound : teams - positionInRound + 1;
    }
    function roundOfPick(overallPick, teams) {
      return Math.ceil(overallPick / teams);
    }
    const teams = 10;
    const real = [
      { pick: 1, id: 1, name: 'Bijan Robinson' },
      { pick: 2, id: 2, name: "Ja'Marr Chase" },
      { pick: 3, id: 3, name: 'Jahmyr Gibbs' }, // the user's own pick 3
      { pick: 4, id: 4, name: 'Puka Nacua' },
      { pick: 5, id: 5, name: 'Christian McCaffrey' },
    ];
    const picks = [];
    for (let n = 1; n <= 17; n++) {
      const r = real.find((x) => x.pick === n);
      picks.push({
        overallPick: n,
        round: roundOfPick(n, teams),
        teamSlot: teamSlotAtPick(n, teams),
        playerId: r ? r.id : null,
        playerName: r ? r.name : `(auto-filled — unknown pick)`,
        timestamp: now,
        entryMode: r ? 'shortcut' : null,
      });
    }
    const state = { leagueId, mockId: 'fr058-verify-mock', picks, queue: [] };
    localStorage.setItem(`prep.draft.${leagueId}`, JSON.stringify(state));
    return state;
  },
  { leagueId, now },
);
console.log(`seeded ${draftState.picks.length} picks, leagueId=${draftState.leagueId}`);

await page.reload({ waitUntil: 'networkidle' });
await page.waitForSelector('text=/generated 20/', { timeout: 30_000 });

await page.getByText('Draft', { exact: true }).first().click();
await page.waitForSelector('text=/ON THE CLOCK/', { timeout: 15_000 });

const onClock = await page.locator('text=/#\\d+ · team \\d+/').first().innerText();
console.log(`on the clock: ${onClock}`);

// ---- FR-055 + FR-050: header row + VBD column on the board list ---------
const rankHeader = page.getByText('RANK', { exact: true });
await rankHeader.waitFor({ state: 'visible', timeout: 10_000 });
const headerTexts = await rankHeader.locator('xpath=..').innerText();
console.log(`header row text: ${headerTexts.replace(/\n/g, ' | ')}`);
const hasVbdHeader = await page.getByText('VBD', { exact: true }).count();
console.log(`VBD header cells found: ${hasVbdHeader}`);

await page.screenshot({ path: join(artifacts, 'fr055-fr050-headers-and-vbd.png'), fullPage: false });

// ---- FR-058: the override explanation panel ------------------------------
const overridePanel = page.getByText('WHY NOT HIGHEST VBD', { exact: true });
const overrideVisible = (await overridePanel.count()) > 0;
console.log(`WHY NOT HIGHEST VBD panel present: ${overrideVisible}`);
if (overrideVisible) {
  const panelText = await overridePanel.locator('xpath=..').innerText();
  console.log(`panel text:\n${panelText}`);
}

const recPanel = page.locator("text=/YOU'RE ON THE CLOCK/").first();
await recPanel.scrollIntoViewIfNeeded().catch(() => {});
await page.screenshot({ path: join(artifacts, 'fr058-vbd-override-explanation.png'), fullPage: false });

// ---- Negative control: user's own real first turn (pick 3), only picks 1-2
// logged (Bijan, Chase). The user IS on the clock here (unlike an untouched
// pick-1 state, where team 1 is on the clock and no RECOMMENDED panel renders
// at all -- that would prove nothing about the override panel specifically).
// Every available position is still unfilled, so the +8 term applies
// uniformly and does not reorder anything; the highest-VBD player left
// (Jahmyr Gibbs) should also be the recommendation's #1 pick -- ordering
// agrees with VBD, so FR-058's "nothing at all when nothing moved" applies.
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
    localStorage.setItem(`prep.draft.${leagueId}`, JSON.stringify({ leagueId, mockId: 'fr058-verify-mock-2', picks, queue: [] }));
  },
  { leagueId, now },
);
await page.reload({ waitUntil: 'networkidle' });
await page.waitForSelector('text=/generated 20/', { timeout: 30_000 });
await page.getByText('Draft', { exact: true }).first().click();
await page.waitForSelector('text=/ON THE CLOCK/', { timeout: 15_000 });
const onClock2 = await page.locator('text=/#\\d+ · team \\d+/').first().innerText();
console.log(`on the clock (negative control): ${onClock2}`);
const recommendedName = await page
  .locator("text=/YOU'RE ON THE CLOCK/")
  .locator('xpath=following::*[self::span][1]')
  .innerText()
  .catch(() => '(could not read)');
console.log(`recommended #1 pick: ${recommendedName}`);
const overridePanelFresh = await page.getByText('WHY NOT HIGHEST VBD', { exact: true }).count();
console.log(`WHY NOT HIGHEST VBD panel present (should be 0 -- recommendation agrees with VBD here): ${overridePanelFresh}`);
await page.screenshot({ path: join(artifacts, 'fr058-no-override-when-order-agrees.png'), fullPage: false });

console.log(`console errors: ${consoleErrors.length}`);
for (const e of consoleErrors) console.log(`  console error: ${e}`);

await browser.close();
