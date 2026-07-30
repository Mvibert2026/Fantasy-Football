# FR-086 — week-to-week volatility, ranked by position and player type

**Ranker, 2026-07-30.** Founder's words:

> *"Do WR's have more or less week to week volatility than other players, can you rank player types
> by volatility (it may help identify where to look for high volatility players or pair them for
> roster builds) — That probably should be part of the player archetype/description profile"*

and, later in the same session:

> *"volatility matters for archetype and I'd like to know also which positions tend to be more
> volatile in general, for my knowledge"*
>
> *"why not use points for volatility, you have an average, and the curve has a shape with tails
> that should naturally figure this out for you"*

**Exploratory. Nothing registered, nothing confirmatory. The sealed 2025 holdout is excluded in code
(`load_player_seasons` raises at ≥2025), not by convention.**

Code: `experiments/volatility/`. Reproduce with

```
.venv/bin/python -m experiments.volatility.volatility
.venv/bin/python -m experiments.volatility.exceedance_dispersion   # 2nd moment
.venv/bin/python -m experiments.volatility.exceedance_shape        # 3rd + 4th moments
.venv/bin/python -m experiments.volatility.dimension_stability
```

---

## 0. Read this before any number below

**348 interval tests across this document** (94 volatility, 55 exceedance-dispersion, 126
exceedance-shape, 73 dimension stability). At the 5% level that is **about 17 false "clears zero"
results by chance alone.** Grades are pass-1 §0's, unchanged: **SURVIVES** / **MARGINAL** (a
hypothesis, not evidence) / **NULL**.

---

## 1. The plain answer to "which positions are more volatile" — and it inverts

**Per player, WR is the most volatile position and QB is far and away the least. Per roster slot in
*this* league, that ordering reverses and TE is the most volatile thing you can start.**

8,703 player-seasons with ≥8 games, 1999–2024, scored under this league's rules with bonuses stacked.

### 1.1 Per player

| position | n | PPG | SD | **CV** | CV incl. missed weeks | skew | weeks ≥20 pts | weeks ≤5 pts |
|---|---|---|---|---|---|---|---|---|
| **WR** | 3,653 | 6.63 | 5.02 | **1.084** | 1.376 | +0.79 | 5.8% | 53.4% |
| **RB** | 2,409 | 7.38 | 5.24 | **1.047** | 1.351 | +0.81 | 8.4% | 51.3% |
| **TE** | 1,754 | 4.59 | 3.80 | **1.002** | 1.341 | +0.88 | 2.0% | 66.8% |
| **QB** | 887 | 14.52 | 7.42 | **0.573** | 0.840 | +0.21 | 24.8% | 14.5% |

**CV is the decision-relevant column, not SD.** A QB has the *highest* raw standard deviation (7.42)
of any position and the *lowest* volatility of any position. Ranking on SD would be arithmetic — QBs
score twice as much, so they vary twice as much — and would say the exact opposite of the truth.

Pairwise, season-clustered bootstrap:

| | difference in CV | 95% CI | grade |
|---|---|---|---|
| QB − RB | **−0.474** | [−0.557, −0.413] | SURVIVES |
| QB − WR | **−0.511** | [−0.594, −0.453] | SURVIVES |
| QB − TE | **−0.429** | [−0.460, −0.398] | SURVIVES |
| RB − WR | −0.037 | [−0.149, +0.075] | **NULL** |
| RB − TE | +0.045 | [−0.030, +0.139] | **NULL** |
| WR − TE | +0.082 | [+0.024, +0.162] | MARGINAL |

**So the direct answer to the founder's question is: WRs are not meaningfully more volatile than
running backs or tight ends. RB vs WR is a clean null.** The only robust position-level statement in
the whole table is that **QB is roughly 45% less volatile than every skill position**, which every
one of the three comparisons supports at SURVIVES. Two-thirds of QB weeks clear 10 points; two-thirds
of TE weeks fail to clear five.

*Second column note:* "CV including missed weeks" scores every week of the season, absences and byes
as zero. It is the higher number everywhere because absence is itself variance. It is the right
column for "what will my lineup actually experience"; the first is the right column for "what is this
player like."

### 1.2 Per roster slot — and this is the number that should change a decision

Per-player volatility is not what a lineup experiences. This league starts **1 QB / 2 RB / 3 WR / 1
TE / 2 FLEX**. A position filling several slots has its spikes and busts partly cancel *inside* the
lineup; a position filling one slot passes its full variance straight through to the weekly score.

Effective slots use ADR-029's **measured** flex split (RB 0.52 / WR 0.48 / TE 0.00, over 26 seasons
under this league's own rules) — not an assumption. Under independence a position contributes k·μ with
SD √k·σ, so CV per slot group = CV per player ÷ √k.

| position | CV per player | effective slots | **CV per slot group** | measured same-position weekly correlation |
|---|---|---|---|---|
| **TE** | 1.002 | **1.00** | **1.002** | +0.004 |
| RB | 1.047 | 3.04 | 0.600 | +0.001 |
| QB | 0.573 | 1.00 | 0.573 | +0.009 |
| **WR** | 1.084 | **3.96** | **0.545** | +0.008 |

**The ranking completely inverts.** WR — the most volatile player type — is the *least* volatile slot
group in this roster shape, because you start four of them. TE — the mildest of the three skill
positions per player — is **the single most volatile thing on the roster**, by 67% over the next
worst, because there is exactly one of it and no flex relief (ADR-029 measured a TE winning a flex
slot in 2 of 26 seasons).

**The independence assumption is measured, not assumed.** Mean pairwise weekly correlation between
same-position players is +0.001 to +0.009 across the top 36 scorers per position-season over the last
ten seasons. That is zero to three decimal places, so the √k diversification is valid rather than
convenient.

**This is the league-specific part of the answer and it was not visible before.** "TE is a volatile
position" and "the TE slot is where your weekly score is most exposed" are different statements, and
only the second one is actionable.

### 1.3 Does variance help or hurt under this league's playoff structure? Neither

`CLAUDE.md` §7 says a slow start is unusually costly (4 teams, weeks 16–17, no reseeding). The
natural hypothesis is that variance hurts you getting in and helps you once in. **Measured, and it is
flat both ways.**

Nine teams at (μ, σ), one at (μ, k·σ) — **identical expected points** — through this league's exact
structure: round-robin weeks 1–15, top 4 by record with points breaking ties, 1v4 and 2v3 in week 16,
final in week 17. 60,000 seasons per cell. Pure structure, no player data, so nothing can leak.

| your SD, as a multiple of the league's | P(make playoffs) | P(win title) | P(title \| made playoffs) |
|---|---|---|---|
| 0.6× | 0.396 | 0.097 | 0.245 |
| 0.8× | 0.400 | 0.099 | 0.248 |
| 1.0× | 0.398 | 0.102 | 0.257 |
| 1.25× | 0.405 | 0.099 | 0.244 |
| 1.5× | 0.401 | 0.100 | 0.249 |
| **2.0×** | **0.408** | **0.102** | 0.249 |

**Across a 3.3× range of roster variance, title probability moves by half a percentage point and
playoff probability by one.** The "worse getting in, better once in" story is not there — both halves
are flat. At equal expected points, **team-level variance is worth approximately nothing in this
league's structure.**

Two honest limits on that. It is a *team*-level result: individual player variance diversifies away
(§1.2), so a player has to be extreme to move team SD at all. And it prices no *optionality* — a real
manager chooses whom to start, and a volatile bench player has option value that a fixed-lineup
simulation cannot see. The case for seeking variance therefore rests on start/sit optionality and on
the bonus, and the bonus is measured at under one point per season in §4.

---

## 2. Ranking player types by volatility

Volatility measured as **excess SD**: the residual of log(SD) on log(mean), fitted **within
(position, season)**. This is the right scale-free measure and CV is not: CV falls mechanically as
the mean rises, so ranking types by CV partly ranks them by how good they are. Positive excess SD =
more variable than a player at that scoring level normally is. Percentages are the same number as a
% of SD.

2009–2024 only — usage features are not real before 2009 (`experiments/bottomup/data.py`).
**Type definitions are position-specific by design**, per the founder's note that different factors
apply at different positions.

| rank | type | n | PPG | **excess SD** | 95% CI | grade | weeks ≥20 |
|---|---|---|---|---|---|---|---|
| 1 | **WR, aDOT high** | 644 | 7.93 | **+5.2%** | [+3.9, +6.4] | **SURVIVES** | 7.5% |
| 2 | RB, snap share low `[PROXY]` | 378 | 2.65 | **+5.6%** | [+4.0, +7.4] | SURVIVES | 0.6% |
| 3 | TE, snap share low `[PROXY]` | 301 | 2.41 | +4.8% | [+2.2, +7.2] | SURVIVES | 0.2% |
| 4 | WR, snap share low `[PROXY]` | 593 | 2.49 | +4.2% | [+3.3, +5.1] | SURVIVES | 0.5% |
| 5 | RB, target share low | 409 | 5.31 | +3.4% | [+1.3, +5.6] | SURVIVES | 3.2% |
| 6 | RB, receiving share **low** | 462 | 8.38 | +3.3% | [+1.8, +4.9] | SURVIVES | 9.4% |
| 7 | QB, rushing share high | 170 | 15.58 | +2.8% | [+0.8, +5.1] | MARGINAL | 29.8% |
| 8 | WR, target share low | 728 | 3.15 | +2.4% | [+0.9, +3.9] | SURVIVES | 0.7% |
| 9 | TE, aDOT high | 275 | 6.88 | +2.4% | [+0.5, +4.4] | MARGINAL | 4.8% |
| … | *(mid-tercile types cluster near zero and are mostly NULL)* | | | | | | |
| −4 | RB, receiving share high | 436 | 6.63 | −3.0% | [−5.5, −0.8] | MARGINAL | 5.8% |
| −3 | TE, aDOT low | 298 | 4.80 | −4.0% | [−6.0, −2.1] | SURVIVES | 1.5% |
| −2 | TE, target share high | 351 | 8.49 | −4.6% | [−5.9, −3.4] | SURVIVES | 6.3% |
| −1 | **WR, aDOT low** | 665 | 7.06 | **−5.1%** | [−6.8, −3.7] | SURVIVES | 5.0% |
| −0 | **RB, target share high** | 388 | 12.66 | **−6.4%** | [−8.1, −5.2] | SURVIVES | 18.3% |

**Three things worth pulling out.**

**Type separates volatility more reliably than position does.** Among RB/WR/TE the position-level CV
differences are NULL (§1.1); the aDOT and target-share terciles inside those positions separate by
10–11% of SD at SURVIVES. If you want to know how variable a player is, "he is a deep-target
receiver" tells you more than "he is a receiver".

**The single largest, most robust axis is target and snap share, and it runs the intuitive way:**
high-volume role → low excess volatility. RB target-share high is −6.4%, RB target-share low +3.4%,
a 9.8-point spread; the same pattern holds at WR and TE. This is the workload story, and it is the
most persistent axis in §5 as well.

**aDOT runs the other way and is genuinely independent of workload.** Deep receivers are more
volatile than their scoring level implies (+5.2% at WR, +2.4% at TE), and the low-aDOT terciles are
symmetric on the other side (−5.1%, −4.0%). This is the closest thing here to "where to look for
high-variance players" — **the deep-target receiver is the archetype**, and it is a *skill/usage*
property rather than a volume one.

**Snap share is labelled `[PROXY]` everywhere.** `CLAUDE.md` §5 says route data is not in nflverse
and anything using it is a proxy that must be flagged. `snap_counts` (2013+) gives offensive snap
share; a blocking TE and a route-running TE are the same row. It is not route participation and its
strong showing here should be read as a workload proxy, not as the route metric the spec asks for.

---

## 3. The founder's mechanism question — and it is the most important result here

> *"why not use points for volatility, you have an average, and the curve has a shape with tails that
> should naturally figure this out for you"*
>
> and, on being told the first test measured dispersion: **"for curve I was talking about skewness
> and kurtosis"**

**The correction is real and it landed after the first test was run.** "The curve has a shape with
tails" was relayed to me as *dispersion*; I tested the **second** moment and returned a decisive
null. He meant the **third and fourth**. That is a genuinely different covariate — two players can
share a mean *and* a standard deviation while one is symmetric and the other carries a long right
tail, and a threshold bonus is paid on the upper tail, which SD cannot see. §3.2 is the dispersion
test as originally run. **§3.4 is the test he actually asked for**, and it is the one that matters.

He is describing the exceedance-curve machinery in the component model, and he is right that it is
the correct mechanism. **The problem is that it currently cannot do what he assumes it does.**
`experiments/bottomup/components/pos_model.py:300`:

```python
def _bonus_design(ypg):
    return np.column_stack([np.ones(len(ypg)), np.log1p(np.clip(ypg, 0, None))])
```

**P(a game clears the threshold) is a function of MEAN yards per game and nothing else.** Two players
at 60 yards a game get identical bonus expectations whether their weekly lines are 60/60/60 or
20/20/140. The tail shape is *inferred from the average*, never measured per player. Same in
`wr_model.py:281`.

So: does a player's own measured dispersion improve that curve beyond his mean?

**This is a different question from PR-002 and from pass-1 §6.1, and neither answers it.** PR-002
asked whether "spike-week player" is a persistent *category* — between-player, categorical. Pass-1
§6.1 asked whether the *residual clearance rate* persists — same idea but the instrument is a count
of threshold crossings, order ten events a season, extremely noisy. **This asks whether a player's
measured dispersion of yards, estimated from every game he played rather than from the handful that
crossed a line, predicts clearance beyond his mean.** Within-player, continuous, far lower-noise.

### 3.2 Design — the dispersion (second-moment) test

Prior-season dispersion only — using the target season's own dispersion to predict its own clearance
is circular and would look spectacular. Feature is excess log SD in season N−1, fitted within
(family, position, season), shrunk toward zero by n/(n+k) with **k = 8 games** primary and
{0, 4, 16} as a declared sweep. Walk-forward: for target season N the GLM is fitted on rows with
season < N only. 5,616 qualifying player-season-family rows 1999–2024 (PR-002's qualifying rules
reused unchanged: ≥8 games, ≥25 ypg scrimmage / ≥150 ypg passing), 3,444 with a qualifying prior
season.

**The setting is deliberately the most favourable one that exists.** Both arms are given the player's
*realised* mean ypg for the target season. In production the mean is a projection and is noisier,
which can only make an added term work harder. If dispersion does not help here it cannot help in the
shipped pipeline.

### 3.3 Result — null, and decisively so

Out-of-sample binomial log-loss per game-trial. **Negative delta = the dispersion arm is better.**
Primary shrinkage k=8:

| family | threshold | baseline | + dispersion | delta | grade |
|---|---|---|---|---|---|
| rec | ≥100 | 0.29549 | 0.29551 | +0.000020 | NULL |
| rec | ≥150 | 0.07484 | 0.07491 | +0.000072 | MARGINAL — **worse** |
| rec | ≥200 | 0.01445 | 0.01450 | +0.000047 | NULL |
| rush | ≥100 | 0.35523 | 0.35528 | +0.000051 | MARGINAL — **worse** |
| rush | ≥150 | 0.09235 | 0.09239 | +0.000036 | NULL |
| rush | ≥200 | 0.01973 | 0.01976 | +0.000035 | NULL |
| pass | ≥300 | 0.50266 | 0.50269 | +0.000032 | NULL |
| pass | ≥350 | 0.28857 | 0.28852 | −0.000057 | NULL |
| pass | ≥400 | 0.11883 | 0.11883 | −0.000002 | NULL |

And the metric that decides it — MAE of **expected bonus points** against realised bonus points, per
player-season, walk-forward:

| family | baseline MAE | + dispersion | delta | grade |
|---|---|---|---|---|
| rec | 0.8072 | 0.8093 | **+0.0021** | NULL |
| rush | 0.9679 | 0.9719 | **+0.0040** | NULL |
| pass | 1.7694 | 1.7669 | **−0.0025** | NULL |

**Not one arm improves anything, at any threshold, in any family, at any shrinkage level from k=0 to
k=16. The two results that clear zero both point the wrong way.** The bonus-point deltas are ±0.002
to ±0.004 points per player-season, on an error of 0.8 to 1.8 points, on a quantity pass-1 §6
measured at 0.57%–2.39% of realised fantasy points.

**`CLAUDE.md` §7's operational claim is dead through this channel, and it should be said plainly.**
The scoring rules do reward ceiling — that part is simply true and is in the rulebook. But the
exceedance curve already extracts everything the ceiling channel has to give from the mean alone.
Adding the player's own measured dispersion, in the most favourable possible setting, buys nothing.

**One thing I am flagging rather than reporting as a finding.** The fitted dispersion coefficient in
the *passing* family is +0.135 with an interval of [+0.108, +0.162] that looks like a strong
SURVIVES. **That interval is invalid and I am not standing behind it.** It bootstraps across
walk-forward target seasons whose training sets overlap almost completely, so the refits are nearly
identical and the effective sample size is close to 1, not 20. The valid instruments are the
out-of-sample metrics above, and those are NULL. A result that looks too good is usually a defect in
how it was measured — this one is.

**Consistency with what was already known.** This does not contradict PR-002 (0 of 36 correlations
survived BH) or pass-1 §6.1 (excess clearance ≈ 0 at WR rec, RB rush, TE rec). It is the third and
lowest-noise instrument to return the same answer, which is worth more than any one of them alone.

### 3.4 Skewness and kurtosis — the test the founder actually asked for

Code: `experiments/volatility/exceedance_shape.py`. Raw:
`data/qa/fr086-exceedance-shape-2026-07-30.json`.

**The prior for this was better than for the dispersion test, and the coordinator was right to say
so.** If the mean fully determined the exceedance curve, dispersion would have been redundant —
which is exactly what §3.3 measured. But right skew puts mass above a high threshold that a
symmetric distribution with identical mean and SD does not. Skew is the moment that could still
carry information the mean does not already contain, and the **top threshold** in each family (200
rushing/receiving, 400 passing) is where it should show up first, because that is where shape
matters more than centre.

**Estimators, named.** Primary is **G1/G2, the adjusted Fisher–Pearson coefficients** (the
bias-corrected forms; `scipy.stats.skew/kurtosis(bias=False)`, SAS/Excel `SKEW`/`KURT`), with
**excess kurtosis on the Fisher convention — Gaussian = 0, not 3**. At n ≈ 17 the bias in the
sample coefficients g1/g2 is not negligible *and scales with n*, which would make the covariate
partly a games-played proxy. g1/g2 run as a declared sensitivity and both are reported.

**Shrinkage, derived rather than chosen.** Two steps. First residualise each moment against
log(mean ypg) within (family, position, season) — yardage is bounded below by zero, so a low-volume
player is right-skewed almost mechanically, and without this the covariate would re-encode the mean
that is already in the design. Then **empirical-Bayes shrink toward zero** with
`w = τ²/(τ² + v_i)`, where `v_i` is the exact normal-theory sampling variance of that estimator at
that player's n and `τ² = max(0, Var(residual) − mean(v_i))` is estimated from the data. **No
hand-picked constant.** The `n/(n+k)` form used in §3.3 runs as a sensitivity over k ∈ {0, 8, 16, 32}.

Arms: `base` · `skew` · `kurt` · `both` (run separately as well as together, so that "skew works and
kurtosis does not" would be visible) · and **`oracle`**, which is given the *target season's own*
skew and kurtosis. The oracle is circular on purpose. It is not a result, it is a **bound**: if
perfect foresight of the season's own shape cannot buy much, no honest version can.

#### The upstream check settles it before the model is even fitted

Does a player's *shape* residual in season N−1 predict his shape residual in season N?

| family : moment | r(N, N+1) | 95% CI | n | grade |
|---|---|---|---|---|
| rec : skew | +0.014 | [−0.029, +0.058] | 2,038 | **NULL** |
| rec : kurtosis | −0.004 | [−0.049, +0.043] | 2,038 | **NULL** |
| rush : skew | +0.049 | [−0.013, +0.108] | 821 | **NULL** |
| rush : kurtosis | −0.031 | [−0.089, +0.030] | 821 | **NULL** |
| pass : skew | +0.071 | [−0.026, +0.158] | 566 | **NULL** |
| pass : kurtosis | −0.000 | [−0.076, +0.076] | 566 | **NULL** |

**Six of six NULL, every point estimate ≤ 0.071, two of six negative.** For comparison, the second
moment — the one that failed downstream — persists at r ≈ 0.08–0.11 and reaches SURVIVES at RB and
WR. **The third and fourth moments persist even less than the second.** From ~17 games they are
close to pure noise, which is what the sampling variances (≈6/n and ≈24/n) predict.

**The empirical-Bayes procedure says the same thing in its own currency, and this is the cleanest
form of the result.** The weight it puts on a player's own estimate:

| family : position | skew weight (τ²) | kurtosis weight (τ²) |
|---|---|---|
| rush : RB | **0.000** (τ² = 0.0000) | 0.535 |
| rec : TE | **0.000** (τ² = 0.0000) | 0.560 |
| rec : WR | 0.027 (τ² = 0.0099) | 0.542 |
| pass : QB | 0.109 (τ² = 0.0440) | 0.152 |
| rec : RB | 0.138 (τ² = 0.0558) | 0.703 |

**Given no hand-picked constant, the estimator concludes there is no detectable between-player
variance in true skewness at all** in two of five cells — τ̂² is exactly zero, the covariate becomes
identically zero, and the skew arm collapses onto the base arm. On the g1/g2 sensitivity that
happens for **skew in all five cells and kurtosis in three of five**. That is not a failed test; it
is the answer, delivered by a procedure that had every opportunity to find something.

#### And downstream, nothing

Out-of-sample log-loss per game-trial, walk-forward, primary estimator and primary shrinkage.
**Negative = the shape arm is better.**

| family | threshold | base | skew | kurtosis | both | **oracle** |
|---|---|---|---|---|---|---|
| rec | ≥100 | 0.29321 | +0.000028 NULL | +0.000026 NULL | +0.000035 NULL | −0.000645 MARGINAL |
| rec | ≥150 | 0.07413 | +0.000044 NULL | +0.000058 NULL | +0.000079 NULL | −0.002163 SURVIVES |
| **rec** | **≥200** | 0.01426 | **+0.000036 NULL** | **+0.000034 NULL** | +0.000071 NULL | −0.000517 NULL |
| rush | ≥100 | 0.34144 | +0.000000 NULL | +0.000033 NULL | +0.000033 NULL | +0.000177 NULL |
| rush | ≥150 | 0.08800 | +0.000000 NULL | +0.000046 NULL | +0.000046 NULL | −0.001204 SURVIVES |
| **rush** | **≥200** | 0.01839 | **+0.000000 NULL** | **+0.000067 NULL** | +0.000067 NULL | −0.001744 SURVIVES |
| pass | ≥300 | 0.50266 | +0.000095 NULL | +0.000035 NULL | +0.000134 NULL | −0.001414 MARGINAL |
| pass | ≥350 | 0.28857 | +0.000092 NULL | −0.000057 NULL | +0.000054 NULL | −0.000012 NULL |
| **pass** | **≥400** | 0.11883 | **−0.000041 NULL** | **+0.000168 NULL** | +0.000088 NULL | −0.002378 MARGINAL |

Expected **bonus points** MAE per player-season, walk-forward:

| family | base | skew | kurtosis | both | oracle |
|---|---|---|---|---|---|
| rec | 0.8016 | −0.00042 NULL | −0.00030 NULL | +0.00018 NULL | +0.02334 NULL |
| rush | 0.9352 | +0.00000 NULL | +0.00122 NULL | +0.00122 NULL | +0.01960 MARGINAL — **worse** |
| pass | 1.7694 | −0.00568 NULL | +0.00790 NULL | +0.00689 NULL | +0.08681 MARGINAL — **worse** |

**Every honest arm is NULL at every threshold in every family, including at the top thresholds where
the effect was predicted to appear first.** Stable across the whole `n/(n+k)` sweep and across both
estimator conventions. Bonus-point deltas are ±0.0004 to ±0.008 on errors of 0.80 to 1.77.

**The oracle is the part that makes this a bound rather than a shrug.** Given the target season's
own shape — perfect, impossible foresight — log-loss improves by at most **0.0024 per game-trial**,
and **bonus-point accuracy gets worse at every family** (+0.023, +0.020, +0.087). So shape does
carry some information about that season's own exceedance, and it is (a) tiny even then and (b) not
predictable a year in advance. **Both halves of the ceiling case fail, and they fail independently.**

#### Two honest notes on the shrinkage, one of which strengthens the null

The normal-theory sampling variances `v_i` assume normality, and per-game yardage distributions are
emphatically not normal — for heavy-tailed data the true sampling variance of G1/G2 is **larger**
than the normal-theory value. So `τ̂² = Var(residual) − mean(v_i)` is **over**-estimated, the
weights are too high, and I am **under**-shrinking. That biases the test *toward* finding an effect.
It still finds none. The kurtosis weights of 0.53–0.70 above are almost certainly too generous, and
the kurtosis arm is null anyway.

The fitted coefficients printed by the module (e.g. rec skew +4.64 at the 200-yard threshold) carry
intervals that are **invalid for the same reason §3.3's were** — they bootstrap across walk-forward
target seasons with near-identical training sets, so effective n ≈ 1. They are in the raw JSON for
completeness and are not evidence.

#### What this closes

**`CLAUDE.md` §7's operational clause now has four independent instruments against it**, at
increasing resolution: PR-002 (categorical), pass-1 §6.1 (clearance-count residual), §3.3 (second
moment), and §3.4 (third and fourth moments, plus an oracle bound). The scoring rules reward ceiling
— that is in the rulebook and is not in dispute. **The exploitable consequence is measured at zero,
and the founder's own proposed mechanism is now the one that has been tested most carefully.**

---

## 4. Does this league actually pay for volatility? Yes, and by less than one point

Bonus points earned per season, players split into terciles by excess SD within position:

| position | low-volatility tercile | high-volatility tercile | difference | grade |
|---|---|---|---|---|
| WR | 0.87 | 1.81 | **+0.94** [+0.75, +1.14] | SURVIVES |
| QB | 3.92 | 5.01 | +1.09 [+0.18, +1.89] | MARGINAL |
| TE | 0.21 | 0.30 | +0.09 [+0.02, +0.16] | MARGINAL |
| RB | 1.45 | 1.58 | +0.13 [−0.06, +0.33] | NULL |

**The mechanism is real and the magnitude is trivial.** A high-volatility WR does collect roughly
twice the threshold-bonus points of a low-volatility WR at the same scoring level — and twice
0.87 points is 1.81 points, across a whole season, against a WR1 total near 300. That is the ceiling
premium this league pays, measured. It is consistent to three significant figures with pass-1 §6,
which found the stacking bonus worth 0.57%–2.39% of realised points and moving three players by three
or more rank positions across 4,792 player-seasons.

---

## 5. Can this be an archetype dimension at all? — the call, and it is mine to make

`researcher`'s archetype work needs one thing from me: **is volatility stable enough to be a label?**
A label implies a durable property of the player.

Year-over-year correlation, bootstrap resampling **players** (not player-seasons — the same player
recurs and resampling rows would shrink every interval):

| position | **excess SD** | CV | boom rate | mean PPG *(reference)* |
|---|---|---|---|---|
| QB | +0.097 [+0.007, +0.186] MARGINAL | +0.366 | +0.447 | +0.542 |
| RB | +0.111 [+0.057, +0.165] SURVIVES | +0.225 | +0.567 | +0.714 |
| WR | +0.098 [+0.054, +0.140] SURVIVES | +0.413 | +0.532 | +0.727 |
| TE | +0.083 [+0.017, +0.148] MARGINAL | +0.419 | +0.435 | +0.715 |

**The verdict, stated as a decision rather than a number:**

> **Player-level volatility must not become an archetype label.** Excess SD persists at r ≈ 0.08–0.11.
> That is real — two of four clear zero at SURVIVES — and it is *seven times weaker* than the
> persistence of the player's scoring level itself (r ≈ 0.71–0.73) on the same players over the same
> seasons. About 1% of next season's excess volatility is explained by this season's. A label built
> on that would describe last year and predict essentially nothing.
>
> **Type-level volatility can, and should be expressed as a property of the role, not the man.** The
> archetype should carry *"deep-target receiver"* and let volatility be an attribute of that type,
> not carry *"volatile player"* as an attribute of the individual.

Do not be misled by the CV column (r ≈ 0.22–0.42) or boom rate (r ≈ 0.44–0.57) looking healthier.
Both are mean-dependent: they inherit their persistence from PPG persisting, which is exactly the
thing already in every model. Excess SD is the part that is *not* the mean, and it is the weak one.

**And here is the form that does work.** Assigning a player a type in season N−1 and asking about his
excess SD in season N+0:

| prior-season type | n | next season's excess SD | grade |
|---|---|---|---|
| RB snap-share low `[PROXY]` | 159 | **+5.9%** | MARGINAL |
| TE snap-share low `[PROXY]` | 131 | **+4.4%** | MARGINAL |
| WR aDOT high | 441 | +1.2% | NULL |
| WR target-share high | 584 | −3.3% | SURVIVES |
| WR aDOT low | 424 | **−4.3%** | SURVIVES |
| RB snap-share high `[PROXY]` | 273 | **−6.3%** | SURVIVES |
| TE snap-share high `[PROXY]` | 216 | −3.9% | SURVIVES |

**Prior-season *role* predicts next season's volatility; prior-season *player* barely does.** The
usable range is roughly −6% to +6% of SD — real, and small. Note that the aDOT axis, which was the
*largest* contemporaneous effect (§2), is the one that mostly **fails** to carry forward (WR aDOT
high: +1.2%, NULL). The forward-looking signal lives in workload, not target depth.

---

## 6. Which archetype dimensions are stable traits and which are situational roles — measured

The founder's rule for the archetype — *"we have multiple seasons of history for most players, the
longer, the more confident we can be"* — is right for a stable trait and can be wrong for a
situational one. The proposed split (aDOT/catch rate/YAC = stable, pool career; snap share/target
share/committee = situational, recent only) was explicitly a hypothesis. **I measured it and it is
close to backwards.**

Year-over-year autocorrelation, 2009–2024, ≥8 games, bootstrap resampling players. Verdict thresholds
(≥0.60 stable, 0.40–0.60 mixed, <0.40 situational) declared in code before the numbers were read.

| dimension | hypothesised | pos | **r(N, N+1)** | 95% CI | measured verdict |
|---|---|---|---|---|---|
| snap share `[PROXY]` | *situational* | WR | **+0.707** | [+0.663, +0.747] | **STABLE** |
| rec. share of touches | *situational* | RB | **+0.704** | [+0.627, +0.763] | **STABLE** |
| snap share `[PROXY]` | *situational* | RB | **+0.678** | [+0.619, +0.728] | **STABLE** |
| target share | *situational* | WR | **+0.667** | [+0.629, +0.699] | **STABLE** |
| aDOT | *stable* | WR | +0.664 | [+0.612, +0.707] | STABLE ✓ |
| target share | *situational* | TE | **+0.661** | [+0.590, +0.719] | **STABLE** |
| team carry share | *situational* | RB | **+0.625** | [+0.567, +0.675] | **STABLE** |
| snap share `[PROXY]` | *situational* | TE | **+0.611** | [+0.529, +0.675] | **STABLE** |
| target share | *situational* | RB | +0.580 | [+0.495, +0.651] | mixed |
| QB rushing share | *stable* | QB | +0.572 | [+0.369, +0.788] | mixed |
| aDOT | *stable* | RB | +0.510 | [+0.362, +0.638] | mixed |
| aDOT | *stable* | TE | +0.500 | [+0.394, +0.586] | mixed |
| catch rate | *stable* | WR | +0.433 | [+0.376, +0.484] | mixed |
| YAC per rec | *stable* | WR | +0.404 | [+0.335, +0.470] | mixed |
| YAC per rec | *stable* | TE | +0.387 | [+0.283, +0.473] | **SITUATIONAL** |
| catch rate | *stable* | TE | **+0.270** | [+0.164, +0.368] | **SITUATIONAL** |
| **yards per carry** | *stable* | RB | **+0.175** | [+0.086, +0.260] | **SITUATIONAL** |
| YAC per rec | *stable* | RB | +0.151 | [+0.059, +0.237] | **SITUATIONAL** |
| catch rate | *stable* | RB | **+0.144** | [+0.048, +0.237] | **SITUATIONAL** |
| *mean PPG (reference)* | — | WR | +0.734 | [+0.702, +0.763] | — |

**Role is more persistent than skill.** The five most persistent dimensions in the entire set are all
usage/role measures that were hypothesised to be situational; three of the four least persistent are
efficiency measures that were hypothesised to be stable traits. Yards per carry at r = +0.175 is the
starkest: it is the classic example of a statistic that feels like a player property and behaves like
noise.

### 6.1 But the *treatment* rule survives, for a different reason

Autocorrelation and "should I pool career history" are not the same question, and separating them is
what makes this usable. Comparing r(prior season only → N) against r(mean of all prior seasons → N),
on identical rows (players with ≥2 prior seasons, so the comparison is not confounded with who has a
career at all):

| dimension | pos | prior season only | career mean | delta | reading |
|---|---|---|---|---|---|
| QB rushing share | QB | +0.644 | **+0.750** | **+0.106** | career pooling **helps** |
| aDOT | TE | +0.503 | +0.585 | +0.082 | career pooling **helps** |
| catch rate | TE | +0.251 | +0.315 | +0.064 | career pooling **helps** |
| YAC per rec | WR | +0.401 | +0.464 | +0.063 | career pooling **helps** |
| catch rate | RB | +0.159 | +0.196 | +0.038 | career pooling **helps** |
| catch rate | WR | +0.422 | +0.455 | +0.034 | career pooling **helps** |
| target share | RB | +0.574 | +0.576 | +0.003 | no difference |
| snap share `[PROXY]` | WR | +0.704 | +0.698 | −0.006 | no difference |
| snap share `[PROXY]` | RB | +0.675 | +0.647 | −0.028 | no difference |
| target share | WR | +0.655 | +0.618 | **−0.037** | career pooling **hurts** |
| **rec. share of touches** | RB | +0.724 | +0.669 | **−0.055** | career pooling **hurts** |
| **snap share** `[PROXY]` | TE | +0.590 | +0.517 | **−0.073** | career pooling **hurts** |

**So the recommended treatment is right even though the classification was wrong, and the reason
matters.** The efficiency/trait dimensions have *low* autocorrelation because a single season measures
them noisily — they are stationary around a stable player mean, so averaging more seasons recovers
it, and pooling helps. The role dimensions have *high* autocorrelation but **drift**: they are closer
to a random walk than to noise around a fixed mean, so the most recent observation is the best single
estimate and older seasons actively dilute it.

That gives a decision rule that is measured rather than intuited, and it is not the one in the
hypothesis table:

> **Pool career history for the noisy-but-stationary dimensions** — catch rate, YAC, aDOT at TE, QB
> rushing share. **Use the most recent season only for the drifting role dimensions** — target share,
> snap share, receiving share of touches — and reset rather than dilute on a depth-chart or coaching
> change.
>
> Note this is the *opposite* of what "higher autocorrelation means more confidence in the label"
> would suggest. High autocorrelation with drift argues for *less* history, not more.

### 6.2 The survivorship confound bites, and it is not correctable here

Career length is not a neutral sample: players survive partly by being good.

| position | corr(seasons observed, PPG) | PPG, ≥5 seasons seen | PPG, ≤2 seasons seen |
|---|---|---|---|
| TE | **+0.462** | 5.77 (n=677) | 2.66 (n=213) |
| WR | **+0.456** | 8.16 (n=1,326) | 3.85 (n=454) |
| QB | +0.435 | 16.99 (n=390) | 11.13 (n=85) |
| RB | +0.374 | 9.17 (n=773) | 4.41 (n=300) |

**Players with five or more observed seasons score roughly twice the points per game of players with
two or fewer, at every position.** So a confidence score shrunk by games observed is **substantially
a quality score wearing a confidence label** — it will report high confidence about good players and
low confidence about marginal ones, largely regardless of how well-measured either actually is.

I cannot correct this cleanly. The obvious fix — condition on PPG — removes the confound and also
removes most of the variation you wanted the confidence score to capture, since games observed and
quality are two views of the same survival process. **The honest options are: (a) report confidence
conditional on a scoring band so it is at least comparable within tier, or (b) label it as what it
is, which is jointly a sample-size and a quality signal.** What must not happen is shipping a
"confidence" number that is quietly ranking players by how good they are.

---

## 7. Connection to FR-094 (late-round sleepers)

`backend`'s sleeper screen and this measurement land on the same fact from opposite ends. §6.1 shows
role dimensions **drift** — high autocorrelation, but the career mean is a *worse* predictor than the
most recent season, at every role dimension where the difference is non-zero. A breakout is by
definition a change in role. **A screen leaning on career averages of usage would therefore
systematically miss the players it exists to find**, and the effect is measurable: −0.037 to −0.073 in
correlation, which is a real amount of predictive power thrown away for free.

The concrete recommendation, and it is narrow: **for the usage features in a sleeper screen, use the
most recent season (or within-season trend), never a career mean.** For efficiency features — catch
rate, YAC — the reverse holds and pooling helps by +0.03 to +0.06. Opened as a
`NEW-` handoff to `backend`.

---

## 8. What I am not claiming

- **Not claiming WRs are more volatile than backs.** RB − WR is a clean NULL. The founder's framing
  question gets a negative answer on its interesting half.
- **Not claiming volatility can be a player-level archetype label.** §5 — it persists at r ≈ 0.10 and
  it must not.
- **Not claiming the exceedance curve should get a dispersion, skewness or kurtosis term.** §3.3
  and §3.4 — null in the most favourable possible setting, at every threshold, and the oracle
  bounds how much any version could ever buy at 0.0024 log-loss per game-trial while making
  bonus-point accuracy worse.
- **Not claiming shape carries no information at all.** The oracle arm shows it carries a little
  about the season it is measured in. It is not predictable a year ahead (r = −0.004 to +0.071,
  six of six NULL), which is the part that would be needed.
- **Not claiming the snap-share results are route participation.** They are labelled `[PROXY]`
  throughout and a blocking TE is indistinguishable from a route-running one in that data.
- **Not claiming the per-slot calculation covers correlated risk.** It assumes within-position
  independence, which is measured at +0.001 to +0.009 — but same-*team* stacks and bye-week clustering
  are not modelled.
- **Not claiming variance is worthless in this league.** §1.3 shows it is worth ~nothing at the *team*
  level at equal expected points. Start/sit optionality is real and this design cannot price it.
- **Not claiming the confidence-by-games-observed idea should be dropped.** §6.2 — it needs to be
  either conditioned or honestly relabelled.

## 9. What should happen next

1. **`researcher` should treat volatility as a type attribute, not a player attribute**, in the
   archetype proposal. §5. Replying on the derivability-review thread with exactly that.
2. **The stable/situational column assignment in that proposal should be replaced with §6's measured
   one**, which is close to its inverse — and the pooling rule should key off *drift*, not off
   autocorrelation.
3. **`backend` should not use career-mean usage in the FR-094 sleeper screen.** §7. `NEW-` handoff
   opened.
4. **`strategist` should decide whether §3's null is worth writing into `CLAUDE.md` §7.** The scoring
   rules do reward ceiling; the exploitable consequence is now measured at zero through **four**
   independent instruments, the last of which (§3.4) is the founder's own proposed mechanism tested
   at its most favourable. That is a change to the standing spec and therefore not mine to make.
6. **Do not spend more effort on the ceiling channel.** §3.4 closes it on an oracle bound rather
   than on a failure to find something, which is the stronger form. Four instruments is enough.
5. **Route participation remains the named gap.** Snap share is the proxy and it is doing real work
   here; the real metric would be worth having. `CLAUDE.md` §5 already names it.
