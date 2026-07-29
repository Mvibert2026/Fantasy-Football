/**
 * Verification for the ADP glossary/methodology gap (PM finding, 2026-07-29):
 * confirms the "ADP" term now renders in Glossary and the new ADP section
 * renders in Methodology, with the display-only / does-not-feed-the-model
 * language visible.
 *
 * Usage: node e2e/verify-adp-glossary-methodology.mjs --url http://localhost:5211
 */
import { mkdirSync } from 'node:fs';
import { join, dirname } from 'node:path';
import { fileURLToPath } from 'node:url';
import { chromium } from 'playwright';

const root = join(dirname(fileURLToPath(import.meta.url)), '..');
const artifacts = join(root, 'e2e', 'artifacts');
mkdirSync(artifacts, { recursive: true });

const args = process.argv.slice(2);
const url = args.includes('--url') ? args[args.indexOf('--url') + 1] : 'http://localhost:5211';
const browsersPath = process.env.PLAYWRIGHT_BROWSERS_PATH || '/opt/pw-browsers';
const executablePath = join(browsersPath, 'chromium');

const browser = await chromium.launch({ executablePath });
const page = await browser.newPage({ viewport: { width: 1600, height: 1200 } });
const consoleErrors = [];
page.on('console', (msg) => { if (msg.type() === 'error') consoleErrors.push(msg.text()); });
page.on('pageerror', (err) => consoleErrors.push('pageerror: ' + err.message));

async function shot(name) {
  const p = join(artifacts, name);
  await page.screenshot({ path: p, fullPage: true });
  console.log(`shot: ${p}`);
}

await page.goto(url, { waitUntil: 'networkidle' });
await page.waitForSelector('text=/generated 20/', { timeout: 30_000 });

// ---- Glossary tab ----
await page.locator('[role="button"]', { hasText: 'Glossary' }).first().click({ timeout: 10_000 });
await page.waitForTimeout(500);
console.log('== GLOSSARY ==');
console.log('has ADP term button:', await page.getByRole('button', { name: 'ADP', exact: true }).count());
await page.getByRole('button', { name: 'ADP', exact: true }).first().click({ timeout: 10_000 }).catch(() => {});
await page.waitForTimeout(300);
console.log('has mfl_proxy mention after expand:', await page.locator('text=/MyFantasyLeague/').count());
await shot('adp-glossary-2026-07-29.png');

// ---- Methodology tab ----
await page.locator('[role="button"]', { hasText: 'Methodology' }).first().click({ timeout: 10_000 });
await page.waitForTimeout(500);
console.log('== METHODOLOGY ==');
console.log('has ADP section heading:', await page.locator('h3', { hasText: 'ADP' }).count());
console.log('has "does not feed" language:', await page.locator('text=/does not feed/').count());
console.log('has adp_source_note text (MyFantasyLeague):', await page.locator('text=/MyFantasyLeague/').count());
await shot('adp-methodology-2026-07-29.png');

console.log('console errors:', consoleErrors);
await browser.close();
