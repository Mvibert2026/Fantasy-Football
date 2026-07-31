---
ID: FR-135
STATUS: NEW
SOURCE: PM session 2026-07-30, founder chat
RAISED: 2026-07-30
PRIORITY: HIGH
NEEDS: researcher (reference), then design, then frontend
SUPERSEDES: the built half of design item 3
---

## Request

Founder's own words:

> "I want the periodic table draft board, not just a list of players - the grid is dumb - I want a
> traditional draft board - it's a grid (empty at first) that fills with picks as they are made across
> the top is teams and then you have two views, one is the order of the pics, snaking, and one is
> ordered by position, this sould have some images in screen shots and research"

## What was built, and why it is the wrong artifact

Design item 3 shipped this morning as `frontend/ui/components/PeriodicTableGrid.tsx` (commit
`deefb17`). Its position view is, in the source's own words:

> `/** Position-by-team: the reason Expand exists. 32 NFL teams by 5 positions -- */`

**32 NFL teams × 5 positions.** That is a grid of the *player universe*, organised by which NFL
franchise employs each player. It is a periodic table of players.

A **draft board** is a different object entirely:

| | Built | Asked for |
|---|---|---|
| Columns | 32 NFL franchises | the **10 managers in the league** |
| Rows | 5 positions | **rounds**, 1..N |
| Cells | every player who exists | **picks, as they are made** |
| State at draft start | fully populated | **empty** |

The founder's phrase "empty at first" is the tell, and it is the part no reading of the built
component satisfies. A draft board's entire job is to fill up. It is a record of what has happened,
not a catalogue of what exists.

**This is a misread, not a regression.** The item-3 dispatch and the spec it came from used the words
"periodic table", and the agent built a periodic table. The founder's underlying want — the thing
every fantasy platform puts on screen during a draft — was not what those words conveyed.

## The two views

1. **Pick order, snaking.** Round 1 left-to-right, round 2 right-to-left, and so on. The snake is the
   point: it is what makes the shape of a draft legible, and it is where the founder's own slot-3
   position and his next pick become visible at a glance.
2. **Ordered by position.** Same board, reorganised so positional runs are visible — the thing that
   tells you the RB room emptied in the third round.

## Research is part of the request, not preamble

He asked for "images in screen shots and research". Every major platform — Yahoo, ESPN, Sleeper — has
a draft board, all of them converged on broadly the same shape, and that convergence is evidence
worth reading before drawing. Dispatched to researcher.

## Disposition of the existing component

Not deleted yet. The position-by-NFL-team view may still be worth keeping as a *separate* thing under
an honest name — it is a reasonable scarcity-by-franchise view, just not a draft board. That is a
decision for after the real board exists, and it is the founder's to make, not a cleanup to do
quietly. The tab-integrity test from `deefb17` stays either way.
