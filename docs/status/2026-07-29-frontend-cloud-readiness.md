# 2026-07-29 — frontend — cloud readiness verification

**Task:** answer, with evidence, whether the full frontend loop (install, typecheck, unit tests,
dev server, real screenshot) can run in this cloud container. Scope explicitly narrowed to
`frontend/**`, `docs/frontend-cloud-runbook.md`, `docs/ideas-inbox.md`, and this file — other
chains were active in `docs/handoffs/**`, `docs/pm/**`, `docs/environment.md`, `CLAUDE.md`,
`docs/CURRENT-STATE.md`, `.claude/**`, `scripts/`, `src/`, `tests/` and were not touched.

**Outcome: yes, with one worked-around gap.** Full detail and the recipe: `docs/frontend-cloud-runbook.md`.

## What was run, in order, stopping only where the task said to check

1. `npm ci` in `frontend/` — 6.2s, 184 packages, clean, no browser download triggered.
2. `npx tsc -b --noEmit` — clean, 0 errors.
3. `npm test` (vitest) — **202 passed, 0 failed, 22/22 test files.** Differs from
   `docs/CURRENT-STATE.md`'s recorded "192 passing / 2 pre-existing-red-by-design" (that line is
   dated 2026-07-26 and the paragraph around it is marked not-re-verified except for four unrelated
   bullets). Reported as a finding in the runbook, not silently reconciled, and not corrected in
   `docs/CURRENT-STATE.md` (outside this session's file boundary).
4. Dev server (`npm run dev -- --port 5199 --strictPort`) — started clean, served `GET /` 200 and
   `GET /data/board.json` with a real 511-player board.
5. Screenshot via Playwright — **hit a real red first**: the pinned `playwright` package expects
   Chromium revision 1234; the container's pre-installed binary is revision 1194 at
   `/opt/pw-browsers/chromium`, and `playwright install` is explicitly disallowed (blocked
   downloads). `frontend/e2e/verify-069-073.mjs` run unmodified confirmed the failure mode exactly
   (`Executable doesn't exist at .../chromium_headless_shell-1234/...`). Fixed by launching with an
   explicit `executablePath` against the pre-installed binary, per the task's own guidance. Wrote
   `frontend/e2e/cloud-board-screenshot.mjs` (new, always uses `executablePath`) rather than editing
   the provenance-marked `verify-069-073.mjs`. Captured
   `frontend/e2e/artifacts/board-cloud-2026-07-29.png` and **looked at it**: WESTWOOD league
   selected, header reads real provenance (`fantasypros_csv_2026draft · half ppr · preseason moving
   · generated 2026-07-28T04:41:54... · 511 players loaded`), table shows real ranked rows (Bijan
   Robinson #1 through row 17, Brock Bowers) with populated PROJ/CONS/Δ/VBD/TIER columns. Not an
   empty state.
6. `npm run smoke` — same executable mismatch, so added an opt-in `PLAYWRIGHT_CHROMIUM_PATH` env
   var to `frontend/e2e/smoke.mjs` (one line changed; default behavior unchanged when the var is
   unset). Ran with `PLAYWRIGHT_CHROMIUM_PATH=/opt/pw-browsers/chromium ... --no-server` against the
   already-running dev server. **18/19 checks passed.** The one failure (console-error check) is
   caused by the reasoning proxy (`server/proxy.ts`) having no `ANTHROPIC_API_KEY` in this container
   and failing at the network layer rather than resolving to its designed "reasoning unavailable"
   response — does not touch the board or draft room, both of which passed every assertion
   including the thread-063 regression table (suggester never reopens after a commit; stays closed
   across Escape, tab-switch, reload, undo). Looked at `draftroom.png`: DRAFT LIVE badge, real pick
   counter, Position Scarcity panel with real tier text, My Roster showing the drafted player.

## Decisions made without asking (per the founder's "decide and log" instruction this session)

- **Did not touch `docs/handoffs/**` or reply to the 15 open frontend inbox threads.** The task's
  explicit file boundary said other chains were active there this session; the standard end-of-
  session protocol (reply to every open thread, run `tools/handoffs.py sync`) was overridden by
  that explicit, narrower scope for this specific verification task. Not logged to
  `docs/ideas-inbox.md` (that file is described in-repo as PM-owned, append-only capture of raw
  founder remarks — this is a scope call, not a founder idea, so it goes in this status file
  instead, where the operating rules already expect session decisions to be recorded).
- **Edited `frontend/e2e/smoke.mjs` (one line) rather than leaving it broken in this environment.**
  Judged in-scope because the task explicitly asked to run it and report the result, and explicitly
  anticipated and prescribed the fix (`executablePath` over `playwright install`). Change is
  additive and env-gated — no behavior change anywhere the env var isn't set.
- **Left `frontend/e2e/verify-069-073.mjs` unmodified** rather than patching it too, since its own
  docstring marks it a one-off provenance record, not a maintained harness; added a new script for
  cloud screenshots instead.

## Evidence

- Commit: see `git rev-parse HEAD` after this session's commit (reported in the final reply).
- Test counts: 202 passed / 0 failed (vitest, frontend), `tsc -b --noEmit` clean.
- Screenshots: `frontend/e2e/artifacts/board-cloud-2026-07-29.png` (new),
  `frontend/e2e/artifacts/board.png` and `frontend/e2e/artifacts/draftroom.png` (regenerated by
  `npm run smoke` this session, both looked at directly, described above).
- Smoke: `frontend/e2e/artifacts/report.json`, 18/19 passed.

## Not done / explicitly out of scope this session

- `docs/CURRENT-STATE.md`'s stale test-count line was not corrected (not this session's file).
- The reasoning-proxy console-error gap was not fixed, only reported.
- No handoff threads were replied to; no ADR was opened (no methodology or architecture decision
  was made — this was operational verification).

---

## Task 2 (same session): standalone single-file board

Founder hit "localhost can't be reached" live — dev-server dependency is exactly what the cloud
move is meant to remove. Built `frontend/dist-standalone/board.html`: one file, all JS/CSS/data
inlined, opens via `file://`, no server, no network, no build step at the far end. Full recipe,
scope (in/out), and the real bug found and fixed along the way (a silently-failing `resolve.alias`
that shipped a real `fetch()` under a wrong assumption it had been eliminated) are in
`docs/frontend-cloud-runbook.md`'s new "Standalone build" section — not duplicated here.

Verified by opening the built file directly with Playwright over `file://` (never through a dev
server) and looking at the captures: `frontend/e2e/artifacts/standalone-board.png` (WESTWOOD,
half ppr, 511 players, real ranked rows through Brock Bowers) and `standalone-player-detail.png`
(full detail sheet, including the honest "Could not load weekly_finishes.json: not included in this
static snapshot..." state for the two sections deliberately not embedded). `e2e/verify-standalone.mjs`
also asserts zero non-`file://` network requests through both the initial load and opening
PlayerDetail — the second half of that check is what caught the `resolve.alias` bug; the first half
alone would have missed it.

## Task 3: phone-responsive layout — built, then reverted on explicit founder instruction

Built a responsive layer (`ui/styles/responsive.css`, an off-canvas Sidebar drawer, sticky Board
columns inside a horizontal-scroll container, 44px touch targets, a full-width PlayerDetail sheet)
against four phone/tablet viewports per the PM's dispatch. **Before this was verified or reported,
the founder pulled the request** — his actual ask was narrower ("optimize for phone viewing" read
as "build responsive layouts," which was an over-read), and his real position is that a mobile
layout on a deliberately dense board is a Design decision, not one to make ad hoc in the app
(FR-025).

**Reverted in full**, not left half-applied:
- `frontend/ui/styles/responsive.css` — deleted.
- `frontend/ui/styles/base.css` — `@import './responsive.css'` line removed.
- `frontend/ui/components/shell/Sidebar.tsx` — restored to its pre-work version exactly (diffed
  against `d0be35c^`, the commit before the WIP started, to confirm byte-for-byte match).
- `frontend/ui/App.tsx`, `frontend/ui/StandaloneApp.tsx`, `frontend/ui/views/Board.tsx`,
  `frontend/ui/components/shell/TopBar.tsx` — these were never committed (working-tree only) and
  were restored via `git checkout -- <path>` before anything captured them. The coordinator's revert
  instruction named only three files because those were the ones already committed and visible in
  the diff; the other four carried the same phone-only edits (hamburger button, sidebar-open state,
  touch-target classes) and were included in the revert on the same reasoning, not left behind on a
  technicality.

**Verified the revert, not just the diff**: full unit suite (202/202 still passing), clean
`tsc -b --noEmit`, and a real screenshot of the desktop app
(`frontend/e2e/artifacts/board-post-revert-2026-07-29.png`) — looked at directly: sidebar back at
full width with all seven Prep entries and the coming-soon list, all three mode buttons (Prep/Draft/
Season) present, board header carrying real provenance, table rendering real ranked rows. Matches
the pre-phone-work baseline screenshot exactly.

**Time cost:** the founder's own framing was "maybe twenty minutes, and it surfaced the real
answer" — not treating this as wasted effort, per his message.

## Task 4: Draft mode restored to the standalone build

The standalone build's first version excluded Draft mode on the assumption it needed a backend.
Challenged directly (the founder's own read of the code, which turned out right): checked
`ui/data/draft.ts` and `DraftRoom.tsx` for `fetch()` calls (none), confirmed the module's own
docstring already says "No backend call per pick," and confirmed "Export draft log" is a client-side
`Blob` download. Put Draft mode back into `ui/StandaloneApp.tsx` (mode switcher now shows Prep and
Draft; Season stays out, confirmed against `docs/CURRENT-STATE.md`'s "not built" listing — nothing
to restore there). Rebuilt the standalone artifact (1.07MB).

Verified with a new script, `frontend/e2e/verify-standalone-draft.mjs`, driving the actual
interaction over `file://`: switched to Draft mode, committed a pick via the digit shortcut (pick
counter 1→2, draft log recorded "Bijan Robinson"), undid it (2→1), triggered "Export draft log" and
confirmed it fires a `download` event rather than a network request, and asserted zero non-`file://`
requests through the whole sequence. All checks passed. Screenshots looked at directly:
`standalone-draft-room.png` (initial state — DRAFT LIVE badge, pick #1, full roster/scarcity/picks
panels, real snake sequence 3/18/23/...) and `standalone-draft-after-pick.png` (after the pick — pick
#2, board re-filtered to 510, draft log entry, scarcity recomputed).

## Evidence, tasks 2-4

- Commits: `1365c56` (standalone build), `833b168` (player-history fetch-bug fix), `d0be35c` (phone
  WIP, then reverted), `fcc1ef6`/`08d2c60` (revert + proof), `98a112b` (Draft mode restored). Final
  hash for this session reported in the closing reply.
- `frontend/dist-standalone/board.html`: 1.07MB, zero `fetch()` calls verified by both standalone
  e2e scripts.
- Unit suite: 202/202 passing after every change in this stretch (checked after the standalone
  build, after the fetch-bug fix, after the revert, and after Draft mode landed — not just once at
  the end).
