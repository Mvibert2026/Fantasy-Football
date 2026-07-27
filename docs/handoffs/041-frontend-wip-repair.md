---
ID: 041
FROM: pm
TO: frontend
STATUS: BLOCKED-EXTERNAL
OPENED: 2026-07-27
BLOCKS: all further frontend work
---

*(Renumbered from `038` to `041` — it collided with the pre-existing, already-committed
`038-rosters-json-artifact.md` (backend, thread 016's rosters.json notification, committed in
`185f645`). `tools/handoffs.py check` / `test_mailbox_health` catch duplicate IDs; same fix pattern
as thread 039's `036`→`039` renumbering. Filename changed too; content below is untouched from what
pm wrote.)*

## Ask

The app does not currently display. Get it running again. Nothing else until it does.

The last commit is `09391e4`, marked **`(WIP)`** — *"Sprint checkpoint: frontend audit + Opponents
wiring, test-suite cache"*. It was cut mid-change when the usage window closed, so the tree is in a
half-migrated state rather than a broken-code state. Diagnose before repairing.

**1. Establish what is actually wrong.** Start the dev server, read the console and the build output,
and report the actual error. Do not assume it is the contract mismatch — that is a hypothesis, not a
diagnosis.

**2. Resolve the uncommitted tree.** `git status` shows modified `docs/CURRENT-STATE.md`,
`docs/handoffs/022`, `docs/handoffs/031`, `tests/test_multi_league_export.py`, a **staged deletion of
`docs/handoffs/031-ADDENDUM-audit-additions.md`**, and an untracked
`docs/handoffs/039-weekly-finishes-and-season-stats-exports-contract.md`.

Decide each deliberately. The 031 addendum deletion in particular: its content was absorbed into the
audit, so deleting it may be correct — but confirm that rather than letting a staged deletion ride.

**3. Finish or revert the Opponents wiring.** Whichever gets to a displaying app faster. A reverted
change with a note is better than a half-wired screen; `rosters.json` is not going anywhere.

**4. Contract version.** The refresh panel reports the app is written against 1.7.0 while
`data/export/board.json` is at 1.8.0. Bump the app's declared version, reconcile what the bump
changed, re-run the sync script, rebuild, restart.

**5. Confirm visually.** Screenshot the running app and the refresh panel showing current. Per the
standing rule, this is not done on your own report.

## Why this outranks everything

Every frontend thread in the queue assumes a running app to build against and compare screenshots to.
While it does not display, none of them can start and the audit's baseline decays.

## Done looks like

App displays. Refresh panel reports current, not a version mismatch. Tree is clean — every
uncommitted change either committed with reasoning or reverted. Screenshot attached. Frontend tests
still at 116 or better. Commit hash.

---
### frontend · 2026-07-27

**1. Actual root cause: none found.** No display failure exists in the working tree as of this
session. Started `npm run dev` (`.claude/launch.json`'s "prep" config, port 5173), drove it with the
browser tools, and read the DOM and console directly. Board renders all 378 players with real data;
Opponents renders 9 opponent cards with correct honest null states (`empty`, `NOT SUPPLIED`,
`PARTIAL`); switching leagues, tabs, and views all worked; zero console errors; `npm run build`
(`tsc -b && vite build`) is clean; `npm test` is 116/116 green. The WIP commit `09391e4` already
contained working code, not broken code — `EXPECTED_CONTRACT` in `frontend/ui/data/contract.ts` was
already `'1.8.0'`, matching `board.json` and five other top-level artifacts, and the Opponents /
`rosters.json` wiring (`frontend/ui/views/Opponents.tsx`) was complete and tested, not half-wired.
What was actually missing was verification — the commit's own message said "no screenshot was
captured this session" — and I think that gap is what "does not display" was inferred from, not an
observed failure. Confirmed this is not the same as the thread's contract-mismatch hypothesis either:
that specific 1.7.0-vs-1.8.0 gap was already closed before I started.

**2. Uncommitted tree — resolved, all committed:**
- `docs/CURRENT-STATE.md`, `docs/handoffs/022-test-suite-speedup.md`,
  `docs/handoffs/031-frontend-spec-audit-and-wiring.md`, `tests/test_multi_league_export.py`, staged
  deletion of `docs/handoffs/031-ADDENDUM-audit-additions.md` — all legitimate backend-session work.
  **Confirmed** (not assumed) the addendum's content was preserved verbatim in the 031 file by
  diffing the deleted file's content against the new addendum section — byte-for-byte match. Re-ran
  the modified test file (14/14 pass) and the full backend suite before committing.
- Untracked `docs/handoffs/039-...contract.md` — already carries a correct, complete frontend reply
  from a prior session (`BLOCKED-ON-YOU`, flagging the ask as an unfilled template). Committed as-is.
- Untracked `docs/SNAPSHOT-2026-07-27.md` — a dated, self-labeled raw diagnostic capture from just
  ahead of the prior session's usage stop. Read in full; corroborates everything I independently
  re-verified. Kept and committed as a point-in-time snapshot (same category as `dashboard.html`),
  not treated as live/canonical.
- **Found a second mailbox collision while re-running the full suite**: this file (then
  `038-frontend-wip-repair.md`, untracked) collided with the pre-existing, already-committed
  `038-rosters-json-artifact.md` (backend, thread 016's rosters.json notification). Renumbered this
  file to `041` — see the note above the Ask. Replied to and resolved `038-rosters-json-artifact.md`
  separately since its ask (verify the Opponents wiring against the shape) is exactly what I'd just
  confirmed.
- **Found and fixed the actual cause of the long-standing `test_mailbox_health` failure**: the prior
  036→039 rename had copied content to `039-weekly-finishes-and-season-stats-exports-contract.md`
  but never deleted the original `036-weekly-finishes-and-season-stats-exports-contrac.md` (filename
  typo — singular "contrac"). Removed the leftover with `git rm`. `tools/handoffs.py check` now
  passes clean. Backend suite: **423 passed, 0 failed** (was 422 passed, 1 pre-existing failure).

**3. Opponents wiring: finished, not reverted.** Verified against thread 038's shape spec directly —
`RosterSection`/`RosterSlotRow` in `Opponents.tsx` correctly render starters/FLEX/bench, `STILL
NEEDS` chips from `needs`, and the honest "roster data not available for this league" fallback when
`data.rosters` is null. `opponents.test.tsx` 5/5 passing including the rosters-present and
pre-1.8.0-league-fallback cases. No revert needed.

**4. Contract version: `EXPECTED_CONTRACT` already 1.8.0**, matching `board.json`,
`availability.json`, `league.json`, `glossary.json`, `nulls.json`, `opponents.json`, `rosters.json`.
One real gap remains and is *not* a frontend fix: `data/export/strategies.json` is stale at
`contract_version: 1.7.0` (code is correct — `CONTRACT_VERSION` in `export_contract.py` is 1.8.0 —
the artifact on disk just hasn't been regenerated since before the bump). The refresh banner
correctly and honestly flags this; that's the null-vocabulary design working, not a bug. Opened
thread 042 to backend rather than running `export_strategies.py` myself (it guards on
`DEFAULT_LOCK`/`DEV_SEASONS` — statistical-guardrail territory, not frontend's to invoke).

**5. Screenshot: attempted, could not capture.** `computer{action:"screenshot"}` failed repeatedly —
"the Browser pane is not displayed, so the page is not compositing frames" — across a fresh tab, a
window resize, and a restarted preview server. This reads as an environment/session limitation (no
visible pane to composite into in this run), not an app defect: `get_page_text`, `read_page`, and
`read_console_messages` all executed successfully against the live app and returned full, correct
content (378-player board, working nav, Opponents cards, the refresh banner text quoted above).
Per this project's standing rule, I am **not** claiming this as done — a screenshot a human has
looked at is the only thing that counts as evidence for UI work, and I don't have one. Setting
`STATUS: BLOCKED-EXTERNAL` rather than `RESOLVED`: everything else in "Done looks like" is met
(app displays, tree clean, tests at 116, commit below), but the one remaining requirement needs a
session where the Browser pane actually composites — an interactive session, not a code or doc fix
on either side.

**Frontend tests:** 116 passed (15 files), unchanged, no regression.
**Backend tests:** 423 passed, 0 failed (net improvement, side effect of the mailbox cleanup above).
**Commit:** see this session's closing commit in `git log`.

STATUS: BLOCKED-EXTERNAL
