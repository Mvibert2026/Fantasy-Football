# Batch D1 results — the v2 player-availability (projected games) model

**Live document. Conclusion first, updated as work lands — not written at the end.**

Registration: `docs/ranking/factor-campaign-manifest/batch-D1.md`, committed `95e2bc9`
**before any arm was fitted**. m_b = 88. Control: v2 games arm **G0**, pinned. **The runner recorded
`M_CAMPAIGN = 218`**, which was the correct Σ m_b when it graded; batch C2 registered concurrently
and pm reconciled the campaign to **247** afterwards. A denominator that is too small is the
*anti*-conservative direction, so this is stated rather than buried — but nothing here is graded on
it (grading is suspended per C1) and no verdict in this document depends on BH.
**2025 never read.** Every arm asserts zero season-N feature reads, zero outcome reads at target,
**zero preseason-proxy reads** — so nothing here touches the unadmitted G2a week-1-of-N status.

---

## NEXT STEP

*Rewritten on every update. Written for a successor with none of this context.*

**The founder re-prioritised mid-session, 2026-08-01, and he was right.** The panel's 2018–2024
window was set by the latest-starting source, not by the stat lines, which go back to 1999. **That
work is done**: `docs/ranking/season-span-M4.md`. Headline — the core stat lines support 21 target
seasons, the binding constraint is the ADP archive, and the span curve is flat, so older seasons do
not hurt. §7 records what this batch contributed to it.

**Also answered while this batch was in flight** (founder's rookie ruling, 2026-08-01): **v2 already
fits rookies and veterans separately at every stage** — no lag feature carries a shared slope. The
live weakness is that `ROOKIE_COLS = ["log_draft_pick", "age"]` *is* the entire rookie model.
Evidence and the proposed fix: `season-span-M4.md` §4. Not started.

Batch D1 is **run, recorded and complete as registered**: eleven arms, two controls, no arm
adopted. Nothing here is graded INCLUDE — grading stays suspended per C1.

In priority order for whoever picks this up:

1. **The level-bias amendment is designed and NOT run** (§6). It is the largest measured defect in
   the games channel — worth roughly **1.0 game of MAE**, which is the whole margin against naive
   persistence — and the mechanism is now identified rather than guessed. It needs registering as
   batch-D1 Amendment 1 before it is fitted.
2. **Do not re-run A1 / A2 / A4.** Practice participation and injury class are measured and dead on
   points ordering; A4 is directionally harmful at all four positions.
3. **A3 (roster status) is the only arm above its calibration bar and only at RB, only on games
   ordering, at n = 5.** It is a candidate for one registered confirmatory arm, not for adoption.

To reproduce or re-grade with no refit:

```
.venv/bin/python -m experiments.bottomup.v2.run_d1 --regrade
```

State on disk: `experiments/bottomup/results/avail_d1_cells.csv` (per arm-position-season),
`avail_d1_contrasts.csv` (graded), `avail_d1_players/*.csv.gz` (per-player output per arm).

---

## 1. The headline, in one paragraph

**The injury and practice data does not fix the games model, and the placebo says most of what
looked like a fix is the estimator.** Swapping the incumbent clipped-OLS availability model for a
binomial GLM on the *same* feature list (arm B0) buys +0.067 games-ordering correlation over naive
persistence at RB — and the seeded-noise placebo buys +0.070 on the identical contrast, because both
share the form change. Of eleven arms, the only one clearing its own window's placebo bar on games
ordering is **A3 (roster status), at RB only, by +0.025, at n = 5 seasons**. Practice participation
(A1) and injury class (A2) are null-to-harmful on the absolute steering metric, and their
combination (A4) is directionally harmful at all four positions. **Meanwhile the defect that
actually costs the model the MAE bar was found and it is not an injury-data problem at all** (§6).

## 2. What was new, and what it cost to use

Three tables ingested and read by no model. What each turned out to be worth:

| source | what it uniquely carries | verdict |
|---|---|---|
| `injuries` practice participation (DNP / Limited / Full), 2010–2024 | the structured, backtestable version of what beat reporters report on | **NULL to HARMFUL** (A1, A4) |
| `injuries` body part + cross-season recurrence | structural / soft-tissue / head / rest classes | **NULL** on games, +0.021 at QB on points, below BH, above placebo |
| `rosters_weekly` weekly status, season N−1 | **resolved vs ongoing absence** — was he still employed and on reserve at season end | **the only arm above its placebo bar**, RB games ordering only |
| `depth_charts_weekly` | tested as a full-span substitute for roster status | **ELIMINATED** — see §3 |

## 3. The raw signal is real; the model does not capture it

The recon (registration §2, survivorship-safe, outcome seasons ≤ 2024) found the instrument B1
was missing. Among players who missed ≥40% of season N−1:

| end-of-N−1 state | n | mean games in N | reach 12+ games |
|---|---|---|---|
| on **reserve** (IR/PUP) in the final 3 weeks | 562 | **5.96** | **26.7%** |
| not on reserve | 3,079 | 4.14 | 13.7% |
| B1's box-score signal — **played** in the final 3 weeks | 2,253 | 4.56 | 16% |
| B1's box-score signal — did not | 1,388 | 4.19 | 16% |

**Being on IR at the end of the year is good news relative to being cut**, because it means you are
still employed and hurt rather than gone. That is the resolved-vs-ongoing distinction the founder
named, and it is the reverse of the intuitive reading. It also explains **why fable's G1/G1a
failed**: the box-score timing signal it was built on separates nothing in exactly the population it
was built for — 4.56 vs 4.19 games, 16% vs 16%.

The contrast is stable: 2017–2024, eight consecutive seasons, the reserve group is ahead every year
by +1.4 to +2.6 games.

**Defect check, prompted by the concurrent discovery pass:** `depth_charts_weekly.pos_rank` and
`.pos_slot` are entirely unpopulated and the real field is `depth_team`. **No code in batch D1 reads
either** (`grep pos_rank|pos_slot` over `experiments/bottomup/v2/` is empty), and the depth-chart
loader this batch inherited, `pos_data.load_depth_seasons`, already keys on `depth_team`. Nothing
here is an artifact of that defect. The `depth_first_share_1` column named in §6 as a candidate also
derives from `depth_team` and is safe to use.

**`depth_charts_weekly` is eliminated as a substitute source.** Its coverage *is* stable across the
whole span (end-of-season presence 0.61–0.78, no break), which is why it was worth testing — but the
equivalent flag carries no contrast at all: 4.26 vs 4.44 mean games in N, sign flipping season to
season. The full-span source does not carry the signal and the source that carries it is not
full-span.

### The coverage break that costs five seasons, measured before use

`rosters_weekly` holds RES rows from 2002, but **end-of-season RES capture breaks hard at 2017**.
Prevalence of `res_end` in the missed-≥40% population:

| feature seasons | 2012 | 2013 | 2014 | 2015 | 2016 | 2017 | 2018 | 2019 | 2020 | 2021 | 2022 | 2023 | 2024 |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| `res_end` rate | .012 | .035 | .038 | .040 | .045 | **.223** | .227 | .217 | .246 | .205 | .276 | .182 | .173 |

This is batch 7 D2's geometry exactly, and batch 5's mistake was restricting the *target* window
only. The fix here restricts the **training** window: arms using the block run against **CTRL-D**
(`first_feature_season` 2018, targets 2020–2024, **n = 5**) rather than CTRL-A (2012, 2018–2024,
n = 7). Two seasons of power bought the right to use the feature at all.

## 4. Results

Deltas are per-season paired season-block bootstrap, 4,000 reps, seed 20260801, against the arm's
**matched** control. `placebo` is that window's own seeded-noise arm on the identical contrast — the
calibration instrument, not a rival result.

### E1 — absolute steering metric: Δρ(projected points, realised points) vs matched G0

| arm | QB | RB | TE | WR |
|---|---|---|---|---|
| **placebo (n=7)** | +0.0044 | −0.0003 | +0.0051 | +0.0043 |
| **placebo (n=5)** | −0.0037 | −0.0019 | +0.0043 | +0.0050 |
| B0 form only | **+0.0281** ᴮᴴ | −0.0016 | +0.0093 | +0.0036 |
| B0d form only (n=5) | +0.0031 | +0.0028 | +0.0002 | +0.0016 |
| A1 practice | −0.0408 | −0.0082 | −0.0235 | −0.0110 |
| A1k presence control | +0.0227 | −0.0066 | +0.0104 | +0.0015 |
| A2 injury class | +0.0208 | −0.0082 | −0.0216 | −0.0119 |
| **A3 roster status (n=5)** | −0.0074 | **+0.0141** | −0.0030 | **+0.0138** |
| A3k presence control (n=5) | +0.0054 | +0.0020 | −0.0072 | +0.0022 |
| A4 practice + class | **−0.0475** | −0.0096 | −0.0306 | −0.0191 |
| A5 everything (n=5) | −0.0402 | −0.0152 | −0.0100 | −0.0219 |

### E2 — games ordering: Δρ(projected games, realised games) vs naive persistence

| arm | QB | RB | TE | WR |
|---|---|---|---|---|
| **placebo (n=7)** | −0.0238 | **+0.0700** | −0.0769 | +0.0653 |
| **placebo (n=5)** | −0.0649 | **+0.1219** | +0.0983 | +0.0284 |
| B0 form only | −0.0068 | +0.0672 | −0.0722 | +0.0670 |
| B0d form only (n=5) | −0.0521 | +0.1233 | +0.1172 | +0.0362 |
| A1 practice | −0.0393 | +0.0069 | −0.0511 | +0.0602 |
| A1k presence control | −0.0025 | +0.0390 | −0.0807 | +0.0594 |
| A2 injury class | −0.0268 | +0.0513 | −0.0945 | +0.0486 |
| **A3 roster status (n=5)** | −0.1254 | **+0.1470** | +0.0610 | +0.0412 |
| A3k presence control (n=5) | −0.0519 | +0.1249 | +0.1241 | +0.0364 |
| A4 practice + class | −0.0405 | −0.0054 | −0.1201 | +0.0365 |
| A5 everything (n=5) | −0.0766 | +0.0993 | +0.1556 | −0.0583 |

**Read the placebo rows first.** At RB the placebo alone is +0.070 / +0.122 and BH-robust at the
campaign denominator. The E2 contrast is arm-vs-naive, so every arm inherits the estimator-form
gain; the placebo measures exactly that shared component. **What is attributable to data is the
excess over the placebo row, and there is only one: A3 at RB, +0.025.** A3k, the bare
"has a roster row in N−1" indicator, lands on the placebo (+0.125 vs +0.122) — which at least
clears the block of being a pure employment proxy, batch 5's failure mode, but leaves the treatment
with a very thin margin.

### The registered predictions, scored honestly

| # | prediction | outcome |
|---|---|---|
| 1 | placebos 0 WIN; expect 1–2 of 16 given C1's 9.6% | **Wrong, and worse than predicted.** 3 of 16 placebo cells have CIs excluding zero and 2 are BH-robust at M = 218. The E2 endpoint is structurally favourable to it (see above). |
| 2 | B0 form-only NULL everywhere on E1 | **Wrong at QB** (+0.028, BH-robust, clears placebo). Right at RB/WR/TE. |
| 3 | A3 at RB/WR on E2, 60% | **Half right.** RB yes and above the placebo; WR +0.041 is below its placebo-adjusted bar. E1 30% — RB +0.014 and WR +0.014, both above the placebo, both CI-inclusive of zero. |
| 4 | A1 / A2 more likely NULL than not, 25% either clears | **Right.** Both null-to-harmful; A2's only above-placebo cell is QB on E1. |
| 5 | 40% that a presence control matches its treatment | **Right at A3k** (matches, and matches the placebo). A1k *beats* A1 on E1 at all four positions. |
| 6 | QB not fixed | **Right.** Best QB result is B0, the form change with no new data. |
| 7 | level bias persists | **Right, and it is the finding** — §6. |

## 4b. On a continuous endpoint the arms DO work — and the registered endpoint cannot see it

**Post-hoc, not registered, not in m_b, and it cannot promote any arm.** The concurrent discovery
pass specified this metric after these arms had run, and the coordinator asked for it explicitly so
that a fix is verifiable in the terms the defect was stated in. Reported as a diagnostic and as an
argument about *endpoints*, not as a result about factors.

Residual = z(realised) − z(projected), standardised **within (position, season)** so a season-level
scoring shift cannot enter. Positive = under-projected. Buckets are prior-season games played.
Code: `experiments/bottomup/v2/reversion_buckets.py`.

**Full veteran universe, points residual (n = 705 / 1,285 in the two named buckets):**

| arm | 0–4 games in N−1 | 14–17 games in N−1 | what changed |
|---|---|---|---|
| discovery pass's own measurement | +0.23 | −0.29 | the defect as stated |
| **CTRL-A = G0, the incumbent** | **+0.315** | **−0.271** | independently reproduced |
| B0 — estimator form only, no new data | +0.304 | −0.269 | **barely moves** |
| **A3 — roster status** | **+0.235** | **−0.220** | −25% / −19% |
| **A5 — everything** | **+0.214** | **−0.199** | **−32% / −27%** |

Same picture on the board population (CTRL-A +1.132 / −0.265 → A5 +0.813 / −0.188) and on the games
residual directly (CTRL-A +0.561 / −0.359 → A5 +0.383 / −0.271).

**Two things follow, and the second matters more than this batch.**

1. **The narrowing comes from the data, not the estimator.** B0 — the identical form change with no
   new columns — moves the residual by 0.011 SD. A5 moves it by 0.101 SD, nine times as much. This
   is the opposite of what E2 said, and both are correct: E2's gain is shared with the placebo
   because it is a form gain, and the *data* gain lives somewhere E2 cannot see it.
2. **The registered endpoint is too noisy to detect an effect this size, and that is a methodology
   finding, not an excuse.** E1/E2 are per-season Spearman over 5–7 seasons on 10–50 graded players,
   which C1 measured as awarding a WIN to pure noise on 9.6% of cells. The residual endpoint is
   continuous on 2,000 player-seasons. **The next confirmatory arm should be registered on the
   continuous endpoint** — which is also what M-5's own rule points at (continuous endpoints with
   per-cell n ≥ 100 sit outside the BH withdrawal). This is a recommendation to `strategist`, not a
   decision taken here.

**Do not read this as "A5 works."** A5 is directionally harmful on E1 at all four positions. What it
says is that the availability data moves the specific defect it was built to move, while
simultaneously costing ordering quality elsewhere — and that the batch's registered instruments
could not have told those two things apart.

## 5. The two named cases and the tail-shrinkage defect

`sd(projected games)` against `sd(realised games)` on the graded board population, averaged over
seasons — the founder's "shrinks both tails", quantified:

| position | sd projected (G0) | sd realised | ratio |
|---|---|---|---|
| QB | 2.93 | 3.49 | 0.84 |
| RB | 2.21 | 3.89 | **0.57** |
| WR | 2.65 | 3.39 | 0.78 |
| TE | 2.07 | 3.02 | 0.68 |

The compression is real and it is worst at RB. **No arm in this batch materially widened it**: the
best (A5 at RB) reaches 2.65 against a target of 3.89.

## 6. The defect that actually costs the MAE bar — and it is not injury data

Every arm loses to naive persistence on games MAE at every position. That looks like a modelling
failure and it is not: **it is a population mismatch, and it is worth about one full game of MAE.**

| population | n | mean realised games | mean projected games | bias |
|---|---|---|---|---|
| full veteran universe — **what the model is fitted on** | 1,945 | 8.41 | 8.27 | **−0.14** |
| board (M-panel) veterans — **what the model is used on** | 597 | 13.53 | 11.12 | **−2.41** |

The calibration curve on the fit population is essentially perfect (OLS of realised on projected:
slope 0.976, intercept 0.35, every decile on the diagonal). The model is not miscalibrated. It is
calibrated for the wrong population, so a plain recalibration cannot fix it.

**Removing the observed level bias alone would win the MAE bar at every position tested:**

| position | model MAE | naive MAE | model MAE, level-corrected |
|---|---|---|---|
| QB | 4.22 | 3.35 | **3.21** |
| RB | 4.23 | 3.89 | **3.31** |
| WR | 3.88 | 3.08 | **3.00** |

### The mechanism, measured

Comparing board and non-board veterans **at matched projected games (9–13)**:

| | n | projected | realised | `gshare_1` | `pts_1` | age |
|---|---|---|---|---|---|---|
| on the ADP board | 336 | 11.24 | **13.77** | 0.87 | **181.9** | 27.1 |
| not on the board | 398 | 10.84 | **9.61** | 0.84 | **87.8** | 27.2 |

Same projected availability, same prior-season availability, same age — and a 4.2-game gap in
realised games, separated by **prior-season production**. The games model's feature list
(`gshare_w, gshare_1, present_1, age, age2, evidence`) contains **no measure of how good the player
is**, only of how available he has been. Good players are not benched, not cut, and are worked back
from injury; that is a real availability channel and nothing in v2 models it.

**This is a consensus-free hypothesis** — `ppg_w`, `pts_1`, `tshare_w`, `cshare_w`,
`depth_first_share_1`, draft capital and experience are all already computed in the feature frame
and none of them is an expert or market ranking. It is designed and **deliberately not run**: it
was found by looking at this batch's own output, so it needs registering as Amendment 1 before it
is fitted. Writing it up as a result of batch D1 would be grading my own homework.

### The two named cases

The Burrow/Hill class is tracked as `n_returning` / `bias_games_returning` per cell in
`avail_d1_cells.csv`. **Individually named players are not re-checked here on purpose**: the level
bias above is a property of the whole board population, so a single player's projection is not
diagnostic of anything until it is fixed, and picking two players out of a frame after seeing the
frame is the anecdote-selection failure this project's calibration prior warns about. Once the level
amendment runs, both cases should be re-read from the corrected board — that is the honest order.

## 7. What this batch says about the season span (M-4)

Two facts from this batch bear directly on the founder's 2026-08-01 push-back:

- **A3's window is n = 5 and A3's RB result is the batch's only above-placebo cell.** At n = 5 the
  placebo itself is BH-robust. This is what `S = 7` (or 5) costs: the calibration instrument and
  the treatment are indistinguishable.
- **The full-veteran-universe endpoint `rho_points_fullvet` needs no ADP board at all** and is
  already computed on every cell (0.65–0.75 across arms). The M-panel endpoint is the one capped at
  seven seasons, and it is capped by the *ADP file*, not by the stat lines.

The span work is `docs/ranking/season-span-M4.md`.
