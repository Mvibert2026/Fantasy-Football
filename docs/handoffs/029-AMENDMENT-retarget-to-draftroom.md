
---

## AMENDMENT — 2026-07-27. Retargeted from Prep Board to Draft room.

**This thread originally said "the Board's inline availability badges." That was wrong.** Build it on
`DraftRoom.tsx`, not `Board.tsx`.

**Why.** The founder looked at the running app and observed that the Prep Board has no availability
column — and that this is arguably correct rather than a defect. The two are genuinely different
quantities:

- **Prep** availability is an *unconditional* average over every possible draft. A planning number.
- **Draft** availability is *conditioned on the picks actually made*. A live number.

The frontend audit marked `LIVE-01` as `partial` on the assumption that the spec was right to put a
two-number cell on the Prep board. That assumption is now itself in question and goes to Design when
the pause lifts. Do not build it there in the meantime.

**What DraftRoom actually needs**, per the audit: it already renders `baseline → live` per row, so the
numbers exist. Missing are the **10-dot frequency array** beside them, and **tier grouping with
headers** ("TIER 2 — 3 players left").

The dots are the point. A bare percentage on a row is the same point-estimate presentation every
competitor ships; the dot array is how this product says the same thing honestly. It already exists on
the player detail sheet and the Availability Explorer — this is applying an existing component to the
screen users spend the draft looking at.

**Constraint unchanged:** density is the product. Ten dots inline must not increase row height or
reduce rows per screen. If it cannot be done inside the existing row height, say so and propose an
alternative rather than trading away density.
