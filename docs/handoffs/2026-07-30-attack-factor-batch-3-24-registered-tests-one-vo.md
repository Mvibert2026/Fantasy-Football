---
ID: 2026-07-30-attack-factor-batch-3-24-registered-tests-one-vo
FROM: ranker
TO: fable
STATUS: OPEN
BLOCKS: none
OPENED: 2026-07-30
---

## Ask

Attack `docs/ranking/factor-batch-3-results.md` at maximum effort. Pre-commitment is
`docs/ranking/factor-batch-3-precommit.md`, content committed `1c452a1` **before any arm was fitted**;
results `c7161ce`; post-hoc diagnostics `b9d1a47`. Raw numbers in
`experiments/bottomup/results/factor_batch3_results.csv` and `factor_batch3_diagnostics.csv`.

**Five places I think it is weakest, offered so you can go somewhere else if you disagree.**

1. **The post-hoc YPC finding is the whole value of the batch and it is post-hoc.** Lagged yards per
   carry, offered to the RB *carry-volume* spec it has never been offered to, beats every registered
   arm: **-0.9331 carries MAE (-1.88%), E1b -0.7200**, against registered X1's -0.7508 / -0.0264. I
   have refused to ship it and routed it to `strategist` for registration. **Is refusing to ship it
   sufficient, or is publishing the number at all already the sin?**

2. **My own registered rows 21-24 are algebraically degenerate.** `B2ra = ppg_1 x gshare_1` is
   `pts_1 / season_len`, rank-identical to the incumbent, residual `1.776e-15`. Four of twenty-four
   registered tests could not return anything. I held m at 24 anyway. **Attack the denominator.**

3. **The VOID rule is mine and its threshold is mine.** 50%, fixed in advance, no external
   justification. It voided NGS separation at WR (|c|/|t| = 0.92) and **spared OC tenure at QB by
   0.04** (0.46). A threshold that a result lands 0.04 from is a threshold worth attacking.

4. **NGS coverage is 0.83 on the board and 0.41-0.45 on the full universe**, and the E1a endpoint is
   the *full universe*. I registered controls and one fired -- but the controls only catch a coverage
   flag entering LINEARLY. They do not catch an interaction between coverage and the imputed value,
   and I did not test for one.

5. **`pbp` includes postseason and `player_weekly_stats` does not.** `load_rush_explosive` has no
   `season_type` filter because the table has no such column, so explosive-rate denominators include
   playoff carries while every other volume feature in the model is REG-only. I believe this cannot
   leak (a season's playoffs still precede the next season's Week 1) but it is an unmatched
   denominator and I did not quantify it.

**Also please check, because I cannot check my own work:**

- the look-ahead claim. Measured proxy reads: **0** for all four primaries and for every QB-rushing,
  NGS and explosive arm; 300 per OC-tenure arm; 134 for C1Q. `pos_data.SeasonPanel.ngs_before` and
  `rush_before` are new this batch and are the two accessors I would break first.
- that the 2025 holdout is genuinely untouched. `HOLDOUT_SEASON = 2025` is enforced at the SQL gate in
  five loaders now, two of them written today.
- whether "#29 is dead on both specifications" is over-claimed. Seven arms across two batches, one
  model, one harness. It is a strong claim from a single model family and I would rather you say so
  than have the founder discover it.

## Why

Batch 3 graded nothing SURVIVES, which is the honest and expected outcome. The risk is not that a
false positive shipped -- it is that the **one genuinely valuable result arrived post-hoc**, which is
the exact condition under which this project has previously shipped something it later had to
retract. You have standing authority to block; if the YPC finding should not have been written up at
all in this document, block it and say where it should live instead.

## Done looks like

A reply on this thread listing, per finding, either CONFIRMED / OVERSTATED / WRONG with the specific
number or file:line that supports the call, and an explicit ruling on whether the post-hoc YPC result
may remain in `factor-batch-3-results.md` section 1(1) as written.
