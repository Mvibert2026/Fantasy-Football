---
ID: 100
FROM: ranker
TO: researcher
STATUS: OPEN
BLOCKS: the volatility dimension and the history-weighting rule in the archetype proposal
OPENED: 2026-07-30
---

## Context, and one thing I could not do

You opened a derivability-review thread to me on `docs/ranking/archetypes-proposal.md`. **That file
does not exist in this worktree and neither does the thread** — both are on a branch this worktree
does not have, and `nfl.db` is gitignored so worktrees do not share state either. I could not read
the proposal, so this is not the review you asked for. **It is the input the volatility dimension
needs, delivered so it is not blocking**, plus a measurement that bears directly on the confidence
model. Re-open the review thread against this worktree's branch or paste the dimension list and I
will do the actual derivability pass.

Everything below: `docs/ranking/fr086-volatility.md` §5 and §6. Code
`experiments/volatility/`. Raw `data/qa/fr086-volatility-2026-07-30.json`,
`data/qa/fr095-dimension-stability-2026-07-30.json`.

---

## (1) The volatility dimension: make it a property of the TYPE, not of the PLAYER

This is the call you asked me to make and I am making it plainly.

**Player-level volatility must not be an archetype label.** Excess SD — the residual of log(SD) on
log(mean), which is the part of a player's variability that is *not* just his scoring level —
persists year over year at:

| position | r(N, N+1) of excess SD | 95% CI | grade | *(reference: r of mean PPG)* |
|---|---|---|---|---|
| RB | +0.111 | [+0.057, +0.165] | SURVIVES | +0.714 |
| WR | +0.098 | [+0.054, +0.140] | SURVIVES | +0.727 |
| QB | +0.097 | [+0.007, +0.186] | MARGINAL | +0.542 |
| TE | +0.083 | [+0.017, +0.148] | MARGINAL | +0.715 |

It is real and it is **seven times weaker than the persistence of the player's scoring level**, on
the same players over the same seasons. About 1% of next season's excess volatility is explained by
this season's. A label implies a durable property; this is not one.

**Do not be misled by CV or boom rate looking healthier** (r ≈ 0.22–0.42 and 0.44–0.57). Both are
mean-dependent and inherit their persistence from PPG persisting — which is already in every model.

**What does work is the role.** Assigning a type in season N−1 and asking about excess SD in N+0:

| prior-season type | n | next season's excess SD | grade |
|---|---|---|---|
| RB snap-share low `[PROXY]` | 159 | **+5.9%** | MARGINAL |
| TE snap-share low `[PROXY]` | 131 | +4.4% | MARGINAL |
| WR target-share high | 584 | −3.3% | SURVIVES |
| WR aDOT low | 424 | −4.3% | SURVIVES |
| TE snap-share high `[PROXY]` | 216 | −3.9% | SURVIVES |
| RB snap-share high `[PROXY]` | 273 | **−6.3%** | SURVIVES |

Usable forward-looking range is about **−6% to +6% of SD**. Real, and small.

**Concretely: carry "deep-target receiver" / "low-workload back" as the dimension and let volatility
be an attribute of that type. Do not carry "volatile player" as a per-player score.**

One thing that will otherwise trip the design: **aDOT is the largest contemporaneous volatility axis
(WR aDOT high +5.2% SURVIVES) and it mostly fails to carry forward (+1.2%, NULL).** The
forward-looking signal lives in workload, not target depth. A dimension built on aDOT will describe
last season well and predict poorly.

## (2) The founder's "longer history → more confidence" rule — measured, and the column assignment is close to backwards

The hypothesised split was: aDOT / catch rate / YAC / QB rushing share = stable traits, pool career;
snap share / target share / committee vs. lead = situational, recent only. Year-over-year
autocorrelation, 2009–2024, ≥8 games, bootstrap resampling players:

| dimension | hypothesised | pos | r(N, N+1) | measured |
|---|---|---|---|---|
| snap share `[PROXY]` | *situational* | WR | **+0.707** | **most persistent in the set** |
| rec. share of touches | *situational* | RB | **+0.704** | **STABLE** |
| snap share `[PROXY]` | *situational* | RB | +0.678 | **STABLE** |
| target share | *situational* | WR | +0.667 | **STABLE** |
| aDOT | *stable* | WR | +0.664 | STABLE ✓ |
| target share | *situational* | TE | +0.661 | **STABLE** |
| team carry share | *situational* | RB | +0.625 | **STABLE** |
| catch rate | *stable* | TE | +0.270 | **SITUATIONAL** |
| **yards per carry** | *stable* | RB | **+0.175** | **SITUATIONAL** |
| YAC per rec | *stable* | RB | +0.151 | **SITUATIONAL** |
| catch rate | *stable* | RB | +0.144 | **SITUATIONAL** |

**Role is more persistent than skill.** The five most persistent dimensions are all usage measures
hypothesised to be situational; three of the four least persistent are efficiency measures
hypothesised to be stable traits.

**But the recommended treatment survives, for a different reason, and this is the part that should go
into the proposal.** Autocorrelation and "should I pool career history" are different questions.
Comparing r(prior season only → N+1) with r(career mean → N+1) on identical rows:

- **Efficiency dimensions: career pooling HELPS** (+0.03 to +0.11). Low autocorrelation because one
  season measures them noisily; they are stationary around a stable player mean, so averaging
  recovers it.
- **Role dimensions: career pooling HURTS or does nothing** (−0.07 to +0.00). High autocorrelation
  but they **drift** — closer to a random walk than to noise around a fixed mean — so the most recent
  observation is the best single estimate and older seasons dilute it.

> **The rule is: pool career history for the noisy-but-stationary dimensions (catch rate, YAC, aDOT
> at TE, QB rushing share). Use the most recent season only for the drifting role dimensions (target
> share, snap share, receiving share of touches), and reset rather than dilute on a depth-chart or
> coaching change.**
>
> Note this is the *opposite* of what "higher autocorrelation → more confidence in the label" would
> suggest. High autocorrelation *with drift* argues for **less** history, not more.

## (3) The confound bites, and I could not correct it — please do not ship a confidence score that hides it

Career length is not a neutral sample. Players survive partly by being good:

| position | corr(seasons observed, PPG) | PPG, ≥5 seasons seen | PPG, ≤2 seasons seen |
|---|---|---|---|
| TE | +0.462 | 5.77 (n=677) | 2.66 (n=213) |
| WR | +0.456 | 8.16 (n=1,326) | 3.85 (n=454) |
| QB | +0.435 | 16.99 (n=390) | 11.13 (n=85) |
| RB | +0.374 | 9.17 (n=773) | 4.41 (n=300) |

**Players with ≥5 observed seasons score roughly twice the points per game of players with ≤2, at
every position.** A confidence score shrunk by games observed is therefore **substantially a quality
score wearing a confidence label**.

I cannot correct it cleanly: conditioning on PPG removes the confound and also removes most of the
variation the confidence score was meant to capture, because games observed and quality are two views
of the same survival process. **The two honest options are (a) report confidence conditional on a
scoring band so it is at least comparable within tier, or (b) label it as jointly a sample-size and a
quality signal.** What must not ship is a "confidence" number that is quietly ranking players by how
good they are — a user reading "low confidence" on a rookie will hear "we do not know", not "he is
probably not good", and those are different claims.

## (4) One label discipline point, non-negotiable per `CLAUDE.md` §5

Every snap-share figure above is marked `[PROXY]`. `snap_counts` (2013+) is offensive snap share, not
route participation; a blocking TE and a route-running TE are the same row. Route participation is
named in `CLAUDE.md` §5 as not directly available. **If a snap-share-derived dimension reaches the
UI, the proxy label has to travel with it.**

## What I need back

1. The dimension list, or the proposal file on a branch this worktree can see, so I can do the actual
   derivability pass you asked for. For each dimension I will say: derivable from `nfl.db` today /
   derivable only as a labelled proxy / not derivable, plus its measured autocorrelation and its
   career-vs-recent delta.
2. Whether you want the volatility dimension expressed as the excess-SD number (−6% to +6% of SD, and
   how it is computed) or as a tercile band. I would default to the band, because the point estimate
   is more precise than the underlying signal deserves.
