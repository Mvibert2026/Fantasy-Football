# PR-DRAFT — the lag-weight decay profile, per position

**Registered by `strategist`, 2026-08-01, before any configuration on this grid has been fitted.**
Needs a `PR-0NN` number allocated at run time (same convention PR-009 used from a `PR-DRAFT-*`
placeholder). **Nothing below may be run until this file is committed.**

**Supersedes:** the proposed two-arm confirmatory test of batch C1's arm **F6** (steeper lag
recency, `0.55/0.30/0.15 → 0.70/0.22/0.08`, +0.0266 at QB). That test is **refused** — reasoning in
§1. C1's F6 verdict (NULL at all four positions) is unchanged by this document and is not re-opened.

**Companion:** `docs/adr-drafts/ADR-DRAFT-factor-inclusion-decision-rule.md`. That ADR's null
construction (permutation of an added column block) **does not apply here** — F6 adds no column —
which is half of why this exists.

---

## 1. Why the two-arm confirmatory test is refused

**F6's reported evidence rests on the wrong null.** It was called a survivor because +0.0266 at QB
exceeds the placebo ensemble's 95th percentile (+0.0110). That ensemble measures what happens when
you **add a noise column** to the design. F6 adds no column; it changes a constant that re-weights
every recency-weighted feature and every efficiency `(num, den)` pair in the model. The two
interventions have different bias signatures (the placebo's null centre, +0.0030 at QB, comes
entirely from a mechanism F6 does not have) and, more importantly, different *variances* — F6
perturbs far more of the design than one column does, so its null is almost certainly **wider** than
the placebo's, and the comparison is anticonservative. **The claim that F6 "clears the placebo null"
is withdrawn.**

**And the question is mis-shaped.** `CLAUDE.md` §6.4 asks *how far back to weight*, per position,
as an empirical question. A comparison of two hand-picked vectors is a weak instrument for a
one-dimensional continuum: it cannot distinguish "steeper is better" from "0.70/0.22/0.08 happens
to sit on a bumpy noise surface," and its result is a p-value about a point rather than a shape.
The informative object is the **profile**, and the profile supplies its own null.

**A significance test is also the wrong frame.** This is a **hyperparameter of the model**, not a
factor competing for a place in the design matrix. The incumbent `0.55/0.30/0.15` was itself never
measured. The right output is a selection with a pre-committed default of *no change*, not a
discovery.

---

## 2. Parameterisation

`pos_features.LAG_WEIGHTS` becomes a one-parameter family: `w_k ∝ r^k`, `k = 0 … N_LAGS − 1`,
normalised to sum 1. `r` is the decay ratio; `r = 1` is equal weighting, `r → 0` is last-season-only.

| `r` | weights (N_LAGS = 3) | note |
|---|---|---|
| 0.15 | 0.870 / 0.130 / 0.020 | near last-season-only |
| 0.25 | 0.762 / 0.190 / 0.048 | |
| **0.34** | 0.687 / 0.234 / 0.079 | ≈ C1's F6 arm (0.70/0.22/0.08) |
| 0.45 | 0.612 / 0.275 / 0.124 | |
| **0.52** | 0.559 / 0.290 / 0.151 | ≈ **the incumbent** (0.55/0.30/0.15) — the reference, Δ̄ ≡ 0 |
| 0.60 | 0.510 / 0.306 / 0.184 | |
| 0.75 | 0.432 / 0.324 / 0.243 | |
| 0.90 | 0.367 / 0.331 / 0.298 | |
| 1.00 | 0.333 / 0.333 / 0.333 | equal weight |

**8 non-trivial grid points × 4 positions.** The exact incumbent vector, not `r = 0.52`'s rounding
of it, is the control run; `r = 0.52` is included so the grid's own discretisation error is visible.

---

## 3. Endpoint, population, controls — inherited, not re-invented

Identical to batch C1 so the numbers are directly comparable: Spearman(`proj_points` order, realised
points) per (position, season), M-panel veterans, **CTRL-A** (`first_feature_season` 2012, targets
2018–2024), v2 games arm **G0** pinned, `allow_preseason_proxy=False` with
`n_preseason_proxy_reads == 0` asserted per position per season. **The 2025 holdout is not opened
and nothing here would warrant opening it.**

Δ̄(r) = mean over the 7 target seasons of `ρ(r) − ρ(incumbent)`, per position. Per-season deltas
stored for every configuration.

---

## 4. The null — lag-order permutation

The null hypothesis is **"the ordering of the lag weights carries no information"**: it is not that
weighting does nothing, it is that *which season gets the big weight* does not matter.

Under that null all `N_LAGS!` assignments of a given weight vector to the lag positions are
exchangeable. For each grid `r` other than 1.00 (where all orderings coincide), the 5 non-monotone
assignments are null draws. **35 null configurations per position.**

This is a genuine randomisation reference, it requires no distributional assumption, it costs the
same per draw as a treatment configuration, and it prices in the one thing a two-arm test cannot:
that the treatment family itself has been searched.

**Its resolution floor is 1/36 = 0.028.** That is stated up front and it is why §5 is a shape rule
with a no-change default and **not** a BH discovery claim. Nothing in this document may be reported
as a BH-robust finding.

---

## 5. The decision rule — fixed now, all four conditions required

Adopt a position-specific `r ≠ incumbent` **only if all of**:

| | condition |
|---|---|
| **(i) shape** | Δ̄(r) is single-peaked across the grid — at most one sign change in the first differences. A ragged profile is noise and adopting its argmax is fitting it. |
| **(ii) magnitude, selection-aware** | `max_r Δ̄(r)` > `max` over all 35 lag-order-permuted configurations of their Δ̄, at that position. **Max against max** — the grid search is priced into both sides. |
| **(iii) stability** | at the peak, `Δ̄_LOOmin` (the mean after deleting the single most favourable season) is > 0 **and** exceeds the null family's maximum `Δ̄_LOOmin`. |
| **(iv) interior** | the peak is not at a grid boundary. A boundary peak means the grid is mis-specified: **re-register a wider grid, do not adopt.** |

**Otherwise: keep the incumbent**, and record `CLAUDE.md` §6.4 as answered negatively for this model
at this power — a legitimate, useful output, to be reported plainly per guardrails §5.

**An adopted `r` is a hyperparameter fitted on 7 target seasons.** It carries a standing
`fitted_on_training_seasons` label wherever it is quoted and is re-verified at the §6.5 release
gate. It is not a finding about football.

**Registry accounting: `m_b = 4`** — one adopt/keep decision per position. The 8 grid points and 35
null configurations per position are *inside* one decision each, priced by condition (ii), and are
**not** 43 tests. Campaign `M` rises by 4 when this runs.

---

## 6. Registered predictions — written before any configuration is fitted

Recorded so the result can embarrass me, and discounted per the standing calibration prior that
four of five registered prediction sets in sessions 3–4 over-credited a situation story
(`docs/reviews/FABLE-EXT3-2026-07-27.md`).

The available story is strong and I am pricing it at half: *§6.4 says regimes shift, this project has
measured a QB regime shift, F6's sign pattern across positions came out exactly as registered.*

1. **Primary prediction: no position adopts.** The incumbent is kept at all four, condition (ii)
   failing at each. I put this at roughly 3-in-4.
2. **The sharpest falsifiable one:** the null family's maximum Δ̄ at QB will be **≥ +0.0266** — i.e.
   F6's headline number is inside the range that arbitrary lag *re-orderings* already produce, and
   its apparent size is an artifact of comparing it to a column-addition null instead of its own.
3. If any position does adopt, it is **QB**, with an interior peak at `r ∈ [0.25, 0.45]` and a
   shallow maximum (Δ̄ < 0.03).
4. **RB, WR and TE profiles are flat within the null family** — no adoption, and Δ̄(r) monotone
   *downward* in steepness, matching C1's observed F6 signs (−0.0091, −0.0107, −0.0115).
5. Condition (i) fails somewhere: at least one position produces a ragged, multi-peaked profile.
   That would be the clean demonstration that this surface is noise at S = 7.

**If prediction 2 holds, F6 is finished** and the ledger records steeper recency as measured and
dead against its own null — not merely "did not reach the bar."

---

## 7. Implementation notes

`steep_recency()` in `experiments/bottomup/v2/factors_c1.py` already does the required patch
(`pos_features.LAG_WEIGHTS` is read at call time in three places, which is why it is a module-global
swap rather than a parameter). Generalise it to `lag_weights(vec)` taking any vector; the treatment
grid and the null family are then the same code path with different vectors, which is what stops the
null being a second implementation with a different bug.

Store per-season deltas for every configuration — the treatment grid **and** all 35 null
configurations — or condition (iii) cannot be computed.

Cost: `(8 + 35) × 4 positions × 7 seasons` walk-forward runs ≈ 172 position-runs, well under an hour
at the one timing figure this repo records. Cheap enough that there is no excuse for running a
subset and no excuse for running it twice.
