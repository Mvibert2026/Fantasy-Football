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
