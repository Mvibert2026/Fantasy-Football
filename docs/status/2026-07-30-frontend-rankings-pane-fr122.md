# 2026-07-30 — frontend — rankings pane (design round-1 item 6) + FR-122

Worktree `agent-a9e24c92a40214afb`, branched from `main` @ `5e82225`.

## Dispatch

Design round-1 item 6 (`docs/design/RANKINGS-PANE.md`) plus FR-122, folded together per FR-122's
own file ("it lives in the same component as item 6... fold it into the item 6 dispatch"). Three
things, all required to ship together:

- **A.** The missing PLAYER column at 1180px width.
- **B.** FR-122 — typing a player name filters the rankings list.
- **C.** The light-theme row treatment, shipped on `Board.tsx` earlier the same day, not yet
  ported to this screen.

## What I found

The "rankings pane" is `DraftRoom.tsx`'s board-list column (RANK/PLAYER/POS/TM/ADP/Δ/VBD/AVAIL) —
confirmed by matching the exact column set the design screenshot showed, not `Board.tsx`'s own
Prep-mode table (different columns: RANK/PLAYER/POS/TM/BYE/PROJ/CONS/ADP(MFL)/Δ/VBD(CI)/TIER).

**Root cause of A:** the PLAYER cell was `flex: 1, minWidth: 0` — a flex child with no floor at
all. Once this pane's own share of the layout-mode grid (`paneColumns()`, 22-52% of the window
depending on Board/Balanced/Decide mode) got narrower than the sum of every other column's fixed
width, PLAYER's resolved width went to (near) zero. `Board.tsx` had already solved exactly this
problem with a real CSS Grid (`GRID_TEMPLATE`, `minmax(180px,1fr)` for its own PLAYER column) —
I ported that pattern rather than inventing a new one: `DRAFT_LIST_GRID_TEMPLATE`, one shared
template consumed via `display: grid` by both the header and every row, PLAYER as
`minmax(64px,1fr)`. Also moved the header inside the same scrollable element as the rows
(`position: sticky`, `Board.tsx`'s own technique) so a pane narrower than the template's minimum
scrolls header and rows together rather than letting them drift apart — which incidentally
satisfies RANKINGS-PANE.md item 3 ("one grid, one column definition") as a side effect, though
item 3 wasn't separately in this dispatch's scope.

**FR-122 (B):** the founder's own "one control, two jobs" — reused the existing pick-entry text
field (`query`, already there for RETROFIT-5's digit-key commit flow), not a new input. New
`ui/data/playerSearch.ts` folds diacritics/punctuation and matches name, team, position, and
`positionalLabel` (`RB10`), so `RB1` narrows to RB1/RB10-19 rather than nothing — the FR's own
named example, verified against the real 511-player board (508 available → 78 match). A non-empty
query searches the full board rather than being additionally constrained by the selected position
tab — the only reading consistent with the FR's own RB1 example (if the QB tab were selected,
"additionally constrained" would make RB1 return zero). Never auto-selects or auto-commits; an
honest empty state replaces a silently blank list.

**C:** ported `Board.tsx`'s `BoardRowLine` row-shading pattern verbatim — alternating
`var(--row-alt, transparent)`, `var(--row-line, var(--line))` hairline fallback, `var(--panel2)`
for the row with its inline detail open. No new values invented.

## Two things I got wrong mid-session, corrected before finishing

1. **A regex escape false alarm turned out fine** — the diacritic-strip regex
   (`[̀-ͯ]`) rendered oddly in my own editor output but verified correct via a direct
   Node check before trusting it.
2. **Real mistake, not corrected, disclosed instead:** this container runs multiple agents
   concurrently sharing the same filesystem. A dev server already listening on port 5199 turned
   out to belong to a *different* worktree (`agent-ae11859768ad7e400`) — caught before trusting
   any screenshot from it, via `/proc/<pid>/cmdline`. I moved my own server to port 5220. While
   cleaning up afterward I ran `kill` against a PID I'd misread from an earlier `ps` listing and
   killed that *other* agent's server, not my own. Not reversible from here. Flagged in
   `CURRENT-STATE.md` so that session (or PM) knows to restart it if still needed. No other file
   or process was touched.

## Verification

- `npx tsc -b --noEmit`: clean.
- Full suite: **484 passed, 0 failed, 63 files** (459 baseline + 25 new). One test
  (`draft-room-search-filter.test.tsx`'s RB1 case) timed out at the default 5000ms on the first
  full-suite run under measured heavy CPU contention (`load average: 9.32` on 4 cores); passed
  cleanly standalone and on every rerun. Raised its own timeout to 15s rather than weakening the
  assertion.
- New tests: `ui/__tests__/playerSearch.test.ts` (9, pure matching-logic), `draft-room-rankings-
  pane-width.test.tsx` (5 — a width-based structural assertion on the grid template, the kind that
  would have caught the original defect), `draft-room-search-filter.test.tsx` (8),
  `draft-room-row-shading.test.tsx` (3).
- Screenshots, looked at directly, both themes, both widths:
  `frontend/e2e/artifacts/rankings-pane-01-wide-dark.png` through `-07-search-no-match.png`.
  `-04-1180w-light.png` is the hardest combination (A+C together) and shows both working.
- `frontend/e2e/verify-rankings-pane.mjs`: new, reusable script covering all three items.

## Not built (out of this dispatch's explicit A/B/C scope)

`RANKINGS-PANE.md` item 2 — dot-string removal, the MFL superscript moving to the header, mono→UI
font on POS/TM/headers, hover-only reveal for the star/✕ icons. All named by design as the
"cheapest" width win and explicitly tied to item 1 in the spec's own reasoning, but the dispatch
that sent me here scoped exactly A/B/C, and item 2 is a look-and-feel change with real visual
surface area (a font-family swap, an icon-interaction change) I judged out of bounds for an
unprompted addition. Left `docs/design/RANKINGS-PANE.md`'s own `STATUS: OPEN` — not this session's
call to close a design doc that's only two-thirds done.

## Commit

See `git log` for the hash; frontend files only (`DraftRoom.tsx`, `ui/data/playerSearch.ts`, four
new test files, `e2e/verify-rankings-pane.mjs`), plus this file and the `CURRENT-STATE.md`/
`FR-122` doc updates.
