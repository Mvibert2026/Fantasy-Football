# Assistant Context

**This file is the ONLY project document the in-app assistant should read for "why" questions.**
Never point it at `decisions.md` (the ADR log) or `test-registry.md` — both are historical
records and both contain figures that have since been superseded. A language model handed
`decisions.md` will find `-92.9` or `RB28/WR41/TE11` and cite them with full confidence; it has
no way to know, from the text alone, that a later entry in the same file overwrote them. This
file holds no history and no superseded numbers, on purpose, so that problem cannot occur here.

**One paragraph per settled decision, current state only.** When an ADR supersedes something
written below, this file is edited in place — not appended to. If you are updating this file
after a new ADR lands, replace the affected paragraph; do not leave the old one for contrast.

Contract version referenced below: **1.16.0** (ADR-062, plus the per-league history export).

---

## What the board is

`board.json` ranks 378 players for this league's exact format — 10 teams, half-PPR with yardage
bonuses, 1QB/2RB/3WR/1TE/2FLEX. Its edge over a generic public list is **structural**: it uses
this league's own replacement levels and scoring rules, not a 12-team RB24/WR36 convention.

**It is not a player evaluation.** Every player at the same consensus positional rank gets an
identical point projection — the board has no opinion about who is *better* than their consensus
rank suggests, only about what a given rank is *worth* under this league's rules. This is why
`evaluative_adjustment` is always null: there is nothing there to report. Do not answer "does the
model like this player more than the experts do" — it cannot.

Projections are weak on their own terms: the rank-to-points curve behind them explains 16–27% of
the variance in what a player actually scores (R² 0.158–0.266 by position). Treat any single
`projected_points` value as noisy, and prefer the confidence interval on VBD over the point
estimate.

## Replacement levels: RB30 / WR40 / TE10 / QB10

Measured, not assumed — derived by ranking 26 seasons of actual outcomes under this league's
rules and counting who wins the flex slots (RB wins roughly 52% of flex slots, WR 48%, TE
effectively 0%). Public boards assume a 12-team RB24/WR36 convention, which is a different
league's math applied to this one.

TE10 is the most solid part of this: a tight end has won a flex slot in only 2 of 26 seasons
tested. The RB/WR split moves by about ±1 rank depending on which years are included — real
variance, not a precision claim.

**DEF has no replacement level, permanently.** No DST scoring data is ingested, so there is
nothing to compute a level from. `league.json` states this explicitly
(`positions_without_replacement_levels: ["DEF"]`) rather than leaving DEF's absence to look like
an oversight — it is a decision, and it is not going to change without new data being ingested.

## Factor test results — cite with the number, interval, effective n, and scope attached

**Rule for this section, not optional.** Never state one of these as a verdict word alone ("NULL",
"harmful", "worst case"). State the number, its interval, how many independent data points it
actually rests on (not how many cells or arms were run over that data), and the exact question the
test answered — a test can be scoped narrower than its plain-English name suggests, and reading
past that scope states a stronger claim than the evidence supports. Full detail and all sources:
`docs/factor-ledger.md`.

- **Spike-week bonus clearance is not a persistent player trait.** Receiving-100 WR YoY residual
  r = +0.041, 95% CI [−0.018, +0.099]; rushing-100 RB r = +0.063, CI [−0.001, +0.124]. **Effective
  n = 26 seasons** of year-over-year pairs (1,541 WR player-season pairs / 404 players — the pairs
  count is not the effective n; seasons are). Zero of 24 testable correlations survived
  Benjamini-Hochberg correction. **Scope:** this tests whether a player clears 100/150/200-yard
  thresholds *more often than his projected volume alone implies* — it does not say the bonuses
  are worth nothing; project the yards and the bonuses follow mechanically. Ever run: **yes**
  (PR-002, `factor-ledger.md` T2-38).

- **Hero RB has no measurable edge over best-available drafting.** Margin −13.3 points vs. BPA,
  95% CI [−98.1, +65.0] — the interval spans zero by a wide margin. **Effective n = 4 seasons**
  (2 of 4 positive; a 4-season sign test cannot reach significance in either direction, p floors
  at 0.125–1.000 depending on split). Ever run: **yes** (PR-003 draft simulation).

- **Reaching early for an elite TE or QB is directionally costly, and the QB arm has the interval
  attached, not a "worst case" label.** `qb_early` point estimate **−115.4** points vs. BPA, 95%
  CI **[−176.3, −54.4]** at σ=10 — the interval, not the point estimate, is the honest range;
  never call −115.4 a worst case, the true worst case within this measurement is −176.3.
  `elite_te_early` **−96.1**, reported as a ±6-point seed-noise band (ADR-028), not a season
  bootstrap CI — a narrower kind of uncertainty than the QB number, do not treat them as
  equivalent precision. Both negative in every cell tested. **Effective n = 4 seasons** — the
  design also varies one guessed opponent-behavior parameter across 3 settings, giving 12 cells,
  but the cells are not independent draws; do not describe this as "12 scenarios." Not
  statistically significant at this sample size (sign-test floor 0.125). Ever run: **yes** (PR-003).

- **The league-format board (re-scoring + corrected replacement levels) shows a directionally
  positive margin over raw expert consensus, not a proven edge.** Development seasons: mean
  +84.9 VBD, 2 of 3 positive, sign-test p=1.000 (power floor 0.250). With the sealed 2025 holdout
  included: +84.6, 3 of 4 positive, p=0.625 (power floor 0.125). **Effective n = 4 seasons** — a
  4-season sign test cannot reach p<0.05 at any effect size; that is a design limit, not a weak
  result being undersold. Ever run: **yes** (ADR-025).

- **Scope trap 1 — a target-share *stability* test, not a test of target share.** A
  stability-weighted reweighting of target share was measured against the plain share the model
  already uses: −0.035 targets MAE full-universe (BH-significant at WR only), but only **0.02% of
  the model's own error on the ADP board** (7 seasons) and no effect on any ranking. **This is not
  a finding about target share itself** — target share as an input is separate, unimplemented in
  the shipped board, and its own year-over-year persistence (a different, descriptive measurement)
  is +0.548 to +0.652 depending on position, 15 seasons of consecutive pairs. Do not answer "is
  target share useful" with this NULL — answer only "does reweighting it by stability help,"
  which it does not. Ever run: **yes**, scoped as above.

- **Scope trap 2 — a proxy-contamination finding, not a verdict on vacated opportunity.** Testing
  whether departed teammates' opportunity predicts a player's own targets/carries ran on a
  **Week-1 depth-chart proxy**, because no pre-season roster table exists in the database. Result:
  harmful at RB (+0.2031 carries MAE, 95% CI [+0.1150, +0.2963]) and TE, null at WR — but the harm
  concentrates entirely in the bucket the proxy is known to mislabel (a Week-1-inactive player
  counted as "departed"). **This experiment cannot distinguish "vacated opportunity doesn't
  matter" from "the proxy used to measure it is broken."** State it as blocked, pending
  `load_rosters_weekly()`, never as a settled null. Effective n = 11 seasons (component-error
  measurement). Ever run: **yes**, but not answerable as designed.

- **A player's own touchdown rate carries real signal; discarding it for the position average is
  worse, not neutral.** Replacing a player's own TD-rate history with the pooled positional mean
  costs +0.0251 to +0.2295 MAE depending on position (worst at QB: +0.2295 pass-TD MAE, 95% CI
  [+0.1256, +0.3253], +4.0% of the position's own error), harmful at all four positions,
  BH-significant at three. **This means the model's existing shrinkage is already extracting the
  signal** — it is not an unbuilt opportunity. Effective n = 11 seasons. Ever run: **yes**.

- **Team-relative opportunity share (carries+targets ÷ team total) is not the "single best RB
  metric"; at RB it measures as doing nothing.** Ablating it costs −0.0168 carries MAE, 95% CI
  [−0.0498, +0.0029] — CI spans zero, NULL. **At WR the same construct does earn its place**:
  removing it costs +0.196 of 31.4 on the ADP board (+0.6%), 95% CI on the full-universe version
  [+0.0132, +0.1547]. State the position when citing this — the RB and WR results point opposite
  directions on the same feature. Effective n = 11 seasons (component), 7 seasons (ADP board).
  Ever run: **yes**.

- **A single global flex-eligible replacement level (~80th rank) shows no advantage over the
  current per-position scheme.** Realised-points margin +1.7, 95% CI [−67.6, +74.8] at one noise
  setting, −6.7 CI [−51.2, +37.8] at another — sign flips between settings, both CIs wide around
  zero. **Effective n = 4 seasons** — this is the binding constraint, not the 300 simulations run
  per cell. No change made to the shipped replacement levels. Ever run: **yes** (PR-006).

- **Pick-gap-aware VONA changes which player gets drafted without reliably changing roster
  quality.** Realised-points margin −37.2, 95% CI [−118.8, +36.0] — NULL, CI spans zero.
  **Separately, and this is the more decision-relevant finding:** the gap-aware and gap-blind
  versions of the same valuation method select a *different full roster* in 100% of paired
  simulated drafts, across all 8 season×noise-setting cells tested. **Effective n = 4 seasons.**
  Not wired into any live strategy. Ever run: **yes** (PR-008).

- **The yardage-bonus stacking structure does not support a variance/ceiling preference in
  rankings, tested four separate ways, all null at the bonus structure's most favorable
  measurement setting.** Perfect foresight of every WR's bonus points would move rank correlation
  by only +0.026 — the ceiling on the entire idea. A model built to capture it achieved +0.0002.
  Per-player shape (skewness/kurtosis, the originally proposed mechanism) does not persist
  year-to-year: empirical-Bayes between-player variance estimate driven to exactly zero, six of
  six tests null. **Do not re-derive a variance preference from the bonus structure** — it has
  been tested at its most favorable setting and there is nothing there (`CLAUDE.md` §7). Ever
  run: **yes**, four independent instruments.

## Why alpha detection is closed for 2026

"Alpha" means beating what the market already believed, not just predicting outcomes well —
those are different questions, and this project only has enough data to answer the second one.
Market-consensus data (needed to measure alpha) only exists for 2021–2025, and one of those five
seasons has to be held back as an honest test rather than used for tuning. That leaves too few
seasons for any statistical test to ever reach a real significance threshold, regardless of how
good or bad the underlying signal actually is — the math rules it out before the test even runs.

No further alpha-detection work is planned until enough additional seasons of consensus data
accumulate (on current pace, around 2028). This is a statement about sample size, not about
whether an edge exists. Work continues on **accuracy** — how well the model predicts outcomes —
which is not limited by this constraint.

## What the availability model does now

Availability answers "who will still be on the board when my pick comes," and it is the most
trustworthy output in the project — it depends only on how the room drafts, not on any weak
scoring projection. It is driven by three things: an opponent's ranking source (currently one
source, FantasyPros consensus), a mechanical positional-need penalty derived directly from this
league's roster rules (not a guessed constant), and a noise parameter reflecting how much a real
room deviates from consensus (reported across three settings, since it is not fitted to any
observed draft).

**It no longer assumes anything about specific named managers repeating past behavior.** An
earlier version of this model produced a wide range of outcomes by assuming two particular people
would repeat a prior pick; that was found to be circular (the range came entirely from the
assumption, not from anything measured) and has been removed. The current TE-survival-to-pick-23
figure is close to what that assumption-free removal implies it should be.

`by_player` and `by_tier` in `availability.json` are **unconditional averages over every possible
draft** — treat them as pre-draft planning numbers, not as live odds once a real draft is
underway. Mid-draft, availability is recomputed against the actual picks made so far using
`live_availability.py`, which re-weights the pre-draft marginal by two mechanisms: a
continuous, share-based roster-need term (a team further above its typical final composition at
a position gets that position's hazard suppressed, not merely un-boosted) and a positional-run
term (a standardized, shrunk signal over the last 10 picks, deliberately timid since the
detection threshold folk wisdom usually reaches for turns out to be noise about a quarter of the
time). The roster-need term's strength was measured from this league's actual 2025 draft, not
assumed; the run term remains an explicit, flagged prior pending mock data with per-pick draft
state, which does not exist yet.

## Known data traps — say these before answering, don't wait to be asked

- **No player-level opinion exists on the board.** See "What the board is," above. Do not
  construct a "we disagree with the consensus about this specific player" answer — the data to
  support that claim does not exist in this project.
- **Not every player has a displayable projection.** Players outside the fitted depth of the
  rank-to-points curve carry no honest confidence interval and must not be given a point number.
- **There is no market ADP for this specific league.** `fantasypros_ecr` is expert *opinion*
  (ECR), not observed draft position. A separate MFL-sourced ADP proxy exists but is drawn from a
  different population (a 50-mock-draft sample on a hobbyist platform, not this league) and must
  never be presented as this league's own draft tendency.
- **Historical stats have a real six-season hole.** Target-share-derived stats (targets, air
  yards, and anything built on them) are unreliable for 2003–2008 — present in the data but
  effectively zero, not measuring anything. Depth-chart data stops at the end of the 2024 season,
  so no depth-chart-based signal is available for the 2026 draft.
- **Most opponents in this league are unknown.** Only draft slot is known for 7 of the league's 9
  other teams; do not invent tendencies, prior picks, or names for them.
- **2025 is a locked holdout season for anything methodology-related.** If asked to evaluate a
  new idea "on 2025," the honest answer is that this project deliberately does not do that
  outside of a small number of pre-committed, already-used checks.
