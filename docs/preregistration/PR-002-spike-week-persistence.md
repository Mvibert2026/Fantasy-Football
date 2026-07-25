---
id: PR-002
title: Is spike-week-ness a persistent player trait, or an artifact of volume?
hypothesis: This league's stacking yardage bonuses (100/150/200 rushing and receiving,
  300/350/400 passing) reward distribution SHAPE, not just season totals. The project has
  treated that as its primary structural edge (test-registry #38, "the most genuinely novel
  item in this registry"). That edge exists only if the propensity to clear bonus thresholds
  MORE OFTEN THAN VOLUME ALONE IMPLIES is a stable property of a player. If the
  volume-adjusted residual does not persist year over year, then bonus-threshold clearance
  is fully predictable from projected yardage, carries no independent information, and the
  premise fails.
metric: Pearson correlation of the volume-adjusted clearance residual between consecutive
  qualifying seasons for the same player (residual_t vs residual_t+1), computed separately
  per position, per stat family (receiving / rushing / passing), and per threshold. Residual
  = observed clearance rate minus the rate expected from that player-season's yards per game,
  where the expected-rate curve is fitted by pooled binned smoothing on development seasons
  only. Spearman reported alongside as a robustness check. 95% confidence intervals from a
  bootstrap that RESAMPLES PLAYERS (not player-season pairs), so repeated appearances by the
  same player do not masquerade as independent evidence.
confirmation_threshold: Evaluated on the PRIMARY case (receiving 100-yard threshold for WR,
  and rushing 100-yard threshold for RB). PERSISTENT requires r >= 0.20 AND a player-clustered
  95% bootstrap CI excluding zero AND survival of Benjamini-Hochberg correction across every
  correlation run in this pass. WEAK requires 0.10 <= r < 0.20 with a CI excluding zero -
  reported as real but too small to build a strategy on. NULL is any of - CI includes zero, or
  r < 0.10, or the BH-adjusted p-value exceeds 0.05. A result that holds pooled but reverses
  or vanishes in the most recent regime (post-2019 per src/regimes.py) is NOT persistence for
  2026 purposes and will be reported as regime-dependent, not confirmed.
status: RUN
result: NULL — the pre-registered thresholds were not met on either primary case, and no
  correlation of the 24 testable ones survived Benjamini-Hochberg correction across the 36
  tests run. Receiving-100 for WR r=+0.041, 95% CI [-0.018, +0.099]. Rushing-100 for RB
  r=+0.063, 95% CI [-0.001, +0.124]. See the Result section below.
run_date: 2026-07-25
qualifying_rules: Pre-committed so they cannot be tuned after seeing results. A player-season
  qualifies if games_played >= 8 AND yards_per_game >= 25 for the relevant stat family
  (receiving or rushing); for passing, games_played >= 8 AND pass_yards_per_game >= 150. The
  volume floor exists because a player averaging 5 yards a game has expected clearance of
  essentially zero and observed clearance of exactly zero, contributing a large mass of
  identical (0,0) points that would inflate a correlation without carrying information.
  Consecutive-season pairs only; a player missing a season contributes no pair across the gap.
window: 1999-2024. Receiving and rushing yards are populated for the full 1999-2025 window
  (docs/data-availability.md §2) and this test touches NO other source, so the 2003-2008
  receiver-attribution gap and the gsis_id join problems are both irrelevant here - targets
  are not used, only yards. 2025 is the LOCKED HOLDOUT (src/holdout.py) and is excluded.
  This is expected to be the largest effective sample in the project.
track: ACCURACY_ONLY. This test involves no consensus data and makes no claim about beating
  the market. It asks whether a property of the data-generating process exists at all.
---

## Why this is decisive rather than incremental

test-registry #38 is described as "the most genuinely novel item in this registry", on the
reasoning that two players with identical projected season totals can differ materially in
this format based purely on distribution shape. That reasoning is sound arithmetic. What it
assumes, and has never tested, is that distribution shape is a **player trait** rather than a
**consequence of volume plus noise**.

The distinction is everything:

- If spike-week-ness is a trait, it is forecastable, it is invisible to public half-PPR
  rankings, and it is a genuine structural edge in this league.
- If it is volume plus noise, then bonus clearance is already fully implied by projected
  yardage. Re-scoring under our rules would still be correct, but it would add nothing beyond
  what any yardage projection already contains, and the "ceiling over floor" framing that has
  been shaping strategy would be decoration rather than signal.

A null here removes a premise the project has been organised around. That is a useful result,
not a failed one.

## Why the volume adjustment is the whole test

A player averaging 90 receiving yards per game clears 100 yards far more often than one
averaging 40. That is arithmetic, not talent, and it is entirely captured by a yardage
projection. The only question that matters is whether, **conditional on volume**, some players
systematically clear thresholds more than others - a "boom/bust" shape independent of level.

So the mechanical baseline is not a nuisance to be controlled away; it IS the null hypothesis.

## Reasons this may return a null, written down in advance

1. **Binomial noise dominates.** A 16-game season yields at most 16 Bernoulli trials per
   threshold. Even a real difference in true clearance probability would be estimated with
   large error, attenuating any YoY correlation toward zero. **A null here is therefore weak
   evidence of no trait**, and that asymmetry must be stated in the result rather than
   glossed.
2. **Errors-in-variables biases toward null.** Yards per game is itself measured with noise
   from the same games that generate the clearances, so the fitted expected-rate curve is
   attenuated and the residual carries volume noise. This pushes the correlation toward (or
   below) zero, not above it.
3. **Selection on qualifying seasons.** Requiring two consecutive qualifying seasons keeps
   established players and drops the volatile fringe, which may be exactly where shape
   variance lives.
4. **Regime change.** Even a real trait may not survive the 2019 structural break
   (src/regimes.py). Pooling 26 seasons could show persistence that no longer holds.

## Pre-committed interpretation

- **PERSISTENT** -> #38 is validated; the bonus-shape edge is real and worth building on.
- **WEAK** -> report the effect size in points, not just correlation, and state plainly that
  it is too small to reorganise a draft strategy around.
- **NULL** -> report that the primary claimed edge does not exist, and state what remains:
  the scoring re-computation itself and the corrected replacement levels (RB28/WR41/TE11/QB10
  against a published RB24/WR36 convention). Both are real and neither depends on this test.
- No re-specification after seeing results. Changing the volume floor, the games minimum, or
  the smoothing method and re-running requires a NEW pre-registration id, and both runs count
  toward the multiple-comparisons total.

---

# RESULT (2026-07-25): NULL

**The pre-registered thresholds were not met, and the premise this project has been organised
around does not survive the test.**

## Primary pre-registered cases

| Case | r (Pearson) | 95% CI (player-clustered) | raw p | BH-adjusted p | Verdict |
|---|---|---|---|---|---|
| Receiving 100, **WR** | **+0.041** | [-0.018, +0.099] | 0.193 | 0.668 | **NULL** |
| Rushing 100, **RB** | **+0.063** | [-0.001, +0.124] | 0.052 | 0.336 | **NULL** |

Both fail every criterion: r is below the 0.10 WEAK floor, the CI includes zero, and neither
survives correction.

## Everything else run

**36 correlations attempted, 24 produced a p-value, and ZERO survived Benjamini-Hochberg
correction across the full run log.** All 36 are recorded in `test_run_log.jsonl`.

Two results were nominally significant before correction, and both are disqualified for
reasons written down in advance:

- **Passing 300, QB, 2012-2019: r = +0.265, raw p = 0.002.** The strongest result in the pass.
  BH-adjusted p = 0.072, so it does not survive correction. More decisively, it **reverses in
  the most recent regime**: 2020-2024 gives r = **-0.234** with a CI excluding zero. A
  coefficient that is significantly positive in one era and significantly negative in the next
  is noise with a trend, not a trait. PR-002 pre-committed that regime reversal disqualifies.
- **Receiving 100, TE, pooled: r = -0.134**, CI excluding zero, raw p = 0.013 (BH 0.234). The
  sign flips across every regime (-0.287, then +0.008, then +0.308). Noise.

Had either been examined alone, without the pre-registered correction and regime checks, it
would have been written up as a finding.

## The 150 and 200 thresholds are not merely unpersistent — they barely occur

Twelve of the 36 tests were **not testable at all** because the threshold is cleared so rarely
that the residual is almost entirely structural zeros. League-wide, across a full season:

- receiving 200+: **1 to 8 games per season** (2025: one)
- receiving 150+: 18 to 41 games per season

So the stacking `+1.5 @ 150` and `+2.0 @ 200` bonuses are close to irrelevant to draft
decisions in expectation, independent of the persistence question. They are worth points when
they land; they are not worth planning around.

## Why a null here is strong, and where it is weak

**Weak in one specific way, stated in advance:** a season supplies at most ~17 Bernoulli trials
per threshold, so binomial noise attenuates any true correlation toward zero. Errors-in-variables
in yards-per-game pushes the same direction. A null is therefore *weak evidence of no trait*.

**But strong on magnitude, which is what matters here.** The confidence intervals bound the
effect from above: the WR upper bound is +0.099 and the RB upper bound is +0.124. Even at the
optimistic end of the interval, the trait would explain about **1% of next-season residual
variance** — inside the pre-registered WEAK band, and far too little to reorganise a draft
around. The test does not merely fail to detect a large effect; it rules one out.

## What this kills

test-registry #38 was described as "the most genuinely novel item in this registry", on the
argument that two players with identical projected totals can differ materially in this format
through distribution shape. The arithmetic was never in doubt. The assumption underneath it —
that shape is a forecastable player property — is not supported.

**Practical consequence: bonus-threshold clearance carries no information beyond projected
yardage.** There is no "spike-week player" to identify. Project the yards and the bonuses
follow mechanically. Any strategy premised on preferring ceiling-shaped players at equal
projected volume has no measured basis.

## What survives

Neither of these depends on PR-002, and both remain real:

1. **Re-scoring under our exact rules.** Public half-PPR lists model neither the yardage
   bonuses nor the -2 interception. Computing points under our rules still reorders players
   against a generic list. Note this is now a smaller claim than before: it is a *level*
   correction to projected points, not an independent *shape* signal.
2. **Corrected replacement levels.** RB28 / WR41 / TE11 / QB10 for this 10-team league against
   the published 12-team RB24 / WR36 convention. This genuinely changes VBD ordering.

Both are modest. And note ADR-016's finding that the re-scored board's positional re-weighting
showed **no demonstrated advantage** over raw consensus on development seasons
(`starter_vbd` delta -84.9, CI [-166.1, +34.7]). So the practical value of even these two is
so far unproven, not established.

## Sample size

This is the largest effective sample in the project and it is not close: 26 seasons
(1999-2024, holdout excluded), 1,541 WR consecutive-season pairs across 404 players, 821 RB
rushing pairs across 243 players, 566 QB passing pairs across 123. The alpha track by contrast
has three development seasons. The null is not a power problem at the level of pair counts.
