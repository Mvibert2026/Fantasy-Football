# 2026-07-29 — frontend — draft-hub fold-in, ADP verification, four screenshot backlog threads

**Scope, per the dispatch:** `frontend/**`, `docs/handoffs/` replies on 027/028/029/041/082 only,
this file. Not touched: `src/`, `tests/` outside frontend, `.claude/`, `docs/pm/`,
`docs/CURRENT-STATE.md`, `docs/design-*`, `wrangler.jsonc`, `.github/`, `scripts/`.

Three jobs, worked in order.

## Job 1 — fold Opponents and Predictions into the draft hub

Premise checked before acting: `DraftRoom.tsx` really did carry three honest "not wired into Draft
mode yet" placeholders (thread 049 item 1's tab shell), and `Opponents.tsx`/`Predictions.tsx` really
were complete, shipping, tested screens elsewhere in the app (Prep mode) — the task's framing held.

**What each screen needs, checked before wiring, not assumed:**
- `Opponents.tsx` takes `{ data: Dataset }` — `DraftRoom` already holds `data` in scope.
- `Predictions.tsx` takes `{ data, rows, league }` — `DraftRoom` already holds all three.
- `Predictions` reads its pick state via `loadDraftState(leagueId)` from the exact same
  `localStorage` key (`ui/data/draft.ts`'s `prep.draft.<leagueId>`) `DraftRoom` already writes to
  via `saveDraftState` on every commit — so folding it in makes it genuinely live, not merely
  present. Verified this by recording 5 picks via the Board tab's digit shortcuts, then switching to
  the Predictions tab in the same session: header moved from "Live availability at pick 3" to "...at
  pick 18," every row's `LIVE` column moved from `not yet` to a real computed percentage, and the 5
  taken players dropped out of the row list. Screenshots:
  `frontend/e2e/artifacts/09-draft-room-after-5-picks.png` /
  `10-predictions-after-5-picks.png`.
- `Opponents.tsx`'s roster/`next #N` picture is sourced entirely from `data.rosters`
  (`rosters.json`) — a backend export built from real, `is_mock=0` picks. Read `ui/data/draft.ts`
  directly and confirmed there is no `fetch`/`POST` anywhere in it: nothing recorded in a live
  Draft-mode session (real tracking or a practice mock) ever reaches the backend, so this tab's
  cards do not move when a pick is recorded in the pane next to it. This is real data
  (`rosters.json` exists, is not "missing"), not a hollow mount — but it is a genuine
  live-vs-static disconnection the founder's "hook up to draft" framing could reasonably expect
  didn't exist. Rather than mount it silently, added one caveat line above the real cards
  (`AdaptedOpponentsPane` in `DraftRoom.tsx`) stating plainly what the tab does and does not track.
  This is the "verify what each screen needs, say so rather than mounting hollow" instruction
  applied to a *connection* gap instead of a *data* gap — there was no case here where a screen
  needed to be left out entirely; both screens' underlying data genuinely exists.

**Built:** `frontend/ui/views/DraftRoom.tsx` imports `Opponents`/`Predictions` (both unmodified,
read-only) and renders them in the two tab bodies that previously read "not wired into Draft mode
yet." New test coverage in `frontend/ui/__tests__/draft-room-recommendation.test.tsx` replaces the
old "shows placeholder" assertions with real-content assertions (heading text, caveat text, absence
of the old placeholder strings) plus a new test for the live-linkage scenario above.

**Stale-doc finding, reported not fixed (out of this session's file boundary):**
`docs/CURRENT-STATE.md`'s "Not built / null-stated" section lists "Predictions tab (**absent from
the shipped app**)." `frontend/ui/views/Predictions.tsx` is a real, complete, tested file and has
been since thread 028's build session (2026-07-27) — it was already reachable from Prep mode's
sidebar before this session touched anything. This line was already stale before this session; now
also folded into Draft mode. Flagging for whoever next edits that file in place.

## Job 2 — ADP display verification (FR-024, thread 082, contract 1.14.0)

**Premise checked first.** `docs/CURRENT-STATE.md`'s build-state table said this was "partially
landed already ... unverified, no screenshots taken." Found the actual state: the wiring across
`board.ts`/`contract.ts`/`trace-fields.ts`/`types.ts`/`Board.tsx`/`PlayerDetail.tsx`/`DraftRoom.tsx`
was **already complete** in this worktree (landed by a concurrent chain across commits
`b6d5a0d`/`75bf095`, this project's documented "coordinator commits in-flight work" pattern — `git
diff HEAD` against those files was empty before I touched anything else). This session's job 2 work
was verification and screenshot capture, not new construction.

**Read every ADP code path directly, not just the diff, and confirmed:**
- All three screens (`Board.tsx` prep board, `DraftRoom.tsx` draft room, `PlayerDetail.tsx` player
  profile) render `adp`/`adp_source`/the proxy caveat, each with its own honest-null treatment
  (`—` on the board/draft-room cells, a full-sentence "No MFL ADP data for this player..." block on
  the player profile).
- The null case is never `0` or an ambiguous dash-without-explanation — every null cell/block
  carries a `title`/inline text naming the reason (MFL's ~230-player coverage limit).
- Never confused with `consensus_rank`: `AdpCell`/`AdpBlock`/`DraftRoomAdpCell` read `row.adp`
  exclusively; the pre-existing `CONS`/`Δ` columns are untouched and visually and semantically
  separate, with code comments in both `Board.tsx` and `DraftRoom.tsx` recording that this was a
  deliberate choice, not an oversight.
- Never presented as this league's own ADP: every label/tooltip/caveat says "MyFantasyLeague proxy"
  or "not this league's own ADP" verbatim.

**Screenshots** (11 total, `frontend/e2e/artifacts/`, all real Playwright captures against a running
dev server, each looked at directly — not just captured): prep board with populated + null ADP
cells, player detail with populated + null MARKET ADP blocks, draft room board tab with inline
`N.NᴹFL` figures and a null case in the tiered RB view, the refresh panel confirming the app is on
contract 1.14.0 with no mismatch.

**Real gap found and flagged, not fixed:** no dedicated `adp.test.tsx` exists. Rendering is covered
incidentally by the general board/draft-room/player-detail suites (all still pass against real
exported data), but nothing asserts the null-vs-populated distinction or the source-label text
directly. Flagged in the thread 082 reply as follow-up, not addressed this session (time budget
went to the fold-in and the four-thread screenshot backlog).

## Job 3 — screenshot the four threads blocked only on compositing

All four (027 Opponents, 028 Predictions, 029 frequency array/tier grouping, 041 frontend WIP
repair) had every "Done looks like" item met except a screenshot, each explicitly blocked by the
same environment limitation ("the Browser pane is not displayed, so the page is not compositing
frames"). That limitation does not exist in this cloud container
(`docs/frontend-cloud-runbook.md`'s `executablePath` workaround against the pre-installed Chromium
at `/opt/pw-browsers/chromium`). Captured and looked at real screenshots for all four, replied on
each thread with the artifact paths and a description of what each image actually shows (league
name, row counts, honest-null examples), and set `STATUS: RESOLVED` on all five threads this
session touched (027, 028, 029, 041, 082) — all five are `TO: frontend`, so this session held the
authority to resolve them, per `docs/handoffs/README.md` rule 6.

## Evidence

**Screenshots** (`frontend/e2e/artifacts/`, 15 new files + 1 new capture script,
`verify-hub-and-adp.mjs`) — see the individual thread replies (027/028/029/041/082) for what each
one shows in detail; not re-duplicated here.

**Tests:** 203 passed, 0 failed, 22 test files (`npm test`, 2026-07-29) — up from 202 baseline (one
net new test added, `draft-room-recommendation.test.tsx`'s live-linkage case). `npx tsc -b --noEmit`
clean.

**Pre-existing, unrelated failure noted, not fixed:** `python tools/handoffs.py check` fails on an
ADR-054/ADR-055 cross-branch numbering collision (`docs/decisions.md`) — confirmed via `git stash`
that this predates every change in this session (present on the untouched `75bf095` HEAD too). Out
of this session's file boundary (`docs/decisions.md`) and out of scope for a frontend chain to
resolve unilaterally — a cross-branch ADR-number collision is exactly the "contradiction between two
docs" class of thing this project's rules say to escalate, not silently fix.

## Not done, flagged for follow-up

- No dedicated `adp.test.tsx` (see Job 2).
- `docs/CURRENT-STATE.md`'s stale "Predictions absent" line (see Job 1) — outside this session's
  file boundary, reported not corrected.
- Thread 049's remaining items (6, 7, and the rest of item 1's design polish — `DRAFT LIVE`
  indicator styling, richer league selector) were not touched; thread 049 itself is outside this
  session's handoff-reply boundary (027/028/029/041/082 only) even though item 1 is now functionally
  closed by this session's job 1 — noted here so the thread's owner can update it, not updated
  directly.
