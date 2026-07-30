# 2026-07-30 — frontend: founder feedback batch (FR-067, FR-079, FR-082, FR-083, FR-087)

Four founder-reported defects, dispatched directly (not via a handoff thread) as a numbered
batch: (1) player card ADP/historical-season figures not matching the selected league's scoring
format, (2) Opponents pane not scrolling, (3) draft-view column headers not aligning with rows,
(4) wanting round context alongside raw pick numbers. Worked section-by-section, verified each
with a real screenshot before moving on, per this session's own effort-discipline instructions.

## Numbering correction (see `docs/ideas-inbox.md` for the full note)

The task brief's FR numbers (074/076/084/077) were stale — a separate branch
(`claude/pm-agent-setup-gobxa0`, commit `ea141f4`) had already captured the same four founder
complaints, verbatim, under FR-079/FR-083/FR-082/FR-087. Cherry-picked those four files' real
content in rather than trust the brief's numbers (which would have collided with four different,
already-real founder requests) or self-allocate a third set.

## Item 1 — FR-079 / FR-083: player card ADP + historical-season format

**Not a frontend propagation bug.** `ui/data/board.ts` already reads whichever league's
`board.json` is currently loaded correctly — verified directly, no cross-league caching exists.
Traced both complaints to real backend gaps instead:

- `board.json:adp_source_note` hardcodes Westwood's own ruleset in its prose for every league
  (`src/export_contract.py`'s `_load_adp_snapshot` takes no `cfg` argument). Reproduced live
  against `espn_10_standard` (a real STANDARD/0-PPR league per FR-042/ADR-062): its export still
  says "this league scores half-PPR," verbatim, false.
- `season_stats.json`/`weekly_finishes.json` (`src/export_history.py`) compute a single fixed
  standard-PPR figure with no `scoring_cfg` parameter, and aren't exported per league at all —
  confirmed they only exist at the unprefixed top-level path.

Per the project's rule against approximating scoring outside the pipeline, did not re-derive
points client-side. Added `league.json:scoring_ruleset_note` (which DOES vary correctly per
league) as a second disclosure next to the ADP block, and a static caveat next to the
weekly-finishes heatmap and three-season table. Screenshot proving the resulting visible
contradiction (backend's ADP note says "half-PPR," frontend's new line says "STANDARD ruleset"):
`frontend/e2e/artifacts/fr083-player-card-standard-league-adp-block.png`.

Backend fix logged: `docs/handoffs/NEW-adp-and-history-not-league-scoring-aware.md` (pending
PM's ID allocation — this session did not self-allocate thread numbers, per its own dispatch
instruction). FR-079/FR-083 marked `IN PROGRESS`, not `SHIPPED` — the founder's actual ask (the
number being right) is still blocked on backend.

## Item 2 — FR-082: Opponents pane doesn't scroll

Coordinator corrected the brief mid-task: this is two separate components now (`Opponents.tsx`
Prep mode, `LiveOpponents.tsx` Draft mode), not one rendered twice — `LiveOpponents.tsx` was
added for FR-032 after FR-036 (the brief's source) was written. Checked both independently.

Prep mode was already correct (its `.view` wrapper already carries `overflow: auto`) — verified
with a real scroll screenshot, no code change. Draft mode's `hubTab === 'opponents'` branch in
`DraftRoom.tsx` genuinely had zero scroll container, unlike its sibling `predictions` branch;
fixed by adding the same `flex: 1, minHeight: 0, overflowY: 'auto'` wrapper. Verified against a
seeded 23-pick draft (10 team cards, two full rows) — before/after screenshots show rows 7-10
going from cut-off to fully reachable.

Logged, not fixed here: real feature divergence between the two components (typed team-name
override and behavioural-tendency fields exist only in `Opponents.tsx`) —
`docs/handoffs/NEW-opponents-and-liveopponents-have-diverged.md`, per the coordinator's explicit
instruction not to consolidate inside this task.

## Item 3 — FR-067: draft-view column headers don't align with rows

Two compounding causes, found by reading the header and row code side by side and confirmed by
testing at two viewport widths: (a) the header stopped after AVAIL while every row rendered three
more fixed-width trailing elements (dots array, watch star, "mark taken" x) the header never
accounted for — since both share one `flex: 1` PLAYER cell absorbing leftover space, this gave
PLAYER (and everything after it) a different width in the header than in a row, a constant offset
at every viewport width; (b) some rows conditionally omitted their AVAIL/dots cells entirely when
there was nothing to show, drifting rows from each other too.

Fixed with one shared `DRAFT_LIST_COLS` width table consumed by both the header and every row,
including reserved (unlabeled) slots for dots/watch/taken, and rows that always render every
column's slot (with a neutral state inside when empty) instead of omitting elements.

Verifying at a second, narrower viewport (1180px, per the ticket's own instruction) surfaced a
real regression from this fix itself: the header's `minWidth: 0` (needed so it shrinks exactly
like a row) let its short "PLAYER" text overflow into POS under space pressure, since it lacked
the row's `overflow`/`whiteSpace` handling. Fixed by matching it. This is exactly the kind of
defect the ticket's "verify at more than one width" instruction exists to catch — it would not
have been visible at the default 1500px screenshot alone.

## Item 4 — FR-087: think in rounds, not only pick numbers

Added `pickWithinRound`/`roundPickLabel` (`ui/data/draft.ts`) beside the existing `roundOfPick` —
display-only formatters ("R3.03") reading `teams` from league config at every call site, never
hardcoded. Threaded into every bare-pick-number display found across the app: draft room's ON THE
CLOCK/YOUR NEXT badges and LIKELY BEST AVAILABLE/LIKELY THERE AT headers; both Opponents
components' "next #N" badges; the player detail sheet's availability section and five-pick strip;
Predictions' header. Left `RoundGrid.tsx` alone — it's already organized one row per round, so a
per-cell label would be density noise, not new information (Principle #4).

## Evidence

Screenshots (all in `frontend/e2e/artifacts/`, script `frontend/e2e/verify-founder-batch-
2026-07-30.mjs`): `fr082-prep-opponents-{top,scrolled}.png`, `fr082-draft-opponents-{top,
scrolled}.png`, `fr067-fr087-draft-board-{1500w,1180w}.png`, `fr067-draft-board-scrolled-
1180w.png`, `fr083-player-card-{westwood,standard-league}-adp-block.png`, `fr079-player-card-
westwood-history.png`, `fr087-clock-badges.png`. All looked at directly, not just captured.

`npx tsc -b --noEmit` clean throughout. Full suite, measured after all edits: **277 passed, 0
failed, 30 test files.** This session added 2 new test cases to `draft.test.ts` (8 → 10, covering
`pickWithinRound`/`roundPickLabel`) and updated 2 existing assertions in
`opponents.test.tsx`/`draft-room-middle-pane-tabs.test.tsx` to match the new round-label text —
did not independently measure a pre-edit baseline (edits were already in place before the first
full run this session), so this is the verified final state, not a stated delta. Green after
every commit split, not just at the end.

## Commits (5, in dependency order)

1. `0ee5556` — FR-079/FR-083 (PlayerDetail.tsx disclosure, handoff thread, screenshots)
2. `583dfc2` — FR-082 (scroll wrapper, handoff thread, screenshots)
3. `750447d` — FR-067 (shared column table, header overflow fix, screenshots)
4. `5dc183e` — FR-087 (round-label helpers + every call site, new/updated tests, screenshot)
5. `7b81fae` — FR status updates (SHIPPED/IN PROGRESS) + `founder-requests/INDEX.md` sync

Split via `git apply --cached` against hand-filtered hunk subsets (verified `--check` clean at
each step, full suite re-run after the split, not assumed safe) rather than one bundled commit,
since `DraftRoom.tsx`/`PlayerDetail.tsx` each carry genuinely separate, spatially-distinct hunks
for different items.

## Not done this session

- Backend fix for FR-079/FR-083's actual root cause (see handoff thread).
- Consolidating `Opponents.tsx`/`LiveOpponents.tsx` (see handoff thread).
- The 16 pre-existing threads in this session's `docs/handoffs/OPEN.md` inbox — out of this
  task's scope, not opened or replied to.
