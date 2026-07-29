/**
 * Opens frontend/dist-standalone/board.html directly via `file://` (NOT through
 * a dev server -- that would defeat the entire point of a standalone build) and
 * screenshots it. Reuses the cloud executablePath workaround documented in
 * docs/frontend-cloud-runbook.md / e2e/cloud-board-screenshot.mjs.
 *
 * Usage: node e2e/verify-standalone.mjs
 */

import { mkdirSync, existsSync } from 'node:fs';
import { join, dirname } from 'node:path';
import { fileURLToPath, pathToFileURL } from 'node:url';
import { chromium } from 'playwright';

const root = join(dirname(fileURLToPath(import.meta.url)), '..');
const artifacts = join(root, 'e2e', 'artifacts');
mkdirSync(artifacts, { recursive: true });

const htmlPath = join(root, 'dist-standalone', 'board.html');
if (!existsSync(htmlPath)) {
  console.error(`FAIL: ${htmlPath} does not exist -- run \`npm run build:standalone\` first.`);
  process.exit(1);
}
const fileUrl = pathToFileURL(htmlPath).href;

const browsersPath = process.env.PLAYWRIGHT_BROWSERS_PATH || '/opt/pw-browsers';
const executablePath = join(browsersPath, 'chromium');

const browser = await chromium.launch({ executablePath });
const page = await browser.newPage({ viewport: { width: 1440, height: 900 } });
const consoleErrors = [];
const requests = [];
page.on('console', (msg) => {
  if (msg.type() === 'error') consoleErrors.push(msg.text());
});
// Any request at all past the initial file:// document load would mean this
// "self-contained" file is not actually self-contained.
page.on('request', (req) => requests.push(req.url()));

console.log(`opening ${fileUrl}`);
await page.goto(fileUrl, { waitUntil: 'load' });
await page.waitForSelector('text=/generated 20/', { timeout: 15_000 });

const provenance = await page.locator('text=/generated 20/').first().innerText();
const bodyText = await page.textContent('body');
const rowCount = await page.locator('[style*="grid-template-columns"] >> text=/^\\d+$/').count();

console.log(`provenance line: ${provenance}`);
console.log(`body text length: ${(bodyText ?? '').length}`);
console.log(`console errors: ${consoleErrors.length}`);
for (const e of consoleErrors) console.log(`  console error: ${e}`);

const nonFileRequests = requests.filter((u) => !u.startsWith('file://') && !u.startsWith('about:'));
console.log(`requests total: ${requests.length}, non-file:// requests: ${nonFileRequests.length}`);
for (const u of nonFileRequests) console.log(`  network request: ${u}`);

let failures = 0;
function check(name, ok) {
  console.log(`  [${ok ? 'PASS' : 'FAIL'}] ${name}`);
  if (!ok) failures += 1;
}
check('no network requests beyond the file:// document itself', nonFileRequests.length === 0);
check('body rendered substantial content', (bodyText ?? '').length > 500);
check('provenance line carries a real player count', /\d+ players loaded/.test(provenance));

await page.screenshot({ path: join(artifacts, 'standalone-board.png'), fullPage: true });
console.log(`screenshot: ${join(artifacts, 'standalone-board.png')}`);

// Click a player row open to prove PlayerDetail (and its honest "not included"
// history-section state) actually renders, not just the table.
await page.locator('text=Bijan Robinson').first().click();
await page.waitForSelector('text=PROJECTION', { timeout: 10_000 });
await page.screenshot({ path: join(artifacts, 'standalone-player-detail.png'), fullPage: true });
console.log(`screenshot: ${join(artifacts, 'standalone-player-detail.png')}`);

await browser.close();
console.log(`\n${failures === 0 ? 'ALL CHECKS PASSED' : `${failures} CHECK(S) FAILED`}`);
process.exit(failures === 0 ? 0 : 1);
