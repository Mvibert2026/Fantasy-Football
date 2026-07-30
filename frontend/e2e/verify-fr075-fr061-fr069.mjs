/**
 * Screenshot verification for FR-075 (archetype card fix), FR-061 (strategy
 * selector), FR-069/FR-040 (League Settings) -- built together, this session.
 *
 * Usage: node e2e/verify-fr075-fr061-fr069.mjs [--url http://localhost:5199]
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
const page = await browser.newPage({ viewport: { width: 1600, height: 1100 } });
const consoleErrors = [];
page.on('console', (msg) => {
  if (msg.type() === 'error') consoleErrors.push(msg.text());
});
page.on('pageerror', (err) => consoleErrors.push(String(err)));

await page.goto(url, { waitUntil: 'load', timeout: 60_000 });
await page.waitForSelector('text=/generated 20/', { timeout: 60_000 });

// ---- FR-075: archetype on the player card -------------------------------
// Click the first board row that has a real archetype label -- Bijan
// Robinson (RB, real label per data/export/player_descriptions.json).
await page.getByText('Bijan Robinson', { exact: false }).first().click();
await page.waitForSelector('text=ARCHETYPE', { timeout: 60_000 });
console.log('FR-075: player detail opened for Bijan Robinson');
const archetypeChipCount = await page.locator('text=/BELL COW|COMMITTEE|ROTATION|UNCLASSIFIED|N\\/A/').count();
console.log(`FR-075: archetype chip text present (${archetypeChipCount} matches)`);
const falseClaimCount = await page.getByText('Not computed: archetype').count();
console.log(`FR-075: old false claim "Not computed: archetype" present: ${falseClaimCount} (must be 0)`);
await page.screenshot({ path: join(artifacts, 'fr075-archetype-card.png'), fullPage: false });

// Scroll to the ARCHETYPE section for a close-up of the fuller detail.
const archetypeHeader = page.getByText('ARCHETYPE', { exact: true }).first();
await archetypeHeader.scrollIntoViewIfNeeded();
await page.screenshot({ path: join(artifacts, 'fr075-archetype-section.png'), fullPage: false });

await page.keyboard.press('Escape');
await page.waitForTimeout(200);

// ---- FR-069/FR-040: League Settings --------------------------------------
await page.getByRole('button', { name: 'Settings' }).click();
await page.waitForSelector('text=SCORED UNDER', { timeout: 60_000 });
console.log('FR-069/FR-040: Settings panel opened');
await page.screenshot({ path: join(artifacts, 'fr069-settings-panel.png'), fullPage: false });
await page.keyboard.press('Escape');
await page.waitForTimeout(200);

// ---- FR-061: strategy selector -------------------------------------------
await page.getByText('Draft', { exact: true }).first().click();
await page.waitForSelector('text=STRATEGY', { timeout: 60_000 });
console.log('FR-061: Draft room loaded, STRATEGY selector visible');
await page.screenshot({ path: join(artifacts, 'fr061-strategy-selector-default.png'), fullPage: false });

// Seed two filler picks so the user (real slot 3) is on the clock at their
// actual first turn, same real-data pattern as verify-fr050-055-058.mjs.
const leagueId = 'primary';
const now = new Date().toISOString();
await page.evaluate(
  ({ leagueId, now }) => {
    function teamSlotAtPick(overallPick, teams) {
      const round = Math.ceil(overallPick / teams);
      const positionInRound = overallPick - (round - 1) * teams;
      return round % 2 === 1 ? positionInRound : teams - positionInRound + 1;
    }
    const teams = 10;
    const picks = [];
    for (let n = 1; n < 3; n++) {
      picks.push({
        overallPick: n,
        round: 1,
        teamSlot: teamSlotAtPick(n, teams),
        playerId: null,
        playerName: `Filler ${n}`,
        timestamp: now,
        entryMode: 'typed',
      });
    }
    localStorage.setItem(`prep.draft.${leagueId}`, JSON.stringify({ leagueId, mockId: 'fr061-verify-mock', picks, queue: [] }));
  },
  { leagueId, now },
);
await page.reload({ waitUntil: 'load', timeout: 60_000 });
await page.waitForSelector('text=/generated 20/', { timeout: 60_000 });
await page.getByText('Draft', { exact: true }).first().click();
await page.waitForSelector('text=/ON THE CLOCK/', { timeout: 60_000 });
await page.waitForSelector('text=STRATEGY', { timeout: 60_000 });

const zeroRbButton = page.getByRole('button', { name: /Zero RB/ }).first();
await zeroRbButton.click();
await page.waitForTimeout(300);
const adjustmentPanelCount = await page.getByText(/STRATEGY ADJUSTMENT/).count();
console.log(`FR-061: STRATEGY ADJUSTMENT panel present after selecting Zero RB: ${adjustmentPanelCount}`);
await page.screenshot({ path: join(artifacts, 'fr061-strategy-zero-rb-adjustment.png'), fullPage: false });

console.log(`console errors: ${consoleErrors.length}`);
for (const e of consoleErrors) console.log(`  console error: ${e}`);

await browser.close();
