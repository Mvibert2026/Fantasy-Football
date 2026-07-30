---
ID: FR-072
STATUS: IN-PROGRESS
SOURCE: ranker session dispatch, 2026-07-30
RAISED: 2026-07-30
---

## Request
Extend the bottom-up component model to RB, QB and TE; do not ship rankings until all positions exist

Founder's own words, both quoted verbatim in the dispatch that opened this session:

> "Ok for our model, let's do the other positions too, why just WR."

> "Don't show our rankings in the app until we can do it for all players."

## Why it matters

The second quote is a **binding shipping constraint, not a preference**, and it is the reason the
first one is urgent. FR-054 delivered component projections at WR only
(`docs/ranking/component-model-wr-pass-1.md`). Under this ruling that work cannot reach the app at
all — a one-position model is not shippable no matter how good it is. Every downstream request that
depends on our own player-level opinion (FR-040 custom scoring, FR-042, FR-053) is gated behind all
four positions existing.

Note the ruling says **all players**, not all positions. Four offensive positions is necessary and
may not be sufficient: this league also starts 1 DEF. Team defense is not modelled by anything in
this project and is not covered by this request's four-position scope. Flagged here so the gap is
visible when someone reads the ruling as satisfied.

## Initial read
*Not the founder's own words — ranker's read on scope, constraints, sequencing.*

Delivered 2026-07-30: RB, QB and TE component models plus a WR re-run on shared code, in
`experiments/bottomup/components/` (`pos_data`, `pos_features`, `pos_model`, `pos_eval`).
Full result: `docs/ranking/component-model-rb-qb-te-pass-1.md`.

**The four-position model now exists, and on current evidence it should still not ship.** Against
consensus ADP the margins are +0.051 (WR), −0.052 (RB), −0.069 (QB), −0.024 (TE) Spearman, none
clearing zero. At RB the test demonstrably has power — ADP beats the naive heuristic by
+0.134 [+0.043, +0.223] — so the RB failure to beat the market is a real null, not an underpowered
one. Meeting the founder's ruling on coverage does not by itself mean the model has earned a place
in the app; the shipping decision is a separate question and is `strategist`'s to register, not
ranker's to make about its own model.
