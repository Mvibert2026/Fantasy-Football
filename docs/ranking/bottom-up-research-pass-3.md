# Bottom-up ranking — research pass 3

## The rank-curve slope collapse: is it real, where, and what does flat pooling cost?

**Ranker, 2026-07-29.** Answers `docs/CURRENT-STATE.md` item 12 and the recency-weighting
request recorded at `docs/ideas-inbox.md:229` (ADR-057). **Exploratory.** Nothing here is
registered, no multiplicity correction is applied, and no result may be reported as an edge or
wired into the board. The confirmatory tests worth running are *asks* in thread **085** (already
open, unanswered) and the new thread opened by this pass.

Code, all committed and reproducing every figure below:
`experiments/bottomup/pass3_rank_curve_regimes.py` · `pass3_artifacts.py` · `pass3_weighting.py` ·
`pass3_persistence.py`. Data: `data/nfl.db`, scored through `src/scoring.py` under the real league
config with stacking bonuses.

---

## 0. The structural fact this whole question turns on, verified first

`make_board.build_board` computes `vbd = curve.predict(rank) - curve.predict(replacement_rank)`.
Substituting the curve:

```
vbd(i) = (a + b·ln i) − (a + b·ln base) = b · ln(i / base)
```

**The intercept cancels exactly.** Verified numerically against the live 2026 board: reconstructing
all 510 rows from the four slopes and the four replacement ranks alone reproduces the shipped
ordering with **zero mismatches**, and the VBD identity holds to rounding (max deviation 0.005,
which is the 2-dp round in the CSV).

So the entire shipped board — every rank, every VBD, every `delta_vs_consensus` — is a function of
**four numbers**: b_QB, b_RB, b_WR, b_TE, against fixed baselines QB10/RB30/WR40/TE10. That is why
the slope question *is* the board question, and it is also why a player-level opinion cannot exist
in this object at any setting of it (§8).

Shipped 2026 values, reproduced exactly by this pass's fitter
(`fit_rank_curves` vs `weighted_fit(scheme="flat")`, delta = 0.0000 at all four positions):

| | QB | RB | WR | TE |
|---|---|---|---|---|
| **shipped pooled slope** | −49.4 | −50.6 | −41.2 | −30.5 |
| season-level bootstrap 95% CI | [−67.4, −25.9] | [−65.4, −39.6] | [−46.5, −36.5] | [−38.9, −22.2] |

---

## 1. Conclusion first

**The QB collapse is not real. It is one season of injury noise seen through a depth cut, and the
fix on record would encode the single least persistent quantity in the whole system.**

Four answers, in the order asked.

**(1) Is the QB collapse real, or a fitting artifact?** **Not established, and three separate
checks push against it.** The five-point series carries error bars that swallow the effect: each
season's slope has a bootstrap 95% CI 60–115 points wide, and 2025's is **[−46.5, +69.2]**, which
contains 2024's point estimate. The trend across all five is **+15.3 slope-units/season
[−3.5, +34.1]** — the interval includes zero. Drop the sealed season and it is +7.9 [−10.5, +26.4],
p_perm 0.33. The monotone appearance is also **a property of the depth cut**: `RELEVANT_DEPTH["QB"]
= 20` is what makes it monotone; at depth 12 the series is −15.0, −106.9, −68.5, −41.7, −38.5 and
2021 is the *flattest* season, not the steepest. And it is **one player**: jackknife drop-one on
2025 spans 45.3 slope-units — dropping Jayden Daniels (consensus QB3, 114 points) alone takes the
slope from −4.1 to **+28.6**. The gap the entire regime story rests on is 40.9. **One player's
availability is larger than the effect.**

**(2) Is it happening at RB, WR, TE?** **No, and RB is running the other way.** Per-season slopes
with intervals are in §3. RB's 2025 slope is **−77.9, the steepest of its five seasons**; WR is
flat within noise (−37.7 → −37.0); TE is the one position with a perfectly monotone series
(ρ = +1.00, p_perm 0.0167 — which is the *exact floor* a 5-point permutation test can reach), but
its magnitude CI still includes zero and it breaks at depth 32. **A flat pool is only wrong where
the regime moved, and at three of four positions there is no evidence it moved.**

**(3) What weighting does the holdout support, per position?** **Position-specific, and opposite
across positions — but for the board's own curve the honest answer is "nothing, n = 2."** The
board's consensus curve has only two evaluable target seasons (2023, 2024) and they disagree, at
the fourth decimal place of Kendall τ. The well-powered version — the *value-spread* curve on
1999–2024, 20 evaluable targets, train/test split at 2016 — gives a clean and useful answer:

| position | recency weighting on a 2016–2024 holdout | best scheme |
|---|---|---|
| **QB** | **Strongly supported.** RMSE 45.00 → 22.41, Δ **−22.6 [−30.3, −13.6]** | hl1 (half-life 1 season) |
| **RB** | **Not supported.** Nothing clears zero; short windows are worse | — (flat is fine) |
| **WR** | **Contraindicated.** last1 is **+2.75 [+0.96, +4.80] worse** — CI excludes zero in the harmful direction | — (flat is fine; longer is better) |
| **TE** | **Weakly supported, and the training split picked the wrong scheme** (train said last2 at −12.4; on test last2 gives −0.30, CI spanning zero). Only hl5/hl10 clear zero | hl5, at −2.7 [−4.7, −0.5] |

**(4) What does the flat fit cost in board positions?** **Essentially nothing, under every
weighting the data can defend.** Under half-life 3, exactly **1 player in the top 150 moves 10 or
more places** and none moves 25. Under half-life 5, **none moves 10**. Only `last1` — fitting on
2025 alone — moves the board meaningfully (84 of 150 move ≥10, max 116 places), and `last1` is
precisely the scheme §4 shows is chasing noise. **Every scheme except last1 and last2 produces
slopes that sit inside the shipped board's own published 95% CI**, which — given the exact identity
in §0 — means it cannot move any player outside his own published VBD interval. The board already
says, in its error bars, that this change is beneath its resolution.

**The single most important thing in this pass, and it inverts the recorded fix:**

> The QB *value* spread did not collapse — 2025's realised QB curve is **−58.7**, dead in line with
> the 1999–2020 era means of −57.7 / −59.0 / −56.8, and over the full 26 seasons the QB value curve
> has been getting **steeper** (−0.461/season [−0.874, −0.034]). What collapsed is the **market's
> ability to order quarterbacks**: Kendall τ_b of consensus rank against realised finish went
> +0.484, +0.305, +0.263, +0.263, **−0.042** — in 2025 the consensus ordering of QBs was
> *slightly worse than random*. Attenuation ratio 0.069.
>
> Recency-weighting the board's **consensus** curve is therefore a bet that the market will be
> exactly as blind about quarterbacks in 2026 as it was in 2025. **Lag-1 autocorrelation of
> consensus ordering skill: r = −0.007 [−0.414, +0.411].** Zero persistence, measured. It is the
> least persistent quantity in the system, and the proposed fix would track it fastest.

This is the same conclusion pass 1 reached from a different angle and referred to `strategist` in
thread 085 — which is still **OPEN and unanswered**. Pass 3 does not resolve it; it prices it.

---

## 2. Premise check

| Claim in the brief | Verdict |
|---|---|
| QB slope ran −67, −73, −59, −45, −4 | **Reproduced exactly**: −66.6, −72.6, −58.6, −45.0, −4.1 |
| The shipped curve pools all seasons flat | **Confirmed**, and reproduced to 4 decimal places |
| "Monotone collapse" | **Confirmed as an ordering; rejected as a finding.** Trend CI includes zero; depth-dependent; one-player-dependent |
| Nobody has checked the other positions | Partly wrong — **pass 1 §4.2 checked them exploratorily**. This pass adds the intervals, artifact checks and holdout that pass 1 did not have |
| `CLAUDE.md` §6.4 asks for recency weighting | Confirmed. **It asks for it as an empirical question per position — which is what §4 answers, and the answer differs by position and by which curve** |

---

## 3. Per-season slopes with uncertainty, all four positions

`points ~ a + b·ln(positional consensus rank)`, universe frozen from the pre-season consensus list
(`fantasypros_ecr`, `as_of_date` late August, strictly before Week 1), never-played players scored
0 and retained. Bootstrap resamples players within season (the estimand is a single season's fit,
so there is nothing to resample at season level). HC3 is reported alongside the classical SE
because point variance is far larger at the top of a position than at the bottom.

| pos | 2021 | 2022 | 2023 | 2024 | **2025** (sealed, descriptive) | trend/season | R² range |
|---|---|---|---|---|---|---|---|
| **QB** | −66.6 [−123.0, −27.0] | −72.6 [−127.8, −24.1] | −58.6 [−119.5, −15.2] | −45.0 [−81.6, −2.7] | **−4.1 [−46.5, +69.2]** | **+15.3 [−3.5, +34.1]** | 0.31 → 0.00 |
| **RB** | −34.9 [−74.9, −12.2] | −51.7 [−75.5, −28.3] | −41.4 [−65.6, −12.3] | −47.1 [−105.5, −8.0] | **−77.9 [−103.9, −58.7]** | **−8.1 [−19.2, +2.7]** | 0.15 → 0.50 |
| **WR** | −37.7 [−55.2, −18.5] | −49.8 [−67.3, −33.6] | −46.1 [−76.9, −26.7] | −35.4 [−56.2, −18.8] | −37.0 [−59.0, −19.3] | +1.6 [−4.3, +7.4] | 0.18–0.41 |
| **TE** | −42.7 [−73.6, −14.6] | −40.7 [−65.0, **+1.0**] | −26.4 [−54.7, **+1.8**] | −25.4 [−52.4, −7.1] | −17.0 [−47.7, **+21.4**] | +6.7 [−3.6, +16.9] | 0.31 → 0.10 |

**Not one of the four trend intervals excludes zero.** Two of the twenty per-season intervals do
not even exclude a slope of zero (TE 2022, TE 2023, TE 2025 — three). The permutation p on the
QB ordering is 0.0833 against a floor of 0.0167; TE's is 0.0167, i.e. *exactly* the floor, and it
is one of eight trend tests run here with no correction applied.

**On the sealed season.** The −4.1 is read here and nowhere else in this pass. It is already
published in the repo (`docs/ideas-inbox.md:229`) and my brief; the question being asked *is*
whether it is real, which cannot be answered without its interval. **It is excluded from every
weighting and selection experiment (§4) and from every board comparison whose purpose is to pick a
scheme.** The judgment call is referred to `strategist` on the same footing as pass 2's.

### 3.1 The three artifact checks, and what each one did to the story

**Depth.** `RELEVANT_DEPTH` pins QB and TE at 20. It is a draft-relevance choice, not a statistical
one, and the slope is not robust to it:

| QB depth | 2021 | 2022 | 2023 | 2024 | 2025 | monotone? |
|---|---|---|---|---|---|---|
| 12 | −15.0 | −106.9 | −68.5 | −41.7 | −38.5 | **no** |
| 16 | −31.4 | −76.1 | −93.1 | −47.2 | +3.4 | **no** |
| **20 (shipped)** | −66.6 | −72.6 | −58.6 | −45.0 | −4.1 | **yes** |
| 24 | −78.8 | −70.5 | −47.9 | −47.1 | −8.5 | yes |
| 32 | −83.4 | −79.7 | −47.2 | −50.8 | −30.6 | **no** |

At depth 12 the 2021 QB slope is **−15.0 against −66.6 at depth 20** — a four-fold change from a
choice nobody made on statistical grounds. TE's monotone series also breaks at depth 32.

**Influence.** Jackknife drop-one, span of the refitted slope:

| pos-season | full | drop-one range | span | flattest if dropped |
|---|---|---|---|---|
| **QB 2025** | **−4.1** | [−16.8, **+28.6**] | **45.3** | **Jayden Daniels** (consensus QB3, 114 pts) |
| QB 2024 | −45.0 | [−50.5, −36.5] | 14.1 | Anthony Richardson (QB5, 163 pts) |
| QB 2023 | −58.6 | [−77.0, −47.8] | 29.2 | Patrick Mahomes II (QB1, 288 pts) |
| RB 2024 | −47.1 | [−76.5, −41.9] | 34.6 | Christian McCaffrey (RB1, **40 pts**) |
| WR 2021–25 | — | — | 7.8–14.4 | — |

WR — 60 observations a season — is stable. QB and TE, at 20, are not. Every "flattest if dropped"
name at QB is a top-5 consensus quarterback who got hurt. **The QB slope series is mostly a record
of which high-consensus quarterbacks stayed healthy.**

**Form and scale.** The pattern is not a log-form artifact (linear and rank^−0.5 fits give the same
shape) and not scoring inflation (normalising each season's points by its positional mean leaves
QB at −0.236, −0.292, −0.257, −0.168, −0.017). But the **model-free** version is the honest one.
Mean realised points of the consensus top-3 minus the realised points of the consensus player *at*
the replacement rank:

| pos | 2021 | 2022 | 2023 | 2024 | 2025 |
|---|---|---|---|---|---|
| **QB** | **−34.3** | +177.8 | **−3.1** | +92.0 | **−91.5** |
| TE | +124.9 | +45.3 | −8.8 | +47.1 | +28.2 |

In three of five seasons the consensus top-3 quarterbacks scored **less** than the consensus QB10.
There is no smooth monotone anything here — the smoothness is entirely supplied by fitting two
parameters to data with R² between 0.00 and 0.31.

### 3.2 The decomposition: it is the market that moved, not the position

`b_consensus ≈ ρ · b_realised`, where `b_realised` is the value-spread curve fitted on **realised**
finish rank (needs no consensus; an order-statistic fit, labelled as such, not a forecast) and ρ is
the attenuation from consensus being an imperfect ordering. Ratio < 1 is mechanical and proves
nothing on its own; only its **movement** is informative.

| pos | | 2021 | 2022 | 2023 | 2024 | 2025 |
|---|---|---|---|---|---|---|
| **QB** | realised (value) | −72.8 | −83.2 | −60.1 | −75.6 | **−58.7** |
| | ratio ρ | 0.915 | 0.873 | 0.975 | 0.595 | **0.069** |
| | τ_b (ordering skill) | +0.484 | +0.305 | +0.263 | +0.263 | **−0.042** |
| **RB** | realised | −65.5 | −67.8 | −60.5 | −80.4 | −82.7 |
| | ratio ρ | 0.533 | 0.764 | 0.685 | 0.585 | **0.942** |
| | τ_b | +0.319 | +0.402 | +0.297 | +0.453 | **+0.507** |
| **WR** | realised | −65.3 | −60.0 | −62.1 | −52.7 | −57.8 |
| | ratio ρ | 0.577 | 0.830 | 0.742 | 0.672 | 0.641 |
| **TE** | realised | −45.9 | −48.4 | −38.9 | −45.2 | −38.8 |
| | ratio ρ | 0.930 | 0.842 | 0.680 | 0.562 | **0.438** |
| | τ_b | +0.305 | +0.263 | +0.326 | +0.200 | **+0.042** |

**QB 2025: the value spread was entirely normal (−58.7 against era means of −57.7 / −59.0 / −56.8)
and the market's ordering was worse than random.** RB's 2025 steepening is the mirror image — the
market was *unusually good* at RB (τ_b +0.507, its best of five) while the RB value curve barely
moved (−80.4 → −82.7). **Both of the two positions whose board slope moved in 2025 moved because of
market skill, in opposite directions, on top of a stationary value curve.**

Value spread over the deep sample, 1999–2024 (era means, and the full-sample trend):

| pos | 1999-07 | 2008-15 | 2016-20 | 2021-24 | trend/season |
|---|---|---|---|---|---|
| QB | −57.7 | −59.0 | −56.8 | **−72.9** | **−0.461 [−0.874, −0.034]** (steepening) |
| RB | −87.7 | −67.5 | −72.9 | −68.5 | **+0.990 [+0.721, +1.274]** (flattening) |
| WR | −57.2 | −56.0 | −50.3 | −60.0 | +0.024 [−0.154, +0.205] (none) |
| TE | −44.8 | −45.8 | −45.4 | −44.6 | −0.097 [−0.406, +0.222] (none) |

---

## 4. What weighting the holdout supports

**These are two different questions and this pass keeps them apart.**

### 4a. The board's own curve — n = 2, and it selects nothing

Target season N, curve fitted on consensus seasons < N under each scheme, evaluated on N. 2025 is
never a target. Targets with more than one training season: **2023 and 2024. That is the whole
sample.** τ_b is of the *induced cross-positional board* against the realised VBD ordering — the
metric that matches what the board is for, since the intercept cancels and RMSE can move while the
ordering does not.

| target | flat RMSE | flat τ_b | best scheme | its τ_b | τ_b spread across **all** schemes |
|---|---|---|---|---|---|
| 2023 | 69.72 | +0.3608 | last1 (69.07) | +0.3642 | 0.3608 – 0.3642 |
| 2024 | **68.89** | +0.3300 | **flat** | +0.3300 | 0.3283 – 0.3321 |

They disagree about which scheme wins, and the total spread across twelve schemes is **0.004
Kendall τ**. Nothing can be selected from this and nothing is.

### 4b. The value-spread curve — 20 targets, a real split, and a position-specific answer

Target N, value curve fitted on realised seasons < N under each scheme, RMSE against season N's
realised curve. Tuned on targets 2005–2015, reported on the held-out targets 2016–2024. Bootstrap
resamples **seasons**. `*` = 95% CI excludes zero.

**TEST, targets 2016–2024 (Δ RMSE vs flat pooling; negative = better):**

| scheme | QB | RB | WR | TE |
|---|---|---|---|---|
| last1 | **−18.79** * | +2.05 | **+2.75** * ← *worse* | +0.07 |
| last2 | **−21.45** * | +0.77 | +1.75 | −0.30 |
| last3 | **−21.77** * | +0.56 | +1.06 | −0.65 |
| last5 | **−22.24** * | +0.08 | +0.51 | −0.93 |
| last8 | **−21.74** * | −0.35 | −0.37 | −1.52 |
| last12 | **−16.36** * | −0.42 | −0.38 | −2.68 |
| **hl1** | **−22.59** * (45.00 → 22.41) | +0.32 | +1.02 | −1.09 |
| hl2 | **−22.52** * | −0.27 | +0.33 | −1.69 |
| hl3 | −20.97 * | −0.61 | +0.06 | −2.22 |
| **hl5** | −16.92 * | −0.84 | −0.09 | **−2.69** * |
| hl10 | −10.01 * | −0.72 | −0.10 | **−2.38** * |

Three things worth naming.

- **QB is the position where CLAUDE.md §6.4's premise is emphatically true.** Flat pooling of 26
  seasons is roughly *twice* as wrong as a one-season half-life, and it replicates across the
  training split (train Δ −11.7 at hl1, test Δ −22.6). This is the strongest result in the pass.
- **WR is the position where it is false in the harmful direction.** `last1` is +2.75 [+0.96, +4.80]
  *worse* than flat, CI excluding zero. Asked to say where adding older seasons degrades: at WR it
  does the opposite — **dropping them degrades.** Longer windows are mildly better.
- **TE is a live demonstration of the overfitting §6.3 warns about.** Training picked `last2` by a
  mile (Δ −12.44 [−15.79, −9.09]); on the holdout `last2` returns **−0.30 with a CI spanning zero**.
  The schemes that survive on test (hl5, hl10) are ones the training split did not point at. Had
  this been tuned without a holdout it would have shipped a scheme worth nothing.

**And the direction at QB is the opposite of the recorded fix.** The QB value curve is steepening;
weighting it recently makes the QB premium **larger**. The board's QB slope fell only because
consensus stopped ordering quarterbacks (§3.2), and **that component has zero measured persistence**
(lag-1 r = −0.007 [−0.414, +0.411], 16 pooled pairs). Persistence of the realised value slope, for
contrast, over 25 transitions per position: QB −0.056 [−0.379, +0.323], **RB +0.434 [+0.153,
+0.691]**, WR −0.034, TE −0.272.

---

## 5. What the flat fit costs, in board positions

The decision-relevant version. Real 2026 board, `src/make_board` construction, only the curve fit
swapped. Movement among the top 150.

| scheme | slopes QB/RB/WR/TE | move ≥5 | **≥10** | ≥25 | median \|move\| | max | slopes inside published CI? |
|---|---|---|---|---|---|---|---|
| **flat (shipped)** | −49.4 / −50.6 / −41.2 / −30.5 | — | — | — | — | — | — |
| last1 | −4.1 / −77.9 / −37.0 / −17.0 | 113 | **84** | 48 | 12 | 116 | **no** (3 of 4 outside) |
| last2 | −24.5 / −62.5 / −36.2 / −21.2 | 61 | 29 | 7 | 3 | 45 | **no** (3 of 4 outside) |
| last3 | −35.9 / −55.5 / −39.5 / −22.9 | 39 | 10 | 0 | 2 | 17 | yes, all four |
| hl1 | −28.1 / −62.2 / −38.6 / −22.7 | 59 | 21 | 4 | 3 | 34 | yes, all four |
| hl2 | −38.2 / −56.6 / −39.9 / −26.1 | 27 | 5 | 0 | 1 | 14 | yes, all four |
| **hl3** | −42.0 / −54.5 / −40.4 / −27.4 | 12 | **1** | 0 | 1 | 10 | yes, all four |
| **hl5** | −45.0 / −52.9 / −40.7 / −28.6 | 3 | **0** | 0 | 1 | 6 | yes, all four |

Because `vbd = b·ln(i/base)` exactly (§0), "the reweighted slope sits inside the pooled slope's own
95% CI" is *equivalent* to "no player moves outside his own published VBD interval." **Every scheme
from last3 down does.** The board's own error bars already say this change is beneath its
resolution.

Three further observations:

- **The movers are all in the wrong place.** Under every defensible scheme the largest movers are
  Zach Charbonnet, Woody Marks, Tyler Allgeier, Chris Rodriguez Jr. — deep running backs at board
  ranks 125–150, where a 10-team 15-round draft has already ended or is picking between bench
  bodies. The top-100 positional composition (RB 33 / WR 45 / QB 11 / TE 11) changes by **at most
  one slot** under every scheme except last1.
- **`last1` does not do what it was proposed to do.** It flattens QB to −4.1, which does remove the
  QB premium — and then puts **more** quarterbacks in the top 100 (11 → 17), because a flat QB curve
  parks every quarterback near replacement value, which beats the strongly negative VBD of the deep
  RBs and WRs it also creates. It also moves Josh Allen's VBD to +9.3 against a published interval
  of [+57.0, +155.2]. That is the only genuinely decision-changing move in the pass, and it comes
  from the one scheme with the least support.
- **The "correct" fix lands almost exactly where the board already is.** Descriptively, and *not*
  as a test: the thread-085 decomposition (recency-weighted realised value curve × mean attenuation)
  would imply b_QB = **−45.3** against the shipped **−49.4**, b_RB −52.0 vs −50.6, b_WR −39.6 vs
  −41.2, b_TE −29.8 vs −30.5. Whatever else is wrong with the shipped board, **flat pooling is not
  costing it four points of QB slope.**

---

## 6. What I am escalating rather than celebrating

**The mean attenuation ratio ρ over 2021–2025 is 0.686 (QB), 0.702 (RB), 0.693 (WR), 0.691 (TE).**
Four positions, four sample sizes, four different value curves, and the answer agrees to within
0.016. That is neat enough to be suspicious. Two readings and I cannot separate them: either
consensus is *equally informative at every position on average* and differs only in year-to-year
reliability (QB's ρ has sd 0.374 against WR's 0.097), or the ratio is partly pinned by the shared
mechanics of fitting the same log form over the same depth window to an order statistic and to a
noisy proxy of it. **It is 20 season-position ratios, uncorrected, spotted after the fact.** I am
recording it, not claiming it, and flagging it to `strategist` as the kind of too-neat number that
has been leakage before.

Second, smaller: **QB 2025's consensus fit has R² = 0.001 and τ_b = −0.042.** A market being
*slightly worse than random* at ordering the position it thinks about hardest is unusual enough to
state. I checked for the obvious mechanism and it is availability, not scoring: mean QB points 245.9
is mid-range, and the drop-one span is 45.3.

Nothing else here looks too good. Most of it is null, and the one strong positive (QB value-curve
recency weighting, §4b) points away from the change that was proposed.

---

## 7. Hypotheses generated, and their status

| Hypothesis | Status |
|---|---|
| The QB rank-curve slope collapsed 2021→2025 | **Not established.** Trend CI includes zero, depth-dependent, one-player-dependent |
| The same collapse is happening at RB / WR | **Rejected.** RB steepened in 2025; WR flat throughout |
| The same collapse is happening at TE | **Not established.** Cleanest monotone series in the pass, magnitude CI still spans zero, breaks at depth 32 |
| The board's slope movement is a *value* regime change | **Rejected.** Realised value curves are stationary 2021–2025 at all four positions |
| The board's slope movement is *market ordering skill* | **Supported, and it is the whole effect at QB and TE** (ρ 0.069 / 0.438 in 2025) |
| Recency weighting the board's consensus curve helps | **Unanswerable, n = 2**, and the component it would track has zero measured persistence |
| Recency weighting the **value** curve helps at QB | **Live and strong.** RMSE halves on a 9-season holdout. The best candidate in this pass |
| …at WR | **Rejected, harmfully.** last1 is +2.75 [+0.96, +4.80] worse |
| …at RB | **Rejected.** Nothing clears zero either way |
| …at TE | **Live but weak** (hl5, −2.69 [−4.71, −0.48]), and the training split picked a scheme that returns nothing on test |
| Flat pooling costs the board real positions | **Rejected.** ≤1 player in the top 150 moves ≥10 places under any scheme the data supports |
| Attenuation ρ ≈ 0.69 is constant across positions | **Recorded, not claimed.** §6 |
| QB value spread has been steepening since 1999 | **Live**, −0.461/season [−0.874, −0.034]. Would make the QB premium *bigger*, not smaller |
| RB value spread has been flattening since 1999 | **Live**, +0.990/season [+0.721, +1.274]. The strongest deep-sample trend in the pass |
| Consensus ordering skill is forecastable season to season | **Rejected.** lag-1 r = −0.007 [−0.414, +0.411] |

---

## 8. What binds this, and what would change it

**Missing market ADP is the binding constraint here exactly as it was in pass 2, and it binds
differently by section.** Everything using `rankings` uses FantasyPros ECR, 2021–2025, five
seasons, one sealed. Thread **055** (`data-ops`, FFC half-PPR 2018–2024) and thread **084**
(pre-2021 consensus) are both open.

| Section | Would thread 055 / 084 change it? |
|---|---|
| §3 per-season slopes and trend tests | **Yes, materially.** 4–5 usable seasons → 7–8. The permutation floor drops from 0.0167 to ~0.0005 and the trend CI narrows by roughly a quarter. **A real QB trend could clear at n = 8 that cannot clear at n = 5.** §3's verdict is "not established", not "disproved", and this is why |
| §4a board-curve weighting | **Yes, decisively.** 2 evaluable targets → 5–6. This is the section that is currently unanswerable and would stop being so |
| §3.2 decomposition, §4b value curve, §5 board cost | **No.** These need realised outcomes, not consensus, and already run on 20–26 seasons |

Also unchanged and worth restating: ECR rank is not draft cost. §5's "board positions" are
positions on our own board, which is the right unit for that question, but any statement about
*rounds* would inherit pass 2's measured ECR→ADP proxy error (median +12 at TE).

**Bearing on FR-054 (the model must output components), noted and not scoped into.** §0 is the
relevant fact: the shipped board's VBD is `b·ln(rank/base)`, the intercept cancels, and every player
at the same positional consensus rank receives an identical number. **It holds no player-level
opinion, and no reweighting of it can create one** — recency weighting changes four numbers, not 510
opinions. Two further constraints a component model inherits: the stacking bonuses are a nonlinear
function of a **per-game** distribution and cannot be recovered from a season total, so a components
model has to be per-game; and the 2,007 Sleeper/Rotowire component projections in
`data/projection-snapshots/` are a **baseline to beat, never an input**. None of this was acted on
in this pass.

---

## 9. Method, and the checks applied

- **Look-ahead.** Two universes kept apart. The consensus curve reads only `fantasypros_ecr`
  snapshots dated late August of their own season, strictly before Week 1; every weighting
  evaluation asserts `max(training seasons) < target`. The value curve reads realised outcomes only,
  1999–2024. §5 builds 2026 boards whose training window (2021–2025) is entirely prior, which is
  what the shipped board already uses.
- **Sealed season.** 2025 outcomes are read in §3 and §3.2 only, for the descriptive slope and its
  interval, because the published −4.1 *is* the question. 2025 is never a target, never a training
  season in a selection experiment, and no scheme in §4 is chosen with knowledge of it. Referred to
  `strategist`.
- **Survivorship.** Consensus universe frozen from the pre-season list; never-played players scored
  0 and retained. The realised-finish universe is by construction an order statistic — that is the
  definition of a value-spread curve, not a forecast, and it is labelled at every appearance and
  never used as a prediction.
- **Uncertainty.** Every slope carries a bootstrap 95% CI. Players are the resampling unit for a
  single-season fit (nothing else exists to resample); **seasons** are the unit wherever the estimand
  pools seasons, per `docs/statistical-guardrails.md` §7. Seed 20260729 throughout. Trend CIs are
  obtained by parametric resampling of each season's slope from N(slope, HC3 se), so the per-season
  estimation error propagates instead of being ignored.
- **Multiple comparisons: not corrected.** Eight trend tests, 48 scheme-position-split comparisons,
  20 depth cells, 20 jackknife series. This pass is exploratory and nothing is claimed as
  significant. The permutation floor is stated wherever a p is quoted so a 5-point series is not
  mistaken for evidence it structurally cannot supply.
- **Reproduction of the shipped object.** `weighted_fit(scheme="flat")` reproduces
  `make_board.fit_rank_curves` to 4 decimal places at all four positions, and reconstructing the
  board from four slopes reproduces the live 510-row ordering with zero mismatches. Every comparison
  in §5 is therefore against the real artefact, not a re-implementation of it.
- **Bug found and fixed in this pass's own code, recorded because it would have hung silently:** the
  trend test used an exact permutation over `n!` orderings, which is fine for the 5-season consensus
  series and infeasible for the 26-season realised one. It now switches to 20,000 sampled
  permutations above n = 8 and reports the attainable floor either way.

**Reproduction:**

```
.venv/bin/python experiments/bottomup/pass3_rank_curve_regimes.py --db data/nfl.db
.venv/bin/python experiments/bottomup/pass3_artifacts.py        --db data/nfl.db
.venv/bin/python experiments/bottomup/pass3_weighting.py        --db data/nfl.db
.venv/bin/python experiments/bottomup/pass3_persistence.py      --db data/nfl.db
```

Verified 2026-07-29 to reproduce every figure in §0, §3, §4 and §5 exactly.

**What would falsify the main conclusion.** More consensus seasons (threads 055 / 084). If the QB
consensus slope keeps falling across 2026–2027, or if a 7–8 season series produces a trend CI
excluding zero, "not established" becomes "established" and §5 has to be re-run. Nothing in this
pass rules a QB regime change out; it rules out *claiming* one from five noisy points.
