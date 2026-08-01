# Batch C1 results — the factor inclusion test against ranking v2

**Conclusion first. Live document, updated as each arm grades — not written at the end.**

> ## The registered decision rule is broken, and the placebo proved it on the first arm.
>
> **F0 — a column of seeded noise that provably cannot carry signal — returned a BH-robust WIN at
> TE (+0.0303, CI [0.0134, 0.0459], p = 0.0002) and the registered inclusion rule graded it
> `INCLUDE`.**
>
> Replicating the placebo across **12 independent noise draws** puts a number on it: the harness
> awards a WIN to pure noise on **14.6% of cells (7 of 48)** against a nominal 2.5% — **QB 33%,
> RB 17%, TE 8%, WR 0%.**
>
> **No factor in this batch may be graded INCLUDE on that rule, and none has been.** Grading is
> suspended pending a `strategist` ruling on a replacement rule; a thread is open. Arms continue to
> **run and record** — the per-season deltas are estimator-independent and re-grading is mechanical.

> ## RUNNING COUNT OF INCLUDED FACTORS: **0 of 6 measured.** All six returned NULL.
>
> | factor | source | result |
> |---|---|---|
> | **F1** offensive snap share | `snap_counts` 2013+ | NULL at RB/WR, **HARM at TE** |
> | **F2** red-zone (inside-20) usage share | `pbp` 2009+ | NULL at all three |
> | **F3** expected fantasy points + luck residual | `ff_opportunity` 2006+ | NULL — **RB +0.0186, p = 0.059, the near-miss** |
> | **F4** NGS average separation | `ngs_receiving` 2016+ | NULL at both |
> | **F5** route participation / TPRR (proxy) | `participation` 2016+ | NULL at all three |
> | **F6** steeper recency weighting | model constant | NULL — **QB +0.0266, sign pattern exactly as predicted** |
>
> **The honest headline is not "the well is dry."** It is that the four factors most often named in
> this repo as *present in the database and untouched* — snap share, red-zone usage, xFP, route
> participation — do not improve v2's ordering at 92–100% coverage on the full available window.
> Two hypotheses survive the placebo calibration and neither is demonstrated: **xFP at RB** and
> **steeper recency at QB**. Both are flagged for a registered confirmatory test, not included.

> ## The registered decision rule is broken, and the placebo proved it on the first arm.
>
> **F0 — seeded noise that provably cannot carry signal — returned a BH-robust WIN at TE
> (+0.0303, CI [+0.0134, +0.0459], p = 0.0002) and the registered rule graded it `INCLUDE`.**
> Replication across independent noise draws measures the harness's false-positive rate at
> **~11–15% of cells against a nominal 2.5%** (QB 15%, RB 15%, TE 12%, WR 0%).
>
> **This cannot have manufactured an inclusion in this batch** — miscalibration inflates false
> *positives*, and there are none: every candidate factor is NULL. The NULLs stand. What it binds is
> the **next** batch. `strategist` owns the replacement rule; thread
> `docs/handoffs/2026-08-01-c1-the-registered-win-rule-has-a-14-6-false-posi.md` is BLOCKED-ON-YOU.

Registration: `docs/ranking/factor-campaign-manifest/batch-C1.md` (+ Amendment 1), committed before
any arm was fitted. Control: **v2 with games arm G0**, pinned — the `strategist` G2a ruling is
ADMIT-WITH-CONDITION with conditions unsatisfied, so G0 stands and **no re-grade is owed**.

---

## NEXT STEP

*Rewritten on every update. Written for a successor with none of this context — assume that
successor is me after a reset.*

**Blocking question, not blocking work:** the WIN criterion registered in batch-C1 (paired
season-block bootstrap 95% CI excluding zero) has a measured false-positive rate of ~14.6% against
a nominal 2.5%. `strategist` owns the replacement rule; thread
`docs/handoffs/2026-08-01-c1-the-registered-win-rule-has-a-146-false-posi.md`. **Do not grade any
factor INCLUDE until that lands.**

**All six candidate factors and all five control arms have run and are graded. Nothing in batch C1
is outstanding.** The next actions belong to other roles or to a next batch:

1. **`strategist` ruling on the WIN criterion** — thread
   `docs/handoffs/2026-08-01-c1-the-registered-win-rule-has-a-14-6-false-posi.md`, `BLOCKED-ON-YOU`.
   No further factor batch should be graded on the current rule. C1's NULLs do not depend on it.
2. **A confirmatory test of the two surviving hypotheses**, registered by `strategist` before it is
   run, one arm each, on the replacement rule: **F3 xFP at RB** (+0.0186, above the RB placebo 95th
   percentile +0.0054 and its observed maximum +0.0085) and **F6 steeper recency at QB** (+0.0266
   vs QB placebo q95 +0.0091). Neither may be included on C1's evidence.
3. **A next batch (C2) of untested factors** — the ledger rows still untested for v2 and reachable
   with data in hand: WOPR (T1-15), QB rushing attempts per game (N9), explosive rush rate (N13),
   YAC per reception (N16), receiving share of an RB's own points (N17), late-season role
   trajectory (N19), contract year (T1-27), combine athleticism (N34). **Odds-derived factors stay
   blocked** until `data-ops` lands Vegas odds; `schedules` carries in-season `spread_line` and
   `total_line` but no pre-season win totals, so nothing there is usable as a pre-draft input.

**To re-grade everything after a rule change, with no refits:**

```
.venv/bin/python -m experiments.bottomup.v2.run_c1 --regrade
.venv/bin/python -m experiments.bottomup.v2.c1_report
```

**State on disk after every arm:** `experiments/bottomup/results/factor_c1_cells.csv` (per
position-season) and `factor_c1_contrasts.csv` (graded, BH recomputed over everything accumulated).
`--regrade` with no `--arms` recomputes verdicts from accumulated contrasts without re-running.

---

## The placebo finding, in full

### What was registered, before measurement

> "**F0 (placebo): 0 WIN, 0 HARM.** Any WIN here is a finding about the harness, and it invalidates
> the batch's WIN rate rather than adding to it." — batch-C1, Registered predictions

### What happened

| factor | position | n | control ρ | arm ρ | Δ | 95% CI | p | verdict | BH |
|---|---|---|---|---|---|---|---|---|---|
| F0 | QB | 7 | 0.2450 | 0.2585 | +0.0135 | [−0.0043, +0.0394] | 0.264 | NULL | — |
| F0 | RB | 7 | 0.4398 | 0.4405 | +0.0007 | [−0.0007, +0.0020] | 0.311 | NULL | — |
| F0 | WR | 7 | 0.5602 | 0.5606 | +0.0005 | [−0.0005, +0.0016] | 0.509 | NULL | — |
| **F0** | **TE** | 7 | 0.3966 | 0.4269 | **+0.0303** | **[+0.0134, +0.0459]** | **0.0002** | **WIN** | **yes** |

The registered inclusion rule reads that row as `INCLUDE`.

### Why — two distinct defects, separated by replication

The per-season TE deltas were `{0, 0, +0.020, +0.035, +0.049, +0.055, +0.055}` — **five positive,
two exactly zero, none negative.** Twelve independent placebo draws separate two mechanisms that
would demand different responses:

**Defect 1 — the estimator is miscalibrated at n = 7, and badly.** Spearman on a graded population
of 10–19 players is *discrete*: a delta is either exactly zero (no pair flips) or a quantum of
±0.02–0.06. Many seasons therefore contribute an exact zero — at QB, a mean of **3.75 of 7 seasons**
per draw. A season-block bootstrap resampling such a vector puts essentially all of its mass on one
side of zero whenever no season goes the other way, **at any effect size**. The CI then excludes
zero almost by construction rather than because the effect is real.

| position | placebo WIN rate (12 draws) | nominal | mean seasons: + / − / exactly 0 |
|---|---|---|---|
| QB | **33.3%** | 2.5% | 2.50 / 0.75 / 3.75 |
| RB | **16.7%** | 2.5% | 3.83 / 2.42 / 0.75 |
| TE | **8.3%** (+8.3% HARM) | 2.5% | 1.92 / 1.92 / 3.17 |
| WR | 0% (+8.3% HARM) | 2.5% | 3.08 / 3.33 / 0.58 |
| **all** | **14.6% (7 of 48)** | **2.5%** | — |

**Defect 2 — adding *any* regressor carries a small upward bias**, concentrated where the graded
population is smallest. Mean placebo delta across 12 draws: **QB +0.0040, RB +0.0019, TE +0.0046,
WR −0.0005** — and the graded populations are QB 19, TE 14, RB 43, WR 50. The ordering of the bias
tracks the ordering of `1/n`. A noise column damps an ill-conditioned small-sample fit; the effect
is small but it is not zero, and it means a factor must clear a *positive* bar, not zero.

The registered F0 draw's TE result (+0.0303) sits ~2.8 sd above the replicated placebo mean at TE
(+0.0046, sd 0.0093). So that specific draw was also an outlier — **both** defects were present in
the single number that triggered this investigation.

### The empirical placebo null — final, 34 independent noise draws

`experiments/bottomup/results/factor_c1_placebo_replication.csv`. The 12-draw figures that triggered
the investigation held up on 34.

| position | graded n | placebo WIN rate | HARM rate | mean Δ | **95th pct** | max Δ |
|---|---|---|---|---|---|---|
| QB | 19 | **14.7%** | 2.9% | +0.0030 | **+0.0110** | +0.0151 |
| RB | 43 | **11.8%** | 0.0% | +0.0006 | **+0.0054** | +0.0085 |
| WR | 50 | 0.0% | 5.9% | −0.0004 | **+0.0015** | +0.0029 |
| TE | 14 | **11.8%** | 2.9% | +0.0062 | **+0.0233** | +0.0280 |
| **all** | — | **9.6%** | 2.9% | — | — | — |

**Only two cells in the entire batch clear their position's placebo 95th percentile**, and both are
NULL under the registered rule:

| hypothesis | Δ | placebo q95 | placebo max |
|---|---|---|---|
| **F3 xFP at RB** | **+0.0186** (p = 0.059) | +0.0054 | +0.0085 |
| **F6 steeper recency at QB** | **+0.0266** | +0.0110 | +0.0151 |

Neither may be included on this batch's evidence. Both are handed to `strategist` for a registered
confirmatory design. **F6 is the one worth prioritising** — it is `CLAUDE.md` §6.4's own question,
it needs no new data, and its sign pattern across positions was exactly as registered. The risk
against it is equally specific: QB is where the placebo wins most often (14.7%) and n = 19.

### What this does and does not say about batch B1

B1 graded the same endpoint with the same estimator at the same n, so the calibration applies to it
too. **It does not overturn B1's headline grades, and saying so would be as wrong as ignoring the
problem:**

- **G2a's wins survive comfortably** — RB +0.072 and WR +0.048 are far outside anything 12 placebo
  draws produced at those positions (RB max +0.0085, WR max +0.0012). QB +0.019 is outside the QB
  placebo range (max +0.0092) but by a smaller margin, and QB is where the placebo wins 33% of the
  time; that cell is the weakest of the three and should be treated as such.
- **The WR HARM that rejected G1 and G1a (−0.0125) is the cell to re-examine.** One placebo draw of
  twelve produced a WR HARM of −0.0068 on the same harness. −0.0125 is larger, but it is the same
  order of magnitude, and a rejection decision resting on it deserves the calibrated comparison.

Both observations are handed to `strategist` and `fable` rather than acted on here — B1 is fable's
batch and I do not re-grade another agent's registered work.

---

## Results and verdicts

<!--C1-TABLE-START-->
### Results table

| factor | position | n | coverage | control ρ | arm ρ | Δ | 95% CI | vs placebo null | verdict | BH |
|---|---|---|---|---|---|---|---|---|---|---|
| F0 PLACEBO | QB | 7 | — | 0.2450 | 0.2585 | +0.0135 | [-0.0043, +0.0394] | **clears** | NULL | — |
| F0 PLACEBO | RB | 7 | — | 0.4398 | 0.4405 | +0.0007 | [-0.0007, +0.0020] | inside | NULL | — |
| F0 PLACEBO | TE | 7 | — | 0.3966 | 0.4269 | +0.0303 | [+0.0134, +0.0459] | **clears** | WIN | yes |
| F0 PLACEBO | WR | 7 | — | 0.5602 | 0.5606 | +0.0005 | [-0.0005, +0.0016] | inside | NULL | — |
| F1 | RB | 7 | 0.998 | 0.4314 | 0.4342 | +0.0027 | [-0.0030, +0.0085] | inside | NULL | — |
| F1 | TE | 7 | 1.000 | 0.4003 | 0.3717 | -0.0285 | [-0.0547, -0.0052] | **below** | HARM | — |
| F1 | WR | 7 | 1.000 | 0.5493 | 0.5468 | -0.0025 | [-0.0091, +0.0030] | inside | NULL | — |
| F1k | RB | 7 | 0.998 | 0.4314 | 0.4319 | +0.0005 | [-0.0023, +0.0033] | inside | NULL | — |
| F1k | TE | 7 | 1.000 | 0.4003 | 0.4003 | +0.0000 | [+0.0000, +0.0000] | inside | NULL (no change) | — |
| F1k | WR | 7 | 1.000 | 0.5493 | 0.5493 | +0.0000 | [+0.0000, +0.0000] | inside | NULL (no change) | — |
| F2 | RB | 7 | 0.985 | 0.4398 | 0.4397 | -0.0001 | [-0.0072, +0.0065] | inside | NULL | — |
| F2 | TE | 7 | 1.000 | 0.3966 | 0.3986 | +0.0020 | [+0.0000, +0.0060] | inside | NULL | — |
| F2 | WR | 7 | 0.994 | 0.5602 | 0.5592 | -0.0010 | [-0.0028, +0.0008] | inside | NULL | — |
| F2k | RB | 7 | 0.985 | 0.4398 | 0.4399 | +0.0002 | [+0.0000, +0.0005] | inside | NULL | — |
| F2k | TE | 7 | 1.000 | 0.3966 | 0.3966 | +0.0000 | [+0.0000, +0.0000] | inside | NULL (no change) | — |
| F2k | WR | 7 | 0.994 | 0.5602 | 0.5600 | -0.0002 | [-0.0007, +0.0000] | inside | NULL | — |
| F3 | QB | 7 | 1.000 | 0.2450 | 0.2484 | +0.0034 | [-0.0300, +0.0371] | inside | NULL | — |
| F3 | RB | 7 | 0.993 | 0.4398 | 0.4584 | +0.0186 | [-0.0003, +0.0404] | **clears** | NULL | — |
| F3 | TE | 7 | 1.000 | 0.3966 | 0.4229 | +0.0263 | [-0.0133, +0.0709] | **clears** | NULL | — |
| F3 | WR | 7 | 1.000 | 0.5602 | 0.5594 | -0.0008 | [-0.0076, +0.0048] | inside | NULL | — |
| F3k | QB | 7 | 1.000 | 0.2450 | 0.2450 | +0.0000 | [+0.0000, +0.0000] | inside | NULL (no change) | — |
| F3k | RB | 7 | 0.993 | 0.4398 | 0.4399 | +0.0001 | [+0.0000, +0.0003] | inside | NULL | — |
| F3k | TE | 7 | 1.000 | 0.3966 | 0.3966 | +0.0000 | [+0.0000, +0.0000] | inside | NULL (no change) | — |
| F3k | WR | 7 | 1.000 | 0.5602 | 0.5602 | +0.0000 | [+0.0000, +0.0000] | inside | NULL (no change) | — |
| F4 | TE | 6 | 0.922 | 0.4044 | 0.3824 | -0.0220 | [-0.0488, +0.0047] | **below** | NULL | — |
| F4 | WR | 6 | 0.928 | 0.5338 | 0.5337 | -0.0000 | [-0.0019, +0.0019] | inside | NULL | — |
| F4k | TE | 6 | 0.922 | 0.4044 | 0.3915 | -0.0128 | [-0.0344, +0.0000] | **below** | NULL | — |
| F4k | WR | 6 | 0.928 | 0.5338 | 0.5346 | +0.0008 | [-0.0007, +0.0020] | inside | NULL | — |
| F5 | RB | 6 | 0.994 | 0.4246 | 0.4266 | +0.0019 | [-0.0137, +0.0192] | inside | NULL | — |
| F5 | TE | 6 | 1.000 | 0.4044 | 0.4047 | +0.0004 | [-0.0059, +0.0062] | inside | NULL | — |
| F5 | WR | 6 | 1.000 | 0.5338 | 0.5355 | +0.0018 | [-0.0007, +0.0053] | **clears** | NULL | — |
| F5k | RB | 6 | 0.994 | 0.4246 | 0.4256 | +0.0010 | [-0.0012, +0.0031] | inside | NULL | — |
| F5k | TE | 6 | 1.000 | 0.4044 | 0.4044 | +0.0000 | [+0.0000, +0.0000] | inside | NULL (no change) | — |
| F5k | WR | 6 | 1.000 | 0.5338 | 0.5341 | +0.0003 | [-0.0025, +0.0027] | inside | NULL | — |
| F6 | QB | 7 | — | 0.2450 | 0.2715 | +0.0266 | [-0.0110, +0.0714] | **clears** | NULL | — |
| F6 | RB | 7 | — | 0.4398 | 0.4307 | -0.0091 | [-0.0229, +0.0044] | **below** | NULL | — |
| F6 | TE | 7 | — | 0.3966 | 0.3851 | -0.0115 | [-0.0477, +0.0239] | **below** | NULL | — |
| F6 | WR | 7 | — | 0.5602 | 0.5495 | -0.0107 | [-0.0284, +0.0050] | **below** | NULL | — |

### Factor verdicts

| factor | verdict | positions won | basis |
|---|---|---|---|
| **F0** PLACEBO (seeded N(0,1) noise) | **HARNESS DEFECT — not a factor verdict** | TE | 4 cells graded |
| **F1** offensive snap share, recency-weighted | **NULL** | — | 3 cells graded |
| **F2** red-zone (inside-20) usage share of team | **NULL** | — | 3 cells graded |
| **F3** expected fantasy points per game + realised-minus-expected residual | **NULL** | — | 4 cells graded |
| **F4** NGS average separation (lag 1) | **NULL** | — | 2 cells graded |
| **F5** route participation and targets per route run (LABELLED PROXY) | **NULL** | — | 3 cells graded |
| **F6** steeper recency weighting of prior seasons (0.70/0.22/0.08) | **NULL** | — | 4 cells graded |

**Included factors: 0. Candidate factors measured: 6 of 6.**
<!--C1-TABLE-END-->

## The hazard watch

The registered expectation was a **higher** hit rate than the old consensus-derived campaign, with a
high rate to be treated as a warning rather than good news. Registered band: **2–5 WIN cells of 19
non-placebo treatment cells (10–26%)**.

**Observed so far:** the placebo alone produces WINs at 14.6% — *inside* the band predicted for real
factors. The hazard was not merely real, it is large enough that the registered band cannot
distinguish a batch of genuine factors from a batch of noise. This is exactly the failure mode the
placebo was registered to catch, and it caught it on arm one.
