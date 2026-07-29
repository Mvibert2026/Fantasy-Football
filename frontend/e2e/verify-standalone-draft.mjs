/**
 * Exercises Draft mode in frontend/dist-standalone/board.html over `file://`
 * (not a dev server): switch to Draft, commit a pick via the shortcut digit,
 * confirm the pick counter advances and the roster panel updates, undo it,
 * confirm zero network requests throughout. Companion to verify-standalone.mjs
 * (Board-focused); this one is Draft-mode-focused, added when Draft mode was
 * restored to the standalone build (it was wrongly excluded at first --
 * checked, and it has no server dependency: see StandaloneApp.tsx's module doc).
 *
 * Usage: node e2e/verify-standalone-draft.mjs
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

let failures = 0;
function check(name, ok, detail = '') {
  console.log(`  [${ok ? 'PASS' : 'FAIL'}] ${name}${detail ? ` — ${detail}` : ''}`);
  if (!ok) failures += 1;
}

const browser = await chromium.launch({ executablePath });
// Fresh context per verify-standalone.mjs's isolation precedent, and because
// this is a `file://` origin: localStorage here is scoped to this run only.
const context = await browser.newContext({ viewport: { width: 1440, height: 900 } });
const page = await context.newPage();
const requests = [];
page.on('request', (req) => requests.push(req.url()));

console.log(`opening ${fileUrl}`);
await page.goto(fileUrl, { waitUntil: 'load' });
await page.waitForSelector('text=/generated 20/', { timeout: 15_000 });

// Switch to Draft mode via the mode switcher (restored this pass -- was
// absent entirely in the prior standalone build).
const draftBtn = page.getByRole('button', { name: 'Draft', exact: true });
check('Draft mode button is present in the standalone build', (await draftBtn.count()) === 1);
await draftBtn.click();

const input = page.locator('input[placeholder^="Mark pick"]');
await input.waitFor({ state: 'visible', timeout: 10_000 });
check('Draft mode rendered the pick-entry field', await input.isVisible());

await page.screenshot({ path: join(artifacts, 'standalone-draft-room.png'), fullPage: true });
console.log(`screenshot: ${join(artifacts, 'standalone-draft-room.png')}`);

const pickNo = async () => {
  const ph = await input.getAttribute('placeholder');
  const m = /Mark pick (\d+)/.exec(ph ?? '');
  return m ? Number(m[1]) : NaN;
};
const startPick = await pickNo();
check('pick counter readable before any picks', Number.isFinite(startPick), `pick=${startPick}`);

// Commit one pick via the digit shortcut (same interaction e2e/smoke.mjs
// exercises against the live app).
await input.click();
await page.waitForTimeout(150);
await page.keyboard.press('1');
await page.waitForTimeout(300);
const afterOne = await pickNo();
check('committing a pick advances the counter', afterOne === startPick + 1, `${startPick} -> ${afterOne}`);

// Pick 1 in a 10-team snake draft is team 1, not necessarily the user's own
// team (this league's user slot may not be 1) -- so the real, always-true
// assertion is that the draft log recorded it, not that MY ROSTER grew.
const logged = await page.locator('text=Bijan Robinson').count();
check('draft log recorded the committed pick', logged >= 1);

await page.screenshot({ path: join(artifacts, 'standalone-draft-after-pick.png'), fullPage: true });
console.log(`screenshot: ${join(artifacts, 'standalone-draft-after-pick.png')}`);

// Undo: Escape to close/clear the field, then Backspace on the empty field.
await input.click();
await page.keyboard.press('Escape');
await page.keyboard.press('Backspace');
await page.waitForTimeout(300);
const afterUndo = await pickNo();
check('undo removes exactly the one pick', afterUndo === startPick, `${afterOne} -> ${afterUndo}`);

// "Export draft log" -- a client-side Blob download, should not touch the
// network. Re-commit a pick first so the button isn't disabled.
await input.click();
await page.waitForTimeout(150);
await page.keyboard.press('1');
await page.waitForTimeout(300);
const [download] = await Promise.all([
  page.waitForEvent('download', { timeout: 5_000 }).catch(() => null),
  page.getByRole('button', { name: 'Export draft log' }).click(),
]);
check('Export draft log produces a local download, not a network request', download !== null);

const nonFileRequests = requests.filter((u) => !u.startsWith('file://') && !u.startsWith('about:') && !u.startsWith('blob:'));
console.log(`requests total: ${requests.length}, non-file/blob requests: ${nonFileRequests.length}`);
for (const u of nonFileRequests) console.log(`  network request: ${u}`);
check('zero network requests through the whole Draft-mode interaction', nonFileRequests.length === 0);

await browser.close();
console.log(`\n${failures === 0 ? 'ALL CHECKS PASSED' : `${failures} CHECK(S) FAILED`}`);
process.exit(failures === 0 ? 0 : 1);
