---
ID: 2026-08-01-c1-the-registered-win-rule-has-a-14-6-false-posi
FROM: ranker
TO: strategist
STATUS: BLOCKED-ON-YOU
BLOCKS: batch C1 grading (arms continue to run and record)
OPENED: 2026-08-01
---

## Ask

**Rule on a replacement WIN criterion for the absolute-rank-correlation endpoint.** The one
registered in batch-C1 — and used unchanged in batch-B1 — awards a WIN to pure noise on 14.6% of
cells against a nominal 2.5%. I own the model; I do not own the decision rule, and I am not going
to pick my own replacement threshold after seeing what it would do to my arms.

## The measurement

Batch C1 registered a **placebo arm F0**: a column of seeded N(0,1) noise appended to v2's volume
design, deterministic in `(player_id, season)` via SHA-256, provably carrying no signal. Registered
prediction, written before compute: *0 WIN, 0 HARM*.

**F0 returned a BH-robust WIN at TE: Δρ = +0.0303, CI [+0.0134, +0.0459], p = 0.0002**, and the
registered inclusion rule graded the placebo `INCLUDE`.

I then replicated the placebo across **12 independent noise draws** on the same harness, same
control (v2 games arm G0, CTRL-A, targets 2018–2024), same estimator
(`experiments/bottomup/v2/placebo_replication.py`; raw at
`experiments/bottomup/results/factor_c1_placebo_replication.csv`):

| position | graded n | placebo WIN rate | placebo HARM rate | mean Δ | sd | max Δ | mean seasons + / − / **exactly 0** |
|---|---|---|---|---|---|---|---|
| QB | 19 | **33.3%** | 0% | +0.0040 | 0.0035 | +0.0092 | 2.50 / 0.75 / **3.75** |
| RB | 43 | **16.7%** | 0% | +0.0019 | 0.0033 | +0.0085 | 3.83 / 2.42 / 0.75 |
| TE | 14 | **8.3%** | 8.3% | +0.0046 | 0.0093 | +0.0197 | 1.92 / 1.92 / **3.17** |
| WR | 50 | 0% | 8.3% | −0.0005 | 0.0021 | +0.0012 | 3.08 / 3.33 / 0.58 |
| **all** | — | **14.6% (7/48)** | 4.2% | — | — | — | — |

## Two distinct defects, and they need different fixes

**1 — The estimator is miscalibrated at n = 7 seasons.** Spearman over 10–19 players is discrete: a
per-season delta is either *exactly zero* (no pair flips) or a quantum of ±0.02–0.06. At QB a mean
of **3.75 of 7 seasons contribute an exact zero**. A season-block bootstrap resampling such a vector
puts essentially all its mass on one side of zero whenever no season goes the other way — the CI
excludes zero **by construction, at any effect size**. This is the dominant defect and it is a
property of the test, not of the model.

**2 — Adding any regressor carries a small upward bias, scaling with 1/n.** Mean placebo Δ is
+0.0040 (QB), +0.0019 (RB), +0.0046 (TE), −0.0005 (WR) against graded populations of 19, 43, 14,
50. A noise column damps an ill-conditioned small-sample fit. Small, but it means the null is **not
centred on zero** and a factor must clear a positive bar.

## What I propose, so you have something to attack rather than a blank page

An **empirical placebo null**: run K independent placebo draws per position, and require a
treatment cell's Δ to exceed the position-specific placebo distribution's 95th percentile — a
permutation-style calibration that fixes both defects at once, because it is centred on the
observed bias and shaped by the observed discreteness. K = 12 is too thin for a 95th percentile; a
**40-draw replication is running now** and will be committed whether or not you adopt this.

Three things I specifically want ruled on, not assumed:

1. **Is the placebo null the right calibration**, or do you want a different estimator entirely
   (sign test across seasons; permutation of the outcome vector within season; a pooled-across-
   seasons rho rather than a mean of per-season rhos)?
2. **Does the campaign BH layer still apply on top**, and at what M? Stacking BH on an
   already-calibrated threshold may be double-counting; dropping it may be under-correcting.
3. **Is per-season Spearman on 10–19 players the right endpoint at all?** The discreteness is the
   root cause. A pooled or top-k-weighted endpoint may be better behaved. This is the expensive
   answer and I am not assuming it is wrong.

## Why

Without a ruling, batch C1 cannot answer the question the founder asked — "tell us whether to
include the factor or not" — because its WIN criterion cannot tell a factor from noise at three of
four positions. Arms keep running regardless, so the cost of a slow ruling is bounded; the cost of
no ruling is a batch of INCLUDE verdicts nobody should believe.

**This reaches beyond C1, and here is the part I am deliberately not acting on.** Batch B1 graded
the same endpoint, same estimator, same n, same positions, so the calibration applies to its grades
too. Stating it precisely, in both directions:

- **G2a's wins survive comfortably.** RB +0.072 and WR +0.048 are far outside anything 12 placebo
  draws produced at those positions (RB max +0.0085; WR max +0.0012). **QB +0.019 is the weak one**
  — outside the QB placebo range (max +0.0092) but by a modest margin, at the position where the
  placebo wins 33% of the time.
- **The WR HARM of −0.0125 that rejected both G1 and G1a is the cell most worth re-examining.** One
  placebo draw in twelve produced a WR HARM of −0.0068 on this harness. −0.0125 is larger, but it is
  the same order of magnitude, and two arms were rejected on it.

**B1 is `fable`'s registered batch and I have not re-graded it and will not.** I am handing you the
calibration; whether it changes anything there is yours and fable's, not mine. Copying `fable` is
your call — I have not opened a second thread, to avoid two rulings on one question.

## Done looks like

A ruling on (1), (2) and (3), specific enough to implement without a follow-up. Batch C1's arms
keep **running and recording** meanwhile — per-season deltas are estimator-independent, so
re-grading is a mechanical pass over
`experiments/bottomup/results/factor_c1_contrasts.csv` (`run_c1.py --regrade`) and costs no refits.
**No factor will be graded INCLUDE until you rule.** Registration and full write-up:
`docs/ranking/factor-campaign-manifest/batch-C1.md`, `docs/ranking/batch-C1-results.md`.
