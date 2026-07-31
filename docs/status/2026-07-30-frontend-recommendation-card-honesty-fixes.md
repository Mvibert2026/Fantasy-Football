# 2026-07-30 — frontend — recommendation-card honesty fixes (3 defects, no measurement)

**Task:** ship the three recommendation-card fixes strategist ruled need no model change and no
evidence — `docs/handoffs/2026-07-30-recommendation-card-states-a-rule-the-code-does-.md`,
disposition in `docs/adr-drafts/ADR-DRAFT-suggested-pick-opportunity-cost-rule.md` §6.

**Verdict: built, pending screenshot verification.** Commits `dfb9a78` (items 1-2) and `7fa7eb9`
(item 3). 466 tests passing (459 baseline + 7 new), `npx tsc -b --noEmit` clean, `npm run build`
clean.

## Why

The founder read an inverted decision rule off the RECOMMENDED card during a live draft and was
right to. The card told him the tool picks a QB *because* the QB is more likely to still be
available later — backwards. The ordering function (`recommendation.ts:64-97`) cannot even see
availability; it takes `(row, round, unfilledPositions)`. The card was describing reasoning the
code does not perform. Fixing what the app *says*, not what it *does* — the ordering itself stays
gated on measurement (thread 111 measured its nearest relative at -106 to -126 roster points).

## What changed

1. **`DraftRoom.tsx:1005`** — *"That difference, not the point gap, is the reason for the order"*
   was false on every render (the ordering has no path to `availability.json`). Replaced with:
   *"Neither figure is an input to the order above -- the order is value over replacement plus
   three unbacktested constants."*
2. **`DraftRoom.tsx:960-961`** — `only` was hardcoded onto every survival percentage, so 71%
   rendered as "only 71%" — scarcity rhetoric on a number usually meaning the opposite, the
   proximate cause of the founder's misreading. Now neutral at every value: "N% likely to still be
   there at your pick at P."
3. **`DraftRoom.tsx:1915`** (board `AVAIL` column) — targeted `nextUserPick`, which equals
   `currentPick` while `userOnClock`, so it showed the probability of an event already resolved
   (the honest figure is 100%). New `boardAvailTargetPick = userOnClock ? followingUserPick :
   nextUserPick`; header now reads `AVAIL @ 18` instead of a bare, unlabelled `AVAIL`, so the board
   and the RECOMMENDED card (which already used `followingUserPick`) can never again show two
   different picks' numbers under one word. Applied the same fix to `watchRows`, `queueRows`, and
   `PeriodicTableGrid`'s `underHalf` (decide-and-log, logged to `docs/ideas-inbox.md` — the thread
   left this as the fixing agent's call) — same defect, same one-line target swap.

**Self-caught during screenshot verification:** the first attempt widened the `AVAIL` header
column (58px → 76px) to fit the pick number without wrapping. A before/after screenshot at the
same viewport showed this shrank `PLAYER`'s `flex:1` share and re-truncated real player names in
the header/rows — a regression this session didn't ask for and a prior session's `FR-055`/`FR-067`
fidelity work had specifically fixed. Reverted; the header text now wraps onto a second line inside
the original 58px, costing header-row height, not another column's width. Verified in a second
screenshot pass.

## Evidence

- `frontend/ui/__tests__/recommendation-card-honesty.test.tsx` — 7 new tests: the false sentence is
  gone and replaced with the true one (2), `only` never renders regardless of the wording used (2),
  and which pick `AVAIL` targets on-clock vs off-clock vs its tooltip (3).
- 2 existing header-text tests updated (`draft-room-scarcity-and-sort.test.tsx`,
  `glossary-header-hover.test.tsx`) for the no-longer-bare `AVAIL` label.
- Screenshots, looked at directly, dark + light, card + board, before + after (8 files) in
  `frontend/e2e/artifacts/rec-card-{before,after}-{dark,light}-{card,board}.png`. The before-dark
  card reproduces the founder's exact bug against real data at the real pick_sequence[0]=3: Bijan
  Robinson recommended over Ja'Marr Chase, card reads *"Bijan Robinson is 4% to still be there at
  18 and Ja'Marr Chase is 0%. That difference, not the point gap, is the reason for the order"* and
  *"only 4% likely to survive."* The board's `AVAIL` column at the same moment showed 75%/71% for
  the same two players at the *current* pick (3) — a third, different, unlabelled number. The after
  screenshots show all three replaced/aligned: the card's causal sentence gone, the wording neutral,
  and the board's `AVAIL @ 18` column matching the card's own 4%/0% for the same players.

## Not done, flagged not silently skipped

- The recommendation ordering itself (`recommendation.ts`) is unchanged — gated on H1-H3
  measurement per the ADR draft §5/§7 D-5, explicitly out of this thread's scope.
- `docs/CURRENT-STATE.md` (as read from the shared checkout, not this worktree's stale copy)
  attributes a `DRAFT_LIST_GRID_TEMPLATE` CSS-grid port of this same row list to a prior session
  that fixed the exact PLAYER-column flex defect this session found still present. No such
  identifier exists in `git log --all` from this worktree. Not investigated further (outside this
  session's scope) — logged to `docs/ideas-inbox.md` for PM/Verifier.

## Commits

- `dfb9a78` — items 1-2, `ui/__tests__/recommendation-card-honesty.test.tsx` (4 tests then, 7 after
  commit 2), before/after card screenshots.
- `7fa7eb9` — item 3, `boardAvailTargetPick` plumbing (board rows, header, `watchRows`,
  `queueRows`, `PeriodicTableGrid` call site), 2 updated header-text tests, before/after board
  screenshots, the screenshot script itself (`e2e/shot-recommendation-card-honesty.mjs`).
