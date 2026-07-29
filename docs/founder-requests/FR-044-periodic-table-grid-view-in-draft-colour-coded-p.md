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

**Colour encodes position, not team. The founder corrected this explicitly:**

> "Not team colors, colors by position, pretty standard draft room stuff. I will share some Yahoo
> and fantasy pros screenshots soon."

So: a fixed colour per position (QB / RB / WR / TE / DEF), applied consistently, matching what every
draft room already does. This is convention, not invention — do not design a novel palette when the
category has a shared one the founder already reads fluently. **Wait for his screenshots before
choosing the hues**; matching what he is used to is the point.

Two things that still need care and are not negotiable:

- **Position must be legible without colour.** Every cell carries its position as text. Hue is the
  fast channel, not the only one — it has to survive a colour-blind reader, and it has to hold up in
  both light and dark mode.
- **Position colour must not collide with the app's two reserved accents**, which already carry
  meaning (good/bad, up/down) elsewhere on the board. `frontend/ui/styles/tokens.css` already
  defines a `--pos` token; check what it currently resolves to before adding five more.

`TEAM_COLOR` (`frontend/ui/data/teamColors.ts`) stays out of the fill. It is documented there as
identity-only. Team belongs on an axis or a label in the position-by-team layout, which is what the
founder described anyway.

**This is design's call before it is engineering's.** It is a new information-display idiom for this
app, not a variation on an existing screen, and the founder has an outstanding instruction that
design catches up to code rather than the reverse — but that applies to *parity on what exists*,
not to inventing a new view. His own stated exception covers this: a new feature needing visibility
before the overhaul still gets specified up front.

**Sequencing:** specify with `design`, build after the four items currently in flight with
`frontend` (league-scoped predictions, opponent names, draft-slot selector, refresh-button removal).
Not before the draft-critical correctness work in `CURRENT-STATE.md`.
