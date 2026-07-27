---
ID: 044
FROM: pm
TO: backend, frontend
STATUS: OPEN
OPENED: 2026-07-27
BLOCKS: none
---

## Ask

Make the recommendation visibly account for the user's own roster — including surplus, not just need.
Founder requirement: *"I do need customization for my team though, if I already have too many of one
or the other."*

## What already exists, and what does not

**Exists.** The roster-need term `N_t(p) = (share_t(p) / share_bar(p))^lambda` is share-based rather
than deficit-based, which means it handles **surplus** as well as shortage: a team already above its
typical final composition at a position gets that position *suppressed*, not merely un-boosted. That
distinction was deliberate. Sanity check #7b exists specifically to catch its failure — a team holding
3 RBs must show a strictly **lower** RB hazard than a team holding 2. ADR-046 wired this into
`strategy_balanced`.

**Does not exist.** None of it is visible in the recommendation. The prototype's `RECOMMENDED` card
reasons purely from VBD and survival probability. A user with three receivers and no tight end sees
the same explanation as a user with an empty roster. The arithmetic is running; the product never says
so.

## The design — and why it resolves D-001 rather than colliding with it

There is an open decision (D-001) on `NEED_ADJUSTMENT_SCALE = 10.0`. The Strategist's ADR-A concludes
the parameter is only *set*-identified and should be deleted or converted to a bounded constraint,
never fitted. That sounds like it conflicts with this request. It does not — it points at the right
implementation.

**Roster awareness as a constraint and a disclosure, not as a hidden scoring weight.**

- **As a constraint:** the engine refuses to recommend something that produces a structurally broken
  roster — a fourth player at a filled position while a mandatory slot has fewer startable options
  remaining than picks left before the roster closes. That is arithmetic on observable state. It needs
  no fitted magnitude and it is defensible.
- **As a disclosure:** when roster state changes the ordering, **say so, in the card**. "You have 3 WR
  and 0 TE with 4 picks left — this moves Bowers ahead of Olave" is traceable, checkable and
  overridable. A silent nudge of unknown size is neither.

This is the difference between the product deciding *for* the user and the product showing its
reasoning so they can disagree — which two independent research passes identified as the single most
trust-building thing it can do.

## Backend

- Surface the need/surplus computation as a **named field on the recommendation**, not just an internal
  multiplier: the position, the current count against target, and the direction of the effect.
- Implement the structural constraint above and expose whether it fired.
- Keep the magnitude question separate. D-001 governs whether `NEED_ADJUSTMENT_SCALE` survives as a
  fitted weight; this thread does not depend on that answer either way.

## Frontend

- The `RECOMMENDED` card gains a roster-context line **when and only when** roster state actually
  changed the ordering. When it did not, show nothing — a line that appears on every pick is noise and
  will be ignored by the third round.
- `WHAT YOU GIVE UP` should name the roster consequence where one exists: not only "you give up 2
  points of value today" but "and you still need a TE with 4 picks left."
- Surplus needs its own treatment. Suppressing a position the user is heavy at is a *different* claim
  from boosting one they are light at, and the card should not blur them.

## Constraint

Every number in that line traces to a named field. No generated prose about roster strategy — the
board holds no player-level opinion, and a sentence like "you should probably go best available here"
is not derived from anything.

## Done looks like

Need and surplus exposed as named fields. The structural constraint implemented with a test covering
the surplus case (three at a filled position while a mandatory slot is short). Card shows the roster
line only when ordering actually changed. Screenshot. Commit hash and test count.
