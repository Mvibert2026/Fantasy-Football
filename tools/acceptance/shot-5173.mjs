#!/usr/bin/env node
/**
 * Phase 6 evidence capture: screenshot the ONE dev server running from the main
 * checkout on port 5173, and re-assert the four runtime claims against the
 * export files while the page is open.
 *
 * Deliberately does not start a server. It attaches to whatever is already on
 * 5173, because the point of Phase 6 is to prove that the server the founder
 * will find running tomorrow is the correct one -- a script that starts its own
 * server would prove nothing about that.
 *
 * Lives inside tools/acceptance/ purely because that is where playwright is
 * installed; it is not part of the harness run.
 *
 * Usage: node tools/acceptance/shot-5173.mjs <output.png>
 */
import { chromium } from 'playwright';
import { readFileSync } from 'node:fs';
import { dirname, join, resolve } from 'node:path';
import { fileURLToPath } from 'node:url';

const here = dirname(fileURLToPath(import.meta.url));
const repoRoot = join(here, '..', '..');
const out = resolve(process.argv[2] ?? join(repoRoot, 'shot.png'));

const board = JSON.parse(readFileSync(join(repoRoot, 'data', 'export', 'board.json'), 'utf8'));
const league = JSON.parse(readFileSync(join(repoRoot, 'data', 'export', 'league.json'), 'utf8'));
const expectedCount = board.players.length;
const expectedLeague = league.league_name;

const browser = await chromium.launch();
const page = await browser.newPage({ viewport: { width: 1440, height: 900 } });
await page.goto('http://localhost:5173', { waitUntil: 'networkidle' });
await page.waitForFunction(
  () => !document.body.innerText.includes('Loading the exports'),
  null,
  { timeout: 30000 },
);
await page.waitForSelector('[data-testid="freshness-note"]', { timeout: 15000 });

const facts = await page.evaluate(() => {
  const text = document.body.innerText;
  const sel = document.querySelector('select[aria-label="Select league"]');
  const vw = window.innerWidth;
  const vh = window.innerHeight;
  const byName = (n) => [...document.querySelectorAll('button')].find((b) => b.textContent.trim() === n);
  const refresh = [...document.querySelectorAll('button')].find((b) => /refresh data/i.test(b.textContent));
  const inViewport = (el) => {
    if (!el) return false;
    const r = el.getBoundingClientRect();
    return r.width > 0 && r.height > 0 && r.left >= 0 && r.top >= 0 && r.right <= vw && r.bottom <= vh;
  };
  // The top bar is the lowest element containing BOTH the refresh button and
  // the mode switcher -- derived from the live DOM, not assumed from a class
  // name, because the shell styles inline and carries no stable class hooks.
  const ancestors = new Set();
  for (let n = refresh; n; n = n.parentElement) ancestors.add(n);
  let topBar = byName('Prep');
  while (topBar && !ancestors.has(topBar)) topBar = topBar.parentElement;

  return {
    loadedCount: Number((text.match(/(\d+)\s+players loaded/) || [])[1]),
    hasDenominator: /of\s+\d+\s+players loaded/.test(text),
    hasOf378: /of\s*378/.test(text),
    boardFooterCount: Number((text.match(/^\s*(\d+) players\s*$/m) || [])[1]),
    leagueShown: sel ? sel.options[sel.selectedIndex].text : null,
    modeSwitcherInViewport: ['Prep', 'Draft', 'Season'].every((n) => inViewport(byName(n))),
    refreshInViewport: inViewport(refresh),
    refreshInsideTopBar: !!(topBar && refresh && topBar.contains(refresh)),
    topBarHeight: topBar ? Math.round(topBar.getBoundingClientRect().height) : null,
    pageScrollsHorizontally: document.documentElement.scrollWidth > vw,
  };
});

await page.screenshot({ path: out, fullPage: false });
await browser.close();

const checks = [
  ['board renders the real player count', facts.loadedCount === expectedCount, `${facts.loadedCount} vs export ${expectedCount}`],
  ['header does not say "of 378"', facts.hasOf378 === false, String(facts.hasOf378)],
  ['header carries no denominator at all', facts.hasDenominator === false, String(facts.hasDenominator)],
  ['board footer count matches export', facts.boardFooterCount === expectedCount, `${facts.boardFooterCount} vs ${expectedCount}`],
  ['league reads the configured league', facts.leagueShown === expectedLeague, `${facts.leagueShown} vs ${expectedLeague}`],
  ['mode switcher fully in viewport, loaded state', facts.modeSwitcherInViewport === true, String(facts.modeSwitcherInViewport)],
  ['refresh button inside the top bar', facts.refreshInsideTopBar === true, `topBar height ${facts.topBarHeight}`],
  ['refresh button fully in viewport', facts.refreshInViewport === true, String(facts.refreshInViewport)],
  ['page does not scroll horizontally', facts.pageScrollsHorizontally === false, String(facts.pageScrollsHorizontally)],
];

let failed = 0;
for (const [name, ok, detail] of checks) {
  if (!ok) failed += 1;
  console.log(`  [${ok ? 'ok' : 'FAIL'}] ${name} -- ${detail}`);
}
console.log(`\n${failed === 0 ? 'PASS' : 'FAIL'} -- ${checks.length - failed}/${checks.length}`);
console.log(`Screenshot: ${out}`);
process.exit(failed === 0 ? 0 : 1);
