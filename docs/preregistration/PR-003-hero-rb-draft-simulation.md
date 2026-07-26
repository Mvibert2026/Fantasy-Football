---
id: PR-003
title: Does Hero RB beat best-available drafting under simulation? (test-registry #44)
hypothesis: Hero RB — spending an early pick on a workhorse running back and then loading
  up on receivers — produces better rosters than simply taking the best available player off
  a consensus board. The strategy has been treated as a live candidate since the project
  began, but it has never been testable, because every metric built so far measures WHICH
  players ended a season in the lineup rather than WHAT WAS GIVEN UP to acquire them. A draft
  simulator with opponents is the first instrument capable of answering it.
metric: Mean roster points over a simulated 10-team snake draft from slot 3, scored against
  ACTUAL historical weekly outcomes for the simulated season under this league's scoring
  rules, using a weekly-optimal starting lineup. Compared to the BPA arm on the SAME simulated
  drafts (paired by season and by random seed). Secondary metric: P(user roster finishes top-4
  of the 10 simulated teams by total points). Uncertainty reported from two separate sources —
  a bootstrap over SEASONS and the simulation-level standard error — because conflating them
  understates the true interval.
confirmation_threshold: HERO RB WORKS requires ALL of — (a) paired mean roster-points margin
  over BPA of at least +20 points, which is roughly 1% of an expected season roster total and
  the smallest margin that could plausibly change a draft decision; (b) a season-level
  bootstrap 95% CI on that paired margin excluding zero; (c) survival of Benjamini-Hochberg
  correction across every strategy comparison run in this pass. WEAK is a CI excluding zero
  with a margin below +20 points — real but not decision-relevant. NULL is a CI including
  zero. A margin that exists at the default opponent-noise setting but disappears under the
  pre-declared sensitivity sweep is reported as ASSUMPTION-DEPENDENT, not as working.
status: RUN
result: NULL on the primary case. Hero RB margin vs BPA is -13.3 pts (sigma=10),
  95% CI [-98.1,+65.0], 2 of 4 seasons positive, sign p=1.000 - a coin flip at every sigma.
  Zero of 15 comparisons survived BH, as anticipated: with 4 seasons the exact sign test
  cannot go below p=0.125. Separately, elite_te_early (-96.1) and qb_early (-115.4) are
  negative in 12 of 12 season-sigma cells.
run_date: 2026-07-25
primary_comparison: hero_rb vs bpa_consensus
sensitivity_requirement: The opponent-noise parameter sigma is the single most important
  assumption in the simulator and is not empirically calibrated — no observed draft-position
  data exists for this league or any other in the repo (ADR-018 established that no ADP source
  is obtainable). Every strategy conclusion must therefore be reported across sigma in
  {5, 10, 20} picks. A conclusion that holds only at one sigma is an artifact of the
  assumption, not a finding about the strategy.
window: Development seasons only. Consensus coverage is 2021-2025 and 2025 is the LOCKED
  HOLDOUT, so simulation runs on 2021-2024. Arms requiring the re-scored board additionally
  cannot use 2021 (no prior consensus season to fit the rank-to-points curve) and are noted
  where they differ.
track: ACCURACY_ONLY for roster quality. This measures whether a drafting rule builds better
  rosters against known outcomes; it is NOT an alpha claim, because opponents are modelled as
  drafting to the same consensus rather than as real adaptive competitors.
---

## Why this could not be answered before

`starter_vbd` (ADR-020) was built to make cross-positional ordering visible, and it does. But
it assumes you receive your top-K picks uncontested. That is exactly wrong for the question
Hero RB poses, which is entirely about **opportunity cost under contention**: taking a running
back at pick 3 means not taking the receiver who will be gone by pick 18. No metric that
ignores opponents can price that.

An earlier attempt (session 3) reported a delta of exactly 0.0 for Hero RB, and that number
was meaningless — the metric was structurally blind to what the strategy does.

## Reasons to expect a null, recorded in advance

1. **Consensus rank explains only 16-27% of outcome variance** (ADR-016, R² 0.158-0.266 with
   residual SD 46-91 points). If the board you draft from is that weak a predictor, the order
   in which you consume it matters much less than the noise in the players themselves.
2. **The bonus-shape edge is gone.** PR-002 returned a null: volume-adjusted threshold
   clearance does not persist. So there is no ceiling-shape reason to prefer one roster
   construction over another at equal projected volume.
3. **Strategies mostly draft the same players.** From slot 3 with 15 skill picks, all six
   strategies pull from the same pool and will overlap heavily. The differences are confined
   to a handful of early picks.
4. **Simulation noise may swamp strategy differences.** With three development seasons and
   real outcome variance, the season-level bootstrap will be wide regardless of how many
   simulations are run — more simulations shrink the simulation-level error but not the
   season-level one.

**The most likely outcome is that most strategies are statistically indistinguishable and BPA
is hard to beat.** That is a legitimate result and will be reported as such.

## Pre-committed interpretation

- **WORKS** → #44 resolved affirmatively; report the margin in points and the sigma sensitivity.
- **WEAK / ASSUMPTION-DEPENDENT** → report plainly that the effect is either too small to act
  on or an artifact of an uncalibrated assumption.
- **NULL** → report that Hero RB is not distinguishable from best-available drafting, and that
  the same instrument now applies to Zero RB, elite-TE-early and QB-early.
- Every strategy comparison run counts toward the multiple-comparisons total, not just the
  Hero RB one. No re-running with a different sigma default or roster-need setting to obtain a
  different answer; that requires a new pre-registration id.

---

# RESULT (2026-07-25)

Run: 600 simulations per strategy per season per sigma = **43,200 simulated drafts**.
Seasons 2021–2024 (holdout excluded). Seed 20260725. 107 illegal rosters (0.25%) were
discarded as failed runs rather than scored as zero.

## Hero RB (the pre-registered primary): NULL

| sigma | margin vs BPA | season 95% CI | seasons positive | sign p |
|---|---|---|---|---|
| 5 | **−31.0** | [−106.5, +23.5] | 2/4 | 1.000 |
| 10 | **−13.3** | [−98.1, +65.0] | 2/4 | 1.000 |
| 20 | **−14.4** | [−80.6, +56.9] | 2/4 | 1.000 |

Fails every pre-registered criterion: the margin is negative rather than ≥ +20, every CI
includes zero, and the sign test is a literal coin flip at all three sigmas. The per-season
margins are pure noise — at sigma=10 they run 2021 −20.2, 2022 +6.3, 2023 **+93.4**,
2024 **−132.8**. A single season could have produced either headline.

**#44 is answered: Hero RB is not distinguishable from best-available drafting.**

## Full strategy table (sigma = 10, the default)

| Strategy | Mean pts | sim SE | P(top-4) | vs BPA | season 95% CI | signs | sign p |
|---|---|---|---|---|---|---|---|
| bpa_consensus | 2144.6 | 7.9 | 0.493 | — | — | — | — |
| zero_rb | 2171.3 | 7.5 | 0.530 | **+26.7** | [−6.2, +59.7] | 2/4 | 1.000 |
| balanced | 2159.9 | 7.8 | 0.501 | **+15.3** | [+1.6, +23.4] | 3/4 | 0.625 |
| hero_rb | 2131.2 | 7.8 | 0.478 | −13.3 | [−98.1, +65.0] | 2/4 | 1.000 |
| elite_te_early | 2051.6 | 7.5 | 0.295 | **−96.1** | [−134.1, −51.8] | **0/4** | 0.125 |
| qb_early | 2029.2 | 7.2 | 0.260 | **−115.4** | [−176.3, −54.4] | **0/4** | 0.125 |

> **RESTATED 2026-07-25 (ADR-028).** `elite_te_early` originally read **−92.9** here. That
> figure was not reproducible: the per-strategy seed was derived from builtin `hash()` on the
> strategy name, which Python salts per process, so every run silently used a different seed
> while reporting the same one. The canonical value is **−96.1**, now reproducible byte-identically
> across processes. Re-running at five fixed master seeds spans **−100.7 to −85.2 (sd 5.6)**, so
> treat this as **−96.1 ± 6**, not a point estimate. **No conclusion moves** — `seasons_positive`
> is 0/4 at every seed tested, and both the old and new figures sit inside the same band. What
> changed is the false precision, not the finding. Other rows in this table are unaffected
> (`vbd_sum`/`starter_vbd` CIs used plain integer seeds).

## The honest headline: BPA is hard to beat

Exactly as anticipated in the pre-registration. Zero of 15 comparisons survived
Benjamini-Hochberg — which is unsurprising and was stated in advance, because with four
development seasons the **smallest attainable two-sided p from an exact sign test is 0.125**.
No strategy comparison can reach conventional significance at the season level here, regardless
of effect size or how many drafts are simulated.

`zero_rb` (+26.7) and `balanced` (+15.3) are positive at every sigma but neither passes a sign
test. `balanced`'s bootstrap CI excludes zero at sigma 10 and 20 while its sign test says
p=0.625 — a direct contradiction, and the sign test is the one to believe. A 4-unit bootstrap
distribution is lumpy enough that its tails are an artifact of the resampling grid. That
disagreement is precisely why both are reported.

## The one result that is not noise: reaching early for TE or QB is costly

`elite_te_early` and `qb_early` are negative in **4 of 4 seasons at all three sigmas — 12 of 12
cells** — with margins of −64 to −115 points, roughly 3–5% of a roster total. The sign test
still cannot go below 0.125 on four seasons, so this is not *significant*; but the direction is
perfectly consistent, the magnitude is large, and it is stable across the entire opponent-noise
sweep, which is the sensitivity check that disqualifies assumption-driven results.

It also corroborates two independent measurements:

| Source | Finding |
|---|---|
| #45 direct measurement | Elite-TE construction cost **−226.4 pts** vs plain BPA |
| ADR-016 slot values | RB1 168.5 > WR1 153.2 > **QB1 114.1 > TE1 73.1** |
| **This simulation** | elite_te_early **−96.1**, qb_early **−115.4** |

Three different instruments, same direction.

**A correction to an inference made earlier today.** Before this ran, the registry note argued
from ADR-016's slot values that TE-before-QB guidance was backwards *because* the QB1 slot
(114.1) outvalues the TE1 slot (73.1). The simulator measures the decision directly and does
not support the implied conclusion that QB-early is therefore preferable: `qb_early` is the
**worst** arm tested, consistently worse than `elite_te_early` at every sigma. Slot value over
replacement and the opportunity cost of *reaching* are different quantities — QBs cluster
tightly (#46), so waiting recovers most of the QB1 slot value, whereas the early pick spent
cannot be recovered. The correct reading is that **both early reaches are costly, and QB-early
is the more costly of the two.**

## Simulation error is not the binding constraint

Simulation SE is ~8 points across every arm, against season-to-season margin swings of ±100
points and CI widths of ±50–100. **More simulated drafts would not narrow any conclusion here.**
Only more seasons would, and consensus coverage caps that at five (four after the holdout).
Convergence check at the default sigma: mean 2118.6 with sim SE 9.82 at n=400, already flat.

## Sigma sensitivity behaved as designed

Absolute values move sharply with the opponent-noise assumption — BPA scores 2108.8 at sigma=5
and 2279.1 at sigma=20, and P(top-4) climbs from 0.417 to 0.737, because sigma controls how
badly the opponents draft. **Only the relative ordering is meaningful**, and the ordering is
stable: elite_te_early and qb_early are last at every sigma; zero_rb and balanced are positive
at every sigma; hero_rb straddles zero at every sigma. No conclusion here rests on the choice
of sigma, which was the point of pre-registering the sweep.

## What this does and does not license

- **Answers #44:** Hero RB is null.
- **Does not** establish Zero RB or balanced drafting as superior — both are suggestive, neither
  is significant, and the data cannot make them so.
- **Strongly suggests** not reaching for a TE or a QB in the first three rounds, on consistency
  and magnitude rather than on a p-value.
- **Assumption-bound:** opponents do not adapt, lineups are set with perfect hindsight, and
  there is no in-season management. All three flatter deep, top-heavy-averse rosters and none is
  calibrated. See the `src/draft_sim.py` docstring.
