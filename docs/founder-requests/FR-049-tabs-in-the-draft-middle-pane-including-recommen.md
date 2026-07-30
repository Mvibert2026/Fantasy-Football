---
ID: FR-049
STATUS: SHIPPED
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

## Resolution (2026-07-30, frontend)

Built per `docs/design/DRAFT-MIDDLE-PANE.md`'s ruling: **one tab set, in the pane, four tabs —
Recommend / Scarcity / Queue / Insights** (not a second level under the pre-existing Board/
Opponents/Predictions hub tabs; the grid stays out per that doc's §1.1, tracked separately as
FR-044). NEXT DECISION is a persistent footer under the tab content, never behind a tab.
Recommend is the default tab.

**"Recommendations before my pick," the specific ask, is the look-ahead toggle inside Recommend.**
Off the clock, Recommend now shows a real recommendation computed as if it were the user's next
turn (round-appropriate — e.g. the early-QB penalty relaxes once round 6 is reached), rather than
nothing. On the clock, a toggle switches between "this pick" and a look-ahead to the turn after
this one. Labelled honestly every time it renders: "computed on today's board — does not account
for players taken between now and then," since this build has no model for which currently-
available players will still be there by the look-ahead pick.

**The standing label survived the promotion**, per this ticket's own instruction: "RECOMMENDED
(unvalidated stopgap score, not a backtested model)" renders in both this-pick and look-ahead
content, unchanged text.

Tests: `frontend/ui/__tests__/draft-room-middle-pane-tabs.test.tsx` (8 new), plus updates to
`draft-room-scarcity-and-sort.test.tsx` for the new tab structure. Screenshots:
`frontend/e2e/artifacts/middle-pane-{1,2}-recommend-*.png`.
