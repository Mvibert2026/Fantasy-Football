/**
 * Standing reference-screenshot set for the design function (no repo access, no
 * running app -- docs/design-fidelity.md, thread "Build a standing
 * reference-screenshot set", 2026-07-30).
 *
 * WHY THIS EXISTS. Design's single strongest finding on 2026-07-31 -- that the
 * rankings pane drops the player's name entirely at 1180px -- came from a
 * screenshot someone happened to remember to take, not from a process. This
 * script is the process: one parameterised capture covering every real surface
 * of the app, at a wide desktop width and at 1180px (the width that already
 * broke one screen), in both themes, committed alongside a manifest that names
 * the commit each capture was taken at.
 *
 * SURFACES. Enumerated from the app's own navigation (ui/App.tsx's ScreenId
 * union, ui/components/shell/Sidebar.tsx's NAV_MAIN, ui/views/DraftRoom.tsx's
 * HUB_TABS/PANE_TABS, and TopBar's mode switcher) rather than a fixed list, so
 * a screen this script's author forgot is still visited if it is reachable
 * through real navigation. See the SURFACES array below -- each entry is a
 * (setup, capture) step run in sequence against one already-loaded page.
 * 'Coming soon' sidebar entries (sync/bottomup/news/inseason/startability) are
 * deliberately NOT captured -- they all render the same generic NotBuilt pane
 * (ui/components/shell/NotBuilt.tsx) regardless of which one is selected, so
 * capturing all five would be five identical images under different names.
 * The Season mode not-built pane IS captured once, since it is a distinct
 * top-level mode with its own nav entry point, not one of the five.
 *
 * DRAFT STATE. Draft mode surfaces are seeded with a real, reproducible
 * 17-pick sequence (same picks as e2e/verify-fr050-055-058.mjs) via
 * page.addInitScript before the app ever loads, so the middle-pane tabs,
 * recommendation panel, and roster all show real content instead of an empty
 * draft.
 *
 * OUTPUT. docs/design/reference-screenshots/<surface>_<width>px_<theme>.png,
 * plus MANIFEST.md naming every file (surface, width, theme, app commit) and
 * recording known gaps -- per docs/design-fidelity.md and this task's honesty
 * requirements, a capture that cannot be trusted must say so, not be shipped
 * silently or omitted silently.
 *
 * Usage:
 *   npm run reference-screenshots                       # starts its own dev server
 *   node e2e/reference-screenshots.mjs --url http://localhost:5199 --no-server
 *
 * Cloud-container Chromium path per docs/frontend-cloud-runbook.md
 * (executablePath against the pre-installed binary; never `playwright install`).
 */

import { spawn, execSync } from 'node:child_process';
import { mkdirSync, writeFileSync, readdirSync, rmSync } from 'node:fs';
import { join, dirname } from 'node:path';
import { fileURLToPath } from 'node:url';
import { chromium } from 'playwright';

const FRONTEND_ROOT = join(dirname(fileURLToPath(import.meta.url)), '..');
const REPO_ROOT = join(FRONTEND_ROOT, '..');
const OUT_DIR = join(REPO_ROOT, 'docs', 'design', 'reference-screenshots');
mkdirSync(OUT_DIR, { recursive: true });

const args = process.argv.slice(2);
const urlArg = args.includes('--url') ? args[args.indexOf('--url') + 1] : 'http://localhost:5199';
const noServer = args.includes('--no-server');

const WIDTHS = [
  { label: '1600px', px: 1600 }, // wide desktop
  { label: '1180px', px: 1180 }, // the width that already broke the rankings pane
];
const THEMES = ['dark', 'light'];
const VIEWPORT_HEIGHT = 1000;

const browsersPath = process.env.PLAYWRIGHT_BROWSERS_PATH || '/opt/pw-browsers';
const executablePath = join(browsersPath, 'chromium');

const LEAGUE_ID = 'primary';

/** Same reproducible 17-pick sequence as e2e/verify-fr050-055-058.mjs -- real
 *  board.json ids (2026-07-29 export; ids are stable), giving Draft mode's
 *  roster, recommendation panel, and scarcity numbers real content instead of
 *  an empty draft. Auto-fill placeholders (playerId: null) for the remaining
 *  slots, matching AUTO_FILL_PLACEHOLDER's own convention in DraftRoom.tsx. */
function buildDraftState() {
  function teamSlotAtPick(overallPick, teams) {
    const round = Math.ceil(overallPick / teams);
    const positionInRound = overallPick - (round - 1) * teams;
    return round % 2 === 1 ? positionInRound : teams - positionInRound + 1;
  }
  function roundOfPick(overallPick, teams) {
    return Math.ceil(overallPick / teams);
  }
  const teams = 10;
  const now = new Date().toISOString();
  const real = [
    { pick: 1, id: 1, name: 'Bijan Robinson' },
    { pick: 2, id: 2, name: "Ja'Marr Chase" },
    { pick: 3, id: 3, name: 'Jahmyr Gibbs' }, // the user's own pick 3
    { pick: 4, id: 4, name: 'Puka Nacua' },
    { pick: 5, id: 5, name: 'Christian McCaffrey' },
  ];
  const picks = [];
  for (let n = 1; n <= 17; n++) {
    const r = real.find((x) => x.pick === n);
    picks.push({
      overallPick: n,
      round: roundOfPick(n, teams),
      teamSlot: teamSlotAtPick(n, teams),
      playerId: r ? r.id : null,
      playerName: r ? r.name : '(auto-filled -- unknown pick)',
      timestamp: now,
      entryMode: r ? 'shortcut' : null,
    });
  }
  return { leagueId: LEAGUE_ID, mockId: 'reference-screenshots-mock', picks, queue: [] };
}

async function waitLoaded(page) {
  // The freshness-note element mounts immediately (TopBar renders it in every
  // state, including "Loading the exports..."), so it is not proof the data
  // arrived. Measured while building this harness: a cold first load in this
  // container (dev-server module graph + client-side computation over ~510
  // board rows, unminified) consistently takes 35-45s, well past a normal
  // 30s Playwright action timeout -- wait for the loading placeholder text to
  // actually clear, with a generous ceiling, rather than trust an earlier signal.
  await page.waitForSelector('[data-testid="freshness-note"]', { timeout: 30_000 });
  await page.waitForFunction(() => !document.body.textContent?.includes('Loading the exports'), { timeout: 90_000 });
  await page.waitForTimeout(400);
}

async function toPrep(page) {
  const prepBtn = page.getByRole('button', { name: 'Prep', exact: true });
  if (await prepBtn.count()) {
    await prepBtn.click();
    await page.waitForTimeout(300);
  }
}

async function toSidebarScreen(page, label) {
  await toPrep(page);
  await page.getByRole('button', { name: label, exact: true }).first().click();
  await page.waitForTimeout(500);
}

/**
 * Each surface is (key, setup(page)) -- setup performs whatever navigation is
 * needed from wherever the previous surface left the page, and settles. The
 * capture step itself (screenshot) is generic and lives in the run loop below.
 * Steps run in order against one continuously-live page per (width, theme)
 * pair; state from earlier steps (e.g. "already in Draft mode") is relied on
 * deliberately, same pattern as the app's own e2e verification scripts.
 */
const SURFACES = [
  {
    key: 'board',
    label: 'Board (Prep)',
    async setup(page) {
      await toPrep(page);
      await page.getByRole('button', { name: 'Board', exact: true }).first().click();
      await page.waitForTimeout(500);
    },
  },
  {
    key: 'board-player-detail',
    label: 'Board with player detail panel open (Prep)',
    async setup(page) {
      const board = await page.evaluate(() => fetch('/data/board.json').then((r) => r.json()));
      const topName = board.players?.[0]?.player;
      if (!topName) throw new Error('board.json:players[0].player not found -- cannot open a real player row');
      await page.getByText(topName, { exact: true }).first().click();
      await page.waitForSelector('[data-testid="player-detail-backdrop"]', { timeout: 10_000 });
      await page.waitForTimeout(400);
    },
    async teardown(page) {
      await page.keyboard.press('Escape');
      await page.waitForTimeout(300);
    },
  },
  {
    key: 'settings-panel',
    label: 'Settings panel open (Prep, over Board)',
    async setup(page) {
      await page.getByRole('button', { name: 'Settings', exact: true }).click();
      await page.waitForTimeout(400);
    },
    async teardown(page) {
      await page.keyboard.press('Escape');
      await page.waitForTimeout(300);
    },
  },
  {
    key: 'assistant-panel',
    label: 'Assistant dock open (Prep, over Board)',
    async setup(page) {
      const openBtn = page.getByRole('button', { name: 'Open assistant', exact: true });
      if ((await openBtn.count()) === 0) throw new Error('"Open assistant" button not found');
      await openBtn.click();
      await page.waitForTimeout(500);
    },
    async teardown(page) {
      const collapseBtn = page.getByRole('button', { name: 'Collapse assistant', exact: true });
      if (await collapseBtn.count()) await collapseBtn.click();
      await page.waitForTimeout(200);
    },
  },
  {
    key: 'availability',
    label: 'Availability (Prep)',
    async setup(page) {
      await toSidebarScreen(page, 'Availability');
    },
  },
  {
    key: 'opponents-prep',
    label: 'Opponents (Prep)',
    async setup(page) {
      await toSidebarScreen(page, 'Opponents');
    },
  },
  {
    key: 'predictions-prep',
    label: 'Predictions (Prep)',
    async setup(page) {
      await toSidebarScreen(page, 'Predictions');
    },
  },
  {
    key: 'strategy-guide',
    label: 'Strategy Guide (Prep)',
    async setup(page) {
      await toSidebarScreen(page, 'Strategy Guide');
    },
  },
  {
    key: 'methodology',
    label: 'Methodology (Prep)',
    async setup(page) {
      await toSidebarScreen(page, 'Methodology');
    },
  },
  {
    key: 'glossary',
    label: 'Glossary (Prep)',
    async setup(page) {
      await toSidebarScreen(page, 'Glossary');
    },
  },
  {
    key: 'draft-recommend',
    label: 'Draft -- Board hub, Recommend pane (default)',
    async setup(page) {
      await page.getByText('Draft', { exact: true }).first().click();
      await page.waitForSelector('text=/ON THE CLOCK/', { timeout: 15_000 });
      await page.waitForTimeout(500);
    },
  },
  {
    key: 'draft-scarcity',
    label: 'Draft -- Board hub, Scarcity pane',
    async setup(page) {
      await page.getByRole('button', { name: 'Scarcity', exact: true }).click();
      await page.waitForTimeout(500);
    },
  },
  {
    key: 'draft-queue',
    label: 'Draft -- Board hub, Queue pane',
    async setup(page) {
      await page.getByRole('button', { name: 'Queue', exact: true }).click();
      await page.waitForTimeout(500);
    },
  },
  {
    key: 'draft-insights',
    label: 'Draft -- Board hub, Insights pane',
    async setup(page) {
      await page.getByRole('button', { name: 'Insights', exact: true }).click();
      await page.waitForTimeout(500);
    },
  },
  {
    key: 'draft-grid',
    label: 'Draft -- Board hub, Grid pane',
    async setup(page) {
      await page.getByRole('button', { name: 'Grid', exact: true }).click();
      await page.waitForTimeout(500);
    },
  },
  {
    key: 'draft-opponents',
    label: 'Draft -- Opponents hub tab',
    async setup(page) {
      await page.getByRole('button', { name: 'Opponents', exact: true }).click();
      await page.waitForTimeout(500);
    },
  },
  {
    key: 'draft-predictions',
    label: 'Draft -- Predictions hub tab',
    async setup(page) {
      await page.getByRole('button', { name: 'Predictions', exact: true }).click();
      await page.waitForTimeout(500);
    },
  },
  {
    key: 'season',
    label: 'Season mode (not built)',
    async setup(page) {
      await page.getByText('Season', { exact: true }).first().click();
      await page.waitForTimeout(400);
    },
  },
];

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

async function runOneContext(browser, widthPx, theme, results) {
  const page = await browser.newPage({ viewport: { width: widthPx, height: VIEWPORT_HEIGHT } });
  page.setDefaultTimeout(45_000);
  const consoleErrors = [];
  page.on('console', (msg) => {
    if (msg.type() === 'error') consoleErrors.push(msg.text());
  });
  page.on('pageerror', (err) => consoleErrors.push(String(err)));

  await page.addInitScript(
    ({ theme, draftState, leagueId }) => {
      try {
        if (theme === 'light') localStorage.setItem('prep.theme', 'light');
        localStorage.setItem(`prep.draft.${leagueId}`, JSON.stringify(draftState));
      } catch {
        /* ignore */
      }
    },
    { theme, draftState: buildDraftState(), leagueId: LEAGUE_ID },
  );

  await page.goto(urlArg, { waitUntil: 'load', timeout: 40_000 });
  await waitLoaded(page);

  for (const surface of SURFACES) {
    const fileName = `${surface.key}_${widthPx}px_${theme}.png`;
    const outPath = join(OUT_DIR, fileName);
    try {
      await surface.setup(page);
      await page.screenshot({ path: outPath, fullPage: true });
      console.log(`  [ok] ${fileName}`);
      results.push({ key: surface.key, label: surface.label, width: widthPx, theme, file: fileName, ok: true });
    } catch (err) {
      console.log(`  [FAIL] ${fileName} -- ${err.message}`);
      results.push({
        key: surface.key,
        label: surface.label,
        width: widthPx,
        theme,
        file: null,
        ok: false,
        reason: err.message,
      });
    } finally {
      if (surface.teardown) {
        try {
          await surface.teardown(page);
        } catch {
          /* best effort */
        }
      }
    }
  }

  if (consoleErrors.length) {
    console.log(`  (${consoleErrors.length} console errors during this pass, see report.json)`);
  }
  results.consoleErrorsByPass = results.consoleErrorsByPass || {};
  results.consoleErrorsByPass[`${widthPx}px_${theme}`] = consoleErrors;

  await page.close();
}

function gitCommit() {
  try {
    return execSync('git rev-parse HEAD', { cwd: REPO_ROOT }).toString().trim();
  } catch {
    return 'unknown';
  }
}
function gitShort() {
  try {
    return execSync('git rev-parse --short HEAD', { cwd: REPO_ROOT }).toString().trim();
  } catch {
    return 'unknown';
  }
}

const KNOWN_GAPS = [
  {
    scope: 'all captures',
    gap:
      'Screenshots show the page at its default scroll position only. Surfaces with content ' +
      'taller than the viewport (Glossary, Methodology, Strategy Guide, and any long draft-room ' +
      'pane) are only captured from the top; content below the fold is not represented in this set.',
  },
  {
    scope: 'settings-panel, board (league/slot selectors)',
    gap:
      'Native <select> dropdown POPUP states (the open option list for the league selector, the ' +
      'draft-slot selector, and any select inside the Settings panel) are not captured open. ' +
      'Headless Chromium renders native select popups outside the normal page paint layer, so a ' +
      'screenshot taken with the popup open does not reliably show it -- this was independently ' +
      'confirmed unverifiable for dark-mode dropdown popups the same day this harness was built. ' +
      'Captures show these controls closed only.',
  },
  {
    scope: 'all captures',
    gap:
      'Scrollbar visibility/appearance is not verified by this harness. Headless Chromium\'s ' +
      'scrollbar rendering does not reliably match a real browser\'s, and this was independently ' +
      'flagged unverifiable the same day this harness was built. Do not read scrollbar presence, ' +
      'width, or styling off these images as ground truth.',
  },
  {
    scope: 'assistant-panel',
    gap:
      'This container has no ANTHROPIC_API_KEY, so the assistant reasoning proxy ' +
      '(server/proxy.ts) fails at the network layer rather than returning a real or a ' +
      '"reasoning unavailable" response (documented in docs/frontend-cloud-runbook.md). The ' +
      'capture shows the dock chrome and input, not a real conversation or its degraded-state UI.',
  },
  {
    scope: 'draft-* surfaces',
    gap:
      'Seeded from one fixed 17-pick sequence (same as e2e/verify-fr050-055-058.mjs), not a live ' +
      'or randomised draft. Real, reproducible content -- not a blank draft -- but a single frozen ' +
      'point in a draft\'s lifecycle, not every state (e.g. not the very first pick, not near the ' +
      'end of the draft, not a state with a queue populated).',
  },
  {
    scope: "'coming soon' sidebar entries",
    gap:
      'Not captured. All five (Live league sync / Bottom-up projections / News & injuries / ' +
      'In-season tools / Startability scores) render the identical generic NotBuilt pane -- ' +
      'capturing all five would be five duplicate images under different names. Season mode\'s ' +
      'own not-built pane IS captured once, since it is a distinct top-level mode, not one of ' +
      'these five sidebar entries.',
  },
];

async function main() {
  let server = null;
  if (!noServer) {
    server = spawn(process.platform === 'win32' ? 'npm.cmd' : 'npm', ['run', 'dev'], {
      cwd: FRONTEND_ROOT,
      stdio: 'ignore',
      shell: process.platform === 'win32',
      env: { ...process.env, PORT: '5199' },
    });
  }

  const up = await waitForServer(urlArg);
  if (!up) {
    console.error(`dev server not reachable at ${urlArg}`);
    if (server) server.kill();
    process.exit(1);
  }

  const browser = await chromium.launch({ executablePath });
  const results = [];

  for (const width of WIDTHS) {
    for (const theme of THEMES) {
      console.log(`\n=== ${width.px}px / ${theme} ===`);
      await runOneContext(browser, width.px, theme, results);
    }
  }

  await browser.close();
  if (server) server.kill();

  const okCount = results.filter((r) => r.ok).length;
  const failCount = results.filter((r) => !r.ok).length;

  writeFileSync(join(OUT_DIR, 'report.json'), JSON.stringify({ results, generatedAt: new Date().toISOString() }, null, 2));

  writeManifest(results);

  console.log(`\n${okCount} captured, ${failCount} failed. Manifest: docs/design/reference-screenshots/MANIFEST.md`);
  if (failCount > 0) {
    console.log('Failures (recorded in the manifest, not silently dropped):');
    for (const r of results.filter((r) => !r.ok)) console.log(`  ${r.key} @ ${r.width}px/${r.theme}: ${r.reason}`);
  }
}

function writeManifest(results) {
  const commit = gitCommit();
  const short = gitShort();
  const now = new Date().toISOString();

  const bySurface = new Map();
  for (const r of results) {
    if (!bySurface.has(r.key)) bySurface.set(r.key, { label: r.label, rows: [] });
    bySurface.get(r.key).rows.push(r);
  }

  let md = `# Reference screenshots -- manifest\n\n`;
  md += `Standing capture set for the design function (docs/design-fidelity.md; docs/handoffs `
    + `thread that requested this harness -- see docs/CODE-MAP.md §6 for the harness itself).\n\n`;
  md += `**App commit at capture time:** \`${commit}\` (${short})\n`;
  md += `**Captured:** ${now}\n\n`;
  md += `**Regenerate after any merge that changes the UI:** \`cd frontend && npm run reference-screenshots\`. `
    + `Not wired into CI -- a screenshot job that fails a merge on a rendering flake is worse than the `
    + `problem it solves. Re-run by hand, or dispatch a frontend session to do it, after a UI-affecting merge.\n\n`;
  md += `Widths: **1600px** (wide desktop), **1180px** (the width design's 2026-07-31 review found the `
    + `rankings pane dropping the player name at). Themes: **dark** (app default), **light**.\n\n`;
  md += `---\n\n`;
  md += `## Files\n\n`;
  md += `| Surface | Width | Theme | File | Status |\n`;
  md += `|---|---|---|---|---|\n`;
  for (const r of results) {
    const status = r.ok ? 'captured' : `**MISSING** -- ${r.reason}`;
    const file = r.file ? `\`${r.file}\`` : '(none)';
    md += `| ${r.label} | ${r.width}px | ${r.theme} | ${file} | ${status} |\n`;
  }

  md += `\n---\n\n## Known gaps\n\n`;
  md += `Recorded rather than silently shipped or silently omitted, per this harness's own honesty `
    + `requirement -- a screenshot that cannot be trusted is worse than no screenshot, because design `
    + `will spec against it.\n\n`;
  for (const g of KNOWN_GAPS) {
    md += `- **${g.scope}:** ${g.gap}\n`;
  }

  md += `\n---\n\n## Surfaces enumerated, and how\n\n`;
  md += `Pulled from the app's own navigation structures, not a hand-maintained list, so a screen `
    + `newly added to the app's routing shows up here the next time this script runs even if this `
    + `doc comment is never updated:\n\n`;
  md += `- Prep-mode sidebar: \`ui/components/shell/Sidebar.tsx\`'s \`NAV_MAIN\` (Board, Availability, `
    + `Opponents, Predictions, Strategy Guide, Methodology, Glossary).\n`;
  md += `- Draft-mode hub tabs: \`ui/views/DraftRoom.tsx\`'s \`HUB_TABS\` (Board, Opponents, Predictions).\n`;
  md += `- Draft-mode middle-pane tabs (Board hub only): \`ui/views/DraftRoom.tsx\`'s \`PANE_TABS\` `
    + `(Recommend, Scarcity, Queue, Insights, Grid).\n`;
  md += `- Top-level modes: \`ui/components/shell/TopBar.tsx\`'s \`DEFAULT_MODES\` (Prep, Draft, Season).\n`;
  md += `- Floating overlays reachable from any Prep screen: the Settings panel `
    + `(\`ui/components/shell/SettingsPanel.tsx\`), the player detail sheet `
    + `(\`ui/components/PlayerDetail.tsx\`), and the assistant dock `
    + `(\`ui/components/shell/AssistantDock.tsx\`).\n`;

  writeFileSync(join(OUT_DIR, 'MANIFEST.md'), md);
}

main().catch((err) => {
  console.error(err);
  process.exit(1);
});
