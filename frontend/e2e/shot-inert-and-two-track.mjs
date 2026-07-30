/**
 * Screenshot recipe for design/INERT-CONTROLS.md and design/TWO-TRACK-EXPRESSION.md
 * (2026-07-29). Pattern per docs/frontend-cloud-runbook.md: explicit executablePath
 * against the pre-installed Chromium, no `playwright install`.
 *
 * Usage: node e2e/shot-inert-and-two-track.mjs [--url http://localhost:5199]
 */
import { chromium } from 'playwright';
import { join } from 'node:path';
import { mkdirSync } from 'node:fs';

const root = join(new URL('.', import.meta.url).pathname, '..');
const artifacts = join(root, 'e2e', 'artifacts');
mkdirSync(artifacts, { recursive: true });

const args = process.argv.slice(2);
const url = args.includes('--url') ? args[args.indexOf('--url') + 1] : 'http://localhost:5199';

const browsersPath = process.env.PLAYWRIGHT_BROWSERS_PATH || '/opt/pw-browsers';
const executablePath = join(browsersPath, 'chromium');

const browser = await chromium.launch({ executablePath });
const page = await browser.newPage({ viewport: { width: 1600, height: 1000 } });

await page.goto(url, { waitUntil: 'networkidle' });
await page.waitForSelector('text=/generated 20/', { timeout: 30_000 });

// 1. Board -- Export CSV/PDF gone, "export not built" in the provenance line.
await page.screenshot({ path: join(artifacts, 'inert-01-board-westwood.png') });
console.log('captured inert-01-board-westwood.png');

// 2. Player detail sheet -- Compare/Ask gone. Screenshot the sheet element itself
// (not the full viewport) so the sticky action row at its bottom is guaranteed
// to be in frame regardless of viewport height.
await page.getByText('Bijan Robinson', { exact: false }).first().click({ timeout: 15000 });
await page.waitForTimeout(400);
const sheet = page.locator('text=WHY OUR RANK DIFFERS FROM THE MARKET').locator('xpath=ancestor::div[contains(@style,"position: fixed")]').first();
await sheet.screenshot({ path: join(artifacts, 'inert-02-player-detail-action-row.png') }).catch(async () => {
  await page.screenshot({ path: join(artifacts, 'inert-02-player-detail-action-row.png') });
});
console.log('captured inert-02-player-detail-action-row.png');
await page.keyboard.press('Escape').catch(() => {});

// 3. Glossary -- no per-term Ask the assistant button.
await page.getByRole('button', { name: 'Glossary', exact: true }).click();
await page.waitForTimeout(400);
await page.screenshot({ path: join(artifacts, 'inert-03-glossary.png') });
console.log('captured inert-03-glossary.png');

// 4. Top bar close-up -- League settings replaced by a plain statement, track badge visible.
const topbar = page.locator('div', { hasText: 'DRAFT ASSISTANT' }).first();
await page.screenshot({ path: join(artifacts, 'inert-04-topbar-westwood-primary-track.png'), clip: { x: 0, y: 0, width: 1600, height: 50 } });
console.log('captured inert-04-topbar-westwood-primary-track.png');

// Back to Board before switching leagues, so the provenance-line wait below
// is checking the screen it actually describes.
await page.getByRole('button', { name: 'Board', exact: true }).click();
await page.waitForSelector('text=/generated 20/', { timeout: 30_000 });

// 5. League switch -- generic track treatment.
const select = page.locator('select[aria-label="Select league"]');
await select.selectOption({ label: /ESPN-default, 10 teams, half scoring/ }).catch(async () => {
  // Label text may include the track marker prefix; fall back to matching by value substring.
  const options = await select.locator('option').allTextContents();
  const match = options.find((o) => o.includes('half scoring'));
  if (match) await select.selectOption({ label: match });
});
await page.waitForTimeout(800);
await page.screenshot({ path: join(artifacts, 'inert-05-league-switch-generic-track-topbar.png'), clip: { x: 0, y: 0, width: 1600, height: 50 } });
console.log('captured inert-05-league-switch-generic-track-topbar.png');

await page.waitForSelector('text=/generated 20/', { timeout: 30_000 });
await page.screenshot({ path: join(artifacts, 'inert-06-league-switch-generic-board.png') });
console.log('captured inert-06-league-switch-generic-board.png');

// 6. Strategy guide on the generic-track league -- the split empty state.
await page.getByRole('button', { name: 'Strategy Guide', exact: true }).click();
await page.waitForTimeout(400);
await page.screenshot({ path: join(artifacts, 'inert-07-strategy-guide-generic-track.png') });
console.log('captured inert-07-strategy-guide-generic-track.png');

await browser.close();
