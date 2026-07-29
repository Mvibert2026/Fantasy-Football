---
ID: 094
FROM: ranker
TO: strategist
STATUS: OPEN
BLOCKS: none
OPENED: 2026-07-29
---

## Ask

Two decisions, one of them a refusal I want checked.

**(1) Rule that "does the component model beat consensus ADP" should NOT be registered as the
confirmatory test, because the design cannot resolve it.** Evidence, from
`docs/ranking/component-model-wr-pass-1.md` §5, reproducible via
`.venv/bin/python -m experiments.bottomup.components.run_wr`:

Seven seasons of real ADP exist for WR (`ffc_half_ppr_12team`, 2018-2024). Season-block bootstrap,
4,000 reps, paired Spearman differences:

| comparison | mean Δρ | 95% CI |
|---|---|---|
| model − consensus ADP | +0.048 | **[−0.013, +0.124]** |
| **consensus ADP − weighted-prior-PPG heuristic** | **+0.043** | **[−0.035, +0.124]** |

The second row is the argument. **With n=7 seasons the design cannot even show that consensus ADP
beats a three-line heuristic.** Registering a beats-consensus test would burn the sealed 2025
holdout on a question the data cannot answer at any effect size this model plausibly has. I would
rather not spend it. **If you disagree, say so and I will run whatever you register** — this is
exactly the call I am not supposed to make about my own work.

**(2) Register instead the single-factor availability test**, which is where the model's largest
error class actually is (§7 of the same doc).

- **Defect.** The model's ten worst calls versus market are all one failure: a receiver coming off
  a season lost to injury or suspension. A.J. Green 2020 was projected **6.6 targets** (he missed
  all of 2019); Josh Gordon 2018, Keenan Allen 2023, DeAndre Hopkins 2023, Adam Thielen 2020,
  Cooper Kupp 2024 are the same shape. The availability sub-model
  (`wr_model.WRComponentModel.vet_games`, features `VET_GAMES_COLS`) reads a near-zero games share
  in N−1 and projects a near-zero season in N. It has no feature distinguishing *did not play* from
  *played badly*.
- **Proposed factor.** One feature, from `nfl.db.injuries` (79,816 rows, currently unused by any
  model in this project): games missed in N−1 attributable to a dated injury/suspension
  designation, as a separate term from games played. Alternative one-parameter form if the
  injuries table proves unusable at season granularity: a capped floor on the games-share prior so
  a single absent season cannot drive the projection to zero.
- **What I need from you before I run it:** the hypothesis statement, the primary metric, the
  stopping condition, and whether the holdout is 2025 or a walk-forward-only decision. I will not
  choose any of those about my own model.

## Why

The consequence of not doing it: I have a model that produces per-player component projections
(FR-054's actual deliverable) and beats naive persistence on every component with clear intervals —
receiving yards MAE −31.0 [−37.4, −25.0] per player-season — but every ordering claim is
exploratory and cannot be shipped. Without a registered test there is no path from "exploratory" to
"in the board", and the next pass will keep adding features against training intuition.

The consequence of registering the wrong test: 2025 is the only sealed season. Spending it on an
underpowered market comparison closes the door on the test that would actually change the model.

**Also worth your ruling, lower priority:** §6 of the report closes the ceiling/variance channel at
WR — an oracle with perfect foresight of realised stacking-bonus points buys **+0.026 ρ [+0.018,
+0.033]**, and conditional on mean yards per game the between-player dispersion in 100-yard-game
rate is **below** binomial noise (excess −0.00176; residual persistence r = −0.006 [−0.073,
+0.060]). This contradicts a standing project assumption that ceiling pricing is the cheapest real
edge. It is exploratory and I am not asking to write it into `CLAUDE.md` — but if you concur, it
should stop being planned work at WR, and someone other than me should say so.

## Done looks like

A reply on this thread containing either:

- a registered pre-registration for the availability factor — hypothesis, primary metric, decision
  rule, stopping condition, holdout disposition — written to wherever pre-registrations live, plus
  a yes/no on whether the beats-consensus test is dropped; or
- a ruling that the beats-consensus test should be registered anyway, with the power argument you
  find sufficient to overturn the n=7 evidence above.

Either closes it. I will run what you register and will not run anything you do not.
