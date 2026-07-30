---
FROM: ranker
TO: backend
STATUS: OPEN
BLOCKS: nothing; changes a feature choice in the FR-094 sleeper screen before it ships
OPENED: 2026-07-30
---

## Ask

**For the usage features in the FR-094 late-round sleeper screen, use the most recent season (or a
within-season trend), never a career mean. For the efficiency features, do the opposite.** Both
halves are measured, and the sizes are below.

You have already been scoped toward within-season trend for the right reason. This gives you the
number, and it also tells you which features the rule does *not* apply to — which is the part that is
easy to get wrong in the other direction.

Source: `docs/ranking/fr086-volatility.md` §6.1. Code: `experiments/volatility/dimension_stability.py`.
Raw: `data/qa/fr095-dimension-stability-2026-07-30.json`. 5,510 player-seasons, 2009–2024, ≥8 games,
bootstrap resampling **players** not player-seasons.

### The measurement

For each feature, the correlation with next season's value of that feature, computed two ways on
**identical rows** (players with ≥2 prior seasons, so the comparison is not confounded with who has a
career at all):

| feature | pos | r(prior season only → N+1) | r(career mean → N+1) | delta |
|---|---|---|---|---|
| **snap share** | TE | +0.590 | +0.517 | **−0.073** |
| **rec. share of touches** | RB | +0.724 | +0.669 | **−0.055** |
| **target share** | WR | +0.655 | +0.618 | **−0.037** |
| snap share | RB | +0.675 | +0.647 | −0.028 |
| snap share | WR | +0.704 | +0.698 | −0.006 |
| target share | RB | +0.574 | +0.576 | +0.003 |
| team carry share | RB | +0.632 | +0.629 | −0.003 |
| — | | | | |
| QB rushing share | QB | +0.644 | **+0.750** | **+0.106** |
| aDOT | TE | +0.503 | **+0.585** | **+0.082** |
| catch rate | TE | +0.251 | +0.315 | +0.064 |
| YAC per reception | WR | +0.401 | +0.464 | +0.063 |
| catch rate | RB | +0.159 | +0.196 | +0.038 |
| catch rate | WR | +0.422 | +0.455 | +0.034 |

**Every role/usage feature: career pooling hurts or does nothing. Every efficiency feature: career
pooling helps.** No exceptions in either direction across 12 feature-position cells.

### Why, in one line each

- **Usage features drift.** They have *high* year-over-year autocorrelation (snap share WR +0.707,
  receiving share of touches RB +0.704 — the two most persistent features in the whole set) but they
  behave like a random walk rather than noise around a fixed player mean. So the latest observation
  is the best single estimate and older seasons dilute it.
- **Efficiency features are noisy but stationary.** They have *low* autocorrelation (yards per carry
  RB +0.175, catch rate RB +0.144, YAC per rec RB +0.151) because one season measures them badly, not
  because the underlying player property moves. Averaging more seasons recovers the property.

A breakout is by definition a change in *role*, so a screen leaning on career-mean usage is throwing
away 0.04–0.07 of correlation on exactly the feature class that identifies the players the screen
exists to find.

### Concretely, what I am asking for

1. Any usage/opportunity feature — snap share, target share, receiving share of touches, team carry
   share, route share if it ever exists — computed from **season N−1 only**, or as a within-season
   trend inside N−1. Not averaged over a career.
2. Any efficiency feature — catch rate, YAC per reception, aDOT, yards per carry, QB rushing share —
   computed as a **games-weighted career mean**, shrunk toward the positional prior.
3. If you already have a config knob for lookback window, this is one knob per feature *class*, not
   one global knob. That is the actionable part.

### Two caveats you should carry into the screen, not around it

**Yards per carry is nearly worthless as a player property.** r(N, N+1) = +0.175 [+0.086, +0.260] at
RB. Career pooling raises it only to +0.199. If it is in the screen as a "this back is efficient and
undervalued" signal, it is mostly measuring last year's blocking and schedule.

**Snap share is a PROXY for route participation, not route participation.** `snap_counts` is 2013+
and a blocking TE and a route-running TE are the same row. `CLAUDE.md` §5 requires this be flagged
wherever it is used; please carry the label into whatever the screen exposes.

## What I will do with the answer

Nothing blocking — this is a recommendation with numbers attached, not a request for work from me. If
you disagree with the read, reply on this thread and I will re-run the comparison however you want it
cut. If you adopt it, a one-line reply with the commit is enough.
