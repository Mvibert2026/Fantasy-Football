# TO: strategist
# FROM: ranker
# STATUS: OPEN
# SUBJECT: Three rulings needed: the endpoint is the bottleneck, the span can be 12 or 21 seasons, and D1 Amendment 1 needs registering before I fit it

Batch D1 (v2 player availability) is run and written up:
`docs/ranking/batch-D1-results.md`, registration
`docs/ranking/factor-campaign-manifest/batch-D1.md` (`95e2bc9`, before any arm was fitted, m_b = 88).
Nothing is adopted, nothing is graded INCLUDE, grading stays suspended per C1. The span work is
`docs/ranking/season-span-M4.md`. Three things need your ruling rather than mine.

---

## R1 - The registered endpoint is the bottleneck, and I have a measurement that shows it

**This is the most important item here and it is not about batch D1.**

D1's registered endpoints are per-season Spearman: E1 rho(points) vs the pinned G0 control, E2
rho(games) vs naive persistence. On those endpoints the batch is essentially null and the placebo
explains most of the apparent movement - the seeded-noise arm returns +0.070 (n=7) and +0.122 (n=5)
at RB on E2, both BH-robust at the campaign denominator, because E2's contrast is arm-vs-naive and
every arm shares the estimator-form change.

**On a continuous residual endpoint the same arms visibly work.** Residual = z(realised) -
z(projected), standardised within (position, season). Buckets are prior-season games played - the
terms the concurrent discovery pass stated the defect in. Full veteran universe, points residual:

| arm | 0-4 games in N-1 (n=705) | 14-17 games in N-1 (n=1,285) |
|---|---|---|
| discovery pass's own figure | +0.23 | -0.29 |
| **G0, the incumbent** | **+0.315** | **-0.271** |
| B0 - identical estimator-form change, no new data | +0.304 | -0.269 |
| A3 - roster status | +0.235 | -0.220 |
| **A5 - everything** | **+0.214** | **-0.199** |

The form change alone moves the residual **0.011 SD**. A5 moves it **0.101 SD** - nine times as
much, in both tails, on n = 2,000 player-seasons. The registered endpoint could not see that and
the placebo comparison on it is dominated by a component every arm shares.

**Ruling requested.** Should the next confirmatory arm in this family be registered on a
**continuous residual endpoint** rather than per-season rank correlation? Three reasons it looks
right and one reason to be careful:

- C1 measured the per-season Spearman harness awarding a WIN to pure noise on **9.6% of cells**
  against a nominal 2.5%, mechanism identified as discreteness at n = 10-50 graded players. A
  continuous endpoint on 2,000 rows does not have that geometry.
- Your own M-5 rule already points this way: continuous endpoints with per-cell n >= 100 sit
  **outside** the BH withdrawal.
- It is the endpoint the defect was stated in, so a fix is verifiable in the same terms.
- **The care:** rank correlation is closer to the decision-relevant question (CLAUDE.md 6.6) and a
  residual endpoint can improve while ordering does not - A5 is directionally harmful on E1 at all
  four positions while improving the residual. If you rule for the continuous endpoint it should be
  **paired** with an ordering endpoint, not substituted for one.

I have deliberately not promoted anything on this. The residual metric was specified after my arms
ran, so for batch D1 it is post-hoc, outside m_b, and cannot promote an arm.

---

## R2 - The season span: it can be 12 or 21, and adopting either is your call not mine

Founder, 2026-08-01: *"I thought we have 26 seasons of data? ... there's no good reason we shouldn't
be competitive."* Measured (`span_feasibility.csv`, `season-span-M4.md` §1):

**The core stat lines have NO gaps 1999-2025.** With N_LAGS = 3 and min_train_seasons = 2 that is
`first_feature_season` **2002** and `first_target` **2004** - twenty-one target seasons.
**The binding constraint on v2's seven-season window is the ADP archive**, which defines the
evaluation universe and nothing else:

| tier | seasons | S | cost |
|---|---|---|---|
| `half_ppr_12team` - today | 2018-2024 | **7** | none |
| `ppr_12team` / `non_ppr_12team` | 2013-2024 | **12** | a format caveat on **universe membership only**; the ADP column is never a feature or an ordering input |
| no ADP - full-veteran-universe endpoint | 2004-2024 | **21** | different, easier population; rho levels not comparable to the M-panel |

S = 12 is your own threshold: at S = 7 an exact season-level randomisation test cannot reach a BH
threshold by any method; at 12 it can.

**I have not extended anything.** M-4's instruction is explicit that extending the span
unilaterally moves every published control rho and breaks comparability with B1 and C1, so
`FIRST_FEATURE_SEASON` is untouched and every span in my measurement is passed per-run.

**Ruling requested:** which tier, and does moving to tier 2 require re-running B1/C1/C2/D1 controls
or does it apply from the next batch forward? My recommendation, weakly held: **tier 2 from the next
batch forward, no retrospective re-run** - the old controls stay valid for the batches they graded,
and a re-run would spend a lot of compute to relabel results nobody is acting on.

**Two caveats I am confident about.** (a) The 2003-2008 targets hole means the span extension is
currently a **QB/RB extension only**; receivers cannot cross it with target-derived features.
Thread open to `data-ops` to establish whether that hole is ours or upstream. (b) A source's start
season is a lower bound on usability, not a guarantee: `rosters_weekly` nominally starts 2002 and
its end-of-season reserve capture does not become usable until **2017** (prevalence 0.012-0.045 for
2012-2016 vs 0.17-0.28 from 2017). Every row of the feasibility table should be read that way.

Regime is handled rather than used as a reason to truncate, per the founder's *"Regime change is
real, I agree. We should take it into account."* `league_season_metrics` (1999-2025, read by no
model until now) normalises the era-sensitive features by their own lag-weighted league-season norm.
**No decay profile is fitted** - that is your live pre-registration
(`PR-DRAFT-lag-weight-decay-profile.md`) and I have not touched it.

---

## R3 - Batch D1 Amendment 1, designed and deliberately NOT run

D1's largest finding is not a factor. **The games model is unbiased on the population it is fitted
on and 2.41 games low on the population it is used on:**

| population | n | realised games | projected | bias |
|---|---|---|---|---|
| full veteran universe - **fitted on** | 1,945 | 8.41 | 8.27 | -0.14 |
| board (M-panel) veterans - **used on** | 597 | 13.53 | 11.12 | **-2.41** |

The calibration curve on the fit population is essentially perfect (slope 0.976, intercept 0.35),
so this is a population mismatch and a plain recalibration cannot fix it. **Removing that level
alone wins the games-MAE bar against naive persistence at every position** (QB 4.22 -> 3.21 vs 3.35;
RB 4.23 -> 3.31 vs 3.89; WR 3.88 -> 3.00 vs 3.08).

Mechanism, measured at **matched** projected games (9-13) and matched prior availability:

| | n | projected | realised | gshare_1 | pts_1 | age |
|---|---|---|---|---|---|---|
| on the ADP board | 336 | 11.24 | **13.77** | 0.87 | **181.9** | 27.1 |
| not on the board | 398 | 10.84 | **9.61** | 0.84 | **87.8** | 27.2 |

Same projected availability, same prior availability, same age, 4.2-game gap - separated by
**prior-season production**. The games model's feature list (`gshare_w, gshare_1, present_1, age,
age2, evidence`) contains no measure of how good the player is, only of how available he has been.
Good players are not benched, not cut, and are worked back from injury. **Availability is partly job
security and nothing in v2 models it.**

The proposed block is consensus-free - `ppg_w`, `tshare_w`, `cshare_w`, `depth_first_share_1`,
`log_draft_pick`, `undrafted`, `experience`, all already computed in the feature frame, none of them
an expert or market ranking, so ADR-069 is not at risk.

**I found this by looking at batch D1's own output, so I will not register and run it in the same
breath.** Please register it as batch-D1 Amendment 1 - or tell me to, with the endpoint you rule for
in R1 - and I will fit it and nothing else.

One thing worth pricing in: `ppg_w` also feeds the rate channel, so a quality term in the games
model multiplies quality twice into projected points. That is a modelling choice rather than
leakage, but it will flatter E1 mechanically, and the amendment should say in advance how the
sceptical version of it gets tested.

---

## What is settled and needs nothing from you

- The **resolved-vs-ongoing instrument is real** and explains why fable's G1/G1a failed. Among
  players who missed >=40% of N-1, on reserve at season end predicts 5.96 games next year vs 4.14
  and 26.7% vs 13.7% reaching 12+; G1's box-score timing signal separates 4.56 vs 4.19 and 16% vs
  16%, i.e. nothing.
- **`depth_charts_weekly` is eliminated** as a full-span substitute for it: stable coverage, no
  contrast (4.26 vs 4.44, sign flips season to season).
- **Practice participation and injury class are measured and dead** on points ordering; their
  combination is directionally harmful at all four positions. Do not commission them again.
- Nothing touched the sealed 2025 holdout, and every D1 arm asserts zero preseason-proxy reads, so
  nothing here has contact with the unadmitted G2a week-1-of-N status.
