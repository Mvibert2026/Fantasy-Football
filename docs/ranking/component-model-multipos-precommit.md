# Component model, RB / QB / TE — pre-commitments

**Ranker, 2026-07-30.** Written and committed **before any position result was computed**, so that
the git history carries the commitment rather than my later account of it. The WR pass
(`component-model-wr-pass-1.md`) had no such artifact and had to be trusted on assertion.

Everything below is **exploratory**. Nothing here is a registered confirmatory test. Thread 094
(`ranker` → `strategist`, still `OPEN`, no reply) asks for the one registration worth making and it
has not been granted, so **the sealed 2025 holdout is not opened by any of this work.**

---

## 1. What is fixed before looking

| | |
|---|---|
| **Walk-forward window** | target seasons 2014–2024 inclusive, expanding training window, no season ever in its own training set |
| **Holdout** | 2025, sealed. Never loaded, never featured, never evaluated. |
| **Feature cutoff** | season N features use seasons ≤ N−1 plus April-of-N draft slot and calendar facts only |
| **Universe** | frozen from pre-N information; players who then play zero games stay in and score 0 |
| **Metric** | Spearman ρ of projected points against realised points under this league's scoring, bonuses stacked |
| **Headline** | the **margin against baselines**, never the raw ρ (`CLAUDE.md` §6.5) |
| **Baselines** | B1 consensus FFC half-PPR 12-team ADP, pre-kickoff dated · B2 prior-season points ranked · B3 recency-weighted prior points per game |
| **Uncertainty** | season-block bootstrap, 4,000 reps, paired differences, seasons as the resampling unit |

## 2. Primary model per position — declared now

The direct analogue of the WR pass: 2009+ usage features, three lags, fixed decay (0.55/0.30/0.15),
empirical-Bayes shrunk rates, linear volume and availability models, a binomial GLM per bonus
threshold on the per-game distribution. No position's primary is chosen by looking at results.

## 3. Secondary variants — reported, never selected on

Each is reported **with its interval alongside the primary**. I am not permitted to promote a
secondary to headline because it won; that is selection on the outcome and this document exists to
stop me doing it.

| Position | Secondary variant | Why it is a live question |
|---|---|---|
| **RB** | opportunity-share parameterisation: project (carries + targets) per game, then the receiving share of it, instead of projecting each stream independently | the rushing/receiving split *is* the RB modelling question; two independent streams ignores that a coach allocates one budget |
| **QB** | deep-sample fit, 1999+ box-score features | **measured, not assumed:** passing attempts are complete 1999–2024 with no 2003–2008 gap. The gap that binds WR/TE/RB is a *targets* gap. QB's data boundary is genuinely different and `CLAUDE.md` §6.4 says how far back to weight is empirical, per position |
| **TE** | fit the efficiency rates on WR+TE pooled with a TE intercept, volume and availability still TE-only | TE has the smallest sample and (pass 1) the largest market error. Those pull opposite ways; pooling is the standard answer and it should be measured, not assumed |

## 4. The availability defect — a three-arm single-factor test

WR pass 1 §7: the model's ten worst calls were all receivers coming off a season lost to injury or
suspension, because the availability sub-model cannot distinguish *did not play* from *played badly*.
`nfl.db.injuries` holds 79,816 rows that no model in this project has read.

Three arms, run at **every** position including WR, one factor apart:

| arm | availability features |
|---|---|
| **A — baseline** | WR pass 1 spec: `gshare_w`, `gshare_1`, `present_1`, `age`, `age²`, `evidence` |
| **B — injury decomposition** | A + weeks missed in N−1 that carry a dated `Out`/`Doubtful` injury report, and weeks missed that carry none, each as a share of the season |
| **C — free control** | A + `gshare_max3`, the best games-share in the last three seasons. **Uses no injury data at all.** |

**C is the arm that makes the test honest.** If B ≈ C then 79,816 rows of injury reporting buy
nothing that a one-line memory of having once been healthy does not, and the correct finding is that
the injuries table is not the fix. Declaring C in advance is the only way that finding stays
available to me.

**Pre-declared reporting rule:** all three arms reported per position with paired season-block
bootstrap CIs against arm A, on both the ranking metric and the availability component's own MAE.
No arm is promoted into a shipped model on this evidence — that requires registration by
`strategist`.

## 5. Known limits, stated in advance

- **Suspension is not in the injuries table.** A suspended player files no injury report. DeAndre
  Hopkins' 2022 six-game suspension is invisible to arm B and will land in the "missed with no
  report" bucket alongside players who were simply cut. Arm B therefore addresses *injury* absence
  only, and the task's framing ("injury or suspension") is half-served. Said now, not after.
- **Injury reports start in 2010.** 2009 has 17 rows and is effectively empty. Arms B and C are
  therefore unavailable for lag seasons before 2010, which is inside the walk-forward's own window.
- **Power at QB and TE is much worse than at WR.** The FFC board carries 14–24 QBs and 11–19 TEs per
  season against 43–67 WRs. The ADP-subset comparison at those positions is close to
  uninformative and will be reported as such rather than presented as a null with a straight face.
