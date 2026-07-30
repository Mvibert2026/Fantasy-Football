/**
 * Screenshot verification for design round-1 item 2, the player profile
 * (`docs/design/PLAYER-PROFILE.md`), specifically the archetype chip placement
 * dual-build (thread 121, `ui/data/archetypePlacement.ts`) plus the §3
 * reading-level rewrite.
 *
 * Captures BOTH arrangements (A = identity-strip, B = disclosed), in BOTH
 * themes, across all four archetype states (a real label, and the three
 * distinguishable absences: unclassified / not-applicable / not-available),
 * plus one composite "three absences side by side" comparison image.
 *
 * Usage: node e2e/verify-item2-player-profile.mjs [--url http://localhost:5199]
 */
import { mkdirSync, readFileSync } from 'node:fs';
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

/** Opens a fresh page with the given theme + archetype-placement flag baked
 *  in via localStorage BEFORE first load (addInitScript), navigates to the
 *  app, waits for real data, and returns the page. A fresh page per
 *  combination -- not a reload of a shared one -- because addInitScript
 *  persists across navigations on the same page object and would otherwise
 *  stack stale localStorage writes (same gotcha documented in
 *  shot-light-theme-shading.mjs). */
async function openPage({ theme, placement, league }) {
  const page = await browser.newPage({ viewport: { width: 1440, height: 960 } });
  await page.addInitScript(
    ({ theme, placement }) => {
      try {
        if (theme === 'light') localStorage.setItem('prep.theme', 'light');
        localStorage.setItem('prep.archetypePlacement', placement);
      } catch {
        /* ignore */
      }
    },
    { theme, placement },
  );
  await page.goto(url, { waitUntil: 'load', timeout: 60_000 });
  await page.waitForSelector('text=/generated 20/', { timeout: 60_000 });
  if (league) {
    // The "Switch which league's data is loaded" title is on the wrapping
    // div, not the <select> itself -- the select's own accessible name is
    // its aria-label, "Select league".
    const select = page.getByLabel('Select league');
    await select.selectOption(league);
    await page.waitForSelector('text=/generated 20/', { timeout: 60_000 });
    await page.waitForTimeout(300);
  }
  return page;
}

async function openPlayerCard(page, playerName) {
  await page.getByText(playerName, { exact: false }).first().click();
  await page.waitForSelector('[data-testid="player-detail-identity-strip"]', { timeout: 60_000 });
  await page.waitForTimeout(250);
}

// Real players from the primary export (see e2e/verify-fr075-fr061-fr069.mjs
// for the same choices, confirmed against public/data/board.json +
// player_descriptions.json this session):
//   Bijan Robinson (RB1)     -- real archetype label
//   James Cook III (RB10)    -- covered position, unclassified (measured, no fit)
//   Josh Allen (QB6)         -- position not covered by the taxonomy at all
// The fourth state (not-available: no player_descriptions.json export at all)
// needs a DIFFERENT league -- espn_10_full is real, on disk, and genuinely has
// no player_descriptions.json (confirmed: `ls data/export/espn_10_full/`).
const REAL_LABEL_PLAYER = 'Bijan Robinson';
const UNCLASSIFIED_PLAYER = 'James Cook';
const NOT_APPLICABLE_PLAYER = 'Josh Allen';
const NOT_AVAILABLE_LEAGUE = 'espn_10_full';

async function shot(page, name) {
  const path = join(artifacts, `${name}.png`);
  await page.screenshot({ path, fullPage: false });
  console.log(`wrote ${name}.png`);
  return path;
}

// ---------------------------------------------------------------------------
// Arrangement A (identity-strip, default), dark theme -- all four states.
// ---------------------------------------------------------------------------
{
  const page = await openPage({ theme: 'dark', placement: 'identity-strip' });
  await openPlayerCard(page, REAL_LABEL_PLAYER);
  await shot(page, 'item2-arrangementA-dark-01-real-label');
  await page.keyboard.press('Escape');
  await page.waitForTimeout(150);

  await openPlayerCard(page, UNCLASSIFIED_PLAYER);
  await shot(page, 'item2-arrangementA-dark-02-unclassified');
  await page.keyboard.press('Escape');
  await page.waitForTimeout(150);

  await openPlayerCard(page, NOT_APPLICABLE_PLAYER);
  await shot(page, 'item2-arrangementA-dark-03-not-applicable');
  await page.keyboard.press('Escape');
  await page.waitForTimeout(150);
  await page.close();
}
{
  const page = await openPage({ theme: 'dark', placement: 'identity-strip', league: NOT_AVAILABLE_LEAGUE });
  await openPlayerCard(page, REAL_LABEL_PLAYER);
  await shot(page, 'item2-arrangementA-dark-04-not-available');
  await page.close();
}

// ---------------------------------------------------------------------------
// Arrangement B (disclosed), dark theme -- all four states. For the three
// absence states, the identity strip should show NO chip at all; the
// disclosed ARCHETYPE section below is scrolled into view so the sentence
// (with its distinguishing border treatment) is visible in the same shot.
// ---------------------------------------------------------------------------
{
  const page = await openPage({ theme: 'dark', placement: 'disclosed' });
  await openPlayerCard(page, REAL_LABEL_PLAYER);
  await shot(page, 'item2-arrangementB-dark-01-real-label');
  await page.keyboard.press('Escape');
  await page.waitForTimeout(150);

  await openPlayerCard(page, UNCLASSIFIED_PLAYER);
  await page.getByText('ARCHETYPE', { exact: true }).first().scrollIntoViewIfNeeded();
  await shot(page, 'item2-arrangementB-dark-02-unclassified');
  await page.keyboard.press('Escape');
  await page.waitForTimeout(150);

  await openPlayerCard(page, NOT_APPLICABLE_PLAYER);
  await page.getByText('ARCHETYPE', { exact: true }).first().scrollIntoViewIfNeeded();
  await shot(page, 'item2-arrangementB-dark-03-not-applicable');
  await page.keyboard.press('Escape');
  await page.waitForTimeout(150);
  await page.close();
}
{
  const page = await openPage({ theme: 'dark', placement: 'disclosed', league: NOT_AVAILABLE_LEAGUE });
  await openPlayerCard(page, REAL_LABEL_PLAYER);
  await page.getByText('ARCHETYPE', { exact: true }).first().scrollIntoViewIfNeeded();
  await shot(page, 'item2-arrangementB-dark-04-not-available');
  await page.close();
}

// ---------------------------------------------------------------------------
// Light theme -- one representative pair per arrangement (real label, the
// arrangement that actually differs visually), so the founder can compare
// both arrangements without a full 8-shot re-run in light mode too.
// ---------------------------------------------------------------------------
{
  const page = await openPage({ theme: 'light', placement: 'identity-strip' });
  await openPlayerCard(page, REAL_LABEL_PLAYER);
  await shot(page, 'item2-arrangementA-light-01-real-label');
  await page.keyboard.press('Escape');
  await page.waitForTimeout(150);
  await openPlayerCard(page, UNCLASSIFIED_PLAYER);
  await shot(page, 'item2-arrangementA-light-02-unclassified');
  await page.close();
}
{
  const page = await openPage({ theme: 'light', placement: 'disclosed' });
  await openPlayerCard(page, REAL_LABEL_PLAYER);
  await shot(page, 'item2-arrangementB-light-01-real-label');
  await page.keyboard.press('Escape');
  await page.waitForTimeout(150);
  await openPlayerCard(page, UNCLASSIFIED_PLAYER);
  await page.getByText('ARCHETYPE', { exact: true }).first().scrollIntoViewIfNeeded();
  await shot(page, 'item2-arrangementB-light-02-unclassified');
  await page.close();
}

// ---------------------------------------------------------------------------
// Reading-level rewrite (§3): default plain-English vs. trace-mode raw
// formula, side by side via two shots of the same PROJECTION section.
// ---------------------------------------------------------------------------
{
  const page = await openPage({ theme: 'dark', placement: 'identity-strip' });
  await openPlayerCard(page, REAL_LABEL_PLAYER);
  await page.getByText('PROJECTION', { exact: true }).scrollIntoViewIfNeeded();
  await shot(page, 'item2-reading-level-default-plain-english');
  // Turn on "show data sources" via Alt+T, same mechanism as FR-114.
  await page.keyboard.press('Alt+t');
  await page.waitForTimeout(200);
  await page.getByText('PROJECTION', { exact: true }).scrollIntoViewIfNeeded();
  await shot(page, 'item2-reading-level-trace-mode-raw-formula');
  await page.close();
}

// ---------------------------------------------------------------------------
// Composite: the three absence states side by side, cropped tight to the
// identity strip so the border-style distinction (dashed / none-italic /
// dotted) is directly comparable in one image. Arrangement A, dark theme --
// all three chips are guaranteed present in the strip in this arrangement.
// ---------------------------------------------------------------------------
{
  const page = await openPage({ theme: 'dark', placement: 'identity-strip' });
  const crops = [];

  await openPlayerCard(page, UNCLASSIFIED_PLAYER);
  const stripU = page.getByTestId('player-detail-identity-strip');
  const boxU = await stripU.boundingBox();
  if (boxU) crops.push({ label: 'UNCLASSIFIED', box: boxU, page });
  await page.keyboard.press('Escape');
  await page.waitForTimeout(150);

  await openPlayerCard(page, NOT_APPLICABLE_PLAYER);
  const stripN = page.getByTestId('player-detail-identity-strip');
  const boxN = await stripN.boundingBox();
  if (boxN) {
    await page.screenshot({ path: join(artifacts, 'item2-absence-crop-not-applicable.png'), clip: boxN });
  }
  await page.keyboard.press('Escape');
  await page.waitForTimeout(150);

  // Re-open unclassified to crop it too (bounding box captured above, but
  // clip needs a live screenshot call against the still-open card).
  await openPlayerCard(page, UNCLASSIFIED_PLAYER);
  const stripU2 = page.getByTestId('player-detail-identity-strip');
  const boxU2 = await stripU2.boundingBox();
  if (boxU2) {
    await page.screenshot({ path: join(artifacts, 'item2-absence-crop-unclassified.png'), clip: boxU2 });
  }
  await page.close();
}
{
  const page = await openPage({ theme: 'dark', placement: 'identity-strip', league: NOT_AVAILABLE_LEAGUE });
  await openPlayerCard(page, REAL_LABEL_PLAYER);
  const strip = page.getByTestId('player-detail-identity-strip');
  const box = await strip.boundingBox();
  if (box) {
    await page.screenshot({ path: join(artifacts, 'item2-absence-crop-not-available.png'), clip: box });
  }
  await page.close();
}

// ---------------------------------------------------------------------------
// Composite the three crops into one side-by-side comparison image. No new
// image-processing dependency needed -- render an HTML page with the three
// crops as data URLs and screenshot THAT page, same tool doing the work
// end to end.
// ---------------------------------------------------------------------------
{
  function dataUrl(name) {
    const b64 = readFileSync(join(artifacts, name)).toString('base64');
    return `data:image/png;base64,${b64}`;
  }
  const compositeHtml = `
  <!doctype html><html><head><meta charset="utf-8"><style>
    body { background:#0d1117; margin:0; padding:32px; font-family:-apple-system,sans-serif; }
    h1 { color:#e6edf3; font-size:16px; margin:0 0 20px; }
    .row { display:flex; gap:24px; align-items:flex-start; }
    figure { margin:0; background:#161b22; border:1px solid #30363d; padding:12px; }
    figcaption { color:#8b949e; font-size:11px; letter-spacing:.05em; margin-top:10px; text-transform:uppercase; }
    img { display:block; }
  </style></head><body>
    <h1>Design round-1 item 2 &mdash; three archetype absence states, side by side (thread 121)</h1>
    <div class="row">
      <figure><img src="${dataUrl('item2-absence-crop-unclassified.png')}" />
        <figcaption>UNCLASSIFIED &mdash; measured, met no threshold (dashed border)</figcaption></figure>
      <figure><img src="${dataUrl('item2-absence-crop-not-applicable.png')}" />
        <figcaption>ARCHETYPE N/A &mdash; position not covered by taxonomy (no border, italic)</figcaption></figure>
      <figure><img src="${dataUrl('item2-absence-crop-not-available.png')}" />
        <figcaption>ARCHETYPE &mdash; &mdash; no player_descriptions.json for this league (dotted border)</figcaption></figure>
    </div>
  </body></html>`;
  const compositePage = await browser.newPage({ viewport: { width: 1500, height: 260 } });
  await compositePage.setContent(compositeHtml);
  await compositePage.waitForTimeout(100);
  await compositePage.screenshot({ path: join(artifacts, 'item2-absence-states-side-by-side.png'), fullPage: true });
  console.log('wrote item2-absence-states-side-by-side.png');
  await compositePage.close();
}

console.log('done');
await browser.close();
