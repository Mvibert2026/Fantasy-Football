# Availability opponent model — ADP central tendency and per-player dispersion: pre-commitment

**Written 2026-07-30 by `strategist`, before any measurement in it has been run.**
Thread 119, FR-131, blocking FR-066 / thread 104 / FR-128.

This is the `full_design` document. A `PR-0NN` registration file referencing it must be created
(with a checked id and a computed `content_hash`) **before** any of M1–M5 executes —
`src/preregistration.require_confirmatory` will refuse otherwise, which is the point. I cannot
compute the content hash without a shell, so the registration file is deliberately not written here.

Everything below was written with **no database access**. The only data consulted are three
committed artifacts: `data/adp-snapshots-ffc/2026-07-29_half_ppr.csv`,
`data/adp-snapshots-ffc/2026-07-30_half_ppr.csv`, and
`data/mock-drafts/yahoo-10team-slot4-2026-07-30.json`.

---

## 0. The decision this is pre-committing

`src/availability.py:simulate_availability` currently runs its opponent model **and** the user's
own BPA arm off `rankings WHERE source='fantasypros_ecr'`, with a single global sigma its own
exported metadata calls "a guess, not fitted to observed drafts."

The proposed change has three separable parts, and they are pre-registered separately so that a
null on one does not drag the others with it:

| Part | Change |
|---|---|
| **A** | Opponent base rank: `fantasypros_ecr` → `ffc_half_ppr_10team`, on a corrected pick axis. |
| **B** | Dispersion: one global sigma → `lambda * s_i`, `s_i` a fitted ADP-position curve normalised to mean 1, `lambda` the swept global scale. |
| **C** | The user's own arm: split off the opponents' array and pointed at `board.json`. |

Part **C** is a defect fix, not a hypothesis — `client_simulation_parameters.algorithm_note`
already claims the user drafts off `board.json` and the code does not (thread 104). It is not in
the BH family and needs no test beyond an assertion that the two arrays are now distinct objects.

---

## 1. Family and multiple-comparisons denominator

- **Family id:** `availability-opponent-model`
- **Declared `m` (confirmatory tests): 4** — H1, H2, H3, H4 below.
- **Exploratory, never in the denominator:** the round-by-round mock deviation figures already
  reported in thread 119 §1, and any descriptive plotting of the dispersion curve.
- BH is applied within family across the declared `m = 4`, and the run log
  (`docs/preregistration/test_run_log.jsonl`) is appended for every run **including nulls**.

**Adding a fifth confirmatory test to this family reopens it and requires every adjusted p in it to
be recomputed.** Declared here so that is a visible cost rather than a silent one.

## 2. Resampling unit and seeds

- **Resampling unit for anything computed over drafts: the draft (room).** Not the pick. Picks
  within a draft are a partition of a fixed set of slots and are strongly dependent by construction.
- **Resampling unit for anything computed over players: the player**, bootstrapped with replacement.
- **The mock drafts are n = 2 rooms.** No confidence interval may be reported from them under any
  resampling scheme. They enter only as a falsification check (H1's secondary) and a shape check.
- **Seeds:** every run records an explicit integer seed. Seeds are never derived from builtin
  `hash()` (guardrails §11.1). Determinism is demonstrated by re-running in a **separate process**
  and comparing byte-for-byte, not by a same-process repeat.
- **Noise floor before any point estimate:** re-run each simulation arm across ≥ 5 seeds and report
  the spread. If the seed-induced range is comparable to the effect claimed, the effect is reported
  as not measurable at that resolution.

---

## M0 — GATE: reconcile FFC's `times_drafted` / `total_drafts_in_sample`

**Not a hypothesis. A data-semantics gate that blocks M2, M3 and H2/H3.**

Every row of `2026-07-30_half_ppr.csv` carries `total_drafts_in_sample = 1254`. Yet:

| player | `average_pick` | `times_drafted` |
|---|---|---|
| Bijan Robinson | 2.0 | 90 |
| Brock Bowers | 44.5 | 225 |
| Brandon Aubrey (PK) | 132.0 | 212 |
| Omarion Hampton | 19.1 | 256 |
| Hunter Henry | 152.3 | 12 |

Bijan Robinson goes at pick 2.0 in effectively every draft; 90 of 1254 is not a selection rate.
Between the 07-29 and 07-30 snapshots Ja'Marr Chase's `times_drafted` fell (189 → 175) while
`total_drafts_in_sample` rose (1187 → 1254).

**Required to clear the gate:**

1. FFC's own documented meaning for both fields, cited.
2. An internal consistency check: `sum(times_drafted)` across the snapshot against
   `picks_per_draft × n_drafts` for whatever `n_drafts` the answer implies. State whether they
   reconcile to within rounding.
3. A stated per-player effective n, `n_i`, to be used as the sampling-variance weight downstream.

**If it does not reconcile:** Part B does not proceed. Part A may. Report the gate failure
plainly; do not substitute a plausible interpretation.

---

## M1 / H1 — Does ADP predict realised pick order better than expert consensus?

**Hypothesis (H1).** For predicting realised draft pick order, `ffc_half_ppr_10team` beats
`rankings WHERE source='fantasypros_ecr'`.

**Data.** All three logged mocks: `yahoo-10team-slot4-2026-07-30`, `yahoo-12team-slot2-2026-07-30`,
`founder-mock-2026-07-29`. Restricted to picks resolved to a canonical player id and to a **common
support** — the set of players carrying a value in *every* candidate source. Report `n` per mock.

**Candidates.** `fantasypros_ecr` (incumbent), `fantasypros_csv_2026draft` (the board),
`ffc_half_ppr_10team`, `ffc_ppr_10team`, `ffc_non_ppr_10team`, each at the snapshot with the
greatest `as_of_date ≤ the draft date`.

**Metric.** Mean absolute error in **picks** between predicted pick position and realised
`overall_pick`, on the corrected pick axis (M4). Spearman ρ reported as secondary only — ρ is
insensitive to the magnitude of a miss and the decision-relevant error here is "how many picks
early/late," not "in what order."

**Reported per mock, never pooled.** Pooling three rooms hides the between-room variance, which is
the entire representativeness question.

**Confirmation threshold.** H1 CONFIRMED iff MAE(`ffc_half_ppr_10team`) < MAE(`fantasypros_ecr`)
in **all three** mocks **and** the mean gap across mocks ≥ 2.0 picks. Otherwise **NULL**.

**This threshold does not gate adoption, and that is deliberate.** Adoption is argued on estimand
grounds (thread 119 §1) and stands whether or not H1 confirms. What the threshold gates is **what
may be claimed**: if H1 is NULL, no export field, tooltip, glossary entry or founder-facing
sentence may state or imply that the ADP-based model is more *accurate*. It may only state that it
is measured in the units of the question and carries a dispersion. Getting this backwards — letting
a null quietly become "well, it's at least as good, so it's better" — is the specific failure this
separation exists to prevent.

**Power, stated honestly.** n = 3 rooms. A sign test floors at p = 0.125. H1 cannot reach
conventional significance and is not claimed to; the threshold is a **consistency-of-direction plus
minimum-effect-size** rule, and it is reported as such.

**Secondary (falsification only, no threshold).** Round-by-round MAE. Already hand-computed for the
10-team mock in thread 119 §1 (R1 1.12 / R2 3.66 / R3 8.22 picks against FFC half-PPR); the run
should reproduce those three numbers as an arithmetic check on the pipeline before trusting
anything else it emits.

---

## M2 / H2 — Is per-player dispersion anything more than a function of ADP position?

**Hypothesis (H2).** After conditioning on ADP position, there is real between-player variance in
true dispersion — i.e. some players are genuinely more unpredictable than their draft position
implies.

**My prior, recorded before the run: H2 is NULL.** The committed CSV shows `std_dev` rising
near-monotonically with `average_pick` (Bijan 2.0→0.7, Breece 28.7→2.9, Bowers 44.5→10.4,
Kittle 117.0→24.9, Strange 145.8→26.9) and compressing at the extreme tail through censoring
(Christian Kirk 194.7→7.7). The eye-catching contrasts FR-131 leads with are ADP-position effects
wearing a disagreement costume. The project's closest prior analogue — FR-086's per-player scoring
*shape* — returned an empirical-Bayes τ̂² of exactly zero.

**Data.** `ffc_adp_snapshots`, `adp_source='ffc_half_ppr_10team'`, latest snapshot, restricted to
`position IN ('QB','RB','WR','TE')` — PK and DEF dropped, since they are not in the simulator's
universe and their dispersion behaves differently (McPherson `std_dev` 36.4).

**Model.** `log(std_dev_i) = a + b·log(average_pick_i) + e_i`, weighted by `n_i` from M0. Report
`b` with a bootstrap SE over players, and R².

**Estimator for H2.** Empirical Bayes on the residuals: treat `log(std_dev_i)` as observed with
within-player sampling variance ≈ `1/(2(n_i − 1))` (delta method for `log s` of a normal sample),
and estimate `tau_hat^2`, the between-player variance of *true* log-dispersion after the ADP trend
is removed. Report `tau_hat^2` with a player-level bootstrap CI.

**Confirmation threshold.**
- **H2 CONFIRMED** iff the lower bound of `tau_hat^2`'s 95% bootstrap CI is **> 0**. Ship an
  EB-shrunk per-player residual multiplier with shrinkage factor
  `tau_hat^2 / (tau_hat^2 + 1/(2(n_i − 1)))`, and report the shrinkage factor alongside each value
  so a heavily-shrunk player is visibly heavily shrunk.
- **H2 NULL** otherwise. Ship `s_i = ghat(adp_i)/mean(ghat)` alone, and the export states:
  *"per-player dispersion beyond the ADP-position effect was tested and found indistinguishable
  from sampling noise."*

**Stability requirement, pre-committed.** Refit on `ffc_non_ppr_10team` and `ffc_ppr_10team`. If
`b_hat` differs across formats by more than its own bootstrap SE, the curve is format-specific, not
structural, and must be fitted per format rather than shared. Also refit on the **07-29** snapshot:
if `b_hat` moves materially in one day, the curve is not stable enough to hardcode and only the
global scale should ship.

**Instability already measured, and it is the reason this test exists.** Between 07-29 and 07-30,
same source and format: Kamara 26.2 → 19.0 (−27%, n = 28), Hunter Henry 28.0 → 24.8 (−11%, n = 12),
Kittle 26.9 → 24.9 (−7%, n = 56), McPherson 39.2 → 36.4 (−7%, n = 12) — while Gibbs (0.6), Bijan
(0.7) and Chase (1.5) did not move at all. The four unstable ones are exactly FR-131's four
headline exhibits and exactly the four with the smallest n.

---

## M3 / H3 — Calibrating the global scale through the simulator

**The error this exists to prevent.** FFC's `std_dev` is the dispersion of a **realised** pick — an
output. The simulator's sigma is a **latent board perturbation**, and the simulator's own mechanics
(need penalty, players being removed, snake order) add variance on top of it. Substituting the
observed sd into the noise term over-disperses, and it over-disperses in a way that *looks like
humility*: every availability probability drifts toward 0.5. Do not substitute. Calibrate.

**Hypothesis (H3).** The global scale that makes the simulator reproduce observed market dispersion
is **below** today's default of 10 over the tracked top-80 range.

**Directional pre-commitment: `lambda_hat < 10`.** Basis, both from committed artifacts:
(i) over players in roughly ADP 1–90 the typical FFC `std_dev` is ~4–5, not the ~9.7 median quoted
for the whole 180-row file including kickers and the tail; (ii) in the 10-team Yahoo mock the
implied per-round dispersion is 1.40 / 4.59 / 10.30 picks for rounds 1/2/3, against the ~8 picks a
flat sigma = 10 implies in every round. Both point the same way in the range the model reports.

Flagging for my own record: this is an **arithmetic** prediction, not a situation narrative. The
category of prediction that has repeatedly failed in my prior sessions is the one that
over-credits a story; this one has no story in it.

**Procedure.** Fix `s_i` from M2. Sweep `lambda` over a grid. For each `lambda`, run
`simulate_availability` and record the simulated distribution of each player's realised pick.
Choose `lambda_hat` minimising `sum_i w_i (sd_sim_i − sd_obs_i)^2`, `w_i = n_i`.

**Reported regardless of outcome:** `lambda_hat`; the residual `sd_sim − sd_obs` by ADP decile
(a systematic sign flip across deciles means the *shape* is wrong, not the scale); and whether
`lambda_hat` falls inside the existing 5 / 10 / 20 sweep.

**Confirmation threshold.** H3 CONFIRMED iff `lambda_hat < 10` and the seed-induced spread in
`lambda_hat` across ≥ 5 seeds is smaller than the gap to 10. NULL otherwise.

**Hard sanity check, pre-committed, blocking.** `lambda_hat` **must** come out below the mean
observed pick sd over the same universe, because the simulator's mechanics add variance. If
`lambda_hat ≥` mean observed sd, the mechanics are wrong and **nothing ships** — that result is a
bug report, not a calibration.

**If `lambda_hat` lands outside [5, 20]**, the sweep's own honesty device has been miscentred since
it was introduced, and the founder is told that directly rather than having the sweep silently
re-based underneath him.

---

## M4 — The pick axis, and the coverage seam

**Not a hypothesis. Two required transforms, either of which biases everything if skipped.**

**(a) Axis correction.** FFC `average_pick` counts kickers and defenses (Aubrey 132.0,
McPherson 162.7, and 11 team defenses in the same file). `draft_sim`'s universe is QB/RB/WR/TE.
Westwood has no kicker slot and 16 rounds; FFC `low_pick` values reach 17.05 / 17.12 / 18.03, so
the sample contains deeper drafts. Required: re-index FFC picks onto the **skill-only Westwood pick
axis** and report the mapping. Report how many picks the correction moves at ADP 50 / 100 / 150.

**(b) Coverage seam.** Report the count of `board.json`'s 510 players carrying an
`ffc_half_ppr_10team` row, before and after dropping PK/DEF (expect ~180 → ~145). A 10-team,
16-round draft consumes ~150 skill players, so **coverage runs out at almost exactly the end of the
draft** — the seam is load-bearing for the user's late picks, not cosmetic.

**Required: a monotone calibration, not a splice.** Fit `board_rank → adp_pick` on the overlap
(isotonic regression, or a log-log fit with the residual sd reported by decile) and project
uncovered players through the fitted map. Splicing raw ECR ranks onto ADP picks at player 181
creates a discontinuity at the seam that the simulator will happily draft through.

**Report:** how many players taken inside the tracked pick range come from the extrapolated region.
If ~none, extrapolation is low-stakes and say so. If many, the seam is a first-order design choice
and returns to strategist before shipping.

---

## M5 / H4 — The closed-form cross-check

**Hypothesis (H4).** With opponents drafting from ADP with per-player dispersion, the simulator's
**unconditional** Prep-mode marginals reproduce the closed form
`P(available at pick p) = 1 − F_i(p)` within Monte Carlo error.

**Why this is worth a confirmatory slot.** It is a free, powerful acceptance test — a disagreement
localises a mechanics bug that no other check in this family would catch. And if it holds, the
unconditional case becomes arithmetic rather than a 628-second-per-league sweep (ADR-061), which
directly changes the cost of FR-128 and the shape of the FR-066 / thread-104 export.

**Metric.** Max and mean absolute difference between simulated and closed-form
`P(available)` across the tracked top-80 × the user's pick numbers.

**Confirmation threshold.** H4 CONFIRMED iff mean absolute difference ≤ 0.02 **and** max ≤ 0.05,
with the Monte Carlo standard error at the chosen `n_sims` reported alongside so the reader can see
whether the tolerance is tighter or looser than the noise.

**If H4 is NULL:** the simulator and the closed form disagree, and the discrepancy pattern
(by ADP decile, by pick number, by position) is the diagnostic. Do not "fix" it by widening the
tolerance.

---

## Deferred, named, and explicitly not in this family

**The shared-vs-idiosyncratic decomposition.** Observed across-draft dispersion has a room-level
component (the market moved on him this week) and a manager-level component (manager A loves him,
manager B does not). The current model contains only the first, and FFC's aggregate feed can never
separate them — it exposes no within-draft, across-seat variation.

The founder's ~30-mock programme is the instrument that can, because `mock_picks` stores per-slot
sequences. **The shared-only structure stays for now by decision, not by inertia**, and the test
that would revisit it is: across logged drafts, is the variance of a player's pick position *within*
a room across seats distinguishable from zero after removing the room-level shift?

That is a separate family with its own denominator, to be opened when the mock count supports it.
It is recorded here so that a future session finds a decision rather than an assumption.

---

## Pre-mortem (guardrails §8), answered before the run

1. **Look-ahead?** Not applicable — no outcome data enters this change anywhere. That is the same
   property that makes availability the project's least projection-contaminated output, and it is
   preserved exactly.
2. **Universe defined before outcomes?** Yes, and trivially — the universe is a pre-draft ADP
   snapshot and a board, both dated before any 2026 game.
3. **Holdout untouched?** The 2025 locked holdout is not accessed and is not relevant; nothing here
   touches season outcomes.
4. **Multiple comparisons?** BH within the declared family, `m = 4`, denominator fixed above before
   any run.
5. **Confidence intervals?** Required on `b_hat`, `tau_hat^2`, and `lambda_hat`. **Explicitly
   refused** on anything derived from the two/three mock rooms, with the reason stated in the
   report rather than omitted.
6. **All three baselines?** M1 carries the incumbent (`fantasypros_ecr`), the board
   (`fantasypros_csv_2026draft`) and market ADP. This is the check the existing mock analysis
   omitted.
7. **If the result looks unusually good, what is the leakage explanation?** For H4 specifically: a
   suspiciously perfect match between simulator and closed form would most likely mean both are
   reading the same array through the same transform and the "independent" check is not
   independent. Rule that out by construction — the closed form must be computed from the raw CSV
   columns, not from the array the simulator was handed.
