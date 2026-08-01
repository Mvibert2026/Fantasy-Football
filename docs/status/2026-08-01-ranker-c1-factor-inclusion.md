# 2026-08-01 · ranker · Batch C1 — the factor inclusion test against v2

**What was asked.** Begin the factor inclusion campaign against ranking **v2**, per the founder's
instruction (`FR-2026-08-01-need-an-inclusion-test-run-candidate-factors-as`): the ~90 nulls from
batches 1–7 were measured against a consensus-derived board and carry almost no information about
what belongs in v2, so the inclusion test has never actually been run.

## Result, conclusion first

**Six candidate factors measured against v2. All six NULL. Zero factors included.**

| factor | source | result |
|---|---|---|
| F1 offensive snap share | `snap_counts` 2013+ | NULL at RB/WR, HARM at TE |
| F2 red-zone (inside-20) usage share | `pbp` 2009+ | NULL at all three |
| F3 xFP + luck residual | `ff_opportunity` 2006+ | NULL — RB +0.0186, p = 0.059, the near-miss |
| F4 NGS average separation | `ngs_receiving` 2016+ | NULL at both |
| F5 route participation / TPRR (proxy) | `participation` 2016+ | NULL at all three |
| F6 steeper recency weighting | model constant | NULL — QB +0.0266, sign pattern as registered |

The four factors most often named in this repo as *present in the database and untouched* — snap
share, red-zone usage, xFP, route participation — do not improve v2's ordering, at 92–100% coverage
on the full available window. Registered hit-rate band was 2–5 WIN cells of 19; **observed 0 of 19**.

## The finding that matters more than the factor results

**The registered WIN rule is broken, and the registered placebo caught it on arm one.** A column of
seeded noise returned a BH-robust WIN at TE (+0.0303, p = 0.0002) and the inclusion rule graded the
placebo `INCLUDE`. Replication across **34 independent noise draws** measures the harness's
false-positive rate at **9.6% of cells against a nominal 2.5%** (QB 14.7%, RB 11.8%, TE 11.8%,
WR 0%). Two mechanisms: the season-block bootstrap is miscalibrated at n = 7 because per-season
Spearman on 10–19 players is discrete and mostly contributes exact zeros; and adding any regressor
carries a small upward bias scaling with 1/n.

**This cannot have manufactured an inclusion in C1** — miscalibration inflates false positives and
there are none. The NULLs stand. It binds the next batch, and `strategist` owns the replacement rule
(thread `2026-08-01-c1-the-registered-win-rule-has-a-14-6-false-posi`, BLOCKED-ON-YOU).

A **second, separate defect** was caught by Amendment 1's control arm: `F2k` graded a BH-robust WIN
on a mean delta of **3.97 × 10⁻¹⁷** — float64 noise whose sub-epsilon per-season deltas shared a
sign. Fixed by snapping |Δ| < 1e−9 to zero; that cleared three spurious wins and left the placebo's
real TE win standing.

## What was built

- `docs/ranking/factor-campaign-manifest/batch-C1.md` — registration + Amendment 1, committed before
  any arm was fitted. m_b = 38, `M_campaign` = 130.
- `experiments/bottomup/v2/factors_c1.py` — factor blocks. Snap share, xFP, NGS separation and
  routes are **imported** from batches 3/5/6/7 rather than reimplemented; red-zone usage (new, `pbp`
  2009+) and the placebo are new.
- `experiments/bottomup/v2/run_c1.py` — the runner, written to be interrupted: every arm appends
  cells and contrasts to disk, and `--regrade` recomputes everything from cells with no refits.
- `experiments/bottomup/v2/placebo_replication.py` — the calibration diagnostic.
- `experiments/bottomup/v2/c1_report.py` — regenerates the results table from the artifact so the
  live document cannot drift from it.
- `docs/factor-ledger.md` **Section 0** — the first dispositions ever measured against v2, with the
  standing warning that Sections 1–6 were assigned under the old frame.

## Method notes

Control pinned to **v2 games arm G0** throughout (the G2a ruling is ADMIT-WITH-CONDITION with
conditions unsatisfied; no re-grade owed, and `games_arm` is recorded per row). Three **matched
controls**, one per feature window, so a late-starting source is never confounded with the shorter
training window it forces. Every arm asserted zero season-N proxy reads — so nothing in C1 inherits
the kickoff-dated week-1-roster defect that ruling exposed. **2025 was never read.**

## Open

1. `strategist` ruling on the WIN criterion — no further factor batch should be graded on the
   current rule.
2. A registered confirmatory design for the two hypotheses that clear the placebo null but fail the
   CI rule: **xFP at RB** and **steeper recency at QB**. F6 is the one to prioritise — it is
   `CLAUDE.md` §6.4's own question and needs no new data.
3. A next batch (C2) from the still-untested ledger rows reachable with data in hand. Odds-derived
   factors stay blocked until `data-ops` lands Vegas odds.
