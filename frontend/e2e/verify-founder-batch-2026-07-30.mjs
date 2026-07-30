import { chromium } from 'playwright';

const url = process.argv[2] || 'http://localhost:5199';
const outDir = new URL('./artifacts/', import.meta.url).pathname;

const browser = await chromium.launch({ executablePath: process.env.PLAYWRIGHT_CHROMIUM_PATH || '/opt/pw-browsers/chromium' });
const page = await browser.newPage({ viewport: { width: 1500, height: 900 } });

page.on('console', (msg) => {
  if (msg.type() === 'error' && !/ERR_CONNECTION_RESET|404/.test(msg.text())) console.log('CONSOLE ERROR:', msg.text());
});

await page.goto(url, { waitUntil: 'networkidle' });

// ---------------------------------------------------------------------------
// FR-082: Prep-mode Opponents scroll.
await page.getByRole('button', { name: 'Opponents', exact: true }).click();
await page.waitForTimeout(400);
await page.screenshot({ path: `${outDir}fr082-prep-opponents-top.png` });
await page.mouse.move(750, 500);
await page.mouse.wheel(0, 3000);
await page.waitForTimeout(200);
await page.screenshot({ path: `${outDir}fr082-prep-opponents-scrolled.png` });
console.log('captured prep opponents scroll');

// ---------------------------------------------------------------------------
// FR-083 / FR-079: player card ADP + history disclosure, from Prep's Board
// (the "player notes card" the founder means). Open the first player row.
await page.getByRole('button', { name: 'Board', exact: true }).click();
await page.waitForTimeout(400);
await page.locator('tbody tr, [role="row"]').first().click().catch(() => {});
// Board.tsx rows may not be <tr> -- fall back to clicking the first player
// name cell if the generic row click above found nothing clickable.
await page.waitForTimeout(300);
const sheetVisible = await page.getByText('PROJECTION', { exact: true }).isVisible().catch(() => false);
if (!sheetVisible) {
  await page.getByText('Bijan Robinson', { exact: false }).first().click();
  await page.waitForTimeout(400);
}
await page.screenshot({ path: `${outDir}fr083-fr079-player-card-westwood-top.png` });
// The side sheet scrolls internally (position: fixed, its own overflow-y:
// auto) -- a page-level screenshot can't reach MARKET ADP / WEEKLY FINISHES /
// THREE SEASONS below the fold without scrolling that specific region.
await page.mouse.move(1280, 500);
await page.mouse.wheel(0, 900);
await page.waitForTimeout(300);
await page.screenshot({ path: `${outDir}fr083-player-card-westwood-adp-block.png` });
await page.mouse.wheel(0, 1400);
await page.waitForTimeout(300);
await page.screenshot({ path: `${outDir}fr079-player-card-westwood-history.png` });
console.log('captured player card (Westwood/primary league) ADP + history disclosure');
await page.keyboard.press('Escape');
await page.waitForTimeout(200);

// Same card under a non-primary (STANDARD-scoring) league, to show the
// scoring_ruleset_note disclosure actually differs from Westwood's -- and
// from board.json's own (backend-side, wrong-for-this-league) adp_source_note.
const leagueSwitcher = page.locator('select, [role="combobox"]').first();
if (await leagueSwitcher.count()) {
  const options = await leagueSwitcher.locator('option').allTextContents().catch(() => []);
  const standardOpt = options.find((o) => /standard/i.test(o));
  if (standardOpt) {
    await leagueSwitcher.selectOption({ label: standardOpt });
    await page.waitForTimeout(600);
    console.log('selected league option:', standardOpt);
    await page.getByText('Bijan Robinson', { exact: false }).first().click().catch(() => {});
    await page.waitForTimeout(400);
    await page.mouse.move(1280, 500);
    await page.mouse.wheel(0, 1150);
    await page.waitForTimeout(300);
    await page.screenshot({ path: `${outDir}fr083-player-card-standard-league-adp-block.png` });
    console.log('captured player card (STANDARD-scoring league) ADP disclosure');
    await page.keyboard.press('Escape');
  }
}

// ---------------------------------------------------------------------------
// Switch to Draft mode, seed a real in-progress draft so LiveOpponents and
// the board list both have real content (many rows -> board scroll triggers;
// several teams -> LiveOpponents cards need scroll too).
await page.getByRole('button', { name: 'Draft', exact: true }).click();
await page.waitForTimeout(400);

const now = new Date().toISOString();
const picks = [];
for (let i = 1; i <= 23; i++) {
  picks.push({
    overallPick: i,
    round: Math.ceil(i / 10),
    teamSlot: ((i - 1) % 10) + 1,
    playerId: i,
    playerName: `Placeholder Player ${i}`,
    timestamp: now,
    entryMode: 'typed',
  });
}
// DraftRoom.tsx keys its localStorage draft state on
// data.manifest.artifacts.board.league_id, which is "primary" for this
// league's export -- not the URL-path selector "default" (ui/data/league-
// registry.ts's DEFAULT_LEAGUE_ID is a different concept). Confirmed against
// the real export before using it here.
await page.evaluate((state) => {
  localStorage.setItem('prep.draft.primary', JSON.stringify(state));
}, { leagueId: 'primary', mockId: 'founder-batch-shot', picks, queue: [] });
await page.reload({ waitUntil: 'networkidle' });
await page.getByRole('button', { name: 'Draft', exact: true }).click();
await page.waitForTimeout(500);

// FR-082: Draft-mode LiveOpponents scroll.
await page.getByRole('button', { name: 'Opponents', exact: true }).click();
await page.waitForTimeout(400);
await page.screenshot({ path: `${outDir}fr082-draft-opponents-top.png` });
await page.mouse.move(750, 500);
await page.mouse.wheel(0, 3000);
await page.waitForTimeout(200);
await page.screenshot({ path: `${outDir}fr082-draft-opponents-scrolled.png` });
console.log('captured draft (live) opponents scroll');

// ---------------------------------------------------------------------------
// FR-067 / FR-087: back to the Board hub tab -- header/row alignment + round
// labels, at two different viewport widths (durability check, not a one-width
// nudge).
await page.getByRole('button', { name: 'Board', exact: true }).click();
await page.waitForTimeout(400);
await page.screenshot({ path: `${outDir}fr067-fr087-draft-board-1500w.png` });

await page.setViewportSize({ width: 1180, height: 900 });
await page.waitForTimeout(300);
await page.screenshot({ path: `${outDir}fr067-fr087-draft-board-1180w.png` });

// Scroll the row list to trigger its scrollbar, then re-check alignment --
// this is exactly the state the old code misaligned in (gutter eats width
// from rows, not from the header).
await page.mouse.move(400, 500);
await page.mouse.wheel(0, 2000);
await page.waitForTimeout(200);
await page.screenshot({ path: `${outDir}fr067-draft-board-scrolled-1180w.png` });
await page.setViewportSize({ width: 1500, height: 900 });
console.log('captured board header/row alignment at two widths');

// ---------------------------------------------------------------------------
// FR-087: ON THE CLOCK / YOUR NEXT badges with round labels -- crop the top
// strip where they live.
await page.waitForTimeout(200);
await page.screenshot({ path: `${outDir}fr087-clock-badges.png`, clip: { x: 850, y: 60, width: 650, height: 90 } });
console.log('captured round-label badges');

await browser.close();
console.log('done');
