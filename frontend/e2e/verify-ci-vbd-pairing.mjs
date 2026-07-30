/**
 * CI/VBD pairing bug fix verification -- the founder's own catch, 2026-07-30:
 * "what is in the parenthesis here -- it's a range, but the projection isn't
 * in it?" Screenshots the three fixed surfaces (Prep board, Draft board
 * RECOMMENDED card, player card) plus the CI header hover, so the corrected
 * labelling can be looked at directly, not just asserted by tests.
 *
 * Usage: node e2e/verify-ci-vbd-pairing.mjs [--url http://localhost:5199]
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

async function newPage() {
  const page = await browser.newPage({ viewport: { width: 1500, height: 950 } });
  page.on('console', (msg) => {
    if (msg.type() === 'error') console.log(`  console error: ${msg.text()}`);
  });
  return page;
}

async function shot(page, name) {
  const outPath = join(artifacts, name);
  await page.screenshot({ path: outPath, fullPage: false });
  console.log(`wrote ${outPath}`);
}

// ---- 1. Prep board: PROJ column has no "(CI)", VBD column does ----
{
  const page = await newPage();
  await page.goto(url, { waitUntil: 'domcontentloaded' });
  await page.waitForSelector('text=/generated 20/', { timeout: 30_000 });
  const body = await page.textContent('body');
  console.log(`[prep board] contains literal "PROJ (CI)": ${body.includes('PROJ (CI)')}`);
  console.log(`[prep board] contains "VBD" header: ${body.includes('VBD')}`);
  await shot(page, 'ci-fix-01-prep-board.png');

  // Hover the "(CI)" suffix next to VBD to capture the glossary tooltip.
  const ciSuffix = page.getByText('(CI)').first();
  if (await ciSuffix.count()) {
    const title = await ciSuffix.getAttribute('title');
    console.log(`[prep board] "(CI)" header hover title: ${title}`);
  }
  await page.close();
}

// ---- 2. Draft board: RECOMMENDED card, range beside VBD not "projected pts" ----
{
  const page = await newPage();
  await page.goto(url, { waitUntil: 'domcontentloaded' });
  await page.waitForSelector('text=/generated 20/', { timeout: 30_000 });
  await page.getByRole('button', { name: 'Draft', exact: true }).click();
  await page.waitForSelector('text=DRAFT LIVE', { timeout: 30_000 });
  // Auto-fill opponent picks so the user reaches their own turn, which is
  // when the RECOMMENDED card (not the strategy-selector placeholder) shows.
  const autofill = page.getByRole('button', { name: 'Auto-fill to my pick' });
  if (await autofill.count()) await autofill.click().catch(() => {});
  await page.waitForSelector('text=RECOMMENDED', { timeout: 15_000 }).catch(() => {});
  await page.waitForTimeout(300);
  const body = await page.textContent('body');
  console.log(`[draft board] contains "honest range": ${body.includes('honest range')}`);
  console.log(`[draft board] contains "Honest points range": ${body.includes('Honest points range')}`);
  await shot(page, 'ci-fix-02-draft-board.png');
  await page.close();
}

// ---- 3. Player card: PROJECTION section, range bar captioned "VBD range" ----
{
  const page = await newPage();
  await page.goto(url, { waitUntil: 'domcontentloaded' });
  await page.waitForSelector('text=/generated 20/', { timeout: 30_000 });
  const firstRow = page.locator('div[style*="grid-template-columns"]').filter({ hasText: /^\d/ }).first();
  await firstRow.click({ timeout: 15_000 }).catch(async () => {
    await page.locator('text=RB1').first().click({ timeout: 15_000 });
  });
  await page.waitForSelector('text=PROJECTION', { timeout: 15_000 });
  const body = await page.textContent('body');
  console.log(`[player card] contains "VBD range": ${body.includes('VBD range')}`);
  await shot(page, 'ci-fix-03-player-card.png');
  await page.close();
}

await browser.close();
console.log('done');
