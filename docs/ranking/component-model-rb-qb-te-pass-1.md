# Bottom-up component model — RB, QB and TE, pass 1

**Ranker, 2026-07-30.** Answers **FR-072** ("Ok for our model, let's do the other positions too,
why just WR"). Method follows `component-model-wr-pass-1.md`; design fixed in advance in
`component-model-multipos-precommit.md`, committed as `5f8efc1` **before any number below existed**.

**Exploratory.** Nothing here is confirmatory, nothing is registered, and **no result below may be
reported as an edge.** The sealed 2025 holdout was never opened. Thread 094 (`ranker` →
`strategist`) asks for the one registration worth making and has had no reply.

Code: `experiments/bottomup/components/`. Reproduce with

```
.venv/bin/python -m experiments.bottomup.components.run_position {RB|QB|TE|WR}
.venv/bin/python -m experiments.bottomup.components.run_variants
.venv/bin/python -m experiments.bottomup.components.run_availability
```

`wr_data.py` / `run_wr.py` are deliberately untouched, so pass 1 still reproduces exactly
(+0.0481 vs ADP, re-verified this session).

---

## 0. Read this before any number in this document

**Roughly 170 interval tests were run.** At the 5% level that yields **about 8.5 false "clears zero"
results by chance alone.** `CLAUDE.md` §6.3 requires this be corrected for or the results treated as
hypotheses. I have not applied a formal correction, because the tests are not independent and a
Bonferroni floor of p<0.0003 would erase real effects along with the false ones. Instead, every
result in this document is graded:

| grade | meaning |
|---|---|
| **SURVIVES** | effect is many times its own standard error; would survive any reasonable correction |
| **MARGINAL** | clears zero but a CI endpoint sits near it; **this is exactly what a false positive looks like at n=170** and it must not be quoted as a finding |
| **NULL** | does not clear zero |

**A MARGINAL result in this document is a hypothesis. It is not evidence.**

---

## 1. Conclusion first

**Six findings. Five are negative, and the negatives are the valuable ones.**

**(1) No position beats consensus ADP, and at RB that is a real null rather than an underpowered
one.** This is the headline under `CLAUDE.md` §6.5 and it is reported as a failure.

| position | model − consensus ADP | 95% CI | power check: can the design see *anything*? |
|---|---|---|---|
| WR | +0.051 | [−0.011, +0.129] | ADP − heuristic +0.043 [−0.032, +0.126] — **no power** |
| **RB** | **−0.052** | **[−0.126, +0.038]** | ADP − heuristic **+0.134 [+0.043, +0.223]** — **HAS power** |
| QB | −0.069 | [−0.255, +0.104] | ADP − heuristic +0.038 [−0.039, +0.137] — **no power** |
| TE | −0.024 | [−0.182, +0.123] | ADP − heuristic +0.058 [−0.055, +0.224] — **no power** |

**Read the right-hand column first.** At WR, QB and TE the experiment cannot resolve the question —
seven seasons cannot even show that consensus beats a three-line heuristic. **At RB it can, and
does, and our model still does not.** That makes RB the one position where "we do not beat the
market" is a measurement rather than a shrug. RB is also where this league's scarcity bites hardest.

**(2) The component projections beat naive persistence decisively at every position.** This is the
FR-072 deliverable and the one unambiguous win. All SURVIVES.

**(3) The availability defect that WR pass 1 called "the highest-value fix available" is real,
partially fixable, and worth approximately nothing.** Arm B (the injury report) fixes projected
games at WR — A.J. Green 2020 goes from **0.91 projected games to 9.09** against an actual 16 — and
**improves the ranking at no position.** My own prior recommendation does not survive contact with a
measurement. §5.

**(4) The injuries table answers the question backwards, and this is the most useful data finding
here.** It accounts for 26–35% of short absences and **2.5–4.8% of absences of nine games or more**,
because a player placed on season-ending IR drops off the weekly report entirely. The absences that
destroy a projection are precisely the ones it cannot see. §5.2 — and it names the table that can.

**(5) WR pass 1 explicitly reserved judgment on whether the ceiling null transfers to RB. I measured
it. It transfers.** The stacking bonus is worth 0.57%–2.39% of realised points and moves **three
players by three or more rank positions across 4,792 player-seasons at four positions.** §6.

**(6) The one place regime change is measurably hurting the model is the QB passing bonus**, whose
calibration drifts **+0.043 per season [+0.003, +0.084]** — right in 2014, over-predicting by 40% by
2024. Meanwhile the QB *rushing* regime, which I expected the model to lag, it tracks: the lag is
+0.176 pct-points/season [−0.105, +0.456], **NULL**. §7.

---

## 2. What was built, and why it is three models rather than one

Same shape as WR per position — component projections plus a per-game distribution, from which a
rank falls out under any ruleset. `pos_model.score_components()` re-scores an existing projection
under a different league without refitting anything.

**Each position is its own ledger. What is shared is the fitting machinery, not the model.**

| | streams | components projected | bonus families |
|---|---|---|---|
| **WR / TE** | 1 | games · targets/g · catch rate · yds/rec · TD/target · small rushing · fumbles | rec 100/150/200 |
| **RB** | 2 | the above **plus** carries/g · yds/carry · rush TD/carry | rec **and** rush 100/150/200 |
| **QB** | 2, different scoring | games · attempts/g · yds/att · TD/att · INT/att · carries/g · yds/carry · rush TD/carry | **pass 300/350/400** and rush 100/150/200 |

Expected bonus points are additive across families by linearity of expectation, so two thresholds in
the same game need no joint distribution — only two exceedance curves.

**Everything is least squares or a one-covariate binomial GLM**, with empirical-Bayes shrinkage
whose single constant is picked on training seasons only. No ML. `CLAUDE.md` §6.3.

### 2.1 The data boundary is not the same at every position — measured, not assumed

This is the constraint the project has been treating as universal, and it is not.

| position | core volume stat | coverage | consequence |
|---|---|---|---|
| **QB** | pass attempts | **1999–2024, complete** | the 2003–08 hole does **not** bind QB |
| **RB** | carries | **1999–2024, complete** | binds only the *receiving* half of RB |
| **WR / TE** | targets | 2009+ (2003–08 empty) | binds fully |

**The 2003–2008 hole is a *targets* hole.** It does not touch passing or rushing volume. QB is the
one position whose data supports a deep sample, which is why §7 tests it rather than assuming it.

### 2.2 Look-ahead and survivorship — enforced, then audited

`SeasonPanel` has no accessor returning everything. `before(cutoff)` filters and asserts;
`outcomes(season)` is separate so reading a target season must be written on purpose. Injury and
depth-chart reads go through their own gated accessors. Every read appends to an access log and the
walk-forward **asserts after every fit** that the maximum feature cutoff and outcome season are
strictly below target and that zero outcome reads occurred at target. **The memoisation added for
speed replays its access-log entries**, so a cache hit is audited identically to a cold read — a
cache that silently suppressed audit entries would have quietly disabled the only check that makes
this harness trustworthy. All four positions PASS.

Universe frozen before the season; busts retained and scoring zero:

| position | universe/season | **played 0 games** | on ADP board |
|---|---|---|---|
| RB | 122–137 | **21–39** (336 of 1441) | 38–64 |
| QB | 68–91 | **12–24** (214 of 869) | 14–24 |
| TE | 84–100 | **14–25** (219 of 1041) | 11–19 |

### 2.3 Power at QB and TE is bad, and it was said in advance

The FFC board carries **14–24 QBs and 11–19 TEs** per season against 43–67 WRs. A Spearman on twelve
players has a standard error around 0.33. **The QB and TE ADP comparisons are close to
uninformative and no reading of them should survive that fact.** This was stated in the
pre-commitment before the numbers existed, precisely so it could not be discovered afterwards and
presented as a caveat.

---

## 3. The headline, measured against all three required baselines

Universe: the season's ADP-board players at that position, so the comparison is on the market's own
universe. Metric: Spearman with realised points under this league's scoring, bonuses stacked.
Season-block bootstrap, 4,000 reps, **seasons as the resampling unit** — the same players recur
every year and resampling players would shrink every interval by roughly the square root of that
autocorrelation.

| season | RB model | RB ADP | QB model | QB ADP | TE model | TE ADP |
|---|---|---|---|---|---|---|
| 2018 | 0.475 | **0.548** | −0.084 | **0.391** | 0.413 | **0.641** |
| 2019 | 0.551 | **0.759** | **0.395** | 0.157 | 0.427 | **0.582** |
| 2020 | 0.437 | **0.574** | 0.296 | **0.417** | **0.365** | 0.074 |
| 2021 | 0.649 | **0.711** | 0.258 | **0.619** | **0.405** | 0.354 |
| 2022 | 0.386 | **0.413** | **0.415** | 0.332 | **0.350** | 0.203 |
| 2023 | **0.418** | 0.245 | 0.109 | 0.110 | **0.330** | 0.261 |
| 2024 | 0.448 | **0.480** | **0.460** | 0.305 | 0.311 | **0.657** |

Against the naive baselines the model does win, clearly, on the full pre-season universe:

| | RB | QB | TE | WR |
|---|---|---|---|---|
| model − B2 prior-season points | +0.145 [+0.116, +0.174] | +0.090 [+0.060, +0.122] | +0.106 [+0.079, +0.131] | +0.139 [+0.116, +0.162] |
| model − B3 weighted prior PPG | +0.269 [+0.229, +0.305] | +0.130 [+0.100, +0.160] | +0.216 [+0.172, +0.264] | +0.240 [+0.219, +0.262] |

All **SURVIVES**. **These are not comparable to the ADP figures** — this universe includes the
15–30% who play zero games, where the availability model does most of its work.

### 3.1 Decision-relevant, not list-relevant (`CLAUDE.md` §6.6)

k sized to what this league actually starts at each position, flex-adjusted.

| | model − ADP, top-k capture | model − ADP, mean actual points of drafted top-k |
|---|---|---|
| RB (k=20) | −0.029 [−0.071, +0.021] | −5.3 pts [−15.0, +5.9] |
| QB (k=10) | −0.043 [−0.114, +0.043] | −15.3 pts [−34.7, +3.2] |
| TE (k=10) | −0.000 [−0.057, +0.071] | −1.4 pts [−5.9, +3.1] |
| WR (k=30) | +0.038 [+0.000, +0.076] | +3.1 pts [−0.1, +6.2] |

**Every interval is open. Nothing here translates into better rosters at any position.**

---

## 4. The components — the actual deliverable, and the one clean win

MAE against naive persistence (last season's own total, the honest zero-work baseline for a
component projection). Negative = model better. **All SURVIVES.**

| RB | | QB | | TE | |
|---|---|---|---|---|---|
| games | −0.77 [−0.91, −0.63] | games | −0.33 [−0.51, −0.16] | games | −0.52 [−0.69, −0.35] |
| carries | −8.10 [−10.37, −5.97] | attempts | −12.60 [−18.48, −7.13] | targets | −2.37 [−3.17, −1.54] |
| rush yards | −35.06 [−45.89, −24.05] | pass yards | −63.73 [−99.64, −27.81] | receptions | −1.51 [−2.07, −0.95] |
| rush TDs | −0.31 [−0.42, −0.20] | pass TDs | −0.41 [−0.55, −0.27] | rec yards | −17.86 [−24.72, −10.86] |
| targets | −2.35 [−2.88, −1.84] | INTs | −0.79 [−1.03, −0.57] | rec TDs | −0.28 [−0.34, −0.21] |
| rec yards | −16.12 [−20.30, −12.11] | rush yards | −9.40 [−14.15, −4.46] | | |

**The projections are real. What is not demonstrated is that they order players better than the
market.** Those are different claims and only the first one is established.

---

## 5. The availability defect — tested at every position, and it does not pay

WR pass 1 §7 diagnosed the model's largest error class and called fixing it "likely worth more than
any feature you could add." **That recommendation was mine and it does not survive measurement.**

Five arms, one factor apart, four positions. A/B/C pre-committed; **D/E post-hoc** (added after A–C
ran, because measuring B produced §5.2's data finding) and reported at a lower evidential standard.

| arm | availability features | data source |
|---|---|---|
| A | `gshare_w`, `gshare_1`, `present_1`, `age`, `age²`, `evidence` | — |
| B | A + weeks missed carrying an `Out`/`Doubtful` report, and weeks missed carrying none | `injuries` |
| C | A + `gshare_max3` | **none — free control** |
| D | A + weeks rostered-but-absent, weeks off-roster | `depth_charts_weekly` |
| E | D + share of N−1 spent first on the depth chart | `depth_charts_weekly` |

**Arm C exists because I declared it in advance.** Without a free control, any arm-B win would have
been unattributable — "the injuries table helps" and "a one-line memory of having been healthy
helps" produce the same number.

### 5.1 It fixes what it targets, at one position, and moves nothing

MAE on projected games, the returning-from-absent class (played ≤35% of N−1):

| | RB | QB | TE | **WR** |
|---|---|---|---|---|
| **B − A** | −0.054 [−0.146, +0.037] NULL | −0.004 NULL | +0.049 NULL | **−0.150 [−0.254, −0.068] SURVIVES** |
| **C − A** (free) | +0.012 NULL | +0.022 NULL | −0.055 [−0.095, −0.014] MARGINAL | +0.008 NULL |
| **D − A** | +0.022 NULL | +0.050 [+0.012, +0.102] **worse**, MARGINAL | +0.130 NULL | +0.018 [+0.003, +0.035] **worse**, MARGINAL |

**At WR the injury report does something real that the free control does not.** The named cases,
projected games against actual:

| player | season | actual | A | **B** | C | D | E |
|---|---|---|---|---|---|---|---|
| A.J. Green | 2020 | 16 | 0.91 | **9.09** | 0.32 | 0.82 | 1.48 |
| Deebo Samuel | 2021 | 16 | 7.66 | **11.27** | 7.27 | 7.68 | 8.37 |
| Davante Adams | 2020 | 14 | 9.72 | **11.47** | 9.75 | 9.71 | 10.60 |
| Keenan Allen | 2023 | 13 | 7.09 | **9.62** | 7.06 | 6.89 | 8.10 |
| Adam Thielen | 2020 | 15 | 8.00 | **9.68** | 7.95 | 7.97 | 8.60 |
| **Patrick Mahomes** | 2018 | 16 | 0.21 | 0.12 | 0.64 | 0.12 | 0.72 |
| **Dak Prescott** | 2021 | 16 | 7.42 | 6.90 | 7.58 | 8.15 | 8.27 |
| **DeAndre Hopkins** | 2023 | 17 | 5.55 | 5.53 | 4.96 | 5.70 | 6.04 |

**And now the ranking effect, which is the only thing that matters:**

| arm − A, ADP-board ρ | RB | QB | TE | WR |
|---|---|---|---|---|
| **B (injury)** | −0.008 MARGINAL | +0.005 NULL | **−0.028 [−0.057, −0.001] worse, MARGINAL** | −0.007 NULL |
| C (free) | −0.007 MARGINAL | +0.014 NULL | +0.004 NULL | −0.001 NULL |
| D (roster) | +0.001 NULL | +0.008 MARGINAL | +0.014 NULL | +0.000 NULL |

**Not one arm improves the ranking at any position, and the only sign-consistent effects are
negative.** The fix improves projected games for ~39 WRs a season by 0.15 games of MAE. That is far
too small to reorder a 200-player list. **The 79,816 unread injury rows were worth reading, and the
answer they returned is "not this."**

### 5.2 Why — and this is the finding worth keeping

**Share of missed weeks each source actually accounts for:**

| missed games | injury report | depth chart |
|---|---|---|
| 1–3 | 26–35% | **93–97%** |
| 4–8 | 15–22% | **74–87%** |
| **9 or more** | **2.5–4.8%** | **35–81%** |

**The injury report is inverted relative to need.** A player on season-ending IR drops off the weekly
report. Verified by hand, not inferred: **Dak Prescott has zero injury rows for 2020** (ankle,
Week 5, season over). Deshaun Watson has two for 2017 with zero `Out` (ACL, season over). J.K.
Dobbins and Michael Thomas have none for 2021; both missed the entire year.

**And the depth chart, despite ten times the coverage, fails too** — it marks an IR player as
*off-roster*, which is the opposite of the truth. Michael Thomas 2022 and J.K. Dobbins 2022 both
carry `offroster = 1.00` going into seasons in which they played 3 and 8 games.

**The real result is that "returning from absence" is not one failure class. It is three, with three
different sources, and only one of them is an injury problem:**

| class | example | fixable from `nfl.db`? |
|---|---|---|
| multi-week in-season injury | Keenan Allen 2023 | **yes** — arm B. Worth ~0 in rank terms. |
| season-ending IR | Dak Prescott 2021 | **no** — injury report blind, depth chart actively wrong |
| offseason role change | **Mahomes 2018: 0.21 projected games, played 16, finished QB1** | **no** — nothing pre-season encodes it |

Mahomes is the one that should be uncomfortable. **Every arm projects him at under one game.** He
was QB2 behind Alex Smith at the end of 2017; Smith was traded that January. The market knew — ADP
had him QB7. A model that refuses to read ADP in order to stay independent of it is *structurally*
blind to offseason role change, and that blindness is not a bug to be fixed with a feature.

**Data commissioned, not designed around** (thread opened to `data-ops`): `nflreadpy`'s
`load_rosters_weekly()` carries `status` ∈ {ACT, **RES** (injured reserve), INA, PUP, DEV, CUT,
**RSN/SUS** (suspended), RET}, is free, and goes back to at least 2002. **It is not in `nfl.db`.**
Verified: Michael Thomas 2021 shows `RES` × 17 weeks where `injuries` has zero rows. It is the only
source found that marks season-ending IR *and* suspension — the two things arm B provably cannot
see. Whether it then buys any *ranking* is a separate question and §5.1 is not encouraging.

---

## 6. The stacking bonus — the WR null transfers, and RB was the open case

WR pass 1 said: *"RB and TE are separate questions — RB rushing yardage clusters differently around
100, and this result does not transfer."* **I measured it. It transfers.**

| | share of realised points | dominant family | oracle ceiling, ADP board | players moved ≥3 ranks |
|---|---|---|---|---|
| WR | 1.5% | rec 100% | +0.026 [+0.018, +0.033] | 5 of 2,271 |
| **RB** | **1.27%** | **rush 95.5%** | **+0.027 [+0.017, +0.037]** | **2 of 1,441** |
| **QB** | **2.39%** | **pass 98.1%** | **+0.043 [+0.019, +0.068]** | **1 of 869** |
| **TE** | **0.57%** | rec 99.3% | +0.030 [+0.005, +0.063] | **0 of 1,041** |

**Across 4,792 player-seasons at four positions the stacking bonus moved three players by three or
more rank positions, and never moved anyone by more than three.** The oracle bound — perfect
foresight of every player's realised bonus points — is +0.026 to +0.043 ρ. **Everything a ceiling
model could ever buy fits inside that, and the modelled version delivers between −0.015 and +0.001.**

QB has the highest ceiling, as expected: a 300-yard passing game is common where a 200-yard
receiving game happened 39 times in 1,360 WR player-seasons. **It is still the least useful, because
the modelled QB bonus is the only one that makes the ranking measurably worse** (−0.015 [−0.039,
−0.000] on the ADP board), for the reason in §7.

### 6.1 There is nothing left to model — except possibly at QB, where it is worthless

Variance decomposition: if two players with the same mean yards per game differed in how often they
spike, the residual around the exceedance curve would exceed binomial noise.

| | n | observed | binomial | **excess** | YoY persistence of the residual |
|---|---|---|---|---|---|
| WR rec ≥100 | 1,360 | 0.00414 | 0.00486 | **−0.00072** | +0.067 [+0.001, +0.134] MARGINAL |
| RB rush ≥100 | 842 | 0.00468 | 0.00462 | **+0.00006** | +0.073 [−0.013, +0.158] NULL |
| TE rec ≥100 | 659 | 0.00191 | 0.00174 | **+0.00017** | +0.122 [+0.029, +0.216] MARGINAL |
| QB pass ≥300 | 362 | 0.00662 | 0.01089 | **−0.00427** | −0.048 NULL |
| **QB rush ≥100** | 362 | 0.00073 | 0.00047 | **+0.00025** | **+0.252 [+0.134, +0.371] SURVIVES** |

**One real positive in five, and it is economically worthless.** QB 100-yard rushing games show
genuine, persistent between-player variation beyond the mean — but there were **37 such games in
362 player-seasons**, worth 43 of the 2,217 QB bonus points in the sample, **1.9%**. It is a real
effect on a quantity too small to matter. Reported because a detectable-but-worthless effect is
exactly the kind of thing that gets promoted into a model if nobody writes down its size.

**The ceiling/variance channel is now closed at all four positions**, on a bound rather than a
failure to find something. The founder's belief that this league pays for ceiling is correct about
the *scoring rules* and wrong about the *exploitable consequence*: the bonus is earned by exactly
the players a mean-based projection already ranks first.

---

## 7. Position-specific: the secondary variants, and the QB regime

Declared in the pre-commitment. **Reported, never selected on.** Promoting one because it won here
would be selection on the outcome.

| | secondary − primary, full universe | ADP board | verdict |
|---|---|---|---|
| **RB** opportunity-share | **+0.0085 [+0.0032, +0.0137]** MARGINAL | −0.001 NULL | carries MAE −0.43 [−0.90, −0.02], rush TD MAE −0.017; rec yards MAE **+0.78 worse**. The reparameterisation genuinely improves the rushing stream and costs the receiving one. Primary stands. |
| **QB** deep 2002+ sample | +0.0040 NULL | +0.018 NULL | **component MAE is clearly worse**: attempts +2.59 [+0.67, +4.83], pass yards +18.9 [+4.6, +34.4], games +0.06 [+0.01, +0.11]. |
| **TE** WR-pooled rates | +0.0007 NULL | +0.0007 NULL | **nothing.** |

**The QB result answers `CLAUDE.md` §6.4 with a measurement.** QB is the one position whose data
supports a deep sample, and using it **degrades the projections**. Older QB seasons are not merely
less relevant, they are actively misleading — which is what §6.4 asserts and nothing in this project
had previously tested.

**The TE result resolves the tension the brief set up.** TE has ~40% of WR's sample at universe
level and ~30% at the decision-relevant level, and pass 1 measured it as where the market is most
wrong. Those pull opposite ways. **Pooling in 2.4× more rows changes the answer by +0.0007.** So the
sample size is not the binding constraint at TE, and the "smallest sample" half of the tension is a
non-issue: what limits TE is that only 11–19 of them are drafted, which no amount of pooled training
data fixes. **I did not average the two concerns or pick one — I measured which one binds.**

### 7.1 QB regime — the model tracks rushing and is losing the passing bonus

I expected the model to lag the QB rushing trend. **It does not, and I am reporting that against my
own prior.**

| | slope, 2014–2024 | 95% CI |
|---|---|---|
| **actual** rushing share of QB points | **+0.755 pct-pt/season** | [+0.583, +0.926] |
| **projected** rushing share | +0.579 pct-pt/season | [+0.381, +0.777] |
| **lag (actual − projected)** | +0.176 pct-pt/season | **[−0.105, +0.456] NULL** |

QB rushing went from 11.5% to 18.3% of QB fantasy points, a 59% relative rise, and **the model's
tracking error is indistinguishable from zero.** The brief warned not to inherit the collapsed-slope
story as established. On this measurement it is not established here either — and this is a
different quantity from the rank-curve slope, so it neither confirms nor refutes that separate claim.

**Where regime change *is* biting is the passing bonus:**

| | slope | 95% CI |
|---|---|---|
| **QB bonus calibration ratio** (1.0 = correct) | **+0.043/season** | **[+0.003, +0.084] MARGINAL** |
| realised QB bonus points, league-wide | −6.65/season | [−13.83, +0.52] NULL |
| RB / WR / TE calibration ratio | +0.012 / −0.003 / +0.047 | all NULL |

The QB bonus model was right in 2014 (ratio 0.96) and over-predicts by **40% in 2024** (ratio 1.40).
300-yard passing games are disappearing and a model trained on pooled seasons keeps expecting the
old rate. **This is the single place in this work where the recency weighting `CLAUDE.md` §6.4 asks
for has a demonstrated, measured need** — and it is MARGINAL, one of four such tests, so it is a
hypothesis worth registering rather than a finding worth acting on.

---

## 8. What I am not claiming

- **Not claiming any position beats consensus.** None does. At RB the design has power and the
  answer is still no.
- **Not claiming the availability fix is worth building.** I proposed it in WR pass 1; I measured it
  here; it does not move the ranking anywhere. **Withdrawn.**
- **Not claiming the depth-chart arms are a finding.** They are post-hoc, they mostly fail, and
  where they clear zero they are MARGINAL among ~170 tests.
- **Not claiming the ceiling channel is worth pricing anywhere.** Bounded at +0.043 by oracle at its
  best; three players moved out of 4,792.
- **Not claiming the RB opportunity-share parameterisation is better.** It is a pre-declared
  secondary and it stays one.
- **Not claiming this is ready to ship.** FR-072's ruling ("don't show our rankings in the app until
  we can do it for all players") is now satisfied on *coverage* at four offensive positions. It is
  not satisfied on *quality*, and this league also starts 1 DEF, which nothing in this project
  models. **Whether it ships is not my call to make about my own model.**

## 9. What should happen next, in order

1. **`strategist` should redirect thread 094.** It asks for the availability factor to be registered
   as the confirmatory test. §5 measures that factor and it is null on ranking at all four
   positions. Spending the sealed 2025 holdout on it would waste it. Replied on that thread.
2. **`data-ops` should ingest `load_rosters_weekly()`.** §5.2. Thread opened. This is a genuine gap,
   the only source found that marks IR and suspension, and it is free.
3. **The QB passing-bonus recency weighting** is the one factor with a measured need (§7.1). It
   needs registering before it is run, not after.
4. **Not more ceiling work, at any position.** §6 closes it on a bound.
