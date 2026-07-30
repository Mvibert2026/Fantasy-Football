/**
 * Screenshots for docs/design/LIGHT-THEME-SHADING.md (2026-07-31, item 5 of 8).
 * Light mode on three screens (Board, a player card, Availability) plus one
 * dark-mode Board shot to evidence dark is unchanged.
 *
 * Usage: node e2e/shot-light-theme-shading.mjs [--url http://localhost:5199]
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
const page = await browser.newPage({ viewport: { width: 1440, height: 900 } });

// --- Light mode: Board ---
await page.addInitScript(() => {
  try {
    localStorage.setItem('prep.theme', 'light');
  } catch {
    /* ignore */
  }
});
await page.goto(url, { waitUntil: 'load', timeout: 40000 });
await page.waitForSelector('text=/generated 20/', { timeout: 40_000 });
await page.screenshot({ path: join(artifacts, 'light-shading-01-board.png'), fullPage: true });
console.log('wrote light-shading-01-board.png');

// --- Light mode: player card (click first data row) ---
// Board rows sit directly below the sticky column header; clicking a fixed
// point inside the first row opens PlayerDetail as a sheet with a known
// data-testid on its backdrop.
await page.mouse.click(360, 275);
await page.waitForSelector('[data-testid="player-detail-backdrop"]', { timeout: 10_000 });
await page.waitForTimeout(300);
await page.screenshot({ path: join(artifacts, 'light-shading-02-player-card.png'), fullPage: true });
console.log('wrote light-shading-02-player-card.png');
// Dismiss it before navigating away.
await page.getByTestId('player-detail-backdrop').click();
await page.waitForTimeout(200);

// --- Light mode: Availability screen ---
await page.getByText('Availability', { exact: true }).click();
await page.waitForTimeout(600);
await page.screenshot({ path: join(artifacts, 'light-shading-03-availability.png'), fullPage: true });
console.log('wrote light-shading-03-availability.png');

// --- Dark mode: Board (evidence dark is unchanged) ---
// A fresh page, not a reload of the light one: page.addInitScript persists
// across every navigation on the same page object, so the light-theme init
// script above would silently re-fire and clobber a same-page dark write.
// A brand-new page has no init scripts and no localStorage yet, so useTheme's
// default ('dark', no data-theme attribute) applies untouched.
const darkPage = await browser.newPage({ viewport: { width: 1440, height: 900 } });
await darkPage.goto(url, { waitUntil: 'load', timeout: 40000 });
await darkPage.waitForSelector('text=/generated 20/', { timeout: 40_000 });
const themeAttr = await darkPage.evaluate(() => document.documentElement.getAttribute('data-theme'));
console.log(`dark page data-theme attribute: ${themeAttr === null ? '(none -- dark, as expected)' : themeAttr}`);
await darkPage.screenshot({ path: join(artifacts, 'light-shading-04-board-dark.png'), fullPage: true });
console.log('wrote light-shading-04-board-dark.png');

await browser.close();
