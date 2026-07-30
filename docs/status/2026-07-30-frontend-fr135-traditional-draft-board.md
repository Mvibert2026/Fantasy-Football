# 2026-07-30 — frontend — FR-135: the traditional draft board

Worktree `agent-aaac1fbaf22827f67`. Branched from `main` at `5e82225`.

## The ask

Founder, direct: *"I want the periodic table draft board, not just a list of players - the grid is
dumb - I want a traditional draft board - it's a grid (empty at first) that fills with picks as they
are made across the top is teams and then you have two views, one is the order of the pics, snaking,
and one is ordered by position."*

`docs/founder-requests/FR-135-traditional-draft-board-teams-across-the-top-fil.md` records why the
previously-shipped `PeriodicTableGrid.tsx` is a different artifact (32 NFL teams × 5 positions, fully
populated from first render — a catalogue of the player universe, not a record of picks). The
researcher's reference study, `docs/design/research/draft-board/FINDINGS.md`, verified Sleeper,
LiveDraftX and FanDraft and is what this build follows section-by-section (§4 is the spec).

## What was built

`frontend/ui/components/TraditionalDraftBoard.tsx` — new component, wired into
`frontend/ui/views/DraftRoom.tsx` as a fourth, additive hub tab ("Draft Board", alongside the
existing Board/Opponents/Predictions — none of the three changed; `draft-room-tabs-integrity.
test.tsx` still passes unmodified).

**Axis and empty state (FINDINGS §4.1/§4.2).** Managers across the top, rounds down the side, one
cell per pick, empty at the start. Every cell — filled or not — carries its own `round.pick` address
from first render (e.g. `3.07`), via a new `overallPickForRoundSlot(round, slot, teams)` in
`ui/data/draft.ts` (the exact inverse of the existing `teamSlotAtPick`; `pickNumbersForSlot` is now
defined in terms of it, same observable output — checked against the pre-existing `forwardPick` test
reference in `draft.test.ts`). Round 2's addresses run backwards across the row (rightmost column
lowest number) so the snake is legible from the numbers alone — nothing is drawn, matching FINDINGS
§2.3's "nobody draws the snake" finding.

**Two views (FINDINGS §4.5), and the founder/category divergence named, not papered over.**
- **Pick order (snaking)** — default. The literal ask.
- **By roster slot** — same manager columns, rows become roster slots (QB/RB/RB/WR.../FLEX/BN/IR),
  built from the existing `buildRosterSlots` (the same function `LiveOpponents.tsx`'s MY ROSTER panel
  already uses, called once with an empty pick list for the row template so every team's column lines
  up at the same row index, and once per team with that team's real picks for the fill).

The founder named view 2's purpose as *"the thing that tells you the RB room emptied in the third
round"* — FINDINGS §2.6 is explicit that the roster-slot view cannot answer that (it discards the
round axis). Rather than silently ship only the roster-slot view and let the founder discover the gap
live, both are built, and the stated purpose is answered on view 1 via a per-round positional tally
in the gutter (FINDINGS §4.5's "cheap addition") — counts only picks resolved to a real board row
(an off-board/typed pick cannot be honestly attributed a position, so it's excluded from the tally,
never guessed).

**Cell-content ladder (FINDINGS §4.3).** `surname + position colour` always — never gated behind any
width tier, the one rule FINDINGS states this project has already violated once (a different screen,
RANKINGS-PANE, dropped a name at 1180px). `+ first initial + pick number` at the `wide` tier;
`+ NFL team + bye week` at `wider`. No projection, VBD, or delta in any cell — unanimous across the
category per FINDINGS. This app has no CSS `@media` anywhere, so the ladder is width-tiered via a
small `useViewportWidth()` hook (window width + a resize listener) rather than a stylesheet — labelled
in the component doc as a window-width proxy, not a per-column pixel measurement, since the board
mounts as its own full-width hub tab with no competing side rail.

**Current pick marked three ways (FINDINGS §4.4).** The on-clock team's column header, the specific
cell, and a persistent "ON THE CLOCK" bar above the grid — all three visible at once, not a single
highlight.

**Narrow-width breakpoint switch (FINDINGS §4.6).** Below 880px window width the two-axis grid is
replaced by a list, never squeezed and never a frozen-column/scroll compromise (FINDINGS found no
product doing that). The un-listed axis becomes a horizontally-scrollable chip row — rounds for
pick-order, teams for roster-slot — mirroring LiveDraftX's own verified ROUND/TEAMS mobile split onto
this build's same two views. Deliberately set below 1180px: one of this dispatch's two required
screenshot widths is 1180, and it must still show the real two-axis grid, not the mobile fallback —
verified directly by a test.

**Never-fabricate (Principle #2, and FR-135's own explicit instruction).** A pick entered without a
board match (`playerId === null` — free-typed text, or the `AUTO_FILL_PLACEHOLDER` synthetic pick)
renders the typed text in neutral styling, never a guessed position colour. The auto-fill placeholder
is labelled `(auto-filled)` rather than shown as an ordinary name.

**Not deleted:** `PeriodicTableGrid.tsx` — FINDINGS §2.7 vindicates it as LiveDraftX's own fourth "NFL
Teams" view, a real, separate, shipped category pattern. Its own Grid pane tab, tests, and the
tab-integrity test pinning Recommend/Scarcity/Queue/Insights/Grid all pass unmodified.

## Verification

`npx tsc -b --noEmit` — clean. `npm run build` — clean.

Full suite: **485 passed, 0 failed, 60 files** (459 baseline measured fresh in this worktree before
any change; +26: 22 in the new `traditional-draft-board.test.tsx`, 3 new in `draft.test.ts` for
`overallPickForRoundSlot`, 1 auto-generated by `no-invented-numbers.test.ts`'s per-file sweep, which
also caught and fixed one real bug — a stray literal `${1}` in an on-clock-bar fallback string that
was never reachable in practice but had no export behind it).

## A real defect found by looking at the screenshots, not just capturing them

The mid-draft roster-slot screenshot (`tdb-07`) should have shown the off-board "Local Waiver
Pickup" pick (seeded at overall #13, team 8) somewhere on that team's bench. It did not — every
bench row for that team rendered an honest dash instead. Traced to `ui/data/rosterSlots.ts`'s
`buildRosterSlots`: its fill loop's first line is `if (pick.playerId === null) continue;`, so an
off-board pick is skipped outright and never occupies a slot — the function's own `target.slot =
"BN (name)"` rename branch a few lines later is unreachable dead code. **Pre-existing, not
introduced by this session** — `LiveOpponents.tsx`'s MY ROSTER and opponent cards already call the
same function and have the same gap. Confirmed directly with a debug test
(`buildRosterSlots` called in isolation, printed the raw output array) before touching anything.
Not fixed here (a board-layout dispatch is not the place to patch a function three existing screens
depend on without its own verification pass) — this component's own `offBoardName` handling in the
roster-slot view was simplified to stop implying the rename happens (it never does), and a
regression test now pins the honest current behaviour (`ui/__tests__/traditional-draft-board.
test.tsx`, "roster-slot view: an off-board pick occupies no slot"). Logged to
`docs/ideas-inbox.md`, 2026-07-30 frontend entry.

## Worktree base, flagged not fixed

This worktree (`agent-aaac1fbaf22827f67`) branched from `main` at commit `5e82225`, which predates
several sessions' work still visible on the shared/outer checkout — most consequentially, the
RANKINGS-PANE session's own edits to this same `DraftRoom.tsx`. `docs/founder-requests/FR-135-*.md`,
`docs/design/research/draft-board/FINDINGS.md`, and the researcher's handoff thread
(`docs/handoffs/2026-07-30-draft-board-reference-axis-unanimous-snake-never.md`) — all read and
followed for this build — do not exist anywhere in this worktree's own git history either, confirmed
directly (`ls`/`grep`, not assumed). This session could not reply to that handoff thread or flip
FR-135's own `STATUS:` to `SHIPPED`, because neither file exists on this branch to edit — recreating
them here risked a spurious merge conflict against main's real copies. A real merge (not a
fast-forward) should be expected when this branch lands; not resolved unilaterally, per the standing
rule that a merge conflict is escalated. Full detail: `docs/ideas-inbox.md`, 2026-07-30 frontend
entry.

New tests, by what they cover:
- Empty board renders full-sized before any pick, every cell addressed, snake numbering direction.
- A made pick shows real surname + position, sourced from the board row.
- An off-board/typed pick and the auto-fill placeholder both render honestly, never a fabricated
  position.
- Current pick marked in all three places at once.
- View toggle switches views; the roster-slot row template is one skeleton (not duplicated per team)
  and an unfilled slot renders `—`, never a fabricated player.
- **Width assertion at 1180px** (the exact width this project's own prior RANKINGS-PANE regression
  dropped a name at) — the surname still renders, and the compact tier's other fields (team/bye) are
  confirmed absent, i.e. *designed out on purpose*, not overflowing.
- A wide-width test (1700px) confirms the richer tier adds the team code back in.
- Mobile breakpoint switch: below 880px the grid is replaced by a list; at 1180px it is confirmed
  the mobile view is NOT engaged (the real grid still renders — this is the test the dispatch asked
  for by name).
- The new "Draft Board" hub tab is reachable and the original three tabs are unaffected.

Screenshots (13, looked at directly — not just captured), `frontend/e2e/artifacts/tdb-*.png`, via
`frontend/e2e/shot-traditional-draft-board.mjs`:

| # | File | Covers |
|---|---|---|
| 1 | `tdb-01-empty-pickorder-wide-dark.png` | Empty board, pick-order, wide, dark |
| 2 | `tdb-02-empty-pickorder-1180-dark.png` | Empty board, pick-order, 1180px, dark |
| 3 | `tdb-03-empty-rosterslot-wide-dark.png` | Empty board, roster-slot, wide, dark |
| 4 | `tdb-04-empty-pickorder-wide-light.png` | Empty board, pick-order, wide, light |
| 5 | `tdb-05-mid-pickorder-wide-dark.png` | Mid-draft (25 picks), pick-order, wide, dark |
| 6 | `tdb-06-mid-pickorder-1180-dark.png` | Mid-draft, pick-order, 1180px, dark |
| 7 | `tdb-07-mid-rosterslot-wide-dark.png` | Mid-draft, roster-slot, wide, dark |
| 8 | `tdb-08-mid-rosterslot-1180-dark.png` | Mid-draft, roster-slot, 1180px, dark |
| 9 | `tdb-09-mid-pickorder-wide-light.png` | Mid-draft, pick-order, wide, light |
| 10 | `tdb-10-mid-pickorder-1180-light.png` | Mid-draft, pick-order, 1180px, light |
| 11 | `tdb-11-mid-rosterslot-wide-light.png` | Mid-draft, roster-slot, wide, light |
| 12 | `tdb-12-mobile-pickorder-dark.png` | 420px width, pick-order mobile list |
| 13 | `tdb-13-mobile-rosterslot-dark.png` | 420px width, roster-slot mobile list |

The mid-draft seed logs 25 real picks (real board players, ids 1-25 in overall-rank order, verified
directly against `public/data/board.json`) plus one off-board typed pick (overall 13, "Local Waiver
Pickup") and one auto-fill placeholder (overall 24) so the never-fabricate rendering is visible in a
real screenshot, not just asserted in a unit test.

## Not built / deliberately out of scope

- Renaming or repositioning `PeriodicTableGrid.tsx` — FR-135's own doc says that's a founder decision,
  not a cleanup for this session.
- Typed opponent-name editing directly inside the new board (the existing Opponents-tab mechanism,
  `ui/data/opponentNames.ts`, is read here but not exposed for inline editing on this screen).
- Live cross-tab sync of typed opponent names into an already-mounted board (read once via
  `useMemo(() => loadOpponentNames(leagueId), [leagueId])`) — low risk, logged to
  `docs/ideas-inbox.md` rather than built speculatively.

## Files touched

- `frontend/ui/components/TraditionalDraftBoard.tsx` (new)
- `frontend/ui/views/DraftRoom.tsx` (new hub tab, additive)
- `frontend/ui/data/draft.ts` (`overallPickForRoundSlot`, `pickNumbersForSlot` refactored onto it)
- `frontend/ui/__tests__/traditional-draft-board.test.tsx` (new, 21 tests)
- `frontend/ui/__tests__/draft.test.ts` (+3 tests)
- `frontend/e2e/shot-traditional-draft-board.mjs` (new screenshot script)
- `docs/CURRENT-STATE.md`, `docs/founder-requests/FR-135-*.md`,
  `docs/handoffs/2026-07-30-draft-board-reference-axis-unanimous-snake-never.md` (this file's
  companions — see those for the exact diffs)
