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

### 1. Two campaign manifests were built for the same problem on the same day — rule on it

Four factor batches ran in parallel on 2026-07-30. **Two of them independently concluded that BH
must be applied at the campaign denominator and each built a manifest, without seeing the other.**

- Batch 5 opened **campaign C2**, `docs/ranking/factor-campaign-manifest/`, one file per batch,
  rule `M_campaign = max(Σ_b m_b, FLOOR = 80)`, batches 1–3 explicitly not re-graded.
- Batch 6 opened `docs/preregistration/families/F-FACTOR-CAMPAIGN-2026-07-30.yaml`, a single
  shared file, and graded at **47** (its own 23 plus batch 3's 24).

**I resolved this myself rather than leaving two manifests standing, and I want the resolution
reviewed.** C2 wins on the point that matters under concurrency — one file per batch cannot be
clobbered by four simultaneous writers, and mine could have been. Batch 6 is now registered at
`docs/ranking/factor-campaign-manifest/batch-6.md` with m = 23, my yaml is retired to a pointer
that records what happened, and **every published batch-6 grade is re-stated at M = 80.**

**Nothing was rerun.** The pre-commitment required every surviving arm to carry a **breaking m** —
the largest denominator at which it would still clear BH q=0.10 — precisely because a running
batch cannot see a concurrent batch's m. Moving 47 → 80 changed **exactly one arm**, in the
conservative direction: X3 (xFP luck residual) at RB, breaking m 56, BOARD-NEUTRAL → MARGINAL.
Every other graded arm has breaking m 140–1721. The CSV carries both `bh_c47_*` and `bh_c80_*`.

**What I need from you, specifically:**

- **Is the breaking-m device sound**, or is it a way of appearing rigorous while still letting the
  denominator move after results are known? It just did the job it was registered for, which is
  the moment to check whether it is legitimate rather than merely convenient.
- **Is C2's FLOOR = 80 the right instrument?** Registered batches are 4 (m=8), 5 (17), 6 (23),
  7 (16), Σ = 64 — so the floor binds and the campaign is being corrected at a denominator larger
  than the tests actually run. That is conservative, but it is also a number chosen a priori
  rather than counted.
- **Should batch 3 be re-graded?** C2 says no. Batch 3 ran and published against its own m = 24
  hours before either manifest existed. Its numbers are unchanged; only the BH threshold moves. I
  did not touch another batch's results.
- Batch 7 grades at m = 80 and states "if the total comes in under 80, nothing is relaxed."
  Batch 6 now matches. Batches 4 and 5 should be checked for the same.

### 2. Register the rate-channel specification — the thing batch 6 says to build next, and it is not an arm

**The finding that motivates it.** At QB, two arms improved the attempts projection
significantly and on the draft board (ANY/A −1.26% full universe / −2.23% board; passer
rating −0.85% / −2.52%, both breaking m = 308) **and the ranking did not improve** — board
Spearman negative for both, and passer rating's interval **excludes zero on the wrong side**
(−0.0180 [−0.0350, −0.0005]). So the QB ranking's error is **not in the attempts channel**,
and five volume arms have now been run at QB (batch 3's A1/A2, batch 6's P1–P4/K1).

**What batch 6 could not test, and why that reason turned out to be wrong.**
`pos_model.ShrunkRate` has no covariate mechanism, so *"does last season's efficiency predict
next season's efficiency beyond the player's own shrunk lagged rate"* was not askable. Batch 6
registered that as a limitation **before fitting** (`factor-batch-6-precommit.md` §4a) on the
grounds that it needed a change to shared model code while three batches were editing those
modules, and routed every arm through the volume spec instead.

**Batch 7 solved it the same day and I did not know.** `factor-batch-7-precommit.md` §2
registers a **batch-local subclass**: after the ordinary fit, the residual of the realised rate
against the model's own shrunk prediction is regressed on the centred covariate by weighted
least squares, weights = the rate's own denominator, veterans only. One extra parameter, an
overridden `_make_model`, **`pos_model.py` untouched**. It is used on `tdpc` and `ypr` at RB.

**So the QB rate-channel test is not a build.** It is batch 7's subclass pointed at `ypa`,
`tdpa` and `intpa` with `epa_db_w`, `anya_w`, `pratg_w`, `cpoe_w`, `sackrate_w` — features batch
6 has already built, validated and shipped in `factor_features6.py`. I am not going to run it
without a registration, which is the ask.

**What is genuinely yours to decide:**

- Which rate(s) it may attach to. Five metrics × three rates is 15 tests; that is a large slice
  of a campaign already at 80 and I do not think it should be run as a full cross.
- Whether γ counts as one test per (metric, rate) cell, and whether a metric that already failed
  in the volume channel gets a second slice of the denominator at all.
- **Whether the rate channel is even the right door.** The batch-6 finding is only that the
  *attempts* channel is not where the QB ranking error is. It does not establish that the rate
  channel is — availability and the rushing stream are equally live candidates, and batch 3
  owns the rushing one.

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

Item 3 will otherwise be re-decided differently by whoever runs batch 8 — batch 7 registers three
coverage controls of its own and will hit the same magnitude-floor problem.

## Done looks like

1. A ruling on the campaign denominator: whether the breaking-m device is legitimate, whether
   FLOOR = 80 is the right instrument now that Σ m_b = 64, and whether batch 3 is re-graded.
   Written into `docs/ranking/factor-campaign-manifest/README.md` so it is not re-litigated.
2. A registered pre-registration for the rate-channel specification (or a reasoned refusal
   naming the channel to attack instead).
3. A yes/no on a magnitude floor in the decision rules, and on the overlap instrument.

## Evidence

- `docs/ranking/factor-batch-6-precommit.md` (`f6e09da`, committed before any arm was fitted)
- `docs/ranking/factor-batch-6-results.md` (`a185a5a`)
- `docs/ranking/factor-campaign-manifest/batch-6.md` (C2 registration)
- `docs/preregistration/families/F-FACTOR-CAMPAIGN-2026-07-30.yaml` (retired, records the correction)
- `experiments/bottomup/results/factor_batch6_results.csv` and three companions
