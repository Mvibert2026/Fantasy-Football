# Bottom-up component model — WR, pass 1

**Ranker, 2026-07-29.** Answers **FR-054**. **Exploratory.** Nothing here is confirmatory, nothing
is registered, no multiplicity correction is applied, and **no result below may be reported as an
edge.** Every number is a hypothesis. The one test worth registering is named in §8 and has not been
run.

Code: `experiments/bottomup/components/` (committed). Reproduce with
`.venv/bin/python -m experiments.bottomup.components.run_wr`. Outputs:
`experiments/bottomup/results/wr_components_{walkforward,metrics}.csv`.

---

## 0. What this is, and how it differs from everything else in the repo

The shipped board is **consensus-derived at player level**: every player at the same positional
consensus rank receives an identical projection, so it holds no opinion about any individual player.
Passes 1 and 2 measured *how wrong consensus is*. Neither built a thing that could disagree.

This does. It projects, per player:

| | |
|---|---|
| `proj_games` | expected games played |
| `proj_targets`, `proj_receptions` | volume |
| `proj_rec_yards`, `proj_rec_tds` | production |
| `proj_carries`, `proj_rush_yards`, `proj_rush_tds`, `proj_fumbles_lost` | the rest of the ledger |
| `p_100yd_game`, `p_150yd_game`, `p_200yd_game` | **per-game distribution** — the stacking bonuses |

**Points are what you get when you score those numbers. A rank is what you get when you sort them.**
Change the ruleset and the same components produce a different rank without refitting anything —
`wr_model.score_components()` does exactly that. This is the object FR-040 and FR-042 need and no
current artifact can produce.

**Sleeper/Rotowire's 2,007 component rows were not read, at all, by any code in this pass.** They are
a baseline to beat, and blending them in would be the thing `CLAUDE.md` §4's `ranking_source` rule
exists to prevent.

---

## 1. Conclusion first

**Four findings, two of them negative and the negatives are the more valuable ones.**

**(1) The model beats both naive baselines cleanly and does *not* clear consensus ADP.** On the
seven seasons where real ADP exists, mean Spearman advantage over consensus is **+0.048, 95% CI
[−0.013, +0.124]**. Per `CLAUDE.md` §6.5 that is **reported as a failure to beat the market**, and it
is the headline. It beats prior-season points by +0.128 [+0.072, +0.186] and the weighted-PPG
heuristic by +0.091 [+0.013, +0.163], both clear of zero.

**(2) The component projections beat naive persistence on every component, decisively.** This is the
FR-054 deliverable and it is the one unambiguous win. Receiving yards MAE falls **31.0 points per
player-season [−37.4, −25.0]**, receptions **2.4 [−2.8, −2.1]**, receiving TDs **0.28 [−0.35, −0.21]**,
games **0.64 [−0.76, −0.51]**. The projection is real; what is not yet demonstrated is that it orders
players better than the market.

**(3) The ceiling channel is bounded, and the bound is small. This is the most important number in
the document.** With **perfect foresight of every player's realised stacking-bonus points**, rank
correlation improves by **+0.026 [+0.018, +0.033]** on the ADP board and **+0.008 [+0.006, +0.010]**
on the full universe. That is the hard ceiling on *everything* a ceiling/variance model could ever buy
at wide receiver. The modelled version captures approximately none of it: **+0.0002 [−0.0000,
+0.0005]**, moving a median WR by **0.15 rank positions** and never more than 5.

**(4) And there is nothing left to model, because conditional on mean yards per game, WRs do not
differ in spike rate.** Variance decomposition on 1,360 player-seasons: observed dispersion of the
100-yard-game rate around the yards-per-game curve is **0.00302**; dispersion implied by binomial
sampling noise alone is **0.00478**. The excess is **−0.00176** — *negative*. Year-over-year
persistence of the spike residual is **−0.006 [−0.073, +0.060]**. **There is no player-level
"spike-week-ness" at WR beyond what the mean already tells you.**

This independently reproduces PR-002's NULL with a sharper instrument (a variance decomposition, not
a correlation) and closes the question the project's own notes called *"the single honest
consensus-relative claim available."* **It is not available. At WR, the stacking bonus is a monotone
function of projected yards per game and therefore cannot reorder anybody.** The founder's belief
that his league pays for ceiling is correct about the *scoring rules* and wrong about the
*exploitable consequence* — the bonus is worth roughly 1.5% of a WR's points and is earned by exactly
the players a mean-based projection already ranks first.

**What I would do next, and it is not more ceiling work:** §7's availability defect. The model's ten
worst calls are all the same failure and it is fixable.

---

## 2. Why wide receiver

Asked to do one position properly. WR, for four reasons, in order of weight:

| | |
|---|---|
| **Data depth** | ~200 draft-relevant WRs a season versus ~75 TEs and ~20 fantasy QBs. Given that the strong feature set has only 2009-2024 and three of those go to lags, rows per season is the binding resource, and WR has the most of them by a factor of 2.5 over TE. |
| **Component identifiability** | A WR is one usage stream: targets → receptions → yards → touchdowns. RB is two streams that behave differently and interact with game script; QB is a different scoring regime and was closed after six failed configurations. WR is where a component model is actually identified rather than a mixture. |
| **Roster weight** | 3 WR + 2 flex of 9 offensive starters. Ordering quality at WR moves more roster decisions than at any other position. |
| **The bonus question is live here** | 100/150/200-yard receiving games happen often enough to measure — across the 1,360 player-seasons with ≥8 games there are **1,682** hundred-yard games, **300** at 150 and **39** at 200. Thin at the top threshold and stated as such; at TE all three would have been unanswerable. |

**Not TE**, despite pass 1 pointing there, and this is a deliberate departure. Pass 1's TE finding was
about *consensus mispricing* — the market's error, measured against the market. This pass builds the
thing that has its own opinion, and that needs sample. TE is the right second position precisely
because pass 1 says the market is weakest there; it is the wrong first one.

---

## 3. How the data boundary was handled

**Measured, not assumed** (`experiments/bottomup/data.py` and re-verified here from
`player_weekly_stats`):

| Seasons | Targets | Air yards / target share |
|---|---|---|
| 1999-2002 | present | **absent** |
| **2003-2008** | **effectively zero** (WR target sums of 3, 1, 0, 29, 6, 5) | absent |
| 2009-2024 | present | present |

**The decision: this model uses the 2009+ feature set only, and pays for it in seasons.** Three lag
seasons are consumed, so the first constructible feature row is 2012 and the first target season with
any training history is 2014. That yields **11 walk-forward seasons, 2014-2024**, of which **7 have
real ADP**. The deep 1999-2008 sample was **not** used, because the only features it supports
(points, games) are the very baselines this model has to beat — training on it would add rows that
teach the model to be its own baseline.

**Reported as a finding rather than routed around:** the 2003-2008 gap does not merely reduce the
sample, it makes the deep sample *useless for this class of model*. Any future claim that "we have 26
seasons" is false for anything usage-based; the real number is 13.

**Two named gaps in `CLAUDE.md` §5 were hit and neither was proxied silently:**

- **Route participation** — not available. `snap_counts` (2013+) is the documented proxy and was
  **not** used here, because introducing a proxy in the same pass that establishes a baseline makes
  the baseline uninterpretable. It is the first candidate for pass 2 and would be labelled as a proxy.
- **Vegas implied team totals** — not in the database. Pass 1 bounded the whole team-environment
  channel at ≤ +0.055 τ_b by oracle, so this remains unfunded on current evidence.

---

## 4. Look-ahead and survivorship — what was actually enforced

**Look-ahead is structural, not conventional, and it is now audited rather than asserted.**

`SeasonPanel` has no accessor that returns everything. `before(cutoff)` filters and asserts;
`outcomes(season)` is a separate method so that reading a target season has to be written on purpose.
Every call appends to an access log, and the walk-forward **asserts after every fit** that the maximum
feature cutoff and maximum outcome season are strictly below the target and that zero outcome reads
occurred at the target season. Output:

```
 max_feature_cutoff  max_outcome_season  n_outcome_reads_at_target  season
               2013                2013                          0    2014
               ...
               2023                2023                          0    2024
PASS
```

This catches the specific bug that matters here — the bonus recalibration in §6 needs projections for
training seasons, and the obvious implementation would have fitted them on all training data
including the season being projected. The audit would have failed. It does not.

**ADP is read at a real pre-draft date, and the gate is recomputed rather than trusted.** FFC's
archived boards carry a window-end `as_of_date`; `adp_baseline.load_adp` **refuses the season** unless
every row is strictly before that season's real Week 1 kickoff, which is parsed from PFR game ids in
`snap_counts` (`201809060phi` → 2018-09-06), not taken from a doc. 2018's window ends Sept 4 against a
Sept 6 kickoff — two days of margin, and it passes on measurement rather than on assertion.

**Survivorship: the universe is frozen before the season and busts are retained.** Inclusion is
(a) ≥15 targets as a WR in N−1 or N−2, (b) drafted at WR in rounds 1-4 of the N draft, or (c) on that
season's pre-kickoff ADP board. All three are pre-Week-1 facts.

| season | universe | on ADP board | **played 0 games** | rookies | mean actual pts |
|---|---|---|---|---|---|
| 2018 | 201 | 46 | **48** | 15 | 69.2 |
| 2020 | 208 | 57 | **53** | 18 | 67.5 |
| 2022 | 213 | 43 | **46** | 20 | 64.9 |
| 2024 | 210 | 61 | **45** | 20 | 66.8 |

**Roughly a quarter of every season's universe plays zero snaps and scores zero, and they stay in.**
Retirees, cuts, season-long injuries. Defining the universe from who produced would have deleted all
of them.

---

## 5. The headline — measured against all three required baselines

Universe: the season's ADP board WRs, so the comparison against consensus is on the market's own
universe. Metric: Spearman rank correlation with realised season points under this league's scoring,
stacking bonuses included.

| season | n | **model** | B1 consensus ADP | B2 prior-season pts | B3 weighted prior PPG |
|---|---|---|---|---|---|
| 2018 | 46 | **0.656** | 0.631 | 0.587 | 0.615 |
| 2019 | 53 | **0.548** | 0.541 | 0.466 | 0.451 |
| 2020 | 57 | **0.421** | 0.406 | 0.214 | 0.410 |
| 2021 | 64 | 0.440 | **0.523** | 0.312 | 0.289 |
| 2022 | 43 | **0.732** | 0.491 | 0.580 | 0.539 |
| 2023 | 67 | **0.604** | 0.580 | 0.597 | 0.690 |
| 2024 | 61 | **0.482** | 0.374 | 0.231 | 0.252 |

Season-block bootstrap, 4,000 reps, paired differences. **Seasons are the resampling unit, not
players** — the same ~200 receivers recur every year, and resampling players would shrink every
interval by roughly the square root of that autocorrelation.

| comparison | mean Δρ | 95% CI | verdict |
|---|---|---|---|
| **model − B1 consensus ADP** | **+0.048** | **[−0.013, +0.124]** | **does not clear 0** |
| model − B2 prior-season points | +0.128 | [+0.072, +0.186] | clears 0 |
| model − B3 weighted prior PPG | +0.091 | [+0.013, +0.163] | clears 0 |
| *B1 ADP − B3 heuristic* | *+0.043* | *[−0.035, +0.124]* | *does not clear 0* |

**Read the last row before reading the first.** With seven seasons, **consensus ADP itself cannot be
shown to beat a weighted average of prior points per game.** The test has so little power that
"beats consensus" is not reachable from this data at any effect size the model plausibly has. This is
the constraint the brief anticipated and it is worse than it looks: it is not that the model failed,
it is that **the experiment cannot resolve the question**. Any future "beats consensus" claim from
seven seasons should be read the same way.

On the full pre-season universe (11 seasons, no ADP available for four of them): model − B2 =
**+0.139 [+0.116, +0.161]**, model − B3 = **+0.239 [+0.218, +0.262]**. Much tighter intervals, and
**they are not comparable to the ADP figures** — this universe includes the ~25% who play zero games,
where the availability model does most of its work.

### 5.1 Decision-relevant, not list-relevant

`CLAUDE.md` §6.6 is right that rank correlation is a proxy. What the top 24 actually scored:

| | model − ADP | 95% CI |
|---|---|---|
| share of the true top 24 captured | +0.012 | [−0.048, +0.071] |
| mean actual points of the drafted top 24 | +0.79 pts | [−7.3, +8.4] |

**Nothing. Both intervals are wide open.** The rho advantage does not survive translation into the
metric that matters.

### 5.2 Where the model disagrees with the market, is it right?

ADP-board WRs, 2018-2024, bucketed by size of disagreement:

| disagreement (ranks) | n | model mean rank error | ADP mean rank error | model closer |
|---|---|---|---|---|
| 0-3 | 103 | 10.6 | 10.5 | 39.8% |
| 4-6 | 64 | 11.4 | 11.8 | 51.6% |
| 7-10 | 68 | 10.0 | 9.0 | 42.6% |
| 11-20 | 107 | 13.6 | 14.8 | 53.3% |
| **21+** | **49** | **15.9** | **18.6** | **51.0%** |

**The model is right about as often as a coin flip wherever it disagrees.** Where it gains, it gains
by having a smaller mean error in the large-disagreement bucket — it avoids the market's worst
misses rather than making better calls. That is a real but much weaker claim than "our model knows
something", and it is the honest description of the +0.048.

---

## 6. The stacking bonuses — the part that was supposed to be the edge

### 6.1 It is modelled correctly and it is worth almost nothing

A threshold bonus cannot be recovered from a season total, so the model carries a per-game
distribution: `logit P(game ≥ t) = a_t + b_t·log(1 + yards per game)`, a binomial GLM fitted on
training seasons only, evaluated at each of 100/150/200 and summed with the stacking weights
1.0/1.5/2.0. The measured empirical curve it is fitting:

| mean yds/game | 11 | 25 | 35 | 45 | 55 | 65 | 74 | 92 |
|---|---|---|---|---|---|---|---|---|
| P(≥100 in a game) | 0.001 | 0.010 | 0.027 | 0.064 | 0.104 | 0.180 | 0.232 | **0.407** |
| P(≥150) | 0.000 | 0.000 | 0.001 | 0.005 | 0.009 | 0.023 | 0.046 | **0.124** |
| P(≥200) | 0.000 | 0.000 | 0.000 | 0.001 | 0.000 | 0.003 | 0.005 | **0.019** |

**The first cut under-predicted league-wide bonus points by 10-50% every season, and the reason is
worth recording.** The exceedance curve is convex over the range that matters, so evaluating it at a
*shrunk* point estimate of yards per game is not the expectation under the projection's own
uncertainty — `E[bonus] ≠ bonus(E[yards])`. Fitting the curve on **out-of-sample projections for the
training seasons** instead of on realised yards absorbs the shrinkage, because the training inputs
are compressed the same way the live inputs will be. Calibration ratio went from 0.5-1.0 (mean 0.79)
to **mean 0.99, sd 0.20**.

**And then it moves nobody.**

| season | mean rank shift from adding the bonus | max | WRs moved ≥3 | bonus as share of projected points |
|---|---|---|---|---|
| 2018 | 0.11 | 2 | 0 | 1.3% |
| 2021 | 0.20 | 3 | 1 | 1.6% |
| 2024 | 0.12 | 2 | 0 | 1.5% |

**Across 2,271 player-seasons the stacking bonus moved five receivers by three or more rank
positions, and never moved anyone by more than five positions.** The founder's project notes asked
how many players the ceiling adjustment moves. **The answer is five, out of 2,271.**

### 6.2 The oracle bound — how much a *perfect* ceiling model could ever buy

Substitute each player's **realised** bonus points for the projected ones. This is not a model, it is
perfect foresight of the entire channel:

| | Δρ vs no bonus at all | 95% CI |
|---|---|---|
| modelled bonus, full universe | +0.0002 | [−0.0000, +0.0005] |
| **oracle bonus, full universe** | **+0.0079** | [+0.0063, +0.0095] |
| modelled bonus, ADP board | −0.0007 | [−0.0018, +0.0004] |
| **oracle bonus, ADP board** | **+0.0257** | [+0.0177, +0.0332] |

**+0.026 rank correlation is the ceiling on everything.** Perfect knowledge of who scores bonus
points is worth about half the model's own (statistically unproven) advantage over consensus. Any
future ceiling-pricing proposal at WR has to fit inside that number, and it will not, because —

### 6.3 There is no signal there to find

If two receivers with the same mean yards per game differed in how often they spike, the residual
around the exceedance curve would show variance in excess of binomial noise. 1,360 WR player-seasons
with ≥8 games, weighted by games:

| | |
|---|---|
| observed variance of the 100-yard-game rate around the ypg curve | **0.00302** |
| variance implied by binomial sampling noise alone | **0.00478** |
| **excess = real between-player spike ability** | **−0.00176** |

**Negative.** Receivers vary *less* around the curve than independent coin flips would — consistent
with the curve absorbing everything and the binomial estimate being mildly conservative inside wide
ypg bins. And the residual does not persist: **r = −0.006, 95% CI [−0.073, +0.060]**, n = 870
consecutive-season pairs.

**One trap, recorded because I nearly reported it as a finding.** The partial correlation of
bonus-points-per-game on its own lag, controlling for *prior-season* yards per game, is +0.156
[+0.091, +0.221] — significant, and it looks like persistent spike ability. It is not. Controlling
for prior ypg is not controlling for *current* ypg; prior bonus rate is simply a second noisy
measurement of the player's yardage level. Controlling instead for the model's own **projected**
yards per game drops it to **+0.089 [+0.023, +0.155]**, and what remains is not spike ability — it is
**prior bonus rate carrying information about the yardage mean that the volume model failed to
capture.** That is a lead about §7's volume projection, not about ceiling. Reported as such.

---

## 7. The defect that actually costs points

The model's ten worst calls are one failure mode repeated:

| season | player | ADP rank | model rank | actual rank | projected games |
|---|---|---|---|---|---|
| 2023 | Keenan Allen | 6 | **53** | 7 | — |
| 2023 | DeAndre Hopkins | 12 | **58** | 20 | — |
| 2020 | Adam Thielen | 9 | **44** | 9 | — |
| 2018 | Josh Gordon | 16 | **45** | 31 | ~1 |
| 2020 | A.J. Green | 30 | **57** | 42 | ~1 |
| 2024 | Cooper Kupp | 15 | **49** | 33 | — |

**Every one is a receiver coming off a season lost or shortened by injury or suspension.** The
availability sub-model reads a near-zero games share in N−1 and projects a near-zero season in N.
A.J. Green's 2020 projection was **6.6 targets** — he missed all of 2019, and the model concluded he
was finished rather than that he had been absent.

The market handles this correctly and trivially, because a human knows the difference between "did
not play" and "played badly". **The model does not have the feature that distinguishes them.** The
per-game rate features already ignore missed time (a zero-game season carries zero weight), so the
error is entirely in the availability component treating one absent season as evidence of permanent
decline.

**This is the highest-value fix available and it is cheap.** The `injuries` table (79,816 rows) is in
the database and unused by any model in this project. A reason-for-absence feature, or simply a
weaker prior on a single missed season, addresses the model's largest error class directly. I would
do this before anything else — including before a second position.

---

## 8. What should be registered, and what I am not claiming

**Nothing above is confirmatory.** Opened to `strategist` as thread **094**: registration of the one
confirmatory test worth running, which is **not** "does the model beat consensus" — §5's ADP-vs-B3
row shows seven seasons cannot resolve that. It is the availability fix in §7, pre-registered as a
single-factor test with the stopping condition committed in advance, evaluated on the **sealed 2025
holdout**, which this pass never opened.

**Claims I am explicitly not making:**

- Not claiming the model beats consensus. It does not, on the evidence.
- Not claiming the ceiling channel is worth pricing at WR. It is bounded at +0.026 by oracle and
  the modelled version delivers +0.0002. **At WR that channel is closed.** RB and TE are separate
  questions — RB rushing yardage clusters differently around 100, and this result does not transfer.
- Not claiming the component projections are better than the vendor's. Sleeper/Rotowire's rows are
  2026-only and cannot be backtested; that comparison needs the 2026 projection, which needs 2025
  features, which needs the holdout unsealed under registration.
- Not claiming anything about the +0.048 that survives §5.1 and §5.2. It does not translate into
  better rosters and it is a coin flip where it disagrees.

---

## 9. Reproduction

```
.venv/bin/python -m experiments.bottomup.components.run_wr
```

`data/nfl.db` required (`scripts/rebuild_database.py`). ADP reads the committed CSVs under
`data/adp-snapshots-ffc/` directly, so the FFC backfill does **not** need to have been run against
the local database. Runtime ~90s. Every table in this document is a section of that output.
