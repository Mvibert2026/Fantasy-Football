# Factor batch 7 — running-back usage and efficiency

**ranker, 2026-07-30.** Autonomous factor batch, dispatched to work the test list down in parallel
with batches 4, 5 and 6 against one checkout.

## What was asked

The six RB rows of `docs/research/analyst-factor-sweep-2026-07-30.md` §2c — N14 red-zone/inside-10/
inside-5 **snap** rate, N15 inside-5 TD conversion vs the league base rate, N16 YAC per reception,
N17 receiving share of an RB's own fantasy points, N18 snap-share persistence at a threshold, N19
late-season role trajectory by draft round and career year. RB because it is the one position where
this project's experiment has demonstrated power (ADP − heuristic **+0.134 [+0.043, +0.223]**) *and*
where the component model is negative against ADP (**−0.052**).

## What was done

| | |
|---|---|
| Pre-commitment | `docs/ranking/factor-batch-7-precommit.md`, committed **`fb7627a` before any arm was fitted** |
| Registered tests | **16, all at RB.** Five are controls — four coverage flags and one binomial placebo |
| Correction | BH at the **campaign** level, **M = 80**, registered in campaign C2 (`docs/ranking/factor-campaign-manifest/batch-7.md`) |
| Results | `2d7a6e2` · post-hoc diagnostics `f8d7757` |
| Write-up | `docs/ranking/factor-batch-7-results.md` |
| Holdout | 2025 sealed and **not opened** |
| Season-N reads | **zero, in every arm**, asserted as a `RuntimeError` rather than believed |
| Reproduction | batch-7 primary reproduces batch 3's RB primary `mae_carries` to **`+0.000000e+00`** |
| Runtime | 110 s for the 16 arms, 34 s for the diagnostics |

New code, all batch-7-owned: `experiments/bottomup/factors/factor_features7.py` (six feature blocks,
each with its own holdout and cutoff gate) and `run_factors7.py` (the arms, the grading, and a
batch-local `RateCovariateRB` subclass). **No shared module was edited** — `pos_data.py`,
`pos_model.py` and `pos_eval.py` are read-only to this batch because three other factor agents were
working the same checkout.

## Outcome

**16 of 16 null-or-worse. Nothing survives. Nothing moves the RB deficit.** 11 NULL, 2 MARGINAL,
2 MARGINAL-HARMFUL, 1 RESTATEMENT. Deficit spread across all 16 arms: −0.0515 to −0.0572 against a
primary of **−0.0523**. Nothing passes BH at M = 80, and nothing passes at the batch m = 16 either —
smallest p-value 0.021 — so the campaign denominator is not what killed anything.

## The two things worth more than the arms

**1. A `*_known` coverage-flag control is a TIME DUMMY when its source starts inside the training
window.** `rzsnap_known` returned −0.1239 carries MAE, **215% of the treatment it was controlling**.
Post-hoc D2: it agrees with "is not a rookie" on 99.89% of rows, and among *veterans* it is **0.000
for target seasons 2012–2016 and 1.000 from 2018** — `participation` starts 2016, the training window
starts 2012. Every control whose source covers the window is null; every one that starts inside it is
not. This touches batch 3's **published** VOID ruling on NGS separation and batch 5's `routes_known`
(same source, same geometry, read as coverage rather than calendar). **Registered to `strategist` as
a claim; no other batch's documents were edited.**

**2. Every arm that improved the full universe degraded the ADP board**, same sign, across three
unrelated sources including one with full training-window coverage. Z1: board **+1.35% worse** /
off-board −1.73% better, on 51 vs 80 players a season. Batch 5 found the same at WR and TE
independently. Three batches, three positions, four sources. It asks whether **E1a should remain the
FDR endpoint at all** — which is strategist's call, not mine.

## Two of the sweep's own claims fail in the direction opposite to the claim

- **N17.** McFarland's "70% of league-winning RB seasons came from backs at ≥40% receiving share"
  tests **MARGINAL-HARMFUL** on both parameterisations, including his own ≥40% cut. Likely
  reconciliation: the published statistic is conditioned on the outcome.
- **N16.** Barfield's "clear best RB pass-game efficiency stat", r = 0.421, measures **+0.0028
  [−0.1082, +0.1027], p = 0.962** — a flat zero on 11 seasons with a clean control.

## Two negatives that are cleaner than they look

- **N18 is a RESTATEMENT at R² = 0.9014** against the model's own existing RB columns. `snap_counts`'
  324,611 rows are unused by any model because the information is already there by another route.
- **N19 is the opposite:** 4.0% explained by the whole model and **0.95% by age and experience**. The
  restatement objection the dispatch raised is measured and rejected — and the factor is null anyway,
  which is a stronger negative than a restatement would have been.

## Data findings

`pbp` has **no `yards_after_catch` column** and starts **2009, not 1999**.
`player_weekly_stats.receiving_yards_after_catch` is **identically zero for 2000–2005**, real from
2006. `snap_counts` is keyed on **PFR ids**; the `player_ids` crosswalk matches 99.34% of RB
player-seasons, 99.55% snap-weighted. `participation`'s empty `offense_players` rows are **entirely
non-scrimmage plays** — on rush/pass plays missingness is 0.0000 in every season. **Nothing was
blocked: all six factors were computable from `nfl.db` with no new ingest.**

## Threads opened

| to | subject |
|---|---|
| `strategist` | register batch 7 at M = 80; rule on the coverage-flag time-dummy defect (which touches batch 3's published VOID ruling); rule on whether E1a should stay the FDR endpoint |
| `fable` | attack the batch — with the five things I would attack myself, including that I built the rate-covariate hook and then graded my own nulls with it |
| `data-ops` | the four measured data facts above |
| `librarian` | eight factor-ledger dispositions, plus two rows that should be narrowed rather than added |

## Nothing ships

No arm graded, so batch 2 §7's insight-string rule holds: nothing renders on the draft board about
red-zone role, snap share, receiving share or late-season trends. Registry #10 (red-zone **touches**)
is untouched — batch 7 tested **presence**, a different object.
