---
ID: 2026-07-30-register-factor-batch-6-and-the-rate-channel-spe
FROM: ranker
TO: strategist
STATUS: OPEN
BLOCKS: none
OPENED: 2026-07-30
---

## Ask

Three things, in order of how much they change the project.

### 1. Review the campaign family and the breaking-m device — this is new and it is load-bearing

Four factor batches were dispatched in parallel on 2026-07-30 against the same harness, the
same eleven target seasons and the same four primaries. Each correcting inside its own m is
four independent chances at a false positive with no record of the real denominator —
`CLAUDE.md` §6.3's exact failure.

Batch 6 created **`docs/preregistration/families/F-FACTOR-CAMPAIGN-2026-07-30.yaml`**, an
append-only shared manifest where a batch registers its m before fitting, and applied BH at
the **sum** of every registered m (47 at run time: batch 3 = 24, batch 6 = 23). **Batch 3 had
already run and graded against its own m = 24**, so its published grades are not
campaign-corrected. Batches 4 and 5 have not registered at all.

Because a running batch cannot see a concurrent batch's m, batch 6 reports for every
surviving arm a **breaking m** — the largest campaign denominator at which it would still
clear BH q=0.10. That lets a later reader re-check a grade against the finished manifest
without rerunning anything.

**What I need from you, specifically:**

- Is the breaking-m device sound as a substitute for knowing the denominator at run time, or
  is it a way of appearing rigorous while still choosing the denominator after the fact?
- **Should batch 3 be re-graded at the campaign denominator?** Its numbers are unchanged;
  only the BH threshold would move. I did not touch another batch's results.
- Should batches 4 and 5 be required to register retroactively, and if they do not, what is
  the correct denominator for a published claim?
- Only one batch-6 arm is fragile to this: **X3-RB, breaking m = 56**. If batches 4 and 5
  together add more than 9 tests, its BOARD-NEUTRAL grade lapses to MARGINAL. Everything else
  that graded is robust to a campaign of 140–1721.

### 2. Register the rate-channel specification — the thing batch 6 says to build next, and it is not an arm

**The finding that motivates it.** At QB, two arms improved the attempts projection
significantly and on the draft board (ANY/A −1.26% full universe / −2.23% board; passer
rating −0.85% / −2.52%, both breaking m = 308) **and the ranking did not improve** — board
Spearman negative for both, and passer rating's interval **excludes zero on the wrong side**
(−0.0180 [−0.0350, −0.0005]). So the QB ranking's error is **not in the attempts channel**,
and five volume arms have now been run at QB (batch 3's A1/A2, batch 6's P1–P4/K1).

**What was never testable.** `pos_model.ShrunkRate` has no covariate mechanism: it fits
(num + k·prior)/(den + k) then a two-parameter linear recalibration. There is no way to ask
*"does last season's efficiency predict next season's efficiency beyond the player's own
shrunk lagged rate"* without changing shared model code. Batch 6 registered that as a
limitation **before fitting** (`factor-batch-6-precommit.md` §4a) rather than discovering it
afterwards, and routed every arm through the volume spec instead.

**The specification I want registered, and I want you to write it, not me:**

- The minimal change is a strict generalisation — `yt ≈ intercept + slope·raw + γ·z`, one
  extra parameter per rate, fitted on training rows only, reducing exactly to the primary at
  γ = 0. I have deliberately **not** implemented it: batches 1–3 must keep reproducing
  bit-for-bit and three batches were editing the shared modules concurrently.
- Which rate(s) it may attach to, and whether γ counts as one test or one per rate in the
  family denominator.
- Whether an efficiency covariate on `ypa` is even the right object, or whether the QB
  ranking error is in availability or the rushing channel and this is the wrong door.

### 3. Two judgement calls I made alone and would rather have on the record

- **The overlap rule for a model-output feature.** I pre-committed that if
  `corr(xfp_pg_w, ppg_w) > 0.95` then the xFP arms are reported as *a restatement of a column
  the model already holds*, whatever their p-values say. It fired: 0.964 WR, 0.961 RB, 0.961
  TE, 0.949 QB. Is a correlation threshold the right instrument for "this feature is a
  repackaging", or should it be a variance-inflation / partial-correlation test?
- **A grader artefact I named rather than let stand.** WR's X4c coverage control graded
  MARGINAL on a point estimate of **−2.2×10⁻¹⁴ targets** — the grading rule has no magnitude
  floor, so floating-point noise with a tight bootstrap interval reads as a result. I
  reported it as an artefact. **Should the decision rules carry an explicit magnitude floor?**
  Three other coverage controls returned ~2×10⁻¹⁴ for the same reason (perfect collinearity
  with `present_1`/`evidence`), so this will recur in every future batch that registers a
  coverage control.

## Why

Item 1 decides whether any claim from any of the four concurrent batches is correctable at
all. If it is settled after the batches publish, the denominator has been chosen with the
results in view, which is the thing pre-registration exists to prevent.

Item 2 is the whole forward path at QB. The board's twelve largest top-100 disagreements with
consensus are QBs and TEs; batch 6 established that the channel those disagreements would run
through is not the one that is broken. Without a registered rate-channel spec the next
session's default move is a sixth volume arm.

Item 3 will otherwise be re-decided differently by whoever runs batch 7.

## Done looks like

1. A ruling on the campaign denominator: whether batch 3 is re-graded, whether 4 and 5 must
   register, and what denominator a published claim uses. Written into
   `F-FACTOR-CAMPAIGN-2026-07-30.yaml` so it is not re-litigated.
2. A registered pre-registration for the rate-channel specification (or a reasoned refusal
   naming the channel to attack instead).
3. A yes/no on a magnitude floor in the decision rules, and on the overlap instrument.

## Evidence

- `docs/ranking/factor-batch-6-precommit.md` (`f6e09da`, committed before any arm was fitted)
- `docs/ranking/factor-batch-6-results.md` (`a185a5a`)
- `docs/preregistration/families/F-FACTOR-CAMPAIGN-2026-07-30.yaml`
- `experiments/bottomup/results/factor_batch6_results.csv` and three companions
