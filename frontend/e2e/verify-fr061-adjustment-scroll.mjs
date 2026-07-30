import { mkdirSync } from 'node:fs';
import { join, dirname } from 'node:path';
import { fileURLToPath } from 'node:url';
import { chromium } from 'playwright';

const root = join(dirname(fileURLToPath(import.meta.url)), '..');
const artifacts = join(root, 'e2e', 'artifacts');
mkdirSync(artifacts, { recursive: true });
const url = 'http://localhost:5199';
const browsersPath = process.env.PLAYWRIGHT_BROWSERS_PATH || '/opt/pw-browsers';
const executablePath = join(browsersPath, 'chromium');

const browser = await chromium.launch({ executablePath });
const page = await browser.newPage({ viewport: { width: 1600, height: 1100 } });
await page.goto(url, { waitUntil: 'load', timeout: 60_000 });
await page.waitForSelector('text=/generated 20/', { timeout: 60_000 });

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
    localStorage.setItem(`prep.draft.${leagueId}`, JSON.stringify({ leagueId, mockId: 'fr061-verify-mock-2', picks, queue: [] }));
  },
  { leagueId, now },
);
await page.reload({ waitUntil: 'load', timeout: 60_000 });
await page.waitForSelector('text=/generated 20/', { timeout: 60_000 });
await page.getByText('Draft', { exact: true }).first().click();
await page.waitForSelector('text=/ON THE CLOCK/', { timeout: 60_000 });
await page.waitForSelector('text=STRATEGY', { timeout: 60_000 });

await page.getByRole('button', { name: /Zero RB/ }).first().click();
await page.waitForTimeout(300);

const panel = page.getByText('STRATEGY ADJUSTMENT', { exact: false }).first();
await panel.scrollIntoViewIfNeeded();
await page.waitForTimeout(200);
await page.screenshot({ path: join(artifacts, 'fr061-strategy-adjustment-panel-closeup.png'), fullPage: false });

const text = await panel.locator('xpath=../..').innerText().catch(() => '(not found)');
console.log('PANEL TEXT:', text);

await browser.close();
