---
ID: FR-049
STATUS: NEW
SOURCE: chat 2026-07-29, PM session
RAISED: 2026-07-29
---

## Request
Tabs in the draft middle pane, including recommendations before my pick

Founder's own words:

> "to show more information there, maybe we need tabs, having the ability to see recommendations
> before my pick would be nice - so within that middle pane, having different tabs I can navigate."

## Why it matters

The middle pane is the highest-value real estate in the app — it is what he is looking at when the
clock is running — and it currently shows one thing at a time with no way to move between views.
Everything else competing for that space (insights per FR-048, the recommendation, the periodic-table
grid per FR-044) needs somewhere to go.

**"Recommendations before my pick" is the specific ask inside the general one.** Today the
recommendation panel populates when the founder is on the clock. He wants to see it while the picks
ahead of him are still coming in — which is when the decision is actually being made, not when the
timer starts.

## Initial read

Not the founder's own words — PM's read.

Tabs themselves are cheap. **What goes in them is the decision**, and it should be settled before
anything is built, or the tabs become a place to put whatever was written most recently.

Candidates already requested or built: the recommendation (with a look-ahead mode), the
periodic-table grid (FR-044), contextual insights (FR-048), position scarcity, opponents. That is
more than fits — which is the point of specifying first.

**One real constraint on "recommendations before my pick."** The current recommendation runs on four
hand-picked constants (`frontend/ui/data/recommendation.ts` — +8 unfilled need, +18 tier-1 TE, −25
early QB), which the module itself calls a stopgap that has never been backtested. Showing it
earlier and more prominently increases how much weight it carries. **The honest sequence is to fix
or label the model before promoting it**, not after.

**Design owns the layout.** This is the fourth request today that lands in the same pane, which is
exactly the case for specifying the whole pane once rather than adding one control at a time.
