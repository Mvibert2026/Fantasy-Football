/**
 * Founder-loop acceptance smoke (Extended mandate Priority 4; thread 063).
 *
 * WHAT THIS IS. The scripted version of the founder's own regression loop:
 * load the app, look at the board, enter picks, confirm the suggester only
 * ever opens on explicit intent, undo, reload, screenshot. It exists because
 * the founder has been the project's only regression sensor for UI behaviour
 * (thread 063 is the second regression of the same rule), and because a green
 * unit suite has already coexisted with a missing screen.
 *
 * WHAT IT ASSERTS. Every row of thread 063's trigger table that a headless
 * session can exercise, plus app-loads, board-renders, picks-persist.
 *
 * HOW FAILURES REPORT. Non-zero exit code; e2e/artifacts/report.json with one
 * entry per assertion (pass/fail + detail); screenshots of the board and the
 * draft room regardless of outcome. A red run blocks round closeout — see the
 * review doc's wiring section.
 *
 * ISOLATION. Runs in a fresh browser context: localStorage starts empty, so
 * it can NEVER touch the founder's real draft state (pre-mortem failure #6),
 * and its own picks vanish with the context.
 *
 * Usage:
 *   node e2e/smoke.mjs                  # starts its own dev server
 *   node e2e/smoke.mjs --url http://localhost:5173 --no-server
 */

import { spawn } from 'node:child_process';
import { mkdirSync, writeFileSync } from 'node:fs';
import { join, dirname } from 'node:path';
import { fileURLToPath } from 'node:url';

const root = join(dirname(fileURLToPath(import.meta.url)), '..');
const artifacts = join(root, 'e2e', 'artifacts');
mkdirSync(artifacts, { recursive: true });

const args = process.argv.slice(2);
const urlArg = args.includes('--url') ? args[args.indexOf('--url') + 1] : 'http://localhost:5173';
const noServer = args.includes('--no-server');

const report = [];
let failures = 0;
function check(name, ok, detail = '') {
  report.push({ name, ok: !!ok, detail: String(detail) });
  // eslint-disable-next-line no-console
  console.log(`  [${ok ? 'PASS' : 'FAIL'}] ${name}${detail ? ` — ${detail}` : ''}`);
  if (!ok) failures += 1;
}

async function waitForServer(url, timeoutMs = 90_000) {
  const start = Date.now();
  while (Date.now() - start < timeoutMs) {
    try {
      const res = await fetch(url);
      if (res.ok) return true;
    } catch {
      /* not up yet */
    }
    await new Promise((r) => setTimeout(r, 750));
  }
  return false;
}

async function main() {
  let server = null;
  if (!noServer) {
    // predev runs sync-exports, so the data the app sees is current.
    server = spawn(process.platform === 'win32' ? 'npm.cmd' : 'npm', ['run', 'dev'], {
      cwd: root,
      stdio: 'ignore',
      shell: process.platform === 'win32',
    });
  }
  try {
    const up = await waitForServer(urlArg);
    check('dev server reachable', up, urlArg);
    if (!up) return finish(server);

    const { chromium } = await import('playwright');
    const browser = await chromium.launch();
    const context = await browser.newContext({ viewport: { width: 1440, height: 900 } });
    const page = await context.newPage();
    const consoleErrors = [];
    page.on('console', (msg) => {
      if (msg.type() === 'error') consoleErrors.push(msg.text());
    });

    await page.goto(urlArg, { waitUntil: 'networkidle' });

    // ---- S1: app loads, board renders -------------------------------------
    const bodyText = await page.textContent('body');
    check('app rendered content', (bodyText ?? '').length > 200);
    check('no load-failure banner', !/failed to load|could not load/i.test(bodyText ?? ''));
    await page.screenshot({ path: join(artifacts, 'board.png'), fullPage: false });

    // ---- S2: enter Draft mode --------------------------------------------
    await page.getByText('Draft', { exact: true }).first().click();
    const input = page.locator('input[placeholder^="Mark pick"]');
    await input.waitFor({ state: 'visible', timeout: 10_000 });
    const suggester = page.locator('[data-testid="suggester-dropdown"]');

    // Trigger table: mount/page load does NOT open the panel.
    check('suggester closed on Draft-tab mount', (await suggester.count()) === 0);

    const pickNo = async () => {
      const ph = await input.getAttribute('placeholder');
      const m = /Mark pick (\d+)/.exec(ph ?? '');
      return m ? Number(m[1]) : NaN;
    };
    const startPick = await pickNo();
    check('pick counter readable', Number.isFinite(startPick), `pick=${startPick}`);

    // Trigger table: click into the field DOES open.
    await input.click();
    await page.waitForTimeout(150);
    check('suggester opens on click into field', (await suggester.count()) === 1);

    // Closes on Escape.
    await page.keyboard.press('Escape');
    await page.waitForTimeout(100);
    check('suggester closes on Escape', (await suggester.count()) === 0);

    // Trigger table: typing DOES open.
    await input.pressSequentially('a', { delay: 30 });
    await page.waitForTimeout(150);
    check('suggester opens on typing', (await suggester.count()) === 1);
    // Clear the query, close.
    await input.fill('');
    await page.keyboard.press('Escape');
    await page.waitForTimeout(100);

    // ---- S3: commit five picks via the digit shortcut ---------------------
    // The 063 regression: the panel must NOT reopen after each commit.
    let reopenAfterCommit = 0;
    for (let i = 0; i < 5; i += 1) {
      await input.click(); // explicit intent: panel may open
      await page.waitForTimeout(120);
      await page.keyboard.press('1'); // commit top candidate
      await page.waitForTimeout(250);
      if ((await suggester.count()) !== 0) reopenAfterCommit += 1;
    }
    const afterFive = await pickNo();
    check('five picks committed', afterFive === startPick + 5, `pick ${startPick} -> ${afterFive}`);
    check('suggester NEVER reopens after a commit (063)', reopenAfterCommit === 0,
      `${reopenAfterCommit}/5 commits reopened it`);

    // ---- S4: undo (Backspace on empty field) ------------------------------
    await input.click();
    await page.keyboard.press('Escape'); // field focused, panel shut, query empty
    await page.keyboard.press('Backspace');
    await page.waitForTimeout(250);
    const afterUndo = await pickNo();
    check('undo removes exactly one pick', afterUndo === afterFive - 1,
      `pick ${afterFive} -> ${afterUndo}`);
    check('suggester closed after undo (063)', (await suggester.count()) === 0);

    // ---- S5: leave the tab and come back ----------------------------------
    await page.getByText('Prep', { exact: true }).first().click();
    await page.waitForTimeout(200);
    await page.getByText('Draft', { exact: true }).first().click();
    await input.waitFor({ state: 'visible', timeout: 10_000 });
    check('suggester closed on return to Draft tab (063)', (await suggester.count()) === 0);

    // ---- S6: reload restores state, panel stays shut ----------------------
    await page.reload({ waitUntil: 'networkidle' });
    await page.getByText('Draft', { exact: true }).first().click();
    await input.waitFor({ state: 'visible', timeout: 10_000 });
    const afterReload = await pickNo();
    check('picks persist across reload', afterReload === afterUndo,
      `pick ${afterUndo} vs ${afterReload} after reload`);
    check('suggester closed after reload (063)', (await suggester.count()) === 0);

    await page.screenshot({ path: join(artifacts, 'draftroom.png'), fullPage: false });

    // ---- S7: console hygiene ----------------------------------------------
    check('no console errors during the loop', consoleErrors.length === 0,
      consoleErrors.slice(0, 3).join(' | '));

    await browser.close();
  } catch (err) {
    check('smoke run completed without harness error', false, err?.message ?? String(err));
  }
  return finish(server);
}

function finish(server) {
  if (server) server.kill();
  writeFileSync(
    join(artifacts, 'report.json'),
    JSON.stringify({ when: new Date().toISOString(), failures, report }, null, 1),
  );
  // eslint-disable-next-line no-console
  console.log(`\nSmoke: ${report.length - failures}/${report.length} passed. `
    + `Artifacts: e2e/artifacts/ (report.json, board.png, draftroom.png)`);
  process.exit(failures === 0 ? 0 : 1);
}

main();
