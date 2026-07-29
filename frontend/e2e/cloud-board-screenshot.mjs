/**
 * Cloud-container board screenshot (docs/frontend-cloud-runbook.md).
 *
 * The pinned @playwright/test in package.json expects Chromium revision 1234;
 * the cloud container ships revision 1194 pre-installed at
 * $PLAYWRIGHT_BROWSERS_PATH/chromium and downloads are disabled
 * (PLAYWRIGHT_SKIP_BROWSER_DOWNLOAD=1). `chromium.launch()` with no options
 * fails looking for the 1234 headless-shell binary, so this script launches
 * against the pre-installed binary explicitly via `executablePath` instead of
 * running `playwright install`.
 *
 * Captures a full-page screenshot of the board (the landing view) against an
 * already-running dev server. Does not start or stop the server itself.
 *
 * Usage: node e2e/cloud-board-screenshot.mjs [--url http://localhost:5199] [--out board-cloud.png]
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
const outName = args.includes('--out') ? args[args.indexOf('--out') + 1] : 'board-cloud.png';

const browsersPath = process.env.PLAYWRIGHT_BROWSERS_PATH || '/opt/pw-browsers';
const executablePath = join(browsersPath, 'chromium');

const browser = await chromium.launch({ executablePath });
const page = await browser.newPage({ viewport: { width: 1440, height: 900 } });
const consoleErrors = [];
page.on('console', (msg) => {
  if (msg.type() === 'error') consoleErrors.push(msg.text());
});

await page.goto(url, { waitUntil: 'networkidle' });
await page.waitForSelector('text=/generated 20/', { timeout: 30_000 });

const provenance = await page.locator('text=/generated 20/').first().innerText();
const bodyText = await page.textContent('body');
console.log(`provenance line: ${provenance}`);
console.log(`body text length: ${(bodyText ?? '').length}`);
console.log(`console errors: ${consoleErrors.length}`);
for (const e of consoleErrors) console.log(`  console error: ${e}`);

const outPath = join(artifacts, outName);
await page.screenshot({ path: outPath, fullPage: true });
console.log(`screenshot written to ${outPath}`);

await browser.close();
