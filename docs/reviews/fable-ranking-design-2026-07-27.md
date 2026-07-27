# Will ADR-E actually produce edge? — 2026-07-27 (Extended mandate, Priority 1)

**Verdict in three sentences.** ADR-E is a methodologically excellent validation harness wrapped
around a projection model whose *edge mechanisms are mostly not in it*: of the four plausible
sources of player-level edge, it fully captures one (age curves), half-captures the best one
(TD regression — the shrinkage side is there, the goal-line-opportunity side has **no data source
in `nfl.db`**), does not design for the second-best (vacated opportunity — no roster-churn feature
exists anywhere in §4.1), and specifies the third with a feature whose data table is **parked and
empty** (coach continuity — `play_callers` refuses its own 22-of-64-cell input,
`ingest_play_callers.py:4-6,133`). The honest statement of what ADR-E as written would produce is:
a well-validated persistence model — last-season usage, regressed — whose realistic gain over a
last-season-rank baseline is small, plus a defensible framework that could later carry the real
mechanisms once their data exists. The durable edge in this project is league-specific (format
re-weighting, variance-under-bonuses, draft mechanics, playoff-structure week-weighting), which
consensus *cannot* price by definition; player-level mispricing of public information is the
weaker, partially-arbitraged channel, and the design should say so.

Method note: every data claim below was measured directly against `nfl.db` this session (schema,
row counts, per-season sums), not read from docs. Where I could not establish something, it says
unresolved.

---

## Q1 · Where is the edge supposed to come from, and is that source real?

**The mechanism, stated in my own words.** ADR-E's implicit theory of edge: consensus ranks
players substantially by *last season's points*, which bundle high-persistence components (usage)
with low-persistence components (TD rate, yards-per-touch luck, games played). A model that
projects usage carefully and forces efficiency to the positional mean will systematically fade
players whose rank was bought with unsustainable efficiency and promote players whose usage
outran their box score. The edge is the gap between "what the box score said" and "what the usage
said," harvested wherever human rankers anchor on the former.

**The attack, in general form, before the per-mechanism table:** that gap is the single most
publicized finding in fantasy analytics. Every serious projection system (and a large fraction of
ECR's own contributing experts) already regresses TD rate and projects volume. The mechanism being
*real* does not make it *mispriced*; ECR is an average over people many of whom run exactly this
model. What consensus demonstrably cannot do is (a) price this league's scoring structure, (b)
publish uncertainty, (c) answer draft-mechanics questions. Those are structural, not
informational, advantages — and only one of the three lives in ADR-E.

Per mechanism, as the mandate requires — captured? / data? / plausibly mispriced?

| Mechanism | Does ADR-E capture it? | Do we have the data? | Plausibly mispriced by consensus? |
|---|---|---|---|
| **TD regression** | **Half.** The defensive half is airtight: S2's `w_player ≤ 0.20` cap on TD rate, no per-player TD model, PR-002's null honoured (ADR-E §1). The offensive half — TD expectation from *goal-line/red-zone opportunity share* — is specified (§1 S2 rules) but | **No, for the offensive half.** There is **no play-by-play table in `nfl.db`** and no red-zone/goal-line usage column in `player_weekly_stats` (schema read directly this session). The TD-rate model ADR-E mandates cannot be built from ingested data today. Shrinkage-to-position-mean needs only box scores: available 1999+. | **Yes, modestly — and this is the most reliable channel.** Positional TD-rate regression to mean is well-established; anchoring on TD-inflated seasons is a documented human bias. But it is also the most-published edge in the industry, so the *residual* mispricing after the market's own regression models is thin. Directly testable on 2021–2024 (n=4, descriptive): does ECR's error correlate with prior-season TD-rate excess? Nobody has run that here. → **R4, R6** |
| **Vacated opportunity** | **No.** §4.1 has usage level, usage shape, trend, team context, age, market, Vegas — **no feature anywhere encodes departed teammates' targets/carries/red-zone touches.** S1 projects each player's own usage from his own history plus team aggregates; a WR whose team just lost 180 targets looks identical to one whose team lost none. This is a design gap, not an implementation detail. | **Partially.** Vacated share is computable from `player_weekly_stats` (who produced last season) × season-N rosters (who left). The hard part is `as_of` hygiene: historical *pre-draft* roster membership is only approximated (depth charts end 2024 and are weekly; contracts lack clean windows). A week-1-roster approximation is the honest, industry-standard compromise and must be flagged as mild look-ahead. | **Yes — arguably the strongest residual mispricing.** The mandate's own framing is right: consensus assumes smooth redistribution; reality is lumpy and depends on depth-chart structure. Less arbitraged than TD regression because it requires modelling the *team's* distribution, which most public systems do crudely. → **R1** |
| **Scheme / personnel turnover** | **Nominally.** §4.1 Context row: prior-season team pace, PROE, team pass rate, coach-continuity flag keyed on `coach_id`. But these features *remember* the old environment rather than *project* the new one — a continuity flag says "something changed," not "what it changed to." | **Mostly no.** `play_callers` is **parked, deliberately empty** (22/64 cells populated; the module refuses to ingest a guess — `ingest_play_callers.py:133`). There is no `coaches` / `coaching_staff_seasons` table in `nfl.db` despite CLAUDE.md §4 declaring one. **PROE requires play-by-play — absent.** Team pace/pass rate are derivable from weekly-stat aggregates (fine). Vegas (`odds_snapshots`): table does not exist. | **Yes in principle — humans are weak at projection vs. memory — but this is the hardest channel to validate:** coach-effect estimates at n≈32 teams/season are noise-dominated, and the data to even *name* the coordinator is not ingested. Treat as a v2 mechanism gated on the data build. → **R2** |
| **Age curves at the tails** | **Yes.** Age, age² within position, experience, declared not discovered (§4.1 Situation row). One quibble: a quadratic is smooth by construction and the mandate's claim is that *decline is not linear and consensus is late at the tails* — a quadratic can under-express a cliff. Positional spline or age-band dummies cost one line and are declared-list-compatible. | **Yes.** Birthdate coverage 11,198/12,468 (89.8%) in `players_canonical`; `draft_year` in `ff_playerids` for experience. | **Weakly.** Age effects are heavily published; the tail claim (consensus too slow on RB30+/WR32+) is plausible but the affected population per season is a handful of players, so the aggregate edge is small even if real. Cheap to include, not a headline. |

**Q1 verdict.** The mechanism is real but the design captures at most half of it, and the data
layer currently supports even less than the design specifies. Three of the four rows have a data
gap column that says no. If ADR-E were implemented tomorrow exactly as written, S1 would run on:
own-usage history + trend + team box-score aggregates + age — a *persistence-plus-regression*
model. That is a good model. It is also approximately what every competent public projection is,
minus red-zone data they do have. **The expected player-level edge over consensus from ADR-E v1
is therefore small — the honest prior is "ties consensus at player level, wins at format level."**
The review's constructive claim: the four mechanisms should be *ranked by residual mispricing ×
data feasibility*, which orders them **vacated opportunity (R1) > TD regression completion (R4) >
age tails (free) > scheme turnover (R2, gated on data)** — almost the reverse of how much ink
ADR-E spends on each.

## Q2 · Is the architecture right?

**The S1/S2/S3 split survives attack.** Volume fitted, efficiency shrunk with per-fold-estimated
`k`, scoring arithmetic — this is the correct decomposition and ADR-E's §1 argument for it
("makes the humility auditable") is better than convention. Regression strength is genuinely
estimated, not assumed (`w = n/(n+k)`, `k` fitted per statistic per fold), with two caveats worth
recording: the **caps themselves (0.60 / 0.20) are assumed priors**, defensible ones, and §1
correctly logs when they bind rather than pretending they were estimated; and shrinkage targets a
`position × regime × volume-tier` mean whose tier boundaries are fold-local (§3.2) — right, and
expensive, and worth it.

**The games-played decomposition exists; the layer the founder keeps asking about does not.**
The mandate asks whether ADR-E has `points = games_played × points_per_game × usage ramp`. Score:
two of three. §2 mandates the `season_points = games_played × ppg` decomposition with R² reported
on all three quantities, and projects games from a base rate (no injury-proneness pseudo-feature
— correct). But the target is the **season total**, an integral that erases *which weeks*. The
three founder requests the mandate cites — injury duration with recovery ramp, suspension
valuation, bye weeks — are all statements about **when** the games occur, and so is the
playoff-structure constraint (4-team, no reseeding: CLAUDE.md §7 — weeks 15–17 are the season).
A season-total target cannot express any of them, ever, no matter how good the model gets.
**This is a design gap, not a feature request** — the fix is cheap at design time and expensive
later: define the S1 output as a **week-indexed availability × per-game-opportunity vector**
(or minimally, segment-level: weeks 1–4 / 5–14 / 15–17), from which season points, suspension
discounts, bye costs and the P2 week-weighting all become integrals with different weights.
ADR-E v1 can ship with the uniform-weight integral; the *object* should be the vector. → **R3**

**One more architectural miss, inherited from the mandate's own Q3:** §2's target is a point
value and §7's comparisons are R²/rank metrics. Nothing in ADR-E emits or validates a
*distribution*, despite §1's bonus machinery already requiring a per-game distribution
internally. See Q3.

**Minor:** §5 (extend `regimes.py`, fold-local breaks), §3.1 (embargoed LOSO), §3.2 (enumerated
fold-local estimation) all survive. The walk-forward-vs-LOSO question: for a *prototype* whose
question is "does this beat baselines at all," expanding-window walk-forward is the more
deployment-honest scheme and is what the build below uses; ADR-E's embargoed LOSO is the right
*confirmatory* scheme for the registered run because it uses the scarce modern seasons more
efficiently. Both respect the same cutoff discipline; this is not a conflict, it is prototype vs.
confirmatory protocol. Stated here so nobody later reads the difference as an inconsistency.

## Q3 · Is a distributional ranking the better objective?

**Yes — and ADR-E is already paying most of its cost while collecting none of its value.** The
argument, made in both directions as the mandate asks:

**For.** (1) §1's bonus expectation *requires* integrating a per-game yardage distribution at
position × volume-tier level — the distribution machinery must exist for S3 to be correct under
this league's bonus rules. Emitting quantiles and P(top-N at position) from machinery you already
built is marginal cost. (2) Calibration is testable on 26 seasons *today* with zero dependence on
consensus history — coverage of an 80% interval is a per-season count, season-level bootstrap
over 24+ folds — which sidesteps the n=4 wall that blocks every consensus claim (session 1, 2C).
(3) The decision consumers are already distributional: `draft_sim` draws board noise; ADR-F's
VONA is an expectation over roster futures; the availability model is a survival curve. A point
projection feeding a simulation stack means the stack invents the uncertainty itself (currently:
Gaussian rank noise), which is *worse* than the model's own residual structure. (4) The league's
bonus structure rewards ceiling (CLAUDE.md §7: "reward ceiling outcomes over floor… should
influence how variance is valued") — two players with equal mean and different variance are
different assets *in this league specifically*, and a point rank cannot see it. (5) Consensus
publishes no uncertainty, so a *calibrated* interval is a product differentiator that requires
beating nobody.

**Against, honestly.** Player-level distributions at n≈150–300 player-seasons/position/fold are
hard at the tails; a mis-calibrated P(top-5) is worse than none because it will be trusted.
Interval calibration tends to be achievable at central coverage (50–80%) and shaky beyond;
P(top-N) compounds every player's tail simultaneously. And the draft decision consumes mostly
the top-of-distribution ordering, where means and quantiles are highly correlated — the
incremental *decision* value over a good mean is real but second-order until ADR-F exists to
consume it.

**Resolution: not either/or.** Keep §2's point target as the confirmatory accuracy object (it is
what the baselines can be scored on), and add a **registered calibration family**
(`F-BOTTOMUP-CALIB`: per-position empirical coverage of the 50% and 80% intervals, season-level
bootstrap CI on coverage error, PIT histogram as exploratory) plus P(top-N) reported
*exploratory-only* until central coverage validates. The distribution is emitted from S1×S2's
existing per-game machinery, not from a new model class. This gets the testable-today benefit and
the product differentiator without betting the confirmatory run on tail calibration. → **R5**

## Q4 · What is the ceiling? (registered before any result — this section also governs the build)

Stated before the prototype below was fitted, per the mandate. Decomposing season-to-season
variance in season fantasy points within the draft-relevant universe: games played (injury —
largely unforecastable beyond base rates), TD deviation from opportunity-implied (PR-002: noise),
per-touch efficiency luck, usage change (the forecastable core), scheme shifts (partially
forecastable). Published professional season-level projections are believed to sit near R²
0.30–0.40 *on friendlier universes than ours* (ours keeps busts and zero-seasons in — §2's
universe rule — which lowers attainable R² relative to any published figure computed on
survivors).

**Registered expectations, frozen 2026-07-27 before any fit:**

| Quantity (within position, frozen universe, out-of-sample) | Expected | Near-ceiling | Suspicious (audit) |
|---|---|---|---|
| Season points R², QB / WR | 0.15 – 0.30 | ~0.35 | > 0.40 (ADR-E §8 concurs) |
| Season points R², RB / TE | 0.10 – 0.25 | ~0.30 | > 0.40 |
| Points-per-game R², all | 0.25 – 0.45 | ~0.50 | > 0.55 |
| Games played R² | 0.00 – 0.15 | ~0.20 | > 0.30 |
| tau_b vs. actual finish, last-season-rank baseline | 0.25 – 0.40 | — | — |
| **Prototype Δtau_b over last-season-rank** | **+0.02 – +0.08** | +0.10 | > +0.15 sustained |

A model explaining ~30% of season-point variance on this universe is **near the ceiling and
should be described as strong**; calling it a failure against an imagined 60–80% would be exactly
the misreading the mandate warns this project is prone to. Symmetrically: ADR-E §8's audit
triggers stand — a number above 0.40 is presumptively a leak, not a breakthrough.

**Registered mechanism predictions (Q1 → falsifiable):** (i) volume features (prior usage/game,
usage trend) carry most of the signal; (ii) TD-rate shrinkage contributes a real but small
improvement over raw prior points — visible mainly at WR/RB; (iii) age terms contribute ≈ nothing
inside the draft-relevant depth except at RB; (iv) games-played projection contributes ~nothing
over position mean (base rates are flat). If (ii) fails, the TD-regression edge channel is
weaker than argued above and R4/R6 drop in priority. These predictions are the review's stake in
the ground; the build reports against them.

## Q5 · What would I build instead?

**The same S1/S2/S3 core, with three amendments and one reframe.** Stated per the mandate's
instruction to say so especially if the answer is ADR-E.

Amendments, in priority order:
1. **Vacated opportunity into S1** (R1) — the largest un-captured, un-arbitraged mechanism, data
   mostly present, one honest `as_of` compromise required.
2. **Week-indexed (or segment-indexed) availability × opportunity as the S1 output object** (R3)
   — unlocks suspension/injury-ramp/bye valuation, the P2 week-weighting primitive, and the
   playoff-structure constraint, for near-zero extra estimation cost (the per-game model already
   exists; the vector is bookkeeping).
3. **Distributional output with a registered calibration family** (R5) — §1's machinery already
   computes it internally; emit it, validate central coverage, feed ADR-F.

The reframe: **stop describing the projection as the edge.** The defensible, unarbitrageable
edge in this project is structural — half-PPR-with-bonuses re-weighting (built), variance
valuation under bonus rules (Q3), draft-mechanics answers at slot 3 with 15/5 gaps (ADR-F; the
FR-005 insight that draft-resampled questions have unlimited n *today*), and week-15–17-weighted
roster value under a no-reseed playoff (R3's vector). ADR-E's projection is the *substrate* those
run on — it needs to be good enough not to embarrass them, and honest about where it merely
matches the market. A mediocre-but-calibrated projection under a superior decision layer beats a
slightly-better point projection consumed naively, and the first of those is buildable now.

---

## Prototype registration (frozen before fitting; the build executes exactly this)

Per the mandate's discipline rules. Branch: `fable/ext-2026-07-27`, new files only.

- **Universe** (per fold, frozen pre-season): prior-season positional finish within ADR-016
  depths — QB20 / RB45 / WR60 / TE20 (`make_board.py:93`). **Rookies excluded from v0**, stated
  in every n; rookie inclusion via NFL draft capital (production-independent, 1980–2026 in
  `draft_picks`) is the registered v1 path (resolves session 1's C3 as option (a)/(b) hybrid).
  Players in-universe who then scored zero stay in at zero. Announced-retirement removal is not
  possible from ingested data; contamination noted, symmetric across arms.
- **Target:** season fantasy points under league scoring; decomposed per ADR-E §2 (season / ppg /
  games all reported).
- **Scheme:** expanding-window walk-forward — train ≤ t−1, predict t. Two arms by feature window
  (§4.3 discipline): **long arm** (box-score volume: carries + receptions + attempts; no targets)
  target seasons 2000–2024, 25 folds; **usage arm** (targets, target share, air yards, WOPR)
  target seasons 2010–2024, 15 folds (targets are absent 2003–2008 and air yards unreliable
  before 2009 — measured this session). 2025 untouched, holdout sealed.
- **Metrics** (registered): primary **Kendall tau_b within position** at ADR-B's primary K
  (repo convention, `backtest.py`); co-primary **draft-weighted VBD-capture**: sum of actual VBD
  (replacement levels RB30/WR40/TE10/QB10 in force) of the model's top-K picks divided by the
  oracle top-K sum — weighting scheme: errors outside the draft-relevant top-K count zero,
  errors inside count by actual VBD. Stated now, not changed after. Secondary: R² triplet above.
- **Baselines, all mandatory:** B1 last-season points (rank and value); B2 positional mean
  (value floor); B3 volume-only rank (prior opportunities/game, no efficiency); B4 the
  consensus board (ECR → rescored curve), 2021–2024 descriptive only, common (veteran) universe,
  no p-values (n=4).
- **The one-line question:** does the prototype beat last-season-rank (B1) on tau_b in a clear
  majority of folds? Everything else is commentary.
- **Reporting:** per-season series, never pooled alone; season-level bootstrap CIs
  (`bootstrap_season_ci`); paired deltas (`paired_bootstrap_delta_ci`); variant log with count
  (the multiplicity denominator) shipped with the result.
- **Ceiling:** Q4's table governs. Registered mechanism predictions (i)–(iv) reported against.

## Work orders

- **R1** [data-ops + backend, ~1–2 sessions] — Vacated-opportunity feature build: per team-season,
  share of targets/carries produced in N−1 by players not on the week-1 roster in season N
  (approximation documented as mild look-ahead; depth-chart-based where available, 2001–2024).
  Add to §4.1 as a declared feature group with `first_reliable_season`.
- **R2** [data-ops, gated] — Coaching-staff table: complete the 64-cell play-caller table from
  PFR coaching pages (licensing check first, per CLAUDE.md §5) or accept the gap and strike the
  coach-continuity feature from §4.1 until data exists. Either outcome closes the current state
  where a declared feature has a deliberately-empty table behind it.
- **R3** [strategist amendment to ADR-E, small] — Redefine S1's output as a week- or
  segment-indexed availability × opportunity vector; season points become the uniform-weight
  integral. Names the week-weighting primitive P2 needs.
- **R4** [data-ops, ~1 session] — Ingest nflverse play-by-play red-zone/goal-line usage
  aggregates (or a documented per-season aggregate table), `first_reliable_season` declared; this
  is the blocking dependency of ADR-E's own TD-rate specification. Until it lands, S2's TD stage
  falls back to position × volume-tier mean only.
- **R5** [strategist, small] — Register `F-BOTTOMUP-CALIB` (interval coverage family) alongside
  `F-BOTTOMUP-CORE`; distribution emitted from existing S1×S2 machinery; P(top-N) exploratory
  until central coverage validates.
- **R6** [backend, small, descriptive] — The ECR-error-vs-TD-excess check on 2021–2024: does
  consensus rank error correlate with prior-season TD-rate excess? Four seasons, descriptive, no
  p-value; directly measures whether the TD channel is *already priced* by the market this
  product must beat.
- **R7** [PM, minutes] — Correct the project's own summary language: ADR-E v1 as-written is a
  persistence-plus-regression model whose expected player-level edge is small; the roadmap edge
  claims should point at the structural channels (format, variance, mechanics, week-weighting).
