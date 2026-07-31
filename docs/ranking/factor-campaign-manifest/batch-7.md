# Factor campaign C2 — batch 7 registration

**Registered by `ranker` (batch 7), 2026-07-30.**

| | |
|---|---|
| batch | 7 |
| agent | ranker |
| **m_7** | **16** |
| pre-commitment | `docs/ranking/factor-batch-7-precommit.md` (`fb7627a`, committed before any arm was fitted) |
| results | `docs/ranking/factor-batch-7-results.md` (`2d7a6e2`), post-hoc `f8d7757` |
| scope | The sweep's six RB rows — N14 red-zone snap rate, N15 inside-5 TD conversion, N16 YAC per reception, N17 receiving share of own points, N18 snap-share persistence, N19 late-season role trajectory. **All 16 arms at RB** |

## Registration is late, and the denominator is unaffected

Batch 7 ran concurrently with batches 4, 5 and 6 and did not see this directory. It registered
**m = 16 at a campaign denominator of 80** in its own pre-commitment (`fb7627a`, §4) and in a
duplicate single-file manifest at `docs/ranking/factor-campaign-manifest.md`, **before fitting**.
That file is now retired in place and points here.

**Batch 7's grades do not change.** C2's rule is `M_campaign = max(Σ_b m_b, 80)`; with batch 7's 16
added, Σ m_b = 56, so the **floor of 80 still binds** and 80 is exactly what batch 7 graded at.
Nothing is re-run and nothing is re-graded.

**The two manifests reached the same number independently.** Batch 5's floor argument (four
concurrent batches, batches 1–3 registered 23/15/24, 4 × 20 = 80 as a round figure below that
median) and batch 7's (four batches × 20 registered tests, declared as a planning figure) are the
same arithmetic from the same premises. That is convergence rather than agreement, and it is worth
recording as such.

## The 16 registered tests

**E1a** = out-of-sample MAE of one declared component, full universe, arm − primary, paired by
season, season-block bootstrap 4,000 reps. **Negative = better.** Position is RB throughout.

| # | id | factor | E1 component | target seasons |
|---|---|---|---|---|
| 1 | Z1 | N14 red-zone (inside-20) **snap** rate → carries | carries | 2018–2024 (7) |
| 2 | Z2 | N14 inside-5 snap rate → carries | carries | 7 |
| 3 | Z3 | N14 red-zone snap rate → targets | targets | 7 |
| 4 | **Z1c** | **CONTROL** — red-zone snap coverage flag | carries | 7 |
| 5 | G1 | N15 inside-5 TD conversion vs league base rate | rush_tds | 2014–2024 (11) |
| 6 | **G1p** | **CONTROL** — binomial placebo, identical shrinkage geometry | rush_tds | 11 |
| 7 | **G1c** | **CONTROL** — inside-5 coverage flag | rush_tds | 11 |
| 8 | Y1 | N16 YAC per reception | rec_yards | 11 |
| 9 | **Y1c** | **CONTROL** — YAC coverage flag | rec_yards | 11 |
| 10 | S1 | N17 receiving share of his own fantasy points | targets | 11 |
| 11 | S2 | N17 ≥40% receiving-share bin (McFarland's cut) | targets | 11 |
| 12 | P1 | N18 prior snap share | carries | 2015–2024 (10) |
| 13 | P2 | N18 ≥60% snap-share gate (McFarland's cut) | carries | 10 |
| 14 | **P1c** | **CONTROL** — snap-count coverage flag | carries | 10 |
| 15 | L1 | N19 his own late/early opportunity ratio | carries | 11 |
| 16 | L2 | N19 group late lift, draft round × career year | carries | 11 |

**Five of sixteen are controls, on purpose.** They are expected to be uninformative and including
them costs the treatment arms power; that is the conservative direction and it is taken deliberately.

**Outcome: nothing passes at M = 80, and nothing passes at m = 16 either.** The smallest p-value in
the batch is 0.021 against a rank-1 BH threshold of 0.00125 (M = 80) or 0.00625 (m = 16). **The
campaign correction changed no batch-7 grade**, which is stated so the denominator cannot be blamed
for a null it did not cause.

## One finding this batch owes the campaign, not just its own write-up

**A `*_known` coverage-flag control is a TIME DUMMY whenever its source starts inside the training
window**, and it is not measuring coverage at all. `rzsnap_known` is **0.000 for veterans in target
seasons 2012–2016 and 1.000 from 2018**, because `participation` starts in 2016 and
`first_feature_season` is 2012.

| batch | control | source starts | covers the 2012+ training window? | result |
|---|---|---|---|---|
| 3 | `sep_known_1` NGS | 2016 | **no** | +0.0584, p = 0.056, MARGINAL-HARMFUL — VOIDed S1 |
| 3 | `expl_known` pbp | 2009 | yes | −0.0058, p = 0.44, **NULL** |
| 5 | `routes_known` participation | **2016** | **no** | **beats every route treatment by 1.06×–19.7×; 8 of 8 cells VOID** |
| 7 | `rzsnap_known` participation | 2016 | **no** | −0.1239, p = 0.038, largest effect in its family |
| 7 | `i5_known` pbp / `yac_known` weekly | 2009 / 2006 | yes | +0.0005, −0.0029, both **NULL** |

**Batch 5's `routes_known` is the same source and the same geometry as batch 7's `rzsnap_known`.**
Batch 5 read its result as a coverage artifact; batch 7's D2 says the mechanism is the calendar.
Both readings condemn the treatment arms, so no batch-5 conclusion is at risk — but the *reason*
differs, and the fix differs with it: restricting the arm's **training** window to covered seasons,
not only its target window.

**Registered to `strategist` as a claim, not applied.** Thread
`docs/handoffs/2026-07-30-register-factor-batch-7-campaign-m-80-and-rule-o`. No batch's published
grade is changed by it.
