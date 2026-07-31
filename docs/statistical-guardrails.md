# Statistical Guardrails

This is the methodology reference for every backtest and ranking model in this project. It expands
`CLAUDE.md` §6 into concrete, checkable procedures. Read this before running any backtest, and
check your design against it before reporting any result.

**Standing rule: a result reported without going through this checklist is not a result — it's an
unverified claim.** Every backtest report must state, explicitly, which of the checks below were
applied and how.

---

## 0. The core problem, stated precisely

We have roughly 250–300 fantasy-relevant players per season, observed across a small number of
seasons (currently 5, growing over time), being evaluated against ~70 candidate factors. This
combination — small N, large candidate-factor space, and strong autocorrelation (the same players
recur year over year) — is close to a worst-case setup for spurious findings. Every guardrail below
exists because of this specific shape of problem, not as generic statistical hygiene.

**The sample size that matters is *seasons*, not player-weeks.** A season with 300 players and 17
weeks is not 5,100 independent data points — player-weeks within a season and within a player are
correlated. Treat effective N as closer to 5 (seasons) than 5,100 (player-weeks) when reasoning
about how much any single finding should be trusted.

---

## 1. Look-ahead bias

**Definition:** using information in a backtest that would not have been available at decision
time.

**Why it's the primary threat here specifically:** nflverse and most public data hand you an
entire season at once. Nothing about the data format prevents you from accidentally using Week 17
data to inform a Week 1 decision. This is the single easiest way to produce a beautiful, false
result.

**Enforcement (structural, not procedural):**
- Every data query for a ranking pass must take a `cutoff_date` parameter.
- The data-access layer must reject — not just discourage — any read of rows dated after
  `cutoff_date`. This is a hard constraint at the code level, enforced by tests, not a convention
  documented and hoped for.
- Injury designations, depth charts, ADP, and odds must be pulled by `as_of_date` matched to a
  realistic pre-decision date — never their current or final values.
- Any code path that computes a feature using full-season aggregates (e.g., "season total target
  share") for a decision made mid-season is a bug.

**Test for this in code review:** for any ranking pass dated `T`, print the max `as_of_date` /
`game_date` across every row the pass touched. It must be ≤ `T`. Automate this as an assertion,
not a manual check.

**Common disguised forms to watch for:**
- Using a player's *final* injury status to decide whether to draft them, instead of their
  pre-draft status.
- Using a stat that's partially a function of full-season role (e.g., "primary starter" flags
  assigned retroactively).
- Cross-validation folds that shuffle player-weeks randomly instead of splitting by season —
  this leaks future weeks into training even within a single split.

---

## 2. Survivorship bias

**Definition:** defining the analysis population using information that depends on the outcome
being studied.

**Concretely here:** if the player universe for season N is built from "players who scored fantasy
points that year," every bust, injury-out player, and non-factor is silently excluded, and measured
performance is inflated because failure was defined out of the sample.

**Correct approach:** define the universe *before* the season, using only pre-season information —
e.g., all players inside a pre-season ADP threshold (say, top 200–250), or all players on a Week 1
active roster. Track this list before pulling any outcome data.

**Check:** for any backtest, confirm the player list was frozen using only pre-`cutoff_date`
information, and that it includes players who later busted, got injured, or were cut. A player
list with zero "failures" in it is a warning sign, not a clean dataset.

---

## 3. Overfitting and multiple comparisons

**The concrete risk:** testing ~70 factors at a conventional significance threshold (α = 0.05)
will produce roughly 3–4 "significant" findings by chance alone, even if none of the factors have
real predictive value. Treating any single factor's apparent significance as a finding without
correction is a direct path to a model built on noise.

**Required procedure:**
1. **Split before testing, not after.** Reserve at least one full season as a holdout before any
   factor is evaluated. No factor selection, weighting, or tuning may touch the holdout season.
   Touch it once, at the end, to report the final number.
2. **Correct for multiple comparisons.** Apply a false discovery rate procedure
   (Benjamini–Hochberg) across the full set of factors tested in a given pass, not just the ones
   that "looked interesting." Testing 70 factors and reporting the 5 that passed p<0.05 uncorrected
   is the textbook error this project must not make.
3. **Prefer simple models over complex ones by default.** Start with weighted linear/regression
   approaches with few parameters. Every additional parameter must earn its place by improving
   *holdout* performance, not training fit. "We should use machine learning" is not, by itself, a
   finding — it's a hypothesis that a simple model is insufficient, and that hypothesis needs its
   own test.
4. **Pre-register the test before running it**, especially for folk-wisdom factors (e.g., "second-
   year WR leap," "third-year TE breakout"). Write down the exact metric and threshold that would
   count as confirmation *before* looking at the holdout result. This prevents post-hoc
   rationalization of a null or weak result into a positive one.
5. **Report effect size, not just significance.** A statistically significant factor with a tiny
   effect size (e.g., 0.1 points/game) is not worth adding model complexity for. State the expected
   points impact in absolute terms alongside any p-value.

**Autocorrelation correction:** because the same players recur across seasons, standard errors
computed as if player-seasons were independent will be too small, inflating apparent significance.
Cluster standard errors by player when testing any factor across multiple seasons.

---

## 4. Non-stationarity / regime change

**Definition:** the assumption that historical relationships hold going forward is unsafe when the
underlying system changes — rule changes, scheme shifts, personnel-package trends.

**Required procedure:**
- **How far back to weight is an empirical question, not an assumption.** For each position, test
  whether adding older seasons improves or degrades *holdout* performance. Do not default to
  "5 years, equal weight" without checking.
- Model trend *direction* as an explicit feature (e.g., 3-year rolling slope of usage) separate
  from trend *level* (3-year average). A player whose role is declining and a player whose role is
  flat can have identical 3-year averages and very different true value going forward.
- Flag any factor derived from FTN charting data (2022+) as having a maximum 4-season sample.
  Do not let a 4-season factor carry equal weight to a 20-season factor in a combined model without
  explicit justification.

**Check:** for any factor added to the ranking model, state its effective sample size in seasons
and whether that sample spans any known rule or scheme discontinuities.

---

## 5. Baseline comparison (the honesty mechanism)

**Rule:** no ranking version's performance may be reported without a baseline comparison. The
baseline comparison *is* the result — a raw accuracy number in isolation is not.

**Required baselines for every backtest — aligned to `CLAUDE.md` §6.5, corrected 2026-07-31.**
This section previously named a different, three-item list (BPA-via-own-VBD, consensus market ADP,
FantasyPros/expert consensus) than `CLAUDE.md` §6.5 did, and the two were used interchangeably
across a full factor-testing campaign before the founder ruled on it (`CLAUDE.md` §6.5, "both
baselines required — founder's ruling, 2026-07-31"). The canonical list is now `CLAUDE.md`'s:

1. **Market ADP** — what drafters actually did.
2. **Expert consensus** — what analysts said (FantasyPros ECR).
3. Prior-season fantasy points, ranked.
4. Simple positional-tier heuristic.

**Baselines 1 and 2 are both required, not either/or** — they are different crowds (empirical
drafter behaviour vs. analyst opinion), and a version can beat one and lose to the other. Report
which one, if either, was beaten; do not report the flattering half.

**Best Player Available (BPA) via our own VBD/replacement levels, this section's former baseline
#1, is not one of `CLAUDE.md`'s four** and is not a market or expert baseline at all — it scores a
candidate ranking against a value computed from the candidate's own scoring engine, which is a
useful internal sanity check but not an external honesty check. Retained here as a *supplementary*
comparison where useful, never as a substitute for baselines 1–4 above, and never reported as if it
were one of the required four.

**Interpretation rule:** if a candidate ranking does not beat baselines 1 and 2 by a margin that
exceeds the uncertainty in the estimate (see §7, confidence intervals), the honest conclusion is
that the candidate has no demonstrated edge. Report this plainly. A negative or null result is a
legitimate, useful output of this project — it is not a failure to hide or re-run until it looks
better.

**Scope — this section binds a *ranking version*, same as `CLAUDE.md` §6.5.** A single feature or
factor tested inside one component of an unshipped model is not a ranking version and this section
does not bind it; labelling a single-arm-vs-primary-model comparison as "the consensus bar" is a
misapplication, not a stricter reading. See `CLAUDE.md` §6.5's own scope paragraph and
`docs/adr-drafts/ADR-DRAFT-edge-vs-absolute-quality.md`.

---

## 6. Evaluation metrics

**Primary metric:** rank correlation (Spearman) between predicted rank and actual season finish,
computed within position group (comparing QB ranks to QB outcomes, not across positions).

**This is a proxy, not the target.** The actual decision-relevant question is whether a ranking
produces better *rosters* under real draft constraints (snake order, positional runs, roster
slots) — not just a better *ordered list* in isolation. Two rankings can have similar rank
correlation and produce very different roster outcomes once draft dynamics are simulated.

**Required secondary metrics:**
- Points scored by the resulting roster vs. baseline rosters (BPA, ADP-drafted, expert-consensus-
  drafted), under an actual draft simulation, not just list comparison.
- Hit rate at the top of the ranking specifically (top-12, top-24) — this matters more than
  aggregate correlation because early-round mistakes are costlier than late-round ones.

**Move toward draft-simulation-based evaluation as the harness matures.** List-comparison metrics
are a legitimate Phase 1 shortcut, not a permanent evaluation method.

---

## 7. Uncertainty quantification

**Every reported metric needs a confidence interval, not just a point estimate.** With ~5 seasons
of holdout data, point estimates alone are close to meaningless — the same underlying skill level
could produce a wide range of observed results by chance.

**Method:** bootstrap resampling at the season level (not the player-week level, to respect
autocorrelation) to generate confidence intervals on any backtest metric (correlation, points
above baseline, etc.).

**Reporting standard:** "beat BPA by 4.2 points/week [95% CI: -1.1, 9.5]" is a correct report.
"beat BPA by 4.2 points/week" is not — it implies certainty the sample doesn't support.

---

## 8. Pre-mortem checklist (run before reporting any result)

Before reporting a backtest result, answer these explicitly:

1. Did any data used in the ranking pass postdate the ranking cutoff? (Verify programmatically,
   not by inspection.)
2. Was the player universe defined before or after outcomes were known?
3. Was this factor/configuration tested against a holdout that was untouched during development?
4. If multiple factors or configurations were tested, was a multiple-comparisons correction
   applied?
5. Does the result include a confidence interval, or just a point estimate?
6. Does the result include the baselines `CLAUDE.md` §6.5 requires — market ADP **and** expert
   consensus, both, not either? (BPA-via-own-VBD is a useful supplementary check, per §5 above,
   but does not substitute for either required baseline.)
7. If the result looks unusually good, what is the most likely leakage explanation, and has it
   been ruled out? **An unusually strong result is evidence of a bug more often than it is evidence
   of a good model.** Treat surprising positive results with more scrutiny, not less.

**If any answer is "no" or "unsure," the result is not ready to report.**

---

## 9. What this looks like in practice for the current backtest queue

- Tests #44, #45, #46 (Hero RB, Elite TE, QB spread): each needs a pre-registered hypothesis and
  metric before running, a holdout season untouched during any tuning, and both required baselines
  (market ADP and expert consensus, per `CLAUDE.md` §6.5).
- Test #53 (WR/TE breakout patterns): explicitly named in `test-registry.md` as a multiple-
  comparisons trap. Pre-registration is mandatory here, not optional.
- Tier 1 tests using FTN data (#16, #17, #31, #32): report sample size (4 seasons) alongside any
  finding, and do not let these factors dominate a combined model without justification.
- The null hypothesis (BPA) is not a formality — given the 2025 roster's 4th-in-scoring /
  6th-in-standings outcome, there's a real, live possibility that roster construction was not the
  binding constraint. Treat "the model loses to BPA" as a plausible and useful outcome, not a bug
  to fix by re-running.

---

## 10. Who enforces this

Per `CLAUDE.md` §8: the **Red-team** agent's mandate explicitly includes checking every backtest
against this document before it is accepted. Red-team has standing authority to block a result that
skips any of the checks in §8 above. The **Statistician** agent designs the methodology up front
using this document; Red-team verifies compliance after the fact. These are deliberately separate
roles — the person who designs a test should not be the sole check on whether it was executed
honestly.

---

## 11. Reproducibility is a property you must demonstrate, not declare

Added 2026-07-25 after ADR-028.

§7 already required seeded RNG. That requirement was satisfied *in letter* while being false in
practice for months: seeds were built from `abs(hash(name)) % 1000`, and Python salts string
hashing per process, so every run used different seeds while printing the same `seed=` value.
The same simulation arm reported −92.9 and −98.6 with no code change between them.

**Rules, all of them cheap:**

1. **Never derive a seed from builtin `hash()`.** It is randomised per process for `str` and
   `bytes`. Use `zlib.crc32` or `hashlib` (`config.stable_offset`). A static test enforces this.
2. **A recorded seed must fully determine the output.** If any other varying input feeds the
   RNG, the recorded seed is misleading — worse than recording nothing, because it invites
   trust.
3. **Prove it by re-running.** Determinism must be tested by executing the code twice *in
   separate processes* and comparing. A same-process check passes while this whole class of bug
   is live.
4. **Two numbers for the same quantity are an incident, not a rounding difference.** Stop and
   find the cause before either is used. Both ADR-025 and ADR-028 were caught this way, and in
   both the conclusion survived while the reported precision did not.
5. **Quantify the noise floor before quoting a point estimate.** Re-run across several seeds
   and report the spread. If the seed-induced range is comparable to the effect being claimed,
   the effect is not measurable at that resolution — say so instead of quoting a decimal.
