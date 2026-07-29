import { chromium } from 'playwright';

const url = process.argv[2] || 'http://localhost:5199';
const outDir = new URL('./artifacts/', import.meta.url).pathname;

const browser = await chromium.launch({ executablePath: process.env.PLAYWRIGHT_CHROMIUM_PATH || '/opt/pw-browsers/chromium' });
const page = await browser.newPage({ viewport: { width: 1500, height: 950 } });

page.on('console', (msg) => {
  if (msg.type() === 'error') console.log('CONSOLE ERROR:', msg.text());
});

await page.goto(url, { waitUntil: 'networkidle' });

// --- Empty state screenshot first: switch to Draft mode, open Opponents tab, no picks yet.
await page.getByRole('button', { name: /draft/i }).first().click();
await page.waitForTimeout(500);
await page.getByRole('button', { name: 'Opponents' }).click();
await page.waitForTimeout(400);
await page.screenshot({ path: `${outDir}live-opponents-empty-2026-07-29.png`, fullPage: false });
console.log('captured empty state');

// --- Seed a real draft state in localStorage: 6 picks across 6 different teams,
// real board player ids/names/positions, team 7 left on the clock.
const draftState = {
  leagueId: 'primary',
  mockId: 'screenshot-demo',
  picks: [
    { overallPick: 1, round: 1, teamSlot: 1, playerId: 1, playerName: 'Bijan Robinson', timestamp: new Date().toISOString(), entryMode: 'typed' },
    { overallPick: 2, round: 1, teamSlot: 2, playerId: 2, playerName: "Ja'Marr Chase", timestamp: new Date().toISOString(), entryMode: 'typed' },
    { overallPick: 3, round: 1, teamSlot: 3, playerId: 6, playerName: 'Josh Allen', timestamp: new Date().toISOString(), entryMode: 'typed' },
    { overallPick: 4, round: 1, teamSlot: 4, playerId: 4, playerName: 'Puka Nacua', timestamp: new Date().toISOString(), entryMode: 'typed' },
    { overallPick: 5, round: 1, teamSlot: 5, playerId: 8, playerName: 'Jonathan Taylor', timestamp: new Date().toISOString(), entryMode: 'typed' },
    { overallPick: 6, round: 1, teamSlot: 6, playerId: 9, playerName: 'Amon-Ra St. Brown', timestamp: new Date().toISOString(), entryMode: 'typed' },
  ],
  queue: [],
};

await page.evaluate((state) => {
  localStorage.setItem('prep.draft.primary', JSON.stringify(state));
}, draftState);

await page.reload({ waitUntil: 'networkidle' });
await page.getByRole('button', { name: /draft/i }).first().click();
await page.waitForTimeout(500);
await page.getByRole('button', { name: 'Opponents' }).click();
await page.waitForTimeout(500);
await page.screenshot({ path: `${outDir}live-opponents-populated-2026-07-29.png`, fullPage: true });
console.log('captured populated state');

// --- Also capture the top bar / RefreshData control in this (dev) build for reference.
await page.getByRole('button', { name: 'Board' }).click();
await page.waitForTimeout(300);
await page.screenshot({ path: `${outDir}topbar-dev-2026-07-29.png`, clip: { x: 0, y: 0, width: 1500, height: 60 } });
console.log('captured dev topbar');

await browser.close();
