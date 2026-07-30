---
FROM: frontend
TO: frontend
STATUS: OPEN
BLOCKS: none
---

## Ask

Flagging for a future session, not fixing here (would collide with other frontend work in
progress in this codebase right now, per this session's own dispatch instructions).

`frontend/ui/views/Opponents.tsx` (Prep mode) and `frontend/ui/views/LiveOpponents.tsx` (Draft
mode) are two separate, hand-duplicated components covering the same concept — "here's what every
team's roster looks like and when they pick next" — that have already diverged in real,
user-visible ways:

- **Typed/overridden team names (FR-036).** `Opponents.tsx` has the full `OpponentNameField`
  click-to-edit affordance (typed name, "typed" tag, edit/clear controls, local per-league
  storage via `ui/data/opponentNames.ts`). `LiveOpponents.tsx` only reads `opponents.json`'s
  `team_name` field read-only (`teamNameBySlot`) — no typed-name override at all. A founder typing
  a team name in Prep mode won't see it in Draft mode's Opponents tab.
- **Behavioural context fields.** `Opponents.tsx` renders `positional_tendencies`,
  `first_pick_by_position`, `consensus_tracking_behaviour` (marked "NOT A MODEL INPUT"). None of
  these appear in `LiveOpponents.tsx` at all — by design per its own docstring (real in-session
  picks vs. sparse historical opponents.json context are different claims), but it means the two
  screens show genuinely different information for the same slot, not just a different data
  source for the same fields.
- **The scroll fix landed in this session (FR-082) touched only the render call sites in
  `DraftRoom.tsx`/`App.tsx`, not the components themselves** — but confirms they really are two
  independent render trees now: the bug existed in `LiveOpponents.tsx`'s Draft-mode mounting only,
  `Opponents.tsx`'s Prep-mode mounting was already fine. A shared component wouldn't have let that
  happen.

This traces back to FR-036's own text, which said "there is no `LiveOpponents.tsx` anywhere in
this repo" — true when FR-036 was written, false since `LiveOpponents.tsx` was added for FR-032.
Any doc or agent still reasoning from FR-036's "one component, two mounts" framing is working from
a stale premise.

## Why it matters

Every future fix to one needs a deliberate check against the other, or they'll silently diverge
further (already happening). Whether the right fix is consolidating into one component with a
`liveMode` prop, or keeping them separate but auditing feature parity deliberately, is a real
design decision — not something to decide inside an unrelated bug-fix task.

## Done looks like

A session picks this up deliberately: either (a) a documented decision that separate components
are intentional going forward, with an explicit feature-parity checklist, or (b) a consolidation,
scoped and reviewed on its own, not bundled into another ticket's diff.
