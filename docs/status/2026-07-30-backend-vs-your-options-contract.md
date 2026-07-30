# 2026-07-30 — backend — vs-your-options contract answer

Dispatched to answer one contract question blocking design: does `docs/design/TWO-VALUE-COLUMNS.md`'s
second value column (`vs your options`, FR-115/FR-118) need a new export field, or can it derive
client-side from what already ships?

**Answer: client computation. No export field, no contract bump, no backend code.**

## What I checked

- Grepped `src/export_contract.py` and `src/make_board.py` (as the dispatch itself had already
  done) and confirmed the negative: no `vona`/`next_flex`/`flex_value` field exists.
- Read `board.json` off disk: 510 players across QB/RB/WR/TE, each carrying `position`,
  `projected_points`, `vbd` — enough to compute a candidate-vs-alternative comparison for any
  player, not just a top-N slice.
- Read `league.json`'s build path (`src/export_contract.py:848-849`): `roster.starters` (with a
  synthetic `FLEX` key) and `roster.flex_eligible` are already exported — the roster-shape half
  of the computation.
- The one missing input — live roster state (which slots are filled, who's still on the board) —
  is missing because it's supposed to be: `board.json`/`availability.json` are static, pre-draft
  snapshots that cannot know a draft that hasn't happened. That's browser session state, same
  place `docs/handoffs/002-per-pick-draft-state.md` already scopes it.

## The reconciliation (the part I was told to get right)

Read `docs/preregistration/PR-006-*`, `docs/ranking/valuation-tests-35-36-precommit.md`, and this
session's own recorded #35/#36 results in `docs/CURRENT-STATE.md` before answering. Built a
comparison table (in the writeup) across what changes, roster-dependence, time horizon, and
measured result for #35, #36, and `vs your options`. Conclusion: **different quantity** from
either test — #35 is a global, roster-independent replacement-level swap; #36 is a forward-looking
selection policy; `vs your options` is roster-conditioned and immediate, and never reorders
anything (design's own spec: rankings never move). CLAUDE.md §6.5's baseline rule doesn't
technically bind a non-ranking display feature, but its spirit does, because this restates the
same underlying hypothesis (flex-aware valuation beats plain VBD) that both pre-registered tests
found NULL for. Specified literal caption text for the column so it doesn't imply an edge that
wasn't found.

## FR-115 / FR-118

FR-118 ("show both numbers") is fully satisfied by design's spec plus this answer. FR-115 ("TE
over-suggestion from pure VBD") is only partially satisfied — the second column lets the founder
*see* a weak TE's `vs your options` number, but doesn't change which player Recommend surfaces
first, since the only tested ranking-side fix (#35) came back NULL. Flagged as open, belongs to
`strategist`/`ranker`, not resolved here.

## Deliverables

- `docs/ranking/vs-your-options-contract.md` — full written answer.
- `docs/handoffs/115-vs-your-options-contract-answer-client-computati.md` — thread to `frontend`,
  OPEN (waiting on their acknowledgment/build, not blocking on backend).
- `docs/CURRENT-STATE.md` updated in place with a new "Last verified" entry.

No export contract change, so no `tests/test_export_contract.py` additions, no `contract_version`
bump. Commit `4e50413`, 3 files changed (204 insertions), no test suite run required since no
production code changed — verified via `git diff --cached` and the marker-check gate before
committing.
