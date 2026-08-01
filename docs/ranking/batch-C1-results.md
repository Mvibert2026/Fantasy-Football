# Batch C1 results — the factor inclusion test against ranking v2

**Conclusion first. Live document, updated as each arm grades — not written at the end.**

> **RUNNING COUNT OF INCLUDED FACTORS: 0 of 0 graded.** (Nothing has been run yet.)

Registration: `docs/ranking/factor-campaign-manifest/batch-C1.md` (+ Amendment 1), committed
before any arm was fitted. Control: **v2 with games arm G0**, pinned — the `strategist` G2a ruling
is ADMIT-WITH-CONDITION with conditions unsatisfied, so G0 stands and **no re-grade is owed**.

---

## NEXT STEP

*Rewritten on every update. Written for a successor with none of this context — assume that
successor is me after a reset.*

**Next arm to run:** `F0` — the registered placebo (seeded N(0,1) noise), positions QB/RB/WR/TE,
against **CTRL-A** (`first_feature_season=2012`, targets 2018–2024).

**Command:**

```
.venv/bin/python -m experiments.bottomup.v2.run_c1 --arms F0
```

**Threshold registered for it (before measurement):** WIN = paired season-block bootstrap 95% CI
of the per-season Spearman delta > 0; HARM = CI < 0; else NULL. 4,000 reps, seed 20260801. BH at
`M_campaign` = 130, q = 0.10. **Registered prediction: 0 WIN, 0 HARM.** A WIN here is a finding
about the harness, not about a factor, and it invalidates the batch's WIN rate.

**Primary config it grades against:** v2, games arm **G0**, `experiments/bottomup/ranking_versions/v2.json`.

**Then, in order:** `F1,F1k` · `F2,F2k` · `F3,F3k` · `F4,F4k` · `F5,F5k` · `F6`. Each `*k` is the
paired coverage-indicator control from Amendment 1 and **must be run before its treatment arm's WIN
may be claimed** — the runner marks an unpaired win `WIN (control pending)` and refuses to grade the
factor INCLUDE.

**State on disk after every arm:** `experiments/bottomup/results/factor_c1_cells.csv` (per
position-season) and `factor_c1_contrasts.csv` (graded, BH recomputed over everything accumulated).
`--regrade` with no `--arms` recomputes verdicts from the accumulated contrasts without re-running.

---

## Results table

*(empty — no arm has been graded)*

| factor | position | n | coverage | control ρ | arm ρ | Δ | 95% CI | verdict | BH |
|---|---|---|---|---|---|---|---|---|---|

## Factor verdicts

*(empty)*

## The hazard watch

The registered expectation is a **higher** hit rate than the old consensus-derived campaign, and
that a high rate is a warning rather than good news. Registered band: **2–5 WIN cells of 19
non-placebo treatment cells (10–26%)**. Two instruments:

1. **F0**, the placebo — measures how often this exact harness hands a WIN to a column that
   provably cannot carry signal.
2. **F1k–F5k**, the coverage-indicator controls — measure how much of any win is the
   presence/join flag rather than the metric. This is the geometry batch 7 measured at 215% of its
   own treatment.

**Observed so far: n/a.**
