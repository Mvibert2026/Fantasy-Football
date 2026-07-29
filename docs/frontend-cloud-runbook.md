# Frontend cloud runbook

Replaces `docs/environment.md`'s frontend sections for a cloud Claude Code session (clone, work,
push — no worktree). Every fact below was observed directly in this container on 2026-07-29,
commit `a617611`. `docs/environment.md` describes the founder's Windows/conda machine and does not
apply here; it is not edited by this doc.

---

## What works, verbatim

```
cd frontend
npm ci                      # 6s, 184 packages, no browser download triggered
npx tsc -b --noEmit          # clean, no output
npm test                     # vitest run; pretest syncs data/export/ -> public/data/
```

No `data/nfl.db` is needed. `npm test`'s `pretest` script (`node scripts/sync-exports.mjs`) reads
only the tracked `data/export/` directory — confirmed by running the full suite with no
`data/nfl.db` present in the repo (it was absent all session; a different chain owns rebuilding it).

`python3` is on PATH here (Python 3.11.15) if a script needs it — the conda path in
`docs/environment.md` does not exist in this container. Node is v22.22.2, npm 10.9.7.

There is no PreToolUse hook in this container. Chained commands (`&&`, `;`) are not blocked. The
git-worktree gotchas in `docs/environment.md` §4–5 (stub `nfl.db`, `.claude/launch.json` port
juggling) do not apply — there is one checkout, not a worktree tree.

---

## Unit suite — measured counts (2026-07-29)

**202 passed, 0 failed, 22 test files, 22 test files passed, 51.6s wall.**

`docs/CURRENT-STATE.md` (line 263) records "192 passing / 2 pre-existing-red-by-design frontend
tests," but that line is dated 2026-07-26 and the surrounding paragraph is explicitly marked "not
re-verified" for everything except four unrelated bullets. This session's run found **no
red-by-design failures** — every test file passed clean. This is a real discrepancy from the
recorded figure (202 vs. 192, 0 red-by-design vs. 2), not a reconciliation of rounding. Reported
as a finding, not corrected in `docs/CURRENT-STATE.md` (out of this session's file boundary).

`tsc -b --noEmit` is clean (0 errors), matching the recorded claim.

---

## Dev server

```
npm run dev -- --port 5199 --strictPort
```

Starts clean, runs `predev`'s `sync-exports.mjs` first (copies `data/export/**` including all 26
league configs into `public/data/`), then Vite serves on the given port. Confirmed with `curl`:
`GET /` → 200; `GET /data/board.json` → real 511-player board with `contract_version`,
`scoring_format`, `snapshot_*` fields present.

No backend process is required — the app is a static-export consumer plus a dev-only
reasoning-proxy middleware (`server/proxy.ts`) for the assistant dock. That proxy has no
`ANTHROPIC_API_KEY` in this container and fails at the network layer (`ERR_CONNECTION_RESET` /
404) rather than resolving to its designed "reasoning unavailable" response — see Known gaps
below. It does not block the board, draft room, or any data-driven screen.

---

## Screenshot recipe — the one that matters

**Chromium is pre-installed at `/opt/pw-browsers/chromium` (revision 1194) with
`PLAYWRIGHT_BROWSERS_PATH` set. Do not run `playwright install` — downloads are blocked and it
will hang/fail.**

The repo's pinned `playwright` (`^1.62.0` in `frontend/package.json`, resolved to a build
expecting Chromium revision **1234**) does not match the pre-installed **1194**. Confirmed by
running `frontend/e2e/verify-069-073.mjs` unmodified: it fails immediately with
`Executable doesn't exist at /opt/pw-browsers/chromium_headless_shell-1234/...` and prints the
"please run playwright install" banner. **Do not follow that banner's advice in this container.**
Instead launch with an explicit `executablePath` pointed at the pre-installed binary:

```js
const browser = await chromium.launch({ executablePath: '/opt/pw-browsers/chromium' });
```

Two scripts now support this:

- **`frontend/e2e/cloud-board-screenshot.mjs`** (new, added this session) — always uses
  `executablePath` (from `$PLAYWRIGHT_BROWSERS_PATH/chromium`, default `/opt/pw-browsers/chromium`).
  Takes a full-page screenshot of the board against an already-running dev server:
  ```
  node e2e/cloud-board-screenshot.mjs --url http://localhost:5199 --out board-cloud-YYYY-MM-DD.png
  ```
  Screenshots land in `frontend/e2e/artifacts/`, which is tracked.
- **`frontend/e2e/smoke.mjs`** (existing, one line changed this session) — now honors an optional
  `PLAYWRIGHT_CHROMIUM_PATH` env var; unset, behavior is identical to before (plain
  `chromium.launch()`, correct on any machine where the pinned revision is actually installed):
  ```
  PLAYWRIGHT_CHROMIUM_PATH=/opt/pw-browsers/chromium node e2e/smoke.mjs --url http://localhost:5199 --no-server
  ```

`frontend/e2e/verify-069-073.mjs` was **left unmodified** (it's a one-off provenance record per
its own docstring) — it will hit the same executable-path failure if run here; use
`cloud-board-screenshot.mjs` instead for new cloud screenshots.

### What the captured screenshots show (looked at directly, not just captured)

- `board-cloud-2026-07-29.png` — Board tab, league selector reads "WESTWOOD · yahoo · snake",
  header line reads `fantasypros_csv_2026draft · half ppr · preseason moving · generated
  2026-07-28T04:41:54... · 511 players loaded`. Table renders real ranked rows (Bijan Robinson #1
  RB ATL, Ja'Marr Chase #2 WR CIN, Jahmyr Gibbs #3 RB DET, ... through row 17), with populated
  PROJ (CI), CONS, Δ, VBD, and TIER columns. Not an empty state, not a 404, not a loading spinner.
- `draftroom.png` (from `npm run smoke`) — Draft tab, "DRAFT LIVE" badge, "Mark pick 5 (team 5)",
  Position Scarcity panel with real tier counts and pace text ("All 2 remaining tier-1 RB sit
  under 50% to reach pick 18..."), My Roster showing Jahmyr Gibbs drafted at RB, Picks history
  strip (3, 18, 23, 38...). Confirms the full draft loop (pick entry, board update, roster/scarcity
  recompute) renders with live data, not just the landing screen.

---

## `npm run smoke`

```
PLAYWRIGHT_CHROMIUM_PATH=/opt/pw-browsers/chromium node e2e/smoke.mjs --url http://localhost:5199 --no-server
```

(`--no-server` reuses the already-running dev server rather than spawning a second one on the
default port 5173.)

**Result: 18/19 checks passed.** The one failure — "no console errors during the loop" — is caused
by the same missing-`ANTHROPIC_API_KEY` condition noted above (`ERR_CONNECTION_RESET` / 404 from
`server/proxy.ts`'s reasoning endpoint), not an app regression. Every board- and draft-room-specific
assertion passed, including the thread-063 regression checks (suggester never reopens after a
commit, stays closed across tab-switch/reload/undo) and the layout checks (mode switcher inside
viewport, refresh button sized correctly).

---

## Known gaps / non-blocking findings from this session

1. **Frontend unit test count is stale in `docs/CURRENT-STATE.md`.** Recorded: 192 passing / 2
   red-by-design. Measured this session: 202 passing / 0 failed. Not corrected here — outside this
   session's file boundary (`docs/CURRENT-STATE.md` is another chain's).
2. **`PLAYWRIGHT_SKIP_BROWSER_DOWNLOAD` was not actually set** in this container's environment at
   session start (checked directly: empty). `PLAYWRIGHT_BROWSERS_PATH` was set. Practical effect is
   the same — do not run `playwright install` regardless of which env vars are present, since the
   proxy blocks the download and it will hang.
3. **Pinned Playwright browser revision (1234) does not match the pre-installed one (1194).** Not
   fixed at the package-pin level (that's a `package.json`/lockfile change with wider blast radius
   than this task's scope) — worked around per-script via `executablePath`, documented above.
4. **The reasoning proxy has no graceful path when it cannot reach the network at all** (as opposed
   to "no API key," which it does handle) — it currently surfaces as a raw connection error rather
   than the designed "reasoning unavailable" response. Does not affect any data screen. Not
   investigated further or fixed (out of this session's scope; reported for the owning chain to
   queue if worth fixing).

---

## Bottom line

**Yes — the full frontend loop runs in this cloud container: install, typecheck, unit tests, dev
server, and a real Playwright screenshot a human has looked at.** The one piece that needed a
deliberate workaround is the screenshot step, because the pinned Playwright package expects a
Chromium build the container doesn't have and can't download — solved with `executablePath`
against the pre-installed binary, not with `playwright install`. That workaround is now captured in
`frontend/e2e/cloud-board-screenshot.mjs` and as an opt-in env var in `frontend/e2e/smoke.mjs`, so
the next cloud session does not have to rediscover it.
