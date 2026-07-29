---
ID: FR-044
STATUS: NEW
PRIORITY: MEDIUM
SOURCE: chat 2026-07-29, PM session
RAISED: 2026-07-29
---

## Request
Periodic-table grid view in Draft — colour-coded positions, sortable by draft order or position-by-team

Founder's own words:

> "in draft, I'd also like the option to see the periodic table style dashboard, color coded
> positions, sortable by draft order, or position by team"

## Why it matters

Every view in Draft mode today is a **list** — the board is a table, the round grid is a schedule.
A list is read one row at a time, which is the wrong shape for the two questions that actually come
up under a draft clock:

- *"How much of this position is left, and how fast is it going?"*
- *"Have I got too much of one team? Who else is on that offence?"*

Both are **pattern** questions. A colour-coded grid answers them at a glance; a sorted table makes
you count. This is the same reasoning behind the app's stated "density as product" principle, one
step further.

It also generalises: a grid where cells drain as players are taken is a live picture of scarcity,
which is the thing the founder is actually drafting against.

## Initial read

Not the founder's own words — PM's read.

**Two layouts, one component.** The founder named both:
1. **By draft order** — cells in rank/ADP sequence, wrapping into rows. The "periodic table" shape.
2. **Position by team** — a matrix with teams on one axis and positions on the other. This is the
   one no existing screen approximates at all, and it is the one that answers stacking and bye-week
   questions.

**What already exists and should be reused rather than rebuilt** (per FR-043 — this project has
already nearly built a second copy of something it already had):

| Asset | Where | Use |
|---|---|---|
| `TEAM_COLOR` — all 32 brand colours | `frontend/ui/data/teamColors.ts` | Team axis / cell tint |
| Round grid — rounds × slots, picks marked | `frontend/ui/views/RoundGrid.tsx` | The closest existing layout; read it first |
| Live pick log and availability | `frontend/ui/data/liveAvailability.ts`, `draft.ts` | Draining cells as players go |
| Tier bands | `Board.tsx` | Existing grouping logic |

**A constraint that is not negotiable, and it is already written down.** `teamColors.ts` states in
its own header that team colours are used *"only for the identity chip and the initials placeholder
— never as a data colour, so it can't collide with the app's two reserved accents."* A grid that
tints cells by team brand colour would break that rule. **Position colour and team colour cannot
both be the primary encoding of a cell.** Pick one as fill and give the other a different channel —
border, grouping, axis position, label. Whichever way round, it has to survive a colour-blind reader
and dark mode, so position should also be legible from its label and not from hue alone.

**This is design's call before it is engineering's.** It is a new information-display idiom for this
app, not a variation on an existing screen, and the founder has an outstanding instruction that
design catches up to code rather than the reverse — but that applies to *parity on what exists*,
not to inventing a new view. His own stated exception covers this: a new feature needing visibility
before the overhaul still gets specified up front.

**Sequencing:** specify with `design`, build after the four items currently in flight with
`frontend` (league-scoped predictions, opponent names, draft-slot selector, refresh-button removal).
Not before the draft-critical correctness work in `CURRENT-STATE.md`.
