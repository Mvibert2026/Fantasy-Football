---
ID: 2026-07-30-availability-adp-measurements-m0-m5
FROM: strategist
TO: backend
STATUS: OPEN
BLOCKS: FR-131, FR-066, thread 104, FR-128, thread 114 (partially)
OPENED: 2026-07-30
---

## Ask

Run the six measurements below and reply here with the numbers. **Do not implement the change
yet** — M0 is a gate and can stop half of it.

Full design and every decision rule: `docs/ranking/availability-opponent-model-precommit.md`.
The methodology ruling that produced them: thread 119's `strategist` reply.
The ADR draft to land afterwards: `docs/adr-drafts/ADR-DRAFT-availability-opponent-model-source-and-dispersion.md`
(allocate its number with `python tools/handoffs.py adr next` — do not hand-type one).

**Before running M1–M5, create the `PR-0NN` registration file** referencing the precommit doc as
`full_design`, with a checked id and a computed `content_hash`, and open the family manifest
`availability-opponent-model` with `m = 4`. I could not do either — no shell. `require_confirmatory`
will refuse to run without it, which is correct.

I have **no database access, deliberately** (it is what makes this an independent check rather than
an extension of your own work). Everything I could compute, I computed by hand from committed
artifacts and it is stated in thread 119 so you can check my arithmetic. Everything below needs a
query I cannot run.

---

### M0 — GATE. Reconcile FFC's `times_drafted` against `total_drafts_in_sample`

**This blocks M2, M3, and the whole dispersion half of FR-131. Do it first.**

In `data/adp-snapshots-ffc/2026-07-30_half_ppr.csv` every row carries
`total_drafts_in_sample = 1254`, yet:

| player | `average_pick` | `times_drafted` |
|---|---|---|
| Bijan Robinson | 2.0 | 90 |
| Omarion Hampton | 19.1 | 256 |
| Brock Bowers | 44.5 | 225 |
| Brandon Aubrey (PK) | 132.0 | 212 |
| Hunter Henry | 152.3 | 12 |

Bijan Robinson goes at pick 2.0 in effectively every draft. 90 of 1254 is not a selection rate. And
between the 07-29 and 07-30 snapshots Ja'Marr Chase's `times_drafted` **fell** (189 → 175) while
`total_drafts_in_sample` **rose** (1187 → 1254).

**Deliver:**
1. FFC's own documented meaning for both fields, cited (not inferred).
2. `sum(times_drafted)` across the snapshot, against `picks_per_draft × n_drafts` for whatever
   `n_drafts` that implies. State whether they reconcile to within rounding.
3. A defensible per-player effective `n_i` to use as the sampling-variance weight downstream, or a
   plain statement that none is available.

**If it does not reconcile, stop and reply.** The central-tendency change can still proceed; the
dispersion change cannot, because every standard error and every shrinkage weight in M2/M3 would be
built on an unverified field semantic. FR-131 quotes these `std_dev` values with no n and no
standard error, which the evidence-standards table forbids for a statistical constant.

---

### M1 — The baseline comparison that has never been run

`docs/analysis/founder-mocks-2026-07-30.md` reports the mocks against FFC ADP (ρ = 0.9485 half-PPR)
and **against no ranking source at all**. A candidate without its incumbent baseline is exactly what
guardrails §5 forbids. ρ = 0.95 against ADP means nothing until we know ECR's number on the same
picks.

**Data.** All three logged mocks (`yahoo-10team-slot4-2026-07-30`, `yahoo-12team-slot2-2026-07-30`,
`founder-mock-2026-07-29`), resolved picks only, restricted to a **common support** — players
carrying a value in every candidate source. Report `n` per mock.

**Candidates**, each at the snapshot with greatest `as_of_date ≤ draft date`:
`fantasypros_ecr` (incumbent) · `fantasypros_csv_2026draft` (the board) · `ffc_half_ppr_10team` ·
`ffc_ppr_10team` · `ffc_non_ppr_10team`.

**Metric: mean absolute error in picks**, on the M4-corrected axis. Spearman ρ secondary only — ρ is
insensitive to the magnitude of a miss, and "how many picks early/late" is the decision-relevant
error here.

**Report per mock. Never pool.** Pooling three rooms hides the between-room variance, which is the
entire question. **No confidence intervals** — n = 3 rooms, the resampling unit is the room, and a
pick-level bootstrap would produce a tight, confident, meaningless number. Say that in the report
rather than omitting it.

**Arithmetic check before trusting anything else the pipeline emits:** the 10-team mock's
round-by-round MAE against FFC half-PPR should reproduce **1.12 / 3.66 / 8.22 picks** for rounds
1/2/3 (I hand-computed all 30 picks from the committed files). If your pipeline disagrees, the
pipeline is wrong or my arithmetic is — find out which before proceeding.

**Threshold (gates claims, not adoption):** H1 CONFIRMED iff FFC half-PPR MAE < `fantasypros_ecr`
MAE in **all three** mocks and the mean gap ≥ 2.0 picks. If NULL, the switch still proceeds on
estimand grounds, but **nothing in the export, UI, glossary or founder-facing copy may state or
imply the ADP model is more accurate.**

**Also deliver the paired per-pick vectors** for the three FFC 10-team formats. Those are what
thread 114's Steiger/Hittner separability question (ρ = 0.9333 / 0.9485 / 0.9541, n ≈ 130) needs,
and it is currently unanswerable without them.

---

### M2 — Is per-player dispersion anything beyond a function of ADP position?

**Data.** `ffc_adp_snapshots`, `adp_source='ffc_half_ppr_10team'`, latest snapshot,
`position IN ('QB','RB','WR','TE')` — drop PK/DEF, they are not in the simulator's universe and
behave differently.

**Fit** `log(std_dev_i) = a + b·log(average_pick_i) + e_i`, weighted by `n_i` from M0. Report `b`
with a player-level bootstrap SE, and R².

**Then empirical Bayes on the residuals**: treat `log(std_dev_i)` as observed with within-player
sampling variance ≈ `1/(2(n_i − 1))`, and estimate `tau_hat^2`, the between-player variance of
*true* log-dispersion after removing the ADP trend. Report `tau_hat^2` with a player-level
bootstrap CI. This is the same estimator FR-086 used for per-player scoring shape, where it came
out at exactly zero.

**Threshold.** Ship a per-player residual multiplier iff `tau_hat^2`'s 95% CI lower bound > 0
(EB-shrunk, shrinkage factor reported per player). Otherwise ship the curve alone, and the export
states: *"per-player dispersion beyond the ADP-position effect was tested and found
indistinguishable from sampling noise."*

**Stability, pre-committed:** refit on `ffc_non_ppr_10team`, `ffc_ppr_10team`, and on the **07-29**
snapshot. If `b_hat` moves by more than its own bootstrap SE across formats, the curve is
format-specific. If it moves materially in one day, only the global scale ships.

**My prior, recorded before you run it: NULL.** From the committed CSV, `std_dev` rises
near-monotonically with `average_pick` (Bijan 2.0→0.7, Breece 28.7→2.9, Bowers 44.5→10.4,
Kittle 117.0→24.9) and compresses at the extreme tail through censoring (Christian Kirk
194.7→7.7). Bijan's dispersion *cannot* be large — pick 1 is a hard floor. FR-131's "factor of
forty between Bijan and Kamara" is close to "ADP 2 versus ADP 156."

Also note, same source and format one day apart: **Kamara 26.2 → 19.0 (−27%, n = 28)**,
Hunter Henry 28.0 → 24.8 (−11%, n = 12), Kittle 26.9 → 24.9, McPherson 39.2 → 36.4 — while Gibbs
(0.6), Bijan (0.7) and Chase (1.5) did not move at all. FR-131's four headline "the room does not
agree" players are precisely the four that moved most and the four with the smallest n.

---

### M3 — Calibrate the global scale THROUGH the simulator. Do not substitute.

**The error this is written to prevent.** FFC's `std_dev` is the dispersion of a **realised** pick —
an output. The simulator's sigma is a **latent board perturbation**, and the simulator's own
mechanics (need penalty, players being removed, snake order) add variance on top. Substituting
`sigma_i = std_dev_i` will over-disperse, and it will look plausible while doing so, because
availability probabilities pushed toward 0.5 read as admirable humility. This is the single most
likely quiet failure in this whole change.

**Procedure.** Fix `s_i` from M2 (normalised to mean 1). Sweep `lambda`. For each, run
`simulate_availability` and record the simulated distribution of realised picks. Choose
`lambda_hat` minimising `sum_i w_i (sd_sim_i − sd_obs_i)^2`, `w_i = n_i`.

**Report regardless of outcome:** `lambda_hat`; the residual `sd_sim − sd_obs` **by ADP decile** (a
systematic sign flip across deciles means the shape is wrong, not the scale); the seed-induced
spread across ≥ 5 seeds; and whether `lambda_hat` falls inside the existing 5 / 10 / 20 sweep.

**Blocking sanity check.** `lambda_hat` **must** be below the mean observed pick sd over the same
universe, because the mechanics add variance. If it is not, **nothing ships** — that is a bug
report, not a calibration.

**My directional pre-commitment: `lambda_hat < 10`.** Basis, both from committed artifacts: over
ADP 1–90 the typical FFC `std_dev` is ~4–5, not the ~9.7 median quoted over all 180 rows including
kickers and the tail; and the 10-team Yahoo mock's implied per-round dispersion is 1.40 / 4.59 /
10.30 picks for rounds 1–3 against the ~8 picks a flat sigma = 10 implies in every round. If this
holds, current availability numbers for top-80 players are systematically too close to 0.5 and the
honest sweep is nearer 2 / 5 / 10 than 5 / 10 / 20 — which the founder should be told directly
rather than having the sweep silently re-based underneath him.

**Seeds:** explicit integer, recorded, never derived from builtin `hash()`. Determinism demonstrated
by re-running in a **separate process** (guardrails §11.3).

---

### M4 — The pick axis and the coverage seam. Two required transforms.

**(a) Axis.** FFC `average_pick` counts kickers and defenses (Aubrey 132.0, McPherson 162.7, plus
11 team defenses in the same file); `draft_sim`'s universe is QB/RB/WR/TE and Westwood has no kicker
slot. FFC `low_pick` values reach **17.05 / 17.12 / 18.03**, so the sample contains drafts deeper
than Westwood's 16 rounds, which stretches the tail and inflates late-round `std_dev`.

Re-index FFC picks onto the skill-only Westwood pick axis. **Report how many picks the correction
moves at ADP 50 / 100 / 150.**

**(b) Seam.** Report how many of `board.json`'s 510 players carry an `ffc_half_ppr_10team` row,
before and after dropping PK/DEF (I expect ~180 → ~145). A 10-team 16-round draft consumes ~150
skill players, so coverage runs out at almost exactly the end of the draft — the seam is
load-bearing for the user's late picks.

**Required: a monotone calibration, not a splice.** Fit `board_rank → adp_pick` on the overlap
(isotonic, or log-log with residual sd by decile) and project uncovered players through it.
Splicing raw ECR ranks onto ADP picks at player 181 creates a discontinuity the simulator will
happily draft through.

**Report** how many players taken inside the tracked pick range come from the extrapolated region.
If ~none, say so and the seam is low-stakes. If many, it comes back to strategist before shipping.

---

### M5 — The closed-form cross-check, and why it changes FR-128 and thread 104

With opponents drafting from ADP with per-player dispersion, the **unconditional** Prep-mode
marginal is nearly closed-form:

```
P(player i still on the board at pick p)  =  P(realised pick > p)  =  1 - F_i(p)
```

computable from `average_pick` and `std_dev` on the M4-corrected axis with no Monte Carlo.

**Test:** max and mean absolute difference between the simulator's unconditional marginals and the
closed form, across the tracked top-80 × the user's pick numbers. **Threshold:** mean ≤ 0.02 and
max ≤ 0.05, with the Monte Carlo SE at your chosen `n_sims` reported alongside so the reader can
see whether the tolerance is tighter or looser than the noise.

**Compute the closed form from the raw CSV columns, not from the array the simulator was handed** —
otherwise the "independent" check is not independent, and a suspiciously perfect match means only
that both sides read the same transform.

**If it holds, two founder requests change shape:**
- **FR-128** — availability is empty for 24 non-primary leagues and ADR-061 measured 628s per
  league. For the unconditional case that collapses to arithmetic.
- **FR-066 / thread 104** — thread 104 currently asks for the raw ECR rank array. The right export
  is per-player `{adp_pick, sigma_pick, coverage_flag}` on the Westwood axis. **Reformulate 104
  before building the field it asks for today**, or the browser gets a field that is obsolete on
  arrival.

---

### Also, and separately from the measurements: three code facts to confirm or refute

1. `simulate_availability` runs the **opponent model and `strategy_bpa` off the same
   `data.consensus_rank`**. Post-change these must be two distinct arrays: opponents ← ADP,
   user ← `board.json`. Thread 104 already flagged that `algorithm_note` claims the latter and the
   code does not. Confirm the split is real, with an assertion, not a comment.
2. **The room-noise structure must not change.** Per-player sigma **rescales the existing shared
   draw**: `z_i ~ N(0,1)` once per player per draft, shared by all teams;
   `effective_rank[t][i] = adp_i + lambda * s_i * z_i`. Add a test asserting
   `Corr(effective_rank[t1][i], effective_rank[t2][i]) = 1` for every team pair before the need
   penalty. Independent per-team draws are a **different model** with different predictions in both
   directions, and adopting them as an implementation side effect is the specific outcome thread 119
   asked to prevent.
3. **ADR-035's labelling constraint extends to FFC half-PPR 10-team.** Required wording carries
   source, format, window and n, plus the clause ADR-035 did not need: FFC pick numbers include
   kickers and defenses and Westwood's do not. The test to apply literally: *could the founder read
   this number and believe it describes his nine leaguemates?* If yes, the label fails.

## Why

Three founder asks are blocked on this (FR-131, FR-066/thread 104, FR-128), and the founder has
repeatedly been told availability is the project's most reliable output. That claim is only as good
as the opponent model underneath it, which currently runs on a superseded ranking and an admitted
guess. After this change it gets stronger — but only if the dispersion is calibrated through the
simulator rather than substituted into it, and only if M0 clears.

## Done looks like

A reply here with: M0's verdict (gate open or closed, with the citation); M1's per-mock MAE table
including the incumbent; M2's `b_hat`, `tau_hat^2` and CI with the ship/don't-ship call;
M3's `lambda_hat`, its decile residuals, its seed spread, and whether the blocking sanity check
passed; M4's two transforms with the reported counts; M5's max/mean difference against the closed
form. Nulls reported as nulls. Then the ADR lands with its allocated number.
