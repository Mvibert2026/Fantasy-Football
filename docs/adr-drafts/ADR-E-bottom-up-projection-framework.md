# ADR-E — Bottom-up projection framework

**Path:** `docs/adr/ADR-E-bottom-up-projection-framework.md`
**Status:** Proposed — draft for `backend` feasibility review
**Date:** 2026-07-27
**Owner:** Strategist (spec) / Backend (feasibility + execution)
**Thread:** 048 (methodology half). Data half is thread 046 (`data-ops`).
**Depends on:** ADR-C (pre-registration), ADR-016 (log-linear rank→points curve), PR-002 (spike-week null), `src/regimes.py`, `src/holdout.py`
**Amended:** E-A1 (2026-07-27, below) — S1's output becomes a week-indexed vector; N3 week-leverage weights specified; sonnet work order in §A1.7

---

## Context

The board's `projected_points` is currently `E[our_points | position, consensus positional rank]`
(ADR-017), fitted per position as `points ~ alpha + beta*ln(rank)` (ADR-016). Its reported R² is
**0.158–0.266 by position, residual SD 46–91 points**. Thread 048 asks for a bottom-up replacement:
project the inputs, not the output.

Three facts constrain the design before any modelling choice is made.

1. **Opportunity persists; efficiency mostly does not.** This project has its own version of that
   finding, and it is stronger evidence than the general claim because it was pre-registered and run
   here: PR-002 / test-registry #38b tested whether volume-adjusted bonus-clearance is a stable player
   trait across 26 seasons and returned **null**. The operational consequence is already written into
   `assistant-context.md`: *project the yards; the bonuses follow automatically.* A stage that predicts
   per-player touchdown rate or per-player bonus propensity confidently has learned noise, and this ADR
   forbids one.

2. **The two claims in play have different sample sizes and must never be merged.**
   *Accuracy* — "is the projection close to what happened" — resamples at the season level over
   1999–2024 and is measurable now. *Beating consensus* — "is it better than the market" — needs
   consensus history, which exists only 2021–2025 with 2025 sealed, so n=4 and the minimum attainable
   sign-test p is 0.0625 before any correction. §7 of this ADR fixes the language that keeps them
   apart.

3. **"26 seasons" is true only of the box-score feature tier.** Snap counts, air yards, NGS-derived
   route data and depth charts each start later, and targets/air yards are unreliable 2003–2008
   (present but effectively zero). The effective n for a model is set by its *scarcest* feature, not by
   the database's earliest row. §4.3 makes this structural rather than a caveat.

---

## Decision

### 1. Two-stage architecture, with a deliberately humble second stage

The projection is a pipeline of three steps, of which only the first two are estimated. The third is
arithmetic.

| Stage | Target | Estimator | Ambition |
|---|---|---|---|
| **S1 — Volume** | Per-game opportunity: `targets/game`, `carries/game`, `pass_attempts/game`, plus `games_played` | Fitted, feature-rich, this is where the modelling effort goes | High. Usage is the persistent thing; this is the stage allowed to be good. |
| **S2 — Efficiency** | `yards/target`, `yards/carry`, `yards/attempt`, `catch rate`, `TD/opportunity` | **Shrinkage estimator only.** Each player's efficiency is his prior-seasons value shrunk toward a position × regime × volume-tier mean, with the shrinkage weight estimated from the reliability of that statistic — not from a feature-rich regression | Deliberately low. See S2 rules below. |
| **S3 — Points** | Fantasy points under this league's rules, incl. yardage bonuses | `src/scoring.py`, deterministic given S1 × S2 | None. It is a scoring function, not a model. |

**S2 rules, binding:**

- **No per-player TD-rate model.** TD/opportunity is estimated as `position × regime × (goal-line or
  red-zone opportunity share)` — that is, TD rate is a function of *where* the opportunities occur,
  which is a volume measure, not of who the player is. Any per-player residual term in TD rate is
  prohibited by PR-002's null.
- **Shrinkage weight is estimated, its ceiling is capped.** `w_player = n_obs / (n_obs + k)` with `k`
  fitted per statistic *inside each training fold* (§3.2). Pre-committed cap: `w_player ≤ 0.60` for
  yards-per-opportunity and `w_player ≤ 0.20` for TD rate. If a fold's fitted `k` implies a weight
  above the cap, the cap binds and the event is logged. The cap exists so that a fold with an unusual
  draw cannot quietly turn S2 into a player-level efficiency model.
- **Bonus expectation is computed, not modelled.** Per-game yardage bonuses (+1 @100, +1.5 @150,
  +2 @200 rushing/receiving; +1 @300, +1.5 @350, +2 @400 passing) are evaluated by integrating the
  projected *per-game distribution*, with the game-level dispersion taken at the **position × volume-tier**
  level, never per player. This is the direct operational form of the PR-002 null: shape is a function
  of volume, not of identity. Dropping bonuses is also prohibited (CLAUDE.md §7).

**Why not project points directly.** A direct point projection lets a high-variance, low-persistence
component (touchdowns) borrow apparent predictability from a high-persistence component (volume),
because the fit optimises the sum. Separating them makes the humility auditable: you can read off how
much of the projection is the stage we believe and how much is the stage we do not.

### 2. Target variable, stated exactly

- **Primary confirmatory target:** season fantasy points under this league's scoring, per player-season,
  within position.
- **Required decomposition, reported alongside and never instead:** `season_points = games_played ×
  points_per_game_played`. R² must be reported for all three of season points, points per game played,
  and games played. A model can look strong on season points purely by predicting that players who
  played 17 games last year will play 17 again. **If ΔR² over baseline on season points is not
  accompanied by ΔR² on points-per-game-played of the same sign, the finding is a games-played artefact
  and must be reported as one.**
- **Games played is projected from a base rate** (position × age band × prior-season games, no
  player-specific injury-proneness term) unless a separately pre-registered test establishes that a
  player-level term beats the base rate out of sample. Injury-proneness is the classic factor that
  survives in-sample and dies out of sample; it does not get a free pass into the model.
- **Universe (survivorship control, guardrails §2):** the player-season universe for target season N is
  frozen using pre-season-N information only — the same draft-relevant depths ADR-016 already declares
  (QB 20 / RB 45 / WR 60 / TE 20 by prior-season positional finish, plus rookies inside the pre-season
  consensus depth where consensus exists). Players who then busted, got hurt or never played stay in
  with their real outcome, including zero. A fold whose evaluation set contains no zero-point seasons
  is a bug report, not a clean dataset.

### 3. Validation

#### 3.1 Cross-validation: embargoed leave-one-season-out

**Scheme:** leave-one-season-out over the eligible seasons (§4.3), with a **one-season embargo on each
side**: when season N is the test fold, seasons N−1 and N+1 are excluded from training.

**Why the season is the resampling unit.** This is the same argument that governs every other decision
in this project and it is not restated for consistency's sake — it is the reason random K-fold is wrong
here. A season is a block of shared conditions: one rule set, one league-wide pass rate, one scoring
environment, one weather year, and largely one set of players. Random player-season folds leak on both
axes simultaneously (guardrails §1 names shuffled folds explicitly). Player-grouped folds fix the
player axis and leave the league-condition axis wide open.

**Why the embargo.** Features for season N are built from season N−1 outcomes. If season N−1 is in the
training set, its *targets* are the same numbers as the test fold's *features*. For a two-parameter
linear model this leak is small; for anything with more capacity it is not, and the framework is
supposed to survive the model getting more capacious. The embargo costs two folds' worth of training
data and removes the channel entirely.

**Pre-registered diagnostic:** report both embargoed and un-embargoed LOSO. The embargoed number is the
headline. **If un-embargoed R² exceeds embargoed R² by more than 0.03 in any position, treat it as a
leakage signal and audit before reporting either number.** The size of that gap is itself information
about how much the model is memorising adjacent seasons.

#### 3.2 Leak control on feature selection — the classic error, and how it is prevented

Selecting features on the full dataset and then cross-validating the selected set is the single most
common way a paper-clean CV produces a fantasy that dies in production. The rule here is mechanical:

> **Everything estimated from data is estimated inside the training fold. No exceptions, and the list
> of "everything" is enumerated, because the leaks come from the items people forget are estimated.**

Refit per fold: feature screening and any univariate filter · standardisation means and SDs ·
winsorisation limits · imputation values · the S2 shrinkage constants `k` · the regime break locations
(§5) · the training-window length · any hyperparameter · the log/sqrt transform choices ·
the volume-tier boundaries used for S2 pooling and bonus dispersion.

Supporting rules:

1. **The candidate feature list is declared in the pre-registration before any fold runs.** Screening
   chooses *within* that declared list, per fold. Adding a feature after seeing a fold result creates a
   new registration and the old result is exploratory.
2. **Selection frequency is a diagnostic, never a selector.** Reporting "feature X was chosen in 22 of
   24 folds" is legitimate. Building a fixed feature set from those frequencies and then re-scoring it
   on the *same* folds is not — that number is contaminated by every fold. If a fixed final feature set
   is wanted, it is frozen from training folds and read out **once**, on the sealed season (§3.3) or
   prospectively on 2026.
3. **The pipeline is one object.** Feasibility note for backend: implement S1+S2 as a single fit/predict
   pipeline object that receives only the training seasons. If any step can see a dataframe containing
   the test season, the guarantee is procedural rather than structural and guardrails §1 requires
   structural.
4. **Automated assertion, per fold:** `max(as_of_date, game_season)` across every row touched while
   building the test fold's features must be `< ` the test season's Week 1. Assert it; do not inspect it.
5. **Identity check:** confirm no player-season appears in both train and test through an `mfl_id` /
   `gsis_id` alias. The identity hub has a quarantine for a reason; a duplicated row under two ids is a
   silent leak that looks like skill.

#### 3.3 Holdout — and whether this framework needs another one

**2025 stays sealed.** No fold, no screening, no diagnostic, no plot. `holdout.load_season(2025,
prereg_id)` with the signed unseal log is the only path, and this framework does not unseal it during
development.

**Does the framework need an *additional* retrospective holdout carved out of 1999–2024? No.** The
failure mode an extra holdout would guard against is real — LOSO gets consulted repeatedly during
development and therefore becomes an optimistically-biased *selection* statistic — but carving out
another block costs modern, regime-relevant training seasons, which are the scarcest thing here. Two
cheaper controls address the same failure:

1. **A logged configuration budget.** The number of distinct model configurations scored against LOSO
   is capped at **20** and every one is written to `test_run_log.jsonl` with its prereg id and content
   hash, *including the ones that looked bad*. Exceeding 20 does not void the work; it converts the
   LOSO estimate from confirmatory to exploratory and requires the sealed read to carry the
   confirmatory claim alone. The count being visible is what makes the optimism boundable instead of
   unknown.
2. **One additional holdout that costs zero training data: 2026, prospectively.** Register the 2026
   projections, in full, per player, before Week 1 of the 2026 season, hashed and committed. Score them
   after the season. A prospective registration cannot leak, because the outcome does not exist yet.
   This is the strongest validation available to this project and it is free; the only cost is
   remembering to do it before September. **Pre-register it now, in the same family manifest.**

**Honest statement about the sealed 2025 read, made before running it:** it is one season. It can
*falsify* — a model that collapses on 2025 after looking good across 24 folds is telling us something
real. It cannot *confirm* at any useful power, because a season-level effect estimated from one season
has no season-level interval at all. The per-player paired comparison within 2025 will have hundreds of
rows and will therefore produce a narrow-looking interval; that interval describes variation across
players within one league-year, not across league-years, and **must not be presented as a confidence
interval on the model's accuracy.**

### 4. Features, and the windows they are available in

#### 4.1 The declared candidate list

All features are computed from seasons ≤ N−1 plus pre-season-N information only.

| Group | Features | Why it is in the list |
|---|---|---|
| **Usage (S1 core)** | target share, carry share, snap share, route participation (or documented proxy, flagged as proxied), team pass attempts/game, team plays/game | The persistent quantity. This is the model. |
| **Usage shape** | aDOT, air-yards share, WOPR, red-zone and goal-line opportunity share, inside-5 carry share | Distinguishes equal volume of unequal quality; goal-line share is how TD expectation enters legitimately (§1) |
| **Trend, not just level** | 3-season rolling slope of target/carry/snap share, separate from the 3-season mean | Guardrails §4: a declining role and a flat role can have identical means and different futures |
| **Context** | prior-season team pace, PROE, prior-season team pass rate, **coach/coordinator continuity flag keyed on `coach_id`** | CLAUDE.md schema principle: tendency follows the person. A team whose OC left is not the same offence. |
| **Situation** | age and age² within position, seasons of experience, prior-season games played | Age curves are real and cheap; they are also where overfitting hides, so they are declared, not discovered |
| **Market (restricted use)** | pre-season consensus rank, where it exists (2021+) | **Only permitted in the baseline arm and in the explicitly-labelled hybrid arm.** The bottom-up model's confirmatory arm must not consume consensus rank, or "bottom-up beats consensus-derived" becomes circular. |
| **Vegas (optional)** | pre-season team win total, implied team total, at a pre-draft `as_of_date` | Optional because history and licensing are uncertain; if unavailable, it is absent, not imputed |

**Not in the list, and why:** depth-chart role for 2026 — the source ends at 2024. It may be used as a
feature for seasons ≤ 2024 in a separately-labelled arm; it **may not be extrapolated to 2026**, and a
model that requires it cannot be the shipping model. Producing a 2026 depth-chart guess to keep a
feature alive is inventing data.

#### 4.2 Refusals inside the feature set

- **No per-player efficiency residual as a feature** (yards over expected, TD over expected, catch rate
  over expected, "spike-week-ness"). PR-002 tested the closest available version of this on 26 seasons
  and it returned null. Adding it back as a predictor requires overturning that result with a new
  pre-registration, not a hunch.
- **No opponent- or schedule-strength feature derived from target-season results.** Strength of schedule
  computed from season-N outcomes is a look-ahead feature wearing a respectable name. Prior-season
  opponent quality is admissible; season-N is not.
- **No latent "team philosophy" or "coaching intent" variable.** Coach continuity is an observable flag.
  Inferring what a staff *intends* to do from a small number of observed play calls is the same class of
  claim as inferring an opponent's draft strategy from their opening picks, and it is refused on the same
  grounds: the arithmetic of who was on the field is observable, the intent behind it is not identifiable
  at this n.

#### 4.3 Feature availability defines the fold set — structurally

Each feature carries a declared `first_reliable_season`. Two rules follow:

1. **A model's eligible fold set is the intersection of its features' availability windows.** A model
   using snap share does not get 26 folds; it gets the seasons where snap share exists. That number is
   reported everywhere the model's accuracy is reported. *"Validated on 26 seasons"* applied to a
   13-season model is a false statement about power, and it is the kind of statement this project has
   already had to retract elsewhere.
2. **No imputation across an availability boundary.** Targets and air yards 2003–2008 are refused, not
   zero-filled — `regimes.py` already models a season gap correctly rather than pretending the series is
   contiguous, and the same discipline applies here. An availability boundary is a regime boundary in
   the data-generating process, not a missing-at-random gap.

**Consequence to accept in advance:** this will likely produce two models — a long-window box-score model
(n large, features weak) and a short-window usage model (n small, features strong) — and the choice
between them is an empirical comparison on the *common* window, not a preference. Comparing a 13-season
model's R² to a 26-season model's R² across different fold sets is not a comparison.

### 5. Regime — extend `src/regimes.py`, do not duplicate it

**What already exists and must not be rebuilt.** `src/regimes.py` implements exactly the two things
thread 048 asks for, at the league level: sup-Wald (Quandt–Andrews) unknown-breakpoint detection with
binary segmentation for multiple breaks, moving-block residual bootstrap p-values, trailing-window trend
slopes (5 and 10) reported *separately* from whole-regime slopes, era similarity, and a poolability
report. **Pass rate, neutral pass rate, plays per game, and both target-concentration measures
(`rb_carry_top30_share`, `wr_target_top45_share`) are already in `METRICS`.** The changepoint half of the
ask is built. Writing a second detector would produce a second set of break dates that disagrees with the
first, which is worse than having none.

**What to add, as an extension:**

- **`rolling_coefficient_path(...)`** — fit the S1 volume model on trailing windows of length
  W ∈ {5, 8, 12, all} ending at each season, and return the coefficient path per feature with
  season-block bootstrap bands. This is the founder's "zoom in and out," and coefficient movement across
  windows is the regime signal at the *model* level rather than the league-aggregate level.
- **Fold-local break detection.** `regimes.detect_breaks` already accepts arbitrary season/value
  sequences, so the extension is a call-site discipline, not new code: **when season N is the test fold,
  break detection is re-run on the truncated series (seasons ≤ N−2, per the embargo).** Using breaks
  detected over all 27 seasons to define the training window for a test fold is a look-ahead leak — mild,
  but exactly the kind §3.2 enumerates. Cheap to do correctly; do it.
- **Additional metrics if and only if needed** — appended to `METRICS`, not forked into a new module.

**Decision rule on regime — stated before running, because this is where "zoom until it looks right"
would otherwise happen:**

> **Coefficient-path instability and detected breaks are diagnostics. They generate the candidate
> training windows. They do not select one.** The only decision-grade evidence about how far back to pool
> is embargoed-LOSO out-of-sample performance under competing window definitions, with the window chosen
> **inside each training fold**. A break that is visible but does not improve out-of-sample performance
> when respected is not actionable, and saying so is a result.

Carry forward `regimes.py`'s own power warning verbatim: n=27 annual observations is a small sample for
structural-break detection, non-detection is not evidence of stability, and detected breaks are
suggestive boundaries rather than facts. **Model structure is not gated on break significance.**

### 6. Recency weighting — a hypothesis with a pre-registered decision rule

Two different questions get conflated under one word. They are tested separately.

**(i) Season-level recency** — how to weight seasons N−1, N−2, N−3 in feature construction.
**(ii) Within-season recency** — whether late-season weeks deserve more weight than early ones.

Question (ii) carries a specific contamination argument that must be tested rather than assumed away:
eliminated teams rest starters, playoff-bound teams manage snaps, weather suppresses passing, and Weeks
15–18 are also when fantasy rosters and real depth charts diverge most. Late-season data is not simply
"more recent" — it is drawn from a partly different process.

**Arms, fixed before any run:**

| Family | Arm | Definition |
|---|---|---|
| Within-season | **A0 (default)** | Uniform across all games played |
| | A1 | Final 8 games weighted 2× |
| | A2 | Exponential decay by week, half-life 8 games |
| | A3 | Uniform, **excluding Weeks 17–18** |
| | A4 | Final 8 games weighted 2×, excluding Weeks 17–18 |
| Season-level | **B0 (default)** | 3 prior seasons, equal weight |
| | B1 | Prior season only |
| | B2 | Exponential, half-life 1.5 seasons |
| | B3 | Window from fold-local regime break (§5) |

**Not fully crossed.** Within-season arms are tested at B0; season-level arms at A0. That is 5 + 4 = 9
arms × 4 positions = **m = 36 confirmatory comparisons**, declared in the family manifest
`F-BOTTOMUP-RECENCY` before the first run. The fully-crossed 20-cell grid may be run, but it is
registered as **exploratory** and never enters the FDR denominator or a shipping decision.

**Metric:** embargoed-LOSO out-of-sample R² on the S1 volume targets *and* on end-to-end season points,
per position.

**Decision rule, pre-committed:**

> Adopt a non-default arm only if it beats its family's default on the primary metric in **≥ 70% of LOSO
> folds** *and* the season-level bootstrap 95% CI on the paired ΔR² excludes 0 after Benjamini–Hochberg
> across all m = 36. Otherwise ship the default. Ties and near-misses ship the default; "directionally
> better" is not a criterion.

**The interpretation rule that matters more than the result:** if A1 beats A0 *and* A3/A4 beat A1, the
gain came from removing contaminated weeks, not from recency, and it is reported that way. Those are
different findings with different implications, and the recency framing is the one that would be
repeated back wrongly.

### 7. Baselines, and the language that separates accuracy from edge

#### 7.1 The baseline comparison is not what it looks like

The 16–27% figure is an **in-sample** fit of a two-parameter log-linear curve on consensus rank, over
**5 seasons (2021–2025)**, of which 2025 is sealed. Three mismatches make a naive comparison invalid:

- **Estimation basis:** in-sample R² vs. our out-of-sample LOSO R². In-sample flatters the baseline, so
  this direction makes our bar *harder* — but the comparison is still not a comparison.
- **Season window:** 4 usable seasons vs. up to 24. Different seasons, different difficulty.
- **Predictor availability:** consensus rank does not exist before 2021 at all.

**Therefore: the baseline is refit under the identical protocol.** Same embargoed-LOSO scheme, same
player universe, same target, same per-position split, same seasons — paired by player-season. The
headline is the paired difference, with a season-level bootstrap CI, not two R² numbers side by side.
Quoting 0.158–0.266 as the bar without refitting it under our own protocol would be an unfair comparison
in our own favour, and it would be the first thing an honest reviewer struck out.

#### 7.2 Which baseline carries the decision

| Baseline | Seasons available | Role |
|---|---|---|
| **Prior-season points, ranked** (CLAUDE.md §6.5 #2) | Full window | **Decision-grade.** Carries the shipping decision. |
| **Positional-mean / tier heuristic** (§6.5 #3) | Full window | **Decision-grade.** The floor a model must clear to be doing anything. |
| **ADR-016 consensus-rank curve, refit** (§6.5 #1) | 2021–2024, n=4 | **Descriptive only.** Reported with the 4 paired season differences as raw numbers, **no p-value, no directional claim** — the same floor ADR-B already pre-committed to. |

That split is the whole point of thread 046's correction. The accuracy question has power; the
consensus question does not, and running it anyway with a p-value attached would manufacture exactly the
claim the project has repeatedly refused to make.

#### 7.3 Language constraints, binding on every artifact

**Permitted:** *"Out-of-sample (embargoed LOSO, N folds, seasons X–Y), the bottom-up projection explains
R² = a [95% CI b, c] of season-point variance at WR, versus R² = d [e, f] for the prior-season-points
baseline refit identically; paired ΔR² = g [h, i]."*

**Forbidden, in code comments, exports, the assistant, ADRs and status entries alike:**

- "beats the market" / "beats consensus" / "our edge over ADP" — from any accuracy result, ever.
- "more accurate than consensus" stated without the n=4 qualifier and without "on 2021–2024."
- Any implication that projection accuracy converts to draft outcome. It does not, automatically:
  accuracy gained outside the drafted depth converts to nothing, and converting accuracy into roster
  points requires the draft-simulation layer (ADR-F), not this ADR.

**The specific trap to name, because it is subtle:** beating the ADR-016 curve out-of-sample *is* an
accuracy comparison against a projection derived from consensus rank — it is not evidence of a draft-day
edge. Those two sentences are close enough that they will be collapsed by anyone summarising in a hurry.
If the distinction cannot be maintained in a given artifact, the consensus comparison is omitted from
that artifact rather than hedged.

### 8. The suspicious-R² thresholds, fixed before anything runs

Stated now so that a good result cannot retroactively define what "plausible" means.

| Quantity | Expected / plausible | **Audit trigger** | **Presumed-bug trigger** |
|---|---|---|---|
| End-to-end **season points**, per position, out-of-sample | 0.15 – 0.35 | **> 0.40** | **> 0.50** |
| End-to-end **points per game played**, per position | 0.25 – 0.50 | > 0.55 | > 0.65 |
| **Games played** | 0.05 – 0.20 | > 0.30 | > 0.40 |
| S1 **volume** targets (target share, carry share, snap share) | 0.45 – 0.70 | > 0.80 | > 0.88 |
| S2 **yards per opportunity** | 0.02 – 0.15 | > 0.25 | > 0.35 |
| S2 **TD per opportunity**, over the positional mean | ≈ 0.00 – 0.05 | **> 0.08** | **> 0.15** |

Two of these rows do most of the work. High R² on S1 volume is **expected and not alarming** — usage is
persistent, and a framework that treats every high number as suspicious will discard its own signal. High
R² on S2 touchdown rate is alarming at a much lower level, because 26 seasons of this project's own data
say that quantity is close to noise. A single global "suspicious" threshold would get both wrong.

**On crossing an audit trigger:** the result is not reported — internally or externally — until the audit
below is complete and signed in `test_run_log.jsonl`. On crossing a presumed-bug trigger, the working
assumption is a defect; the burden of proof is on the model, not on the sceptic.

**The audit, in the order I would actually run it** (first three catch the overwhelming majority):

1. **Target contamination.** Is any feature a deterministic or near-deterministic function of the target?
   Receiving yards in the features and PPR points in the target is the canonical version and it is easy to
   introduce through a helper that "just adds the box score."
2. **Cutoff violation.** Run the §3.2 rule-4 assertion on the exact fold that produced the number. Print
   the max season/`as_of_date` touched. Not by inspection — by assertion.
3. **Fold contamination.** Was any statistic in the §3.2 enumeration fitted outside the fold? Check the
   shrinkage constants and the standardisation means first; they are the two that get hoisted for speed.
4. **Universe contamination.** Was the evaluation set filtered on an outcome — dropped players with 0
   games, "qualified" players, players with a valid target share? Every one of those quietly deletes busts
   and inflates R² without touching a single line of modelling code.
5. **Duplicate rows / identity aliasing.** Same player-season in train and test under two ids.
6. **Metric definition.** Is R² computed against the correct mean — the *training* mean, out-of-sample, or
   the test-fold's own mean? The second is the correct one and the first is optimistic in the direction
   that would produce exactly this surprise.
7. **Only then:** consider that it is real. Even then, published professional season-level projections do
   not clear ~30–40%; a number well above that on this data has a much larger prior on defect than on
   discovery, and CLAUDE.md §8 requires escalating "a result that looks too good" to the founder rather
   than shipping it.

### 9. Pre-committed ship / no-ship rule

Registered in `F-BOTTOMUP-CORE` before the first confirmatory run, with m = 4 (one test per position).

**Adopt the bottom-up projection as the board's `projected_points` source, per position independently, iff
all four hold for that position:**

1. Embargoed-LOSO paired ΔR² over the **prior-season-points** baseline (refit identically) is positive in
   **≥ 75% of folds**, and the season-level bootstrap 95% CI on mean ΔR² excludes 0 after BH across the 4
   positions.
2. The same sign holds on **points per game played** (§2's artefact guard).
3. No audit trigger from §8 is outstanding.
4. The determinism check passes: two runs in **separate processes** from the recorded seed produce
   byte-identical outputs (guardrails §11 — this project has already shipped a "seeded" result that was
   not).

**Per-position adoption is deliberate.** If RB and WR clear and QB and TE do not, the honest outcome is a
mixed board — bottom-up where it earned its place, ADR-016 curve where it did not — with the source named
per row. Forcing a single global decision would either discard real signal or ship unearned signal, and
which of the two happened would be invisible.

**Shelve** if no position clears. The output is then: *"a bottom-up projection built from usage features
is not measurably more accurate out-of-sample than the existing rank-derived curve on N seasons."* That is
a publishable, useful finding about the ceiling of this data, and it is registered here in advance as an
acceptable result so that it cannot later be reframed as a failed sprint.

### 10. Registration, seeds, FDR

- Families declared before the first run: `F-BOTTOMUP-CORE` (m=4), `F-BOTTOMUP-RECENCY` (m=36),
  `F-BOTTOMUP-REGIME` (m = number of confirmatory window comparisons, fixed at registration).
  BH is applied within family, across the **declared** m — not across the subset that looked interesting.
- Every exploratory pass — coefficient paths, break plots, the fully-crossed recency grid, any "let's see
  what this looks like" — is registered as `mode: exploratory` under ADR-C, produces no p-value or CI in
  its artifact (ADR-C's CI check enforces this), and never enters an FDR denominator.
- One seed per registration, recorded in `frozen.seed`, derived via `config.stable_offset` and never from
  builtin `hash()`. Determinism proven by cross-process re-run, not asserted.
- Every reported metric carries a **season-level** bootstrap CI. Where n is small enough that the interval
  is degenerate, the existing `degenerate=True` flag surfaces it rather than a decimal implying precision.

---

## Consequences

- Backend gains a specified pipeline whose leak surface is enumerated rather than assumed away, at the
  cost of refitting more per fold than a naive implementation would.
- Fold counts will differ per model. Reporting becomes wordier and honest instead of terse and wrong.
- The 2026 prospective registration must be written before Week 1 or the cheapest holdout available is
  lost for a year. This is a calendar dependency, not a backlog item.
- One open decision goes to the founder: **D-023** in `decisions-needed.md` — whether a per-position
  mixed-source board is acceptable in the product, and how the source is disclosed per row.

## What would falsify this ADR

- **The two-stage split failing to earn its complexity.** If a single direct point projection matches the
  S1×S2 pipeline out-of-sample across positions, the split is decoration and should be collapsed. That is
  a testable comparison and it belongs in `F-BOTTOMUP-CORE` as a declared arm from the start.
- **PR-002's null being overturned** by a properly pre-registered test on more data — in which case the S2
  caps in §1 are too tight and should be revisited by amendment, not by quietly raising them.
- **The embargo proving inert** — if embargoed and un-embargoed LOSO agree to within noise across every
  position and model, the embargo is costing two folds for nothing and can be dropped by amendment. Note
  the asymmetry: discovering the embargo was unnecessary is cheap, discovering it was necessary after
  shipping is not.

## AMENDMENT E-A1 (2026-07-27, Fable session 4) — R3: the week-indexed projection object; N3: week-leverage weights

**Status: adopted into this draft.** Written to be executable by a sonnet `backend` agent without
further strategist input — the work order is §A1.7. Everything above this line is unchanged except
where this amendment explicitly supersedes it (§2's *target* is untouched; §2's *output object* is
widened). The V5 vacated/arrived feature group, R5 (calibration family) and C3 (rookie universe
rule) are **not** part of this amendment — they remain queued for the return-week registration
discussion, per `ACTION-PLAN-2026-08.md`.

### A1.1 What changes, and why

The founder's decomposition — **points = games played × points per game × usage ramp** — is
already half-mandated by §2 (games × ppg, both reported). What §2's season-total target erases is
*which weeks* the games occur in. Suspension valuation (games 1–N missed), bye cost, injury-ramp
valuation, the no-reseed playoff structure (CLAUDE.md §7), and every in-season consumer
(`fable-in-season-2026-07-27.md` §2) are statements about *when*. A season total cannot express
any of them at any model quality. The fix is cheap at design time: **S1's output object becomes a
week-indexed vector; the season total becomes its uniform-weight integral.** No new estimation is
introduced in v1 — the vector is bookkeeping over quantities S1 already produces.

### A1.2 The object, defined exactly

For player p, target season t:

- `W_t` — the NFL week set for season t (1–17 through 2020, 1–18 from 2021). `G_max(t) = |W_t| − 1`
  (one bye) is the scheduled-games count.
- `q_p` — per-active-week play rate: `q_p = Ĝ_p / G_max(t)`, where `Ĝ_p` is §2's base-rate
  games projection, unchanged.
- `Z_p ⊆ W_t` — **structural zeros**, all knowable pre-season with `as_of` discipline:
  the team's bye week (published schedule); suspension weeks 1..N (T4's source, status as of the
  pre-draft date); pre-season-announced absences (PUP ⇒ weeks 1–4 minimum, season-ending IR).
- **Availability:** `a_p(w) = 0` for `w ∈ Z_p`, else `q_p` (capped at 1; a cap event is logged —
  it means Ĝ_p exceeded the weeks available).
- **Opportunity:** `u_p(w) = u_p × r_p(w)` — S1's per-game opportunity vector times a
  **usage ramp** `r_p(w)`, default ≡ 1. Ramp forms (injury recovery, suspension re-entry,
  rookie ramp) are hooks: any non-unit ramp requires its own registered test before it ships.
- **Week points:** `ŷ_p(w) = a_p(w) × S3(S2(u_p(w)))` — S2/S3 unchanged, applied at the week's
  opportunity level (S3's bonus integration already keys on per-game volume, so it composes).

**Binding identities, asserted in tests, not inspected:**

- **I1:** `Σ_w a_p(w) = Ĝ_p` when `Z_p` contains only the bye. Each additional structural zero
  reduces expected games by exactly `q_p` — this *is* T4's games-adjustment, falling out
  mechanically rather than being a bespoke formula.
- **I2:** with `r ≡ 1`, `Σ_w ŷ_p(w)` equals the season-aggregate projection to float tolerance.
  The vector must reproduce the number the backtests score, or it is a second model in disguise.
- **I3:** the leverage-weighted integral (§A1.3) with `leverage ≡ 1` equals season points.

### A1.3 N3 — week-leverage weights, specified once, every consumer named

`leverage(w; league_config) → weight ≥ 0`, **normalised to mean 1** over the league's scored weeks
(regular ∪ playoff weeks, both read from `league_config` — never hardcoded).

**Semantics (the measured form, N2's job):** `leverage(w)` = the marginal effect of one expected
win in week w on P(championship), estimated by the season simulator via paired perturbation
(`fable-in-season-2026-07-27.md` §4). Until N2 exists, the interim form below applies.

**Interim default (unvalidated, D-004-style):** shape 1.0 on regular weeks, 2.0 on playoff weeks,
then normalised to mean 1 — for this league (15 regular + 2 playoff) that is ≈ 0.895 / 1.789.
The utility **refuses to emit weights without a provenance label** (`interim_hand_set_v1` vs
`simulated`), and every surfaced number downstream carries it. Structural asymmetry, encoded as a
comment and a test guard: **no reseeding + 4-team playoff means early losses compound** — the
interim deliberately does not discount weeks 1–4, and N2's measurement is expected to *raise*
early-week leverage relative to mid-season, not lower it. Refinements are checked against the
simulator, never hand-tuned twice.

**Unit bridge, stated because it will otherwise be glossed:** leverage is defined on *wins*;
consumers apply it to *points*. The bridge (points → win probability, locally linear) is an
approximation — fine for ranking deltas, and stated wherever a leverage-weighted number ships.

**Config discrepancy to verify (founder, one minute):** `league_config.py` says
`playoff_weeks=(16,17)`; the founder's session-4 note says "championships are weeks 15–17."
The utility reads config, so whichever is right is a one-line config fix that corrects every
consumer at once — but it must be verified against the live platform (T2-adjacent), not assumed.

**Consumers (the complete list — this primitive is built once):**

1. **T4 suspension valuation:** cost = `V_L(vector without suspension zeros) − V_L(vector with
   them)` — a difference of two integrals, no bespoke formula. Games 1–N are the *low*-leverage
   end under the interim shape, so a 6-game suspension costs less than 6/17 of season value —
   subject to the early-loss asymmetry note above.
2. **Bye-week cost:** `leverage(bye_w) × ŷ_p^{cond}` — near-uniform across weeks 5–14 today; the
   machinery is free and becomes meaningful under measured weights.
3. **R3's leverage-weighted value:** `V_L(p) = Σ_w leverage(w) × ŷ_p(w)` — the draft-time
   "championship-weighted value" column.
4. **In-season start/sit thresholds and trade valuation** (future, N2/N4): rest-of-season
   truncated integrals against the same weights.
5. **Injury-recovery / missed-early-weeks valuation:** the same integral with a ramp `r_p(w)`.
6. **N2 season simulator:** consumes the vector for weekly team scores; *produces* the measured
   weights that replace the interim.

### A1.4 Guardrails specific to the vector

- **Look-ahead:** for backtest seasons, nothing in `a_p`, `u_p`, `r_p` may use target-season
  information beyond pre-season-known structural zeros (published schedule; suspensions with
  `as_of` ≤ pre-draft date). The experiments' weeks-1–4 roster canon assignment (V3/V5, disclosed
  look-ahead) is **not** permitted in the production vector.
- **This is not a weekly projection.** No opponent, no home/away, no weather. Surfacing
  `ŷ_p(w)` as a "Week w projection" in any UI or export is **forbidden**; permitted uses are
  integrals and structural-zero displays. Start/sit remains the genuinely new modelling lift (N4).
- **No week-level calibration claim.** v1 validates identities I1–I3 only. Week-level accuracy is
  unmeasured and stays unclaimed.

### A1.5 Interim forms that remain valid (nothing stalls if the vector slips)

- **All backtesting and F-BOTTOMUP-CORE:** unaffected. Confirmatory metrics stay season-level;
  the vector integrates to the same number (I2).
- **N3 alone (action plan 5.3)** can land without the vector: consumers use
  `ppg × Σ leverage(w)` sums with `q_p ≈ Ĝ_p/G_max`. This amendment only adds the mean-1
  normalisation and the provenance requirement to 5.3's spec.
- **T4-interim** (fixture + board flag) is unchanged. Until the vector lands, a crude adjusted
  total `season_points × (1 − n_susp/G_max)`, labelled crude, is acceptable; the vector replaces
  it mechanically.
- **Bye cost interim:** `leverage(bye_w) × season_points/Ĝ_p`.

### A1.6 What would falsify or revisit this amendment

- N2 measures leverage ≈ flat (playoff within CI of regular): the interim 2.0 overweights the
  playoffs; every interim-labelled number is restated, which the provenance flag makes findable.
- Per-position games base rates differ materially by depth tier: `q_p` from a position-level rate
  is too crude — revisit via a registered test, not a silent refit.
- If the vector's bookkeeping cost exceeds its consumer value (no consumer ships by the time
  ADR-E builds), collapse back to season aggregates by amendment — the identities make the
  collapse lossless.

### A1.7 Work order, sonnet-executable

**R3-A — `src/week_leverage.py` (backend, ~0.25 session, no dependencies).** The N3 utility.
`week_leverage(cfg: LeagueConfig) -> WeekLeverage` with `weights: dict[int, float]`,
`source: str`, mean-1 invariant. Playoff and regular weeks from `cfg`; shape 1:2 interim;
normalise after shaping. Tests: mean 1 over scored weeks; playoff/regular ratio == 2.0 exactly
after normalisation check; changing `cfg.playoff_weeks` moves the weights (config-driven, no
constants); constructing without a known `source` raises; docstring carries the unvalidated
label and the early-loss asymmetry note verbatim.

**R3-B — `src/week_vector.py` (backend, ~1 session; needs R3-A, the T4-interim fixture, and
schedule byes).** The vector over the *live board* (the current ADR-017 curve projection — this
does not wait for the bottom-up model):
- `q_pos`: per-position mean play rate measured once from `player_weekly_stats` seasons
  2015–2024 within board-relevant depths (historical constant, not target-season data; record the
  query in the module docstring; test pins the values).
- `ppĝ_p = projected_points / (q_pos × G_max)`; `a_p(w)` per §A1.2 with byes from the schedule
  and suspension weeks from the T4 fixture; `ŷ_p(w) = a_p(w) × ppĝ_p`.
- Emits: suspension-adjusted season points, `V_L`, `bye_leverage`. **Internal module only — no
  export-contract change** (a contract change is a version bump + a `frontend` thread, and is
  deliberately out of this order's scope; the PM sequences it).
- Tests: I1/I2/I3 identities; a suspension of n weeks reduces the total by exactly
  `n × q_pos × ppĝ_p`; a player with a null bye (the live JAC/LAR defect, T3) gets an unchanged
  vector plus a logged warning — not a crash and not a silent zero — until T9 lands, with a test
  pinning that behaviour.

**R3-C — binding on the ADR-E confirmatory build (no work now).** When S1 is implemented, it
emits the vector natively (`q` from the fitted games model, ramp hooks in place), asserts
I1–I3 per fold, and the confirmatory target remains the season integral.

Order: R3-A anytime; R3-B after the T4-interim fixture exists (action plan Day 3–4); R3-C at
build time. None of it blocks, or is blocked by, this week's T1/T5/T2 critical path.

---

## Measurements needed from `backend` (I cannot run these)

Specified precisely enough to execute without a round trip:

1. **Per-feature `first_reliable_season`** for every feature in §4.1, as actually present in `nfl.db`
   (not as documented upstream), plus the row count and null rate per season. This determines the fold
   sets and therefore every stated n.
2. **Fold count** for (a) the box-score-only feature set and (b) the full usage feature set, after the
   §4.3 intersection rule and the 2003–2008 target refusal.
3. **The ADR-016 curve refit under embargoed LOSO** on the common 2021–2024 window — per position, R² and
   season-level bootstrap CI. This is the honest baseline number; 0.158–0.266 is not it.
4. **The same refit for prior-season-points-ranked and the positional-mean heuristic**, over the full
   eligible window. These are the decision-grade bars.
5. **Wall-clock cost of one full embargoed-LOSO pass** over the candidate pipeline, so the 20-configuration
   budget can be checked against a real session.
