---
ID: 047
FROM: pm
TO: frontend, backend
STATUS: OPEN
OPENED: 2026-07-27
BLOCKS: usable mock drafting
---

## Ask

Let the user manually enter the draft setup, not just the picks. Founder: *"A user including me should
be able to manually enter some draft information (like opponents and order)."*

Manual entry is already a first-class feature for *picks* — deliberately, because every third-party
tool in the market breaks when platform sync fails, and the competitive research identified that as a
real and recurring failure. This extends the same principle to setup.

**What must be enterable:**

- **Draft order / slot.** Which seat the user is in, and therefore the derived pick sequence. Currently
  hardcoded to slot 3 with picks 3, 18, 23, 38, 43, 58, 63. See thread 040 — in a public mock the slot
  is assigned, not chosen.
- **Opponent identities.** Team names per slot. The Opponents screen already handles the null case
  honestly ("Slot N (no team name supplied)") — this lets the user fill it in.
- **Draft type.** Snake versus linear. The pick sequence derivation depends on it and it is currently
  assumed.
- **Team count**, which drives the sequence and the replacement levels.

**What must not be enterable, and should be visibly refused:** opponent *tendencies*, strategies, or
predicted behaviour. Inferring an opponent's latent draft plan was explicitly rejected as
methodologically indefensible, and letting a user type it in is the same claim with a different
author. Names and slots are observable facts; intentions are not.

## Interaction

This happens under time pressure — a mock lobby fills fast. Entry should be quick and forgiving:
tab-through the slots, paste a list of names if the platform shows one, and edit any of it mid-draft
without resetting.

**Mid-draft editability matters.** Getting the slot wrong is discovered at pick 2, not before, and
correcting it must not discard logged picks. Per thread 040's amendment the draft is event-sourced, so
a setup change replays rather than destroys — same mechanism as undo.

## Backend

Draft setup becomes part of the draft record rather than league config: slot, team count, draft type,
and the opponent name map. It varies per draft, and a mock in someone else's lobby shares none of it
with the user's home league.

This overlaps thread 040's per-draft configuration stamp. Coordinate — one structure, not two.

## Done looks like

Slot, team count, draft type and opponent names all enterable and editable mid-draft without losing
picks. Pick sequence derived rather than hardcoded. Tendencies not enterable. Screenshot. Commit hash
and test count.
