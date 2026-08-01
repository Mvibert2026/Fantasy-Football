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

> **RUNNING COUNT OF INCLUDED FACTORS: 0 — 1 of 6 candidate factors measured.**
> **F1 offensive snap share: NULL at RB and WR, HARM at TE.** The single most-cited untouched factor
> in the ledger (T0-9 / N18), present in `nfl.db` at **99.8–100% coverage**, and it does not improve
> v2 anywhere. Registered prediction was a WIN at RB; it did not deliver one.

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

**Next arm to run:** `F2` and its paired control `F2k` — red-zone (inside-20) usage share of
team, positions RB/WR/TE, against **CTRL-A** (`first_feature_season=2012`, targets 2018–2024).

**Command:**

```
.venv/bin/python -m experiments.bottomup.v2.run_c1 --arms F2,F2k
```

**Threshold registered for it:** as batch-C1 §"Endpoint" — WIN = paired season-block bootstrap 95%
CI of the per-season Spearman delta > 0, 4,000 reps, seed 20260801, BH at `M_campaign` = 130,
q = 0.10 — **plus the interim placebo-null floor below, which is what any WIN must actually clear.**
Registered prediction: NULL-to-WIN at RB, NULL at WR/TE, with the registered downside that red-zone
share is largely a monotone function of volume the model already holds. Control `F2k` predicted NULL.

**Primary config it grades against:** v2, games arm **G0**,
`experiments/bottomup/ranking_versions/v2.json`.

**Interim calibration applied to every cell (pending the strategist ruling):** a cell counts as a
candidate WIN only if its delta exceeds the **position-specific placebo null** in
`experiments/bottomup/results/factor_c1_placebo_replication.csv` — the `vs placebo null` column of
the results table does this automatically. From 12 draws the observed placebo maxima are
**QB +0.0092, RB +0.0085, TE +0.0197, WR +0.0012**; a 40-draw replication is running to give a
stable 95th percentile.

**Then, in order:** `F2,F2k` · `F3,F3k` · `F4,F4k` · `F5,F5k` · `F6`. Each `*k` is the paired
coverage-indicator control from Amendment 1 and **must be run before its treatment arm's WIN may be
claimed** — the runner marks an unpaired win `WIN (control pending)`.

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

### The empirical placebo null (12 draws — provisional, larger replication running)

| position | mean | sd | min | max | q90 |
|---|---|---|---|---|---|
| QB | +0.0040 | 0.0035 | −0.0010 | **+0.0092** | +0.0086 |
| RB | +0.0019 | 0.0033 | −0.0042 | **+0.0085** | +0.0052 |
| TE | +0.0046 | 0.0093 | −0.0067 | **+0.0197** | +0.0192 |
| WR | −0.0005 | 0.0021 | −0.0068 | **+0.0012** | +0.0011 |

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
| F1k | TE | 7 | 1.000 | 0.4003 | 0.4003 | +0.0000 | [+0.0000, +0.0000] | inside | NULL | — |
| F1k | WR | 7 | 1.000 | 0.5493 | 0.5493 | +0.0000 | [+0.0000, +0.0000] | inside | NULL | — |

### Factor verdicts

| factor | verdict | positions won | basis |
|---|---|---|---|
| **F0** PLACEBO (seeded N(0,1) noise) | **HARNESS DEFECT — not a factor verdict** | TE | 4 cells graded |
| **F1** offensive snap share, recency-weighted | **NULL** | — | 3 cells graded |

**Included factors: 0. Candidate factors measured: 1 of 6.**
<!--C1-TABLE-END-->

## The hazard watch

The registered expectation was a **higher** hit rate than the old consensus-derived campaign, with a
high rate to be treated as a warning rather than good news. Registered band: **2–5 WIN cells of 19
non-placebo treatment cells (10–26%)**.

**Observed so far:** the placebo alone produces WINs at 14.6% — *inside* the band predicted for real
factors. The hazard was not merely real, it is large enough that the registered band cannot
distinguish a batch of genuine factors from a batch of noise. This is exactly the failure mode the
placebo was registered to catch, and it caught it on arm one.
