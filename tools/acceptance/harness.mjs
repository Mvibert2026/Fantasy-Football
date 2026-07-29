#!/usr/bin/env node
/**
 * Standalone content-assertion acceptance harness.
 *
 * Starts the real frontend dev server, drives it with a real headless
 * browser, exercises the main screens, and cross-checks what's rendered
 * against the real data/export/*.json files -- not against a stored
 * screenshot. See README.md for why this is a separate tool from
 * frontend/e2e/smoke.mjs, and for what each check catches.
 *
 * Usage: node harness.mjs [--port 5199] [--keep-server]
 */
import { chromium } from 'playwright';
import { mkdirSync, writeFileSync } from 'node:fs';
import { dirname, join } from 'node:path';
import { fileURLToPath } from 'node:url';

import { loadGroundTruth } from './lib/groundTruth.mjs';
import { startDevServer, waitForServer, stopDevServer } from './lib/server.mjs';
import { ALL_CHECKS } from './lib/checks.mjs';

const here = dirname(fileURLToPath(import.meta.url));
const repoRoot = join(here, '..', '..');
const frontendDir = join(repoRoot, 'frontend');
const artifactsDir = join(here, 'artifacts');
const screenshotsDir = join(artifactsDir, 'screenshots');

const args = process.argv.slice(2);
const portFlagIdx = args.indexOf('--port');
const port = portFlagIdx >= 0 ? Number(args[portFlagIdx + 1]) : 5199;
const baseUrl = `http://localhost:${port}`;

mkdirSync(screenshotsDir, { recursive: true });

async function main() {
  const groundTruth = loadGroundTruth(repoRoot);
  const results = [];
  const screenshots = [];

  const { child: serverProcess } = startDevServer({ cwd: frontendDir, port });
  let browser = null;

  // A crash anywhere below is itself a reported failure row, not a silent
  // exit -- a harness that dies must look red in the evidence file, not
  // absent from it. Everything through the screen walkthrough is one big
  // try so any exception (a selector timeout because a fault broke
  // navigation, etc.) still reaches the evidence write below.
  try {
    await waitForServer(baseUrl, { timeoutMs: 45000 });

    browser = await chromium.launch();
    const page = await browser.newPage({ viewport: { width: 1440, height: 900 } });
    await page.goto(baseUrl, { waitUntil: 'networkidle' });

    // Wait for the load to resolve one way or another -- either real content
    // or an explicit error -- rather than racing a fixed timeout.
    await page.waitForFunction(
      () => !document.body.innerText.includes('Loading the exports'),
      null,
      { timeout: 20000 },
    );

    const loadError = await page.getByText('The exports could not be loaded.').count();
    if (loadError > 0) {
      results.push({
        name: 'app-loads',
        ok: false,
        expected: 'dataset loads without error',
        actual: await page.locator('.empty').innerText(),
        detail: 'Nothing else can be checked meaningfully if the app failed to load at all.',
      });
    } else {
      results.push({ name: 'app-loads', ok: true, expected: 'dataset loads without error', actual: 'loaded', detail: null });

      // Main screen 1: Board (Prep mode, default state) -- this is also
      // where most of the content checks run, since it's the default screen.
      const boardShot = join(screenshotsDir, 'board.png');
      await page.screenshot({ path: boardShot, fullPage: false });
      screenshots.push({ screen: 'board', path: boardShot });

      for (const check of ALL_CHECKS) {
        results.push(await check(page, groundTruth));
      }

      // The rest of the walkthrough (Draft, Opponents, Player detail) is a
      // second, separate try: it depends on the mode switcher and nav
      // working at all, which is exactly what checkModeSwitcher above might
      // just have reported broken. If it crashes here, the five content
      // checks above have already landed in `results` either way.
      try {
        // Main screen 2: Draft mode / DraftRoom.
        await page.getByRole('button', { name: 'Draft', exact: true }).click({ timeout: 10000 });
        await page.waitForSelector('[data-testid="my-picks"]', { timeout: 10000 }).catch(() => null);
        const draftShot = join(screenshotsDir, 'draft-room.png');
        await page.screenshot({ path: draftShot, fullPage: false });
        screenshots.push({ screen: 'draft-room', path: draftShot });
        results.push(
          await (async () => {
            const ok = (await page.locator('[data-testid="my-picks"]').count()) > 0;
            return { name: 'draft-room-renders', ok, expected: 'my-picks panel present', actual: ok ? 'present' : 'absent', detail: null };
          })(),
        );

        // Back to Prep mode, Opponents screen.
        await page.getByRole('button', { name: 'Prep', exact: true }).click({ timeout: 10000 });
        await page.getByRole('button', { name: 'Opponents', exact: true }).click({ timeout: 10000 });
        await page.waitForSelector('h2:has-text("Opponents")', { timeout: 10000 }).catch(() => null);
        const opponentsShot = join(screenshotsDir, 'opponents.png');
        await page.screenshot({ path: opponentsShot, fullPage: false });
        screenshots.push({ screen: 'opponents', path: opponentsShot });
        results.push(
          await (async () => {
            const ok = (await page.getByRole('heading', { name: 'Opponents' }).count()) > 0;
            return { name: 'opponents-renders', ok, expected: 'Opponents heading present', actual: ok ? 'present' : 'absent', detail: null };
          })(),
        );

        // Back to Board, open a player's detail panel.
        await page.getByRole('button', { name: 'Board', exact: true }).click({ timeout: 10000 });
        await page.waitForSelector('[data-testid="freshness-note"]', { timeout: 10000 });
        const rowText = page.getByText(/^\d+ players$/).first();
        await rowText.waitFor({ timeout: 10000 });
        // Board's sticky header row and every data row share the same inline
        // grid-template-columns (Board.tsx's GRID_TEMPLATE) -- nth(0) is the
        // header, nth(1) is the first real data row. A plain "cursor: pointer"
        // selector isn't specific enough: the sidebar's nav items use the same
        // style and sit earlier in the DOM.
        const firstRow = page.locator('div[style*="minmax(180px"]').nth(1);
        await firstRow.click({ timeout: 10000 });
        const detailOk = await page
          .waitForSelector('[data-testid="player-detail-backdrop"]', { timeout: 10000 })
          .then(() => true)
          .catch(() => false);
        const playerDetailShot = join(screenshotsDir, 'player-detail.png');
        await page.screenshot({ path: playerDetailShot, fullPage: false });
        screenshots.push({ screen: 'player-detail', path: playerDetailShot });
        results.push({
          name: 'player-detail-opens',
          ok: detailOk,
          expected: 'player-detail-backdrop present after clicking a board row',
          actual: detailOk ? 'present' : 'absent',
          detail: null,
        });
      } catch (err) {
        results.push({
          name: 'screen-walkthrough',
          ok: false,
          expected: 'Draft/Opponents/Player-detail walkthrough completes',
          actual: `crashed: ${err.message}`,
          detail: 'A crash here usually means an earlier check already found the real problem (e.g. the mode switcher).',
        });
      }
    }
  } catch (err) {
    results.push({
      name: 'harness-crashed',
      ok: false,
      expected: 'harness runs to completion',
      actual: `crashed: ${err.message}`,
      detail: null,
    });
  } finally {
    if (browser) await browser.close();
    stopDevServer(serverProcess);
  }

  const ok = results.length > 0 && results.every((r) => r.ok);
  const evidence = {
    ranAt: new Date().toISOString(),
    baseUrl,
    ok,
    groundTruth: { playerCount: groundTruth.playerCount, leagueName: groundTruth.league.league_name },
    results,
    screenshots,
  };
  writeFileSync(join(artifactsDir, 'evidence.json'), JSON.stringify(evidence, null, 2));

  console.log(`\n${ok ? 'PASS' : 'FAIL'} -- ${results.filter((r) => r.ok).length}/${results.length} checks passed`);
  for (const r of results) {
    console.log(`  [${r.ok ? 'ok' : 'FAIL'}] ${r.name}${r.ok ? '' : ` -- expected ${JSON.stringify(r.expected)}, got ${JSON.stringify(r.actual)}${r.detail ? ` (${r.detail})` : ''}`}`);
  }
  console.log(`Evidence: ${join(artifactsDir, 'evidence.json')}`);

  process.exit(ok ? 0 : 1);
}

main();
