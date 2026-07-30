---
ID: 115
FROM: backend
TO: frontend
STATUS: OPEN
BLOCKS: none
OPENED: 2026-07-30
---

## Ask
Design (`docs/design/TWO-VALUE-COLUMNS.md`) blocked on one contract question for the second
value column (`vs your options`, FR-115/FR-118): is it an export field or a client computation?

**Answer, full writeup at `docs/ranking/vs-your-options-contract.md`:** client computation. No
export field, no `contract_version` bump, no backend build.

Every non-live-roster input already ships:
- `board.json:players[].position` / `.projected_points` / `.vbd` — all 510 players (QB/RB/WR/TE),
  not a top-N slice (`src/export_contract.py:412,424,443`).
- `league.json:roster.starters` (includes synthetic `FLEX` key), `roster.flex_eligible`
  (`src/export_contract.py:848-849`).

The one input this computation depends on that does *not* exist in any export — live roster
state (which slots are filled, who's still on the board) — is not supposed to. `board.json`/
`availability.json` are static, pre-draft snapshots; they cannot know a draft that hasn't
happened yet. That's browser-only state, same place `docs/handoffs/002-per-pick-draft-state.md`
already scopes it. Confirms design's own structural argument.

Prep-board empty-roster `—` rendering (design's constraint 3): trivially achievable client-side
off the same "any picks made yet" session flag the app already needs for other draft-state
logic. No export concern.

**#35/#36 reconciliation (read `docs/ranking/vs-your-options-contract.md` §3 in full):**
`vs your options` is NOT the quantity either test measured — #35 changed the replacement-level
constant feeding every player's VBD globally (roster-independent); #36 changed a forward-looking
selection *policy* reasoning about a future turn. `vs your options` is roster-conditioned,
immediate, and purely informational — it never reorders the board or the Recommend pane. So
CLAUDE.md §6.5's baseline rule doesn't technically bind it (that governs ranking versions), but
its spirit does: this is the same underlying hypothesis (flex-aware valuation beats plain VBD)
restated as a display feature, and two independent pre-registered tests of that hypothesis came
back NULL at this project's current sample size. Ship the honest caption text verbatim from
§3 of the writeup (or materially equivalent) on the `vs your options` header/tooltip so the
column doesn't imply a proven edge that wasn't found.

**FR-115/FR-118:** FR-118 ("show me both numbers") — fully satisfied by design's spec plus this
answer. FR-115 ("TE over-suggestion from pure VBD") — only *partially* satisfied. Showing the
second column lets the founder see a TE's weak `vs your options` number, but it does not change
which player the Recommend pane surfaces first (design's spec: rankings never move), and the
only tested fix to the ranking itself (#35) came back NULL. The ranking-side fix for FR-115
remains open — that's a `strategist`/`ranker` methodology question, not resolved by this ticket.

## Why
Design is blocked on exactly this question before building `TWO-VALUE-COLUMNS.md`. Answering it
unblocks the build with zero backend dependency — frontend can start immediately against the
current export, no waiting on a contract bump.

## Done looks like
Frontend implements `vs your options` as a client computation per the writeup, ships the honest
caption text (or materially equivalent) on the column header/tooltip, and confirms the Prep-board
`—` behavior. No backend artifact is required to close this from backend's side — this thread is
DONE once frontend has read and acknowledged the answer (reply here), even before the UI ships.
