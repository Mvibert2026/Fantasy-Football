# 2026-07-30 — ranker — factor batch 6: QB passing efficiency, sack avoidance, xFP

**23 registered tests, run once, BH at campaign m = 47. Zero SURVIVES.**

## What happened

Dispatched to run N10 (passing efficiency), N11 (sack avoidance) and registry #18 (expected
fantasy points). Pre-commitment committed at `f6e09da` before any arm was fitted; runner
`3541f40`; results `a185a5a`.

**A shared campaign family manifest was created before anything ran.** Four factor batches were
dispatched in parallel against the same harness on the same day. Correcting inside each batch's
own m is the multiplicity failure `CLAUDE.md` §6.3 names, so
`docs/preregistration/families/F-FACTOR-CAMPAIGN-2026-07-30.yaml` now holds one m per batch and
BH is applied at the sum (47 at run time). Because a running batch cannot see a concurrent
batch's m, every surviving arm also reports a **breaking m** — the largest denominator at which
it would still clear q=0.10.

**The dispatch's data premise was wrong and was corrected before fitting, not routed around.** It
stated `passing_cpoe` was "11% populated" and that EPA had to come from `pbp`. Measured: 2.7%
across all positions but **99.9%** on QB rows with ≥10 attempts; `passing_epa` **100%** populated
1999–2025; and `pbp` as ingested has **no `epa`, `cpoe`, `sack` or `success` column at all**. So
EPA/dropback went from "blocked" to a deep-sample arm, and `pbp`'s missing payload became a
`data-ops` thread.

## What was found

**#18 xFP is rejected with evidence.** Replacing realised prior points per game with the prebuilt
xFP model's *expected* points per game is worse at all four positions (+0.66% to +1.64% of the
model's own error; 3 of 4 BH-significant; all four worse on the ADP board). The overlap diagnostic
— mandated in the pre-commitment with its threshold fixed in advance — says why:
`corr(xFP/g, points/g)` is 0.949–0.964, and the rule "above 0.95 it is a restatement" fires at WR,
RB and TE. A pre-registered directional prediction (the luck residual should carry a negative
coefficient) **failed**: positive in 33 of 44 fits, unanimous at QB, RB and WR.

**QB now has two measured inputs and the board cannot use either.** ANY/A and passer rating are the
first QB-specific arms in this project to clear both E1a and E1b (−1.26%/−2.23% and −0.85%/−2.52%
on the board, breaking m 308), and both are PROJECTION-ONLY — board Spearman negative, and passer
rating's interval excludes zero on the wrong side (−0.0180 [−0.0350, −0.0005]). **Projecting QB
attempts better does not rank quarterbacks better.** EPA/dropback, the strongest external claim,
is board-negative and weaker than a box-score passer rating. CPOE NULL. Sack rate MARGINAL and
board-negative.

**Descriptively**, the external stickiness ordering does not reproduce: EPA, passer rating, CPOE
and sack rate are indistinguishable at YoY r ≈ 0.47 on 782 pairs, and ANY/A — the best-performing
arm — is the *least* persistent of the five.

## Hygiene

- **Zero season-N reads across all 23 arms and 4 primaries**, enforced by the harness rather than
  asserted. Batch 6 has no proxy block at all.
- **The VOID coverage rule did not fire.** Three coverage controls returned |E1a| ≈ 2×10⁻¹⁴ —
  perfect collinearity with columns the model already holds. The batch-2 coverage-artifact channel
  is closed here.
- **The leak trigger did not fire.** Largest improvement anywhere is 1.26% against a 2% threshold.
- One **grader artefact** named rather than left standing: WR's coverage control graded MARGINAL on
  a point estimate of −2.2×10⁻¹⁴ targets. The decision rules have no magnitude floor.

## Threads opened

| to | subject |
|---|---|
| `strategist` | campaign denominator ruling (incl. whether batch 3 is re-graded), the rate-channel specification §7 recommends, magnitude floor, overlap instrument |
| `data-ops` | `pbp` re-ingest with `epa`/`cpoe`/`sack`/`success`/`first_down_pass`/`yards_after_catch`/`season_type`; pin or checksum `ff_opportunity`'s model version |
| `librarian` | five registry/ledger row changes — #18, N10, N11, the wrong 11% figure, and the PBP-dependent rows that must stay blocked |

**Not dispatched by me and still required:** `fable`, at maximum effort, on the result.

## What must not happen next

A sixth QB volume arm. Five have been run (batch 3's A1/A2, batch 6's P1–P4/K1) and the batch
established that the QB ranking error is not in the attempts channel.
