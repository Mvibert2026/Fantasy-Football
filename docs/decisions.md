# Architecture Decision Log

**Historical log, append-only. Do not read this for current decisions** — settled outcomes are in
`docs/decisions-needed.md`'s Resolved table and `docs/CURRENT-STATE.md`. Read this only to learn what
changed and when.

## 2026-07-25 — Data ingestion (Phase 1, Step 1)

**Single wide `player_weekly_stats` table, schema generated from the source, not hand-typed.**
`src/ingest_weekly_stats.py` builds the SQLite `CREATE TABLE` from the polars DataFrame that
`nflreadpy.load_player_stats()` returns, mapping dtypes programmatically instead of hardcoding
~145 column definitions. This avoids silent drift if nflverse adds/renames columns upstream.

**No `user_id` / `league_id` on this table**, despite `CLAUDE.md` §4's multi-user-from-day-one
principle. Reasoning: this table is shared reference data (what actually happened in the NFL) —
identical for every user/league, not owned by one. The multi-user principle applies to tables
holding user- or league-specific state (rosters, rankings, ADP snapshots, outcome feedback), not
to the raw stats fact table. Revisit only if a future requirement makes per-user *overrides* of
raw stats a real thing (currently inconceivable).

**No `as_of_date` on this table.** `CLAUDE.md` §6.1 requires `as_of_date` for time-sensitive
records (ADP, injuries, depth charts, odds) because their *meaning* depends on when they were
observed. Weekly stats are the opposite: they are final, already-realized outcomes for a game
that already happened, not a snapshot of a belief. The look-ahead-bias risk this table poses is
structural (a season-N ranking model must not be handed season-N rows) and belongs to the
backtest harness (Step 3), not to this cache. Flagging so Step 3's harness design accounts for it
explicitly rather than assuming `as_of_date` filtering will handle it.

**No `season_weight` on this table.** That's a ranking-algorithm-time concept (how much a given
season should count toward a projection), applied by the model, not a static property of a
historical row. Belongs in `ranking_versions` config (Step 4).

**Filtered out rows with `player_id IS NULL` before writing.** Verified via direct inspection:
~22 rows/season in the nflreadpy output are team-level aggregates (only `def_safeties`,
`penalties`, `penalty_yards` are ever non-zero on them) with no player attribution. None of
those stat categories are in this league's scoring rules (`CLAUDE.md` §7) anyway. Left in, they
would also break upsert idempotency: SQLite does not treat `NULL` as equal to `NULL` in a
composite primary key, so these rows would duplicate on every re-ingestion run. Caught by a
failing idempotency test before it reached `data/nfl.db`.

**Primary key: `(player_id, season, season_type, week)`.** Verified empirically (no duplicate
key groups in any pulled season) rather than assumed. `INSERT OR REPLACE` on this key makes
re-running ingestion for a season safe — it updates corrected stats in place instead of
duplicating rows.

**Provenance column `ingested_at`** added (not present in the source) so we can tell when a row
was last (re)written — cheap, useful for debugging cache staleness, not a modeling field.

## 2026-07-25 — Scoring engine, rankings ingestion, backtest harness (Phase 1, Steps 1-3)

**`player_week_scoring_inputs` is a SQL view, not a second ingested copy.** Rather than
re-pulling nflverse data under the narrower column set requested, `src/db.py` adds a view over
the already-ingested `player_weekly_stats` table. Same reasoning as the deferred `players` table
decision above: a second cached copy can drift from the raw cache; a view can't. Zero extra
network cost, always current.

**The view carries three columns beyond what was literally requested** (`return_tds`,
`two_point_conversions`, `offensive_fumble_return_tds`). Omitting them would silently under-score
any player with a return TD, a 2-point conversion, or an offensive fumble-return TD — all of
which are real categories in this league's scoring rules (`CLAUDE.md` §7). Verified real, if rare,
values exist in the source data before deciding to include them.

**FantasyPros preseason rankings are ingested as Expert Consensus Rank (ECR), explicitly labeled
`source = "fantasypros_ecr"` — not relabeled "ADP."** ECR (aggregated expert opinion) and ADP
(observed average draft position from real drafts) are different things; conflating them would
misrepresent data provenance. Sourced via `nflreadpy.load_ff_rankings()`, which mirrors
DynastyProcess.com's public FantasyPros snapshot archive — already vetted for redistribution by
nflverse the same way the rest of this pipeline's data is. Verified the `fantasypros_id` →
`gsis_id` crosswalk (`load_ff_playerids()`) resolves 98.9% of non-DST/non-K rows before trusting
the join.

**True multi-source ADP (FFC/Yahoo/ESPN/Sleeper/Underdog) was not ingested.** See
`docs/deferred.md`. The backtest harness reports `consensus_adp` as `available: False` with a
reason, rather than substituting FantasyPros ECR under the ADP label or fabricating a number.
`CLAUDE.md` §6.5 requires baseline comparisons to be honest about what they are; a mislabeled
baseline is worse than a missing one.

**BPA baseline = prior season's actual fantasy points, ranked** (`CLAUDE.md` §6.5 baseline #2),
not a simulated live mock draft. This is a disclosed proxy for "draft best available off a good
half-PPR list": it requires no external projections source, so it's always buildable, and it's
routed through the same look-ahead-cutoff-enforced store as the candidate ranking — baselines get
the same structural guarantee, not an exemption.

**"Points vs. baseline" = sum of actual value-over-replacement (VBD) for the top-N ranked players
per position, N = that position's replacement-level baseline** (`ReplacementLevels().baselines()`
— QB10/RB28/WR41/TE11, used unmodified). The replacement baseline itself is computed once from
the *full* actual player population for the season, then shared across every ranking system being
compared, so all comparisons sit on the same empirically-grounded scale. Chosen over a full
mock-draft-with-opponents simulator as the smallest model that actually answers "did this ranking
put the players who'd beat replacement level at the top" (`CLAUDE.md` §6.6) without building
infrastructure nobody asked for.

**Self-consistency check:** running the backtest with the FantasyPros ranking itself as the
candidate reproduces the `fantasypros_preseason` baseline exactly (`delta_vs_candidate == 0.0`).
Kept as a permanent regression test (`test_run_backtest_self_consistency_on_real_2025_data`) since
it's a cheap, strong signal that candidate scoring and baseline scoring haven't diverged.

## ADR-011: Single base ranking with strategy-specific lensing, not per-strategy models

**Decision:** Build one proprietary base ranking. Apply strategy-specific weights (Hero RB, Elite
TE, etc.) as overlays. Enable real-time re-ranking as the draft unfolds.

**Rationale:**
- One base ranking is easier to validate and maintain than N separate models.
- Strategy variations are weights, not separate rankings — changes propagate cleanly.
- Draft-responsive re-ranking requires a live baseline to deviate from; per-strategy models lose
  that reference.
- Enables pivot recommendations: "the room is taking RBs aggressively; shift to WR strategy" is a
  single decision, not a model swap.

**Timeline:** Phase 3 (after Phase 2 validates that rankings work). Phase 1 builds the base.
Phase 2 tests it. Phase 3 adds the strategy + draft-response layers.

---

## 2026-07-25 (session 4) — Alpha pivot: Tasks 1-5

### ADR-012: Scoring floor removed

`score_offensive_game()` returned `max(0.0, score)`. Yahoo permits negative player scores;
clamping silently inflated poor performances and biased season totals upward, which understates
the cost of a bust. Removed.

Measured impact on 2025: 98 of 18,521 player-weeks (0.53%) were negative, totalling 93.5 points
previously erased; 25 players now carry negative season totals; largest single-player inflation
was 6.0 points. Real bug, small magnitude, concentrated in low-usage players — it does not
overturn the #44/#45/#46 conclusions. The pre-existing "Negative game" self-test
(40 rush yds, 2 fumbles lost) nets to exactly 0.0 and never exercised the floor; genuinely
negative cases were added.

### ADR-013: Feature availability is a first-class, empirically-verified constraint

`docs/data-availability.md` is now the authority on what is testable when, and every factor test
must cite its effective sample from it. Verified by query, not documentation.

The finding that motivated it: `targets` and `receiving_air_yards` are **100% non-null back to
1999 and still unusable before 2009**. Season sums for `targets` are 3 / 5 / 0 / 67 / 14 / 17 for
2003-2008 versus ~17,000 in working years. They are zeros, not nulls, so both a null check and a
column-exists check pass. Root cause, consistent across sources: receiver *identification* in PBP
is unreliable 2003-2008 — metrics needing the intended receiver fail, while passing-side metrics
needing no receiver attribution (`passing_air_yards`, `cpoe`) are fine from 2006.

**Rule: affected features must REFUSE those seasons and raise, never zero-fill.** Imputation is
inappropriate where data is absent rather than noisy. `ingest_league_metrics.py` demonstrates the
pattern (`wr_target_top45_share` is NULL for 2003-2008), and `regimes.py` reports excluded
seasons explicitly in its output.

### ADR-014: Season weighting is a config parameter, never a constant

`src/config.py` supplies `SeasonWeighting` (uniform / exponential / linear, with optional
`max_lookback`). How far back to weight is an empirical question to be answered by holdout
testing (statistical-guardrails.md §4), so the code supplies the knob and the backtest supplies
the answer. `weights()` refuses any season at or after the reference season — weighting the
season being predicted is look-ahead, not a weighting choice.

### ADR-015: Unknown-breakpoint tests, not Chow tests, for regime detection

The task specified Chow tests. A Chow test requires the break date to be specified in advance,
so using it to *find* breaks means assuming the answer (e.g. testing only known rule-change
years). `src/regimes.py` uses a **supremum-Wald (Quandt-Andrews)** test over all admissible
breakpoints, with binary segmentation for multiple breaks (the greedy form of Bai-Perron).

sup-F does not follow an F distribution — maximising over candidates inflates it — so p-values
come from a **moving-block residual bootstrap** under the no-break null, seeded and recorded.
Blocks rather than iid draws because annual league series are autocorrelated (observed lag-1
residual autocorrelation runs +0.44 to +0.75 across metrics); an iid bootstrap would be
anti-conservative.

**n = 27 annual observations is low power.** Detected breaks are suggestive boundaries for
pooling decisions, not established facts, and non-detection is not evidence of stability.

Two implementation points that changed the answers: the time regressor is the **actual season**,
not the row index, so a series with excluded seasons is not silently compressed (this changed the
`wr_target_top45_share` slope from -0.00290 to -0.00259); and **trailing-window trends are
reported alongside regime slopes**, because a metric that rose for a decade and has fallen for
five years still fits a positive line overall. Era similarity excludes the 5 seasons adjacent to
the target, since "2025 most resembles 2024" answers nothing.

### ADR-016: Isotonic regression REJECTED for the rank-to-points curve; log-linear adopted

**This is the most consequential decision of the session, and it reversed a headline result.**

`make_board.py` first fitted an isotonic (monotone-decreasing) regression per position on
per-rank mean points. Inspection killed it. With 5 training seasons there are only 5 observations
per rank, and the raw rank-to-points relation is dominated by noise: consensus QB10 outscored
consensus QB1 in 2 of 5 seasons (2021: 400.2 vs 375.2; 2023: 352.8 vs 287.7), and consensus RB1
season outcomes ranged from 40 to 366 points. Isotonic regression responded by imposing
monotonicity the data does not support — forcing the QB10 replacement value ~70 points below its
own raw mean (233 fitted vs 302.7 raw) and putting Josh Allen at overall #1 as a result.

That was an artifact of the estimator, not a finding about quarterbacks. Under the replacement
estimator the positional ordering **reverses**: RB1 168.5, WR1 153.2, QB1 114.1, TE1 73.1.

Adopted: per position, `points ~ alpha + beta*ln(positional_rank)`, fitted on all individual
player-seasons inside a declared draft-relevant depth (QB 20 / RB 45 / WR 60 / TE 20 — beyond
which players go undrafted in a 10-team league and the tail of never-played zeros would bend the
curve in the range we draft from). Two parameters from 100-300 observations is far more stable
than ~50 parameters from 5 observations each, and it is monotone by construction rather than by
imposition.

**Reported R-squared is 0.158-0.266 by position, with residual SD of 46-91 points.** That is not
a defect in the fit; it is the size of the signal. Consensus draft rank explains under a third of
the variance in what a player actually scores. Every board row therefore carries a season-level
bootstrap 95% CI on its VBD, and ranks whose intervals overlap are not distinguishable.

### ADR-017: The board is positional re-weighting, not player-level re-scoring

Task 5 asked to "re-score every player under our league rules." That needs **component-level**
projections (pass yds, rush yds, receptions, TDs per player). No source has them: FantasyPros ECR
is rank-only (verified — `ecr`/`sd`/`best`/`worst`, zero projection columns), which is exactly
test-registry.md #2, the project's biggest external blocker.

`projected_points` is therefore `E[our_points | position, consensus positional rank]`, fitted
from history **using our scoring engine** so the currency is correct (bonuses, negatives, half-PPR).

- It **does** capture our league's positional value structure — what a positional rank is worth
  under our rules, which drives VBD and the whole board ordering.
- It **does not** capture player-specific scoring-rule edges. A spike-week WR who clears the
  100/150/200 bonuses more often than the average WR at his rank is invisible; he receives the
  average for his rank. That needs component projections (#2) or a player-level distribution
  model (#38).

Every player at a given positional rank receives an identical projection. The board's value is in
the positional re-weighting, not in disagreeing with consensus about individuals.

### ADR-018: Consensus coverage bounds the alpha claim; no market ADP exists

Investigated (Task 4) and recorded in `ingest_rankings.py`'s docstring and
`docs/data-availability.md` §5:

| Source | Finding |
|---|---|
| nflverse | No ADP in any of its 20 loaders (checked individually) |
| DynastyProcess | Player IDs, FP ECR, dynasty trade values only. No ADP. GPL-3.0 |
| Fantasy Football Calculator | **Has** historical ADP back to 2007, but `robots.txt` disallows `/api/` and `/adp/csv/`. Blocked, not attempted |
| FantasyPros ADP pages | `/nfl/adp/overall.php` is not in their `robots.txt` disallow list, but Terms of Use were not affirmatively verified. Not built — CLAUDE.md §10 requires checking terms *before* building a scraper. **Most promising remaining path if the user will review those terms.** |

Consequence: `ranking_source='market_adp'` has no rows. The alpha track is measured against
**expert consensus only**, over **5 seasons (2021-2025)** — the only years with an August
preseason snapshot (2020's earliest is 2020-10-16, in-season, unusable).

This bounds several things requested for Tasks 6-9: per-regime alpha coefficients are not
estimable (all 5 consensus seasons sit inside one modern regime), season-level bootstrap
resamples only 5 units, and reserving a holdout leaves 4 development seasons.

---

## 2026-07-25 (session 5) — Tasks 9 and 7

### ADR-019: No pooled cross-position correlation, ever

`_rank_correlation` is gone. `_rank_correlation_by_position` returns a per-position dict and
there is no scalar correlation on `SeasonMetrics`. A test asserts both facts so the defect
cannot silently return.

Pooling QB/RB/WR/TE into one Spearman mostly measured whether a ranking sorted *positions*
by scoring scale, not whether it ranked *players* well — QBs score on a different scale, so
any ranking that puts QBs in roughly the right band scores well regardless of within-position
skill. That is why the original blended figure was simultaneously high and uninformative.

A single number is still available via `weighted_aggregate(per_position, weighting=...)`,
which requires the caller to name a weighting and returns it carrying the label
"NOT a pooled cross-position correlation". Unknown weightings raise.

### ADR-020: `starter_vbd` — because the existing metrics were blind to the primary baseline

Running the corrected harness produced a delta of **exactly zero** between the re-scored
consensus board and raw consensus, on every metric. Not a small delta — zero, to floating
point, with a zero-width interval.

The cause is structural, not a bug. The board's only effect is CROSS-positional reordering.
`vbd_sum` takes the top-N *per position*, and Spearman is computed *within* position. Both
are mathematically invariant to cross-positional reordering. **The metrics could not see the
one thing the primary baseline does.**

`top_k_starter_vbd` fixes this: take the ranking's top K picks under a fixed budget
(K = 15 roster picks), fill the 1QB/2RB/3WR/1TE/2FLEX lineup from them, and sum actual VBD.
A budget makes cross-position ordering matter — spend early picks on a position you did not
need and the lineup is worse. Two tests lock the complementarity: one asserts `starter_vbd`
IS sensitive to cross-position order, the other asserts `vbd_sum` is NOT.

LIMITATION, stated in the docstring: no opponents. It assumes you receive your top-K
uncontested, so it measures ordering quality, not draft-day scarcity. A real draft simulation
(test-registry.md #44) remains the missing evaluation layer — see docs/deferred.md P3-4.

A `DELTA_TOLERANCE` was also added: a delta of ~1e-13 with an interval of the same width was
being labelled "BEATS" by a bare sign test. It now reports
"IDENTICAL (metric cannot distinguish these arms)".

### ADR-021: Season-level bootstrap only, with degeneracy reported rather than hidden

Every reported metric carries a CI from resampling SEASONS. Player-week resampling is never
used: player-weeks within a season are correlated, so it would produce intervals far too
narrow and make weak results look solid.

The cost is stated in the output rather than engineered away:

- **n = 1 season → no interval at all.** `MetricCI.lo/.hi` are None and the note explains
  that a player-level bootstrap would look narrower and would be wrong.
- **n < 8 seasons → `degenerate=True`** with a note that the interval is itself poorly
  estimated. Every real run currently hits this, since the development set has 3-4 seasons.

Arm-vs-baseline deltas use a PAIRED bootstrap — the same resampled season indices for both
arms within a replication. Independent resampling would add between-arm variance that does
not exist and would understate real differences. A test asserts identical arms produce a
delta of exactly zero with a zero-width interval, which only holds under pairing.

### ADR-022: Holdout is 2025, and locking governs SELECTION, not FITTING

Locked: **2025**. The reasoning, since this was a genuine tradeoff:

2025 is at once the truest forward test for a 2026 draft and the most informative season for
projecting 2026. The apparent conflict mostly dissolves once the distinction is made explicit:
**the lock constrains which seasons may inform decisions about which factors to use, not which
seasons the final model is fitted on.** Once selection is frozen, the chosen model refits on
everything including 2025 to produce the live board. `release_for_final_fit()` marks that
transition and logs it under a different event type from `final_evaluation()`, so the audit
trail distinguishes "we measured on the holdout" from "we trained the shipped model on
everything".

The alternatives were worse. **2021 cannot serve as a holdout at all** — the primary baseline
needs a prior consensus season and cannot be built for the first year of coverage. A middle
season such as 2024 would mean tuning on 2025 data to evaluate 2024: using the future to
predict the past.

**Power warning, recorded up front:** one held-out season is N=1. Given observed variance
(consensus RB1 outcomes have ranged 40 to 366 points), a single-season result cannot confirm
an edge — a win is weak evidence, a loss is meaningfully bad news. `walk_forward_splits()`
supplies rolling-origin evaluation on the development set so development decisions rest on
several forward-looking observations instead of the one final test.

**Enforcement is structural.** `run_backtest_multi` calls `HoldoutLock.guard()` and raises
`HoldoutViolation` outside a logged context. Three existing tests failed the moment this
landed — they had been evaluating on 2025 — which is precisely the leak the lock exists to
catch. Every attempt, permitted or denied, appends to
`docs/preregistration/holdout_access_log.jsonl`, tracked in git. A session-scoped fixture
redirects that log during tests so the audit trail is not buried under synthetic accesses.

**Immediate empirical consequence:** the board's apparent advantage over raw consensus does
NOT survive removal of the holdout as a *statistically distinguishable* result.

> **CORRECTION 2026-07-25 (ADR-025). The original wording of this paragraph was wrong and is
> retracted.** It claimed the delta "flips sign" between the two runs. It does not. The two
> figures were quoted in opposite sign conventions and I misread the reversal into existence:
>
> - Including the holdout (4 seasons): consensus − board = **−84.6**, CI [−153.0, −2.3]
> - Development only (3 seasons): consensus − board = **−84.9**, CI [−176.0, +34.7]
>
> Both are the *same direction* and essentially the *same magnitude* — the board is better by
> ~85 points in both. The only thing that changes is the interval: dropping from four seasons
> to three widens it enough to include zero.
>
> The correct claim is therefore narrower than what was written: **holdout discipline showed the
> board's advantage is not statistically established on development data alone.** It did not
> reverse the finding. The per-season decomposition (ADR-025) makes this unambiguous.

### ADR-023: The FDR denominator lives in git, not in the database

`docs/preregistration/test_run_log.jsonl` is append-only and tracked in version control on
purpose. A test counter living in the gitignored `data/nfl.db` would reset on any rebuild,
silently shrinking the multiple-comparisons denominator to whatever was run most recently —
which is exactly the failure the correction defends against. `correct_against_full_log()`
takes its `n_total` from that file, and `benjamini_hochberg` raises if `n_total` is smaller
than the number of p-values supplied.

Pre-registration is enforced by refusal, not warning: `require_preregistration()` raises
`PreRegistrationMissing` when no file exists and `PreRegistrationInvalid` when required
fields are absent. A warning would be scrolled past.

`docs/preregistration/PR-001-rb-carry-concentration-reversal.md` is the first entry, covering
the post-2019 RB carry-concentration reversal found by `src/regimes.py`. It states the
confirmation threshold, and — deliberately — four specific reasons the finding might be
nothing (n=6 post-break seasons, a possible COVID-era artifact, the likelihood consensus has
already priced it, and that league-level concentration need not imply player-level
predictability). Writing the failure modes down before running is the point.

### ADR-024: ADP schema preserves cross-source dispersion

`rankings` now stores `spread_sd`, `rank_best` and `rank_worst` alongside the point estimate.
This was already being discarded: ingestion kept only `ecr`.

VONA at pick 18 requires `P(player survives to pick 23)`, which needs a distribution over
where the room might take a player. A collapsed consensus point estimate makes that
probability permanently unrecoverable for that date — no later analysis can reconstruct
dispersion that was never stored. Any future ADP source must be ingested the same way:
per-source rows keyed by `as_of_date`, never a pre-blended consensus. See docs/deferred.md
P3-1.

---

## 2026-07-25 (session 7)

### ADR-025: Per-season decomposition, and a correction to ADR-022

Block 1A asked for the per-season breakdown behind two aggregates that had only ever been
reported pooled. The decomposition:

| Season | Board | Raw consensus | Board − consensus | Status |
|---|---|---|---|---|
| 2022 | 1001.8 | 825.8 | **+176.0** | development |
| 2023 | 626.1 | 660.8 | **−34.7** | development |
| 2024 | 673.9 | 560.5 | **+113.4** | development |
| 2025 | 693.1 | 609.3 | **+83.8** | **HOLDOUT** |

- Development mean: **+84.9**, sign test **2/3 positive, p = 1.000**, power floor **0.250**.
- Including holdout: **+84.6**, sign test **3/4 positive, p = 0.625**, power floor **0.125**.

**The correction.** ADR-022 stated that the board's advantage "flips sign" when the holdout is
removed, contrasting +84.6 with −84.9. That was a misreading of my own output: the harness
reports deltas as `arm − primary`, so the −84.9 figure was *consensus minus board*, while the
+84.6 had been quoted as *board minus consensus*. Both describe the board being better by ~85
points. Nothing flipped.

What actually changes between the two runs is only the confidence interval: three seasons
instead of four widens it from [−153.0, −2.3] to [−176.0, +34.7], i.e. from excluding zero to
including it.

**Corrected claim: holdout discipline showed the board's advantage is not statistically
established on development data alone — not that the advantage reverses.** The narrower claim is
still worth having, but the original overstated it, and the per-season view (which the pooled
figure was hiding) makes that obvious. This is a reminder that an aggregate quoted in one
direction and a delta quoted in the other are easy to mistake for a contradiction.

The per-season pattern is also more informative than either aggregate: the board wins big in
2022 (+176), loses modestly in 2023 (−35), wins in 2024 (+113) and 2025 (+84). One negative
season out of four, with high variance. Consistent with a real but modest effect that three
seasons cannot pin down.

### ADR-026: The ALPHA track is CLOSED for the 2026 draft — arithmetic, not pessimism

**Decision:** no alpha-detection work will be attempted for 2026. `src/alpha.py` will not be
built this cycle, and PR-001 is marked **frozen-for-future** rather than pending.

**Reason, which is a counting argument rather than a judgement about any factor:**

Consensus coverage is 2021–2025 (`data-availability.md` §5). One season is the locked holdout,
leaving **four** for development, and arms requiring the re-scored board lose 2021 as well,
leaving **three**. At that sample size:

- The exact two-sided sign test's smallest attainable p is **0.125 at n=4** and **0.250 at n=3**.
- Both floors sit above the conventional 0.05 threshold *before any multiple-comparisons
  correction is applied at all*.
- Benjamini–Hochberg across a realistic factor sweep (the run log already stands at 51 tests)
  pushes the effective bar far below the floor.

**No factor can reach significance regardless of its true merit.** This is not a statement that
alpha is absent — it is a statement that the instrument cannot detect it. Running the sweep
anyway would produce a list of nulls indistinguishable from a list of undetected real effects,
consume FDR budget, and create a standing temptation to reinterpret noise.

**Evidence this is the right call, not premature surrender:** three separate pre-registered or
measured results have now each been bounded by the same arithmetic — PR-002 (36 correlations,
zero surviving BH), PR-003 (15 comparisons, zero surviving, floor p=0.125), and ADR-025 above
(3/4 seasons positive, p=0.625). In every case the data ran out before the question did.

**Reopening condition — explicit, so a future session does not relitigate this:** the track
reopens when consensus coverage reaches a size where the sign-test floor clears 0.05, i.e.
**n ≥ 6 development seasons** (floor 0.031). Coverage accrues one season per year, so on current
trajectory that is **2028** (2021–2027 minus a holdout = 6). Ingesting an additional *source* of
consensus does not help; the binding constraint is seasons, not sources.

**What continues instead.** The ACCURACY track is not bounded this way — it extends as far back
as each feature's own availability allows, up to 27 seasons for outcome-based work (PR-002 used
26). Bottom-up projection, startability, availability distributions and the draft simulator are
all accuracy-track and all remain open. The 2026 edge, if there is one, has to come from
correct league-specific mechanics and better roster construction, not from out-predicting
consensus on a sample that cannot demonstrate it.

### ADR-027: AI-generated prose is separated into fact extraction and rendering

**Decision.** Dynamic narration (live draft commentary, player-panel prose, post-draft
summary) is built as two layers. `src/narrate.py` is layer 1 and is built now: a pure,
deterministic function from draft state plus the Block 7 exports to a list of `Fact` objects.
Layer 2, the renderer that may involve a language model, is deferred and constrained.

**The problem.** A language model given the underlying data will write fluent, confident,
causal sentences regardless of whether the data supports them. "He's sliding because the room
is worried about his workload" is precisely the kind of claim this project has spent its
effort *not* making — and it is the kind a narrator produces by default, because it reads
better than "his availability probability at pick 23 is 0.10".

**The mechanism.** The renderer never receives the exports. It receives Facts. Each Fact
carries a stable id, a `source_path` that must resolve against a real field in the exports,
a numeric value, and a plain-language template. The renderer may reword a template; it may not
introduce a claim, a comparison, a cause, a prediction or a recommendation that is not already
a Fact. Every emitted sentence must trace to exactly one `Fact.id`.

Two safety properties are enforced in code rather than by convention:

- **Unresolvable facts raise.** `extract_facts` validates every `source_path` before
  returning. A stale or restructured export cannot silently yield a confident sentence about a
  field that no longer exists.
- **The render entry point rejects non-Facts.** `validate_render_input` raises on a dict, a
  string, a bare Fact, or a list containing anything else — so the renderer cannot be handed
  raw data and reason from it.

**Confidence travels with the fact.** Availability numbers never pass through the ADR-016
projection curve and are marked `high`; structural arithmetic is `medium`; anything
projection- or VBD-derived is `low`, because that curve's R-squared is 0.16-0.27. The renderer
is required to respect the distinction rather than flattening everything into one confident
register — which is the specific failure mode that makes generated commentary untrustworthy.

**Nulls are first-class.** `nulls.json` feeds `registered_null` facts, so when a viewer asks
why the guide does not recommend chasing spike-week players, the renderer can state that we
tested it and found no evidence, rather than improvising a plausible-sounding reason.

**Cost accepted.** This is more machinery than piping the JSON into a prompt, and the prose
will be less lively. That is the intended trade: the project's whole claim to credibility is
that it reports what it measured and refuses what it did not. A narrator that invents
causation would undo that in one paragraph.

### ADR-028: The −92.9 / −98.6 discrepancy was an unstable seed, not a model change

**Trigger.** The design handoff recorded `elite_te_early` at −92.9; a later export reported
−98.6 for the same arm, same seasons, same sigma, with no code change between them and no
stated reason. Flagged as the same failure shape as the sign-convention incident (ADR-025).

**Root cause.** Both `run_draft_sim.py` and `export_strategies.py` derived their per-strategy
seed as:

```python
seed = args.seed + int(sigma * 1000) + si * 97 + abs(hash(name)) % 1000
```

**`hash()` on a `str` is salted per process.** Python randomises `PYTHONHASHSEED` at
interpreter start unless it is pinned, so `abs(hash("elite_te_early")) % 1000` returned a
different value in every run — measured directly: 62, 49, 843 across three processes. Every
simulation therefore used a different effective seed while *reporting* `seed=20260725`, which
made the recorded seed actively misleading rather than merely incomplete.

**Neither number was wrong; neither was reproducible.** Re-running the arm across five fixed
master seeds:

| master seed | margin | seasons positive |
|---|---|---|
| 20260725 | −94.5 | 0/4 |
| 1 | −85.2 | 0/4 |
| 42 | −100.7 | 0/4 |
| 999 | −95.1 | 0/4 |
| 123456 | −92.4 | 0/4 |

Spread −100.7 to −85.2, sd 5.6. **Both previously reported values fall inside the
seed-induced band.** They were two draws from simulation noise presented as two measurements.

**Does it change any conclusion? No.** `seasons_positive` is **0/4 at every seed tested** —
`elite_te_early` is consistently negative regardless of seed, and the magnitude is stable at
roughly −93 ± 6. The finding survives; only the false precision of the point estimate does not.

**Scope was wider than the reported symptom.** The same pattern appeared twice more, in
`backtest.py`, seeding the per-position Spearman confidence intervals (`seed + hash(pos) %
1000`). Those intervals were also not reproducible. The `vbd_sum` and `starter_vbd` CIs used
plain integer seeds and were unaffected, so the ADR-025 board-vs-consensus figures stand.

**Fix.** `config.stable_offset()` — `zlib.crc32`, deterministic across processes — replaces
every `hash()`-derived seed. Four regression tests now guard it, including one that spawns
subprocesses (a same-process determinism check would have passed while the bug was live) and a
static scan that fails if any source file derives a seed from builtin `hash()` again.

**Lesson, and it is the same one as ADR-025.** Both incidents were a *reporting* failure rather
than an analysis failure: the arithmetic was fine and the conclusion was fine, but a number was
presented as more solid than it was. "Seeded RNG, seed recorded" was in the standing
requirements and was satisfied in letter while being false in practice. A claim of
reproducibility is worth nothing unless something actually re-runs and compares.

### ADR-029: Replacement levels re-derived from measurement — RB30/WR40/TE10/QB10

**Was** RB28/WR41/TE11/QB10, from an assumed flex split of RB 0.40 / WR 0.55 / TE 0.05.
**Now** RB30/WR40/TE10/QB10, from a measured split of RB 0.52 / WR 0.48 / TE 0.00.

**Method.** Rank every flex-eligible player by points scored under this league's exact rules,
remove the mandated starters (RB20/WR30/TE10), count who wins the 20 flex slots. 26 seasons,
2025 holdout excluded. Scoring engine verified empirically rather than assumed: a 100-yard
receiving game returns 13.5 against a generic half-PPR 12.5, and 200 yards stacks to 24.5.

**Regime breakdown, because a pooled mean is the construct `src/regimes.py` says to distrust:**
1999-2011 → RB31/WR39; 2012-2019 → RB29/WR41; post-2019 → RB31/WR39; last-10 → RB30/WR40.

**This is explicitly NOT a claimed improvement.** RB flex ranges 5 to 17 across seasons (sd
3.0), and the answer moves ±1 rank depending on window. RB28 vs RB30 is inside that noise.
Adopted for consistency with measurement — the project should not carry an assumed constant
when the thing it approximates is cheaply measurable — not because anything is expected to get
better. No result is predicted to change.

**TE is the one robust part.** Zero flex slots in every window tested; a tight end won a flex
slot in 2 of 26 seasons. TE11 → TE10 is the best-supported element of the change.

Downstream: every VBD changes, so `board.json` was regenerated and the data contract bumped to
**v1.3.0**. Additivity re-verified across all 378 players.

### ADR-030: Falling-TE claim refused on a code read, no measurement taken

`elite_te_early` is `_positional_bias({"TE": -45.0}, early_rounds=3)`: it applies a 45-rank
subsidy to tight ends in rounds 1-3 and then takes the argmin. **It never forces a TE — it is
already value-conditioned**, with a 45-rank tolerance.

The proposed "elite TE that *falls* to 23" policy is take-the-tier-1-TE-iff-he-is-the-highest-VBD-player,
i.e. a **0-rank** subsidy. That is a strict subset of the 45-rank case: whenever a TE is
genuinely best available, `elite_te_early` takes him too. **The fall cases are already inside
the measured −96.1.**

Per the red-team's own stated precondition, the pre-registration is **void** and the claim is
refused. No measurement taken, no FDR budget consumed.

One refinement the red-team did not state: in the conditional branch both policies select an
*identical player*, so the hypothesis "conditional ≈ BPA" is true **by construction rather than
by measurement** — the delta is exactly zero modulo path-dependence through later picks. That
is a stronger closure than measuring parity would have been.

The `+18` tier-1 TE weight stays out of the recommendation engine.

### ADR-031: FTN cannot answer alignment — a structural absence, not a sample limit

Slot-vs-outside alignment was ruled undeterminable from participation data and NGS cushion;
FTN charting (2022+) was the remaining candidate. It fails, and the distinction matters.

FTN is **play-level, not player-level**. All 29 columns describe the play, and **the table
carries no player identifier at all**. There is nothing to attach an alignment to.
`qb_location` is quarterback alignment, not receiver alignment.

So this is not "determinable on four seasons" nor "not determinable at this sample size" — it
is **not expressible in the source**. A short sample can be reported with a caveat; an absent
dimension cannot be reported at all. Any factor requiring alignment is blocked across every
ingested source.

### ADR-032: Play-caller table parked, schema defect fixed pre-emptively

Not ingested — 22 of 64 cells populated, the rest genuinely unknown because play-calling duty
is usually unannounced until camp. A plausible-looking table that is wrong in a dozen places
and gets ingested as fact is the failure being avoided.

**The schema was fixed now rather than at ingestion time.** The source CSV keys on
`(team, season)` with a single `play_caller`, which cannot represent a mid-season handoff —
Cleveland 2025, Stefanski to Rees, is the cited case. `src/ingest_play_callers.py` keys on
`(team, season, start_week)` with an explicit `end_week`: no change is one row spanning weeks
1-18, a handoff is two rows.

This is not cosmetic for test-registry #29/#30, which are *continuity* tests: a schema blind to
mid-season changes scores a team that switched play-callers in week 8 as perfectly continuous —
the exact opposite of the truth.

Ingestion refuses to run without a verified file and validates confidence values, source
citations, week ranges and key uniqueness before writing anything. Completion trigger is the
ESPN 32-team roundup published in late August; precedent verified for 2024 (id 41018846) and
2025 (id 46137832).

---

## 2026-07-25 (session 8) — backlog ADRs 033-038, written up from session 7's decision list

These six were decided in session 7 and recorded only as bullets in `status.md`. Written up here
so they are decisions of record. Short by intent — the reasoning, not prose.

### ADR-033: Prior-year repeat behaviour is demoted to display-only

**Decision.** The `repeat_2025 / half_repeat / no_repeat` switch no longer selects between
models. Prior-year manager behaviour is display context only.

**Why.** The switch was circular. The 60/13/0 spread in the TE availability table came almost
entirely from *assuming* two managers repeat their 2025 round-3 TE picks — so the output restated
the input with a probability attached. A number whose entire range is set by an unmeasured
assumption about two people is not a forecast.

**Status: NOT YET IMPLEMENTED.** The switch is still live in `availability.py` and the
`te_scenarios` block still ships in `availability.json`. Removing it requires recomputing
P(tier-1 TE at 23) under ADR-034's model and reporting the delta against 60/13/0. Until that
lands, **the shipped availability figures remain circular** and the contract's existing warning
(te_scenarios is "a conditional forecast under a named assumption", not a marginal probability)
is the only thing holding the line.

### ADR-034: New availability model — marginalise over ranking sources, never hard-assign

**Decision.** Replace the current model with: a ranking mixture per manager, mechanical roster
need, and rank noise. Ranking sources enter as a **posterior marginalised over** — never
hard-assigned, never argmax.

**Why.** Picking the single most likely ranking source per manager throws away the uncertainty
that is the entire quantity of interest. P(player survives to pick 23) is a question about the
spread of plausible rooms, and argmax collapses that spread to a point before the question is
asked.

**Pre-registered expectation:** no separation between managers before round 4. **If it never
separates, that is the finding** — it means opponent modelling cannot pay for itself at this
sample size, which is a legitimate result and must be reported as one rather than tuned around.

---

**Status: IMPLEMENTED (2026-07-25, session 9).** Also implements ADR-033's demotion —
`ScenarioPick`, `SCENARIO_PICKS`, `REPEAT_PROBS` and the named-manager repeat mechanism are
**deleted**, not kept as an option, from `src/availability.py` and `src/run_availability.py`.
`availability.json.te_scenarios` is removed from the contract (bumped to v1.6.0).

**The three inputs, applied per simulated draft:**

1. **Ranking mixture per manager.** Each of the 9 opponent teams draws a ranking source from a
   shared prior, freshly every draft — never assigned to a team, never collapsed to argmax.
   `RankingSource(name, rank)` + `default_ranking_sources()` gives one source today
   (`fantasypros_ecr`, weight 1.0), so the mixture is a no-op in practice, but the sampling path
   is real: a second source (MFL ADP, ADR-035) is a list entry, not a rewrite.
2. **Mechanical positional need.** `draft_sim.MECHANICAL_NEED_TARGETS`, derived as
   `STARTERS[pos] + FLEX_SLOTS` for flex-eligible positions (QB 1, RB 4, WR 5, TE 3) —
   structural, not assumed. Kept **separate** from `NEED_TARGETS` (QB 2, RB 5, WR 6, TE 2),
   which stays the judgement-call default for `opponent_pick`/`simulate_one` so the PR-003
   strategy-comparison numbers (already reproducibility-verified, ADR-028) do not move.
3. **Rank noise**, unchanged: one shared Gaussian(0, sigma) draw per player per simulated draft.

**Result: TE T1 @ pick 23 = 0.596** (sigma=10, 3000 sims), against the old unconditional
baseline of 0.5963 (the deleted table's 0%-forced-repeat row) — a move of **−0.0003**, inside
the pre-declared sanity bracket `[0, 0.60]`. Confirms "flatter, not flat" as predicted: the
mechanical TE need target (3) essentially never binds by pick 23 (round 3), regardless of model,
so removing the two-named-manager assumption barely moves the number. Most of the old table's
0.60-to-0.13 spread was the assumption itself, not signal the room actually contains.

**Pre-registered expectation partially addressed, not tested.** "No separation between managers
before round 4" needs per-manager output broken out, which the current `tier_avail`/`by_tier`
aggregates do not expose (they're pooled across all 9 opponents). Not measured this session —
flagging so a future session does not assume it was.

**Client-side re-simulation.** `availability.json` gains `client_simulation_parameters`
(ranking-source weights, mechanical need targets, room-noise spec, plain-English algorithm
description) so a client can recompute availability conditioned on live draft state.
`by_player`/`by_tier` remain unconditional marginals for Prep mode, flagged
`metadata.figures_are_unconditional_marginals`. **The client-side simulator itself is not
built here** — this is model parameters for a client to consume, not client code; building the
actual JS belongs to whichever session owns `ui/`.

### ADR-035: MFL ADP as `adp_source='mfl_proxy'` — partially supersedes ADR-018

**Decision.** Ingest MyFantasyLeague ADP under `adp_source='mfl_proxy'`. Joins natively on
`mfl_id`.

**Why it partially supersedes ADR-018.** ADR-018 concluded no market ADP was legally obtainable
(FFC blocked by `robots.txt`, Yahoo/ESPN behind OAuth). MFL is a source that route missed. It is
a **proxy**, not this league's ADP: different scoring, different room, different format.

**Binding constraint: never present it as this league's ADP.** It is a separate `adp_source`
value precisely so it cannot be silently blended into a consensus figure. Per ADR-024, ingest
per-source rows keyed by `as_of_date` with dispersion preserved — never a pre-blended point
estimate.

**Does NOT reopen the alpha track.** ADR-026 closed it on a count of *seasons*, not sources; an
additional source does not move the sign-test floor.

---

**Status: IMPLEMENTED (2026-07-25, session 9).** `src/ingest_mfl_adp.py` against the documented,
free, no-login endpoint `https://api.myfantasyleague.com/{period}/export?TYPE=adp&...&JSON=1`.
Descriptive User-Agent; 429 backoff honouring `Retry-After`; a new `adp_snapshots` table
(`CLAUDE.md`'s own core-tables sketch reserved this name) keyed
`(adp_source, mfl_id, retrieved_at)`, carrying `fcount`/`is_ppr`/`is_keeper`/`is_mock`/`cutoff`/
`period` per row per ADR-024's "never a pre-blended estimate" rule. One fetch per UTC calendar
day (`already_fetched_today()`), `--force` to bypass.

**MFL's `id` field is confirmed to BE `mfl_id`, not a value requiring a crosswalk.** Verified
against 10 sampled players (Ja'Marr Chase #1, Jahmyr Gibbs #2, Josh Allen #4, ...): 232/232
(100%) resolved directly against `ff_playerids.mfl_id`. No name matching was needed or used —
exactly as expected, since MFL is the source `mfl_id` itself comes from.

**Deliberately NOT a separate table joined against `rankings`.** `rankings` already has
`spread_sd`/`rank_best`/`rank_worst` (ADR-024) and CLAUDE.md's own `ranking_source` enum names
`market_adp` for exactly this case — reusing it was considered and rejected, because wiring a new
source into the table `make_board.py`/`backtest.py` read from risks changing board or backtest
behaviour as a side effect of an ingestion task, which nobody asked for this session.

**Sample size is small — flagged loudly, not buried.** `totalDrafts=50` behind this snapshot;
individual players' `draftsSelectedIn` ranged 5-58. `main()` prints a caution below 100 drafts.
This bounds what comes next.

**`load_mfl_adp_source()` (in `availability.py`) exists, is tested, and is NOT wired into the
shipped default.** It builds a second `RankingSource` for ADR-034's mixture, mfl_id-joined via
the ADR-036 hub (`player_ids WHERE source='gsis'`, reverse-looked-up against `SeasonData`'s
gsis-keyed player array). Against the live 2026 board: **138 of 378 players resolved to a real
MFL average pick**; the remaining 240 fall back to their FantasyPros ECR rank, since MFL's
snapshot only covers its own top ~232 picks across all rostered positions. Three reasons it stays
off by default, so a future session does not flip it on without addressing them:

1. A 50-draft sample is not an equal-weight peer to FantasyPros ECR's far larger analyst base —
   giving it a mixture weight (even 0.5) is an assumption, not a measurement, in exactly the
   sense CLAUDE.md §6.3 warns against. No holdout comparison has been run to justify any weight.
2. "The MFL source" is a blend by construction (real MFL data at the top, a copy of FP-ECR
   beneath) — worth knowing before trusting a mixture weight against it.
3. Enabling it would change `data/export/availability.json`'s shipped output as a side effect of
   an ingestion task. This session already moved that file once (ADR-034, bounds-checked against
   a pre-declared bracket); a second silent move in the same session, unmeasured, is exactly the
   failure shape ADR-025/028 both warned about.

**9 tests in `tests/test_ingest_mfl_adp.py`**, covering format-metadata storage, the
never-league_adp invariant, daily caching, and the fallback-to-consensus behaviour for
MFL-uncovered players.

### ADR-036: The identity hub is `mfl_id`, not `gsis_id`

**Decision.** `mfl_id` is the hub of the player-identity resolution layer. Collisions go to an
explicit table and are **EXCLUDED**; `resolve()` returns `None` and never guesses.

**Why.** Measured, not assumed (`data-availability.md` §8.2): `gsis_id` is **62.1% populated**
in the crosswalk with **10 known collisions**, and the `pfr_player_id -> gsis_id` leg that
snap-share features depend on resolves only 77-78% overall. A hub that is missing on a third of
rows is not a hub.

**Returning `None` is the point.** A guessed identity produces a confident wrong join that no
downstream check will catch. Per the standing rule, cross-source features must **state their
coverage and refuse unresolved rows**, never drop them silently — the drops are non-random,
skewing toward fringe roster spots where role changes actually happen.

---

**Status: IMPLEMENTED (2026-07-25, session 9), Task B.** `src/identity.py`. Built entirely from
`ff_playerids` (already ingested, no re-fetch) — `players_canonical` (one row per `mfl_id`),
`player_ids` (source, source_id, confidence, method, resolved_at), `player_id_collisions`.

**Re-measured over the full 12,468-row crosswalk, not the earlier estimate:**

| Source | Non-null | Collision groups | Resolvable (post-exclusion) |
|---|---|---|---|
| mfl_id | 100.0% | 0 | — (the hub) |
| gsis | 62.1% | 10 | 61.9% |
| pfr | 76.8% | 16 | 76.5% |
| espn | 65.3% | 13 | 65.1% |
| yahoo | 44.0% | 5 | 43.9% |
| sleeper | 50.9% | 6 | 50.9% |
| fantasypros | 38.3% | 2 | 38.3% |
| sportradar | 59.6% | 5 | 59.5% |

57 (source, source_id) pairs excluded to `player_id_collisions` project-wide. The prior estimate
(62.1% / 10 collisions for gsis) is confirmed almost exactly — the small gap between "non-null"
and "resolvable" in each row is the collision exclusion itself.

**`depth_chart` is not a distinct ID space.** `depth_charts_weekly`/`depth_charts_snapshots` key
rows by `gsis_id` (and `espn_id`), so a depth-chart row resolves through those spokes. Listed in
the requested source enum for completeness; there is no `depth_chart_id` column to crosswalk.
`resolve()` still accepts `"depth_chart"` as a valid source name and raises on anything not in
the enum, but there will never be a row under it in `player_ids`.

**Coverage restricted to the 378 board_2026 players — the number that matters, not the global
rate.** Board players carry no external ID (rankings has name only), so this first name-matches
against `players_canonical.display_name`: **402 of 408 matched (98.5%)** after normalizing
suffixes (Jr./Sr./II/III/IV/V) and punctuation — normalization improved the raw exact-match rate
from 91.2%. The remaining 6 are nicknames a simple normalizer cannot resolve (Hollywood Brown =
Marquise Brown, Gabe Davis = Gabriel Davis) or very recent additions the crosswalk may not carry
yet. **This name join feeds only the coverage REPORT, never `player_ids`** — a wrong match here
mislabels a statistic, not a downstream join a feature would trust.

Among the 402 matched, coverage is high for every source except Yahoo:

| Source | Coverage of matched board players |
|---|---|
| gsis / espn / sportradar | 99.0% |
| sleeper / fantasypros | 98.8% |
| pfr | 99.0% |
| yahoo | 80.6% |

Board-player coverage is far better than the global rate for every source, which makes sense —
the crosswalk is thinnest for players outside any current relevance (retired, practice-squad,
never-active), and the board only contains players FantasyPros ranks.

**Note: `board_players` was 408, not the 378 quoted elsewhere.** `board.json` holds 378 after
depth-of-fit filtering; the `rankings` table for `season=2026, source='fantasypros_ecr'` that
this coverage check queries directly holds 408 distinct names (30 more — likely players ranked
by FantasyPros but outside the board's drafted-relevance cut). Flagging the discrepancy rather
than silently reconciling it; it does not change any conclusion here.

**`name_dob_match_candidates()` / `manually_confirm()` exist with zero consumers this session.**
The requested schema names `method='name_dob_match'` as an enum value, so the function exists —
but MFL ADP (ADR-035) resolves against `mfl_id` directly and needs no name matching at all.
Nothing calls it in production. Birthdate narrowing is unimplemented for the same reason: no
caller supplies one, and writing DOB-matching logic with no test case to verify it against would
be exactly the over-engineering CLAUDE.md's gates flag. `manually_confirm()` stamps
`method='manual'` so a human-confirmed pair is never visually indistinguishable from an automated
crosswalk hit.

**13 tests in `tests/test_identity.py`**, including the core invariant: a source_id shared by two
`mfl_id`s must resolve to `None` for *both*, never a tiebreak.

**Status: NOT STARTED** (this is Task B). Gates the feature pipeline.

### ADR-037: Player profiles are display-only, enforced by test

**Decision.** Profile data is display-only and **test-enforced never to reach** `board`,
`backtest`, `scoring`, or `Facts`.

**Why enforcement is a test rather than a convention.** The project has already been burned twice
by a rule that was believed and not checked: three tests were silently evaluating on the 2025
holdout (ADR-022), and `hash()`-derived seeds satisfied "seeded RNG, seed recorded" in letter
while being false in practice (ADR-028). Profile content is unvalidated, partly absent (7 of 9
opponents have no data) and partly narrative; a leak into the board would be invisible in the
output and would contaminate a ranking with vibes.

The `Facts` exclusion matters most: ADR-027's whole mechanism is that the renderer can only say
what a Fact says. A profile reaching the Fact layer would route unverified prose straight to the
page with the project's credibility attached.

**Status: NOT STARTED.**

### ADR-038: Draft state records all ten teams, not just the user's

**Decision.** Draft state records every team's roster and picks. `team_slot` is derived from
snake order rather than stored per pick.

**Why.** Positional-run detection (test-registry #68), VONA, and any "the room is taking RBs
aggressively" signal are all questions about *other* teams. A user-only draft state cannot answer
them and would force a schema migration mid-draft — the worst possible time.

Deriving `team_slot` from snake order rather than storing it keeps the pick sequence the single
source of truth; a stored slot can disagree with the pick number, and then neither is trustworthy.

**Status: NOT STARTED.**

### ADR-039: DEF is permanently excluded from replacement levels — stated, not merely absent

**Decision.** No DEF replacement level. `league.json` gains
`positions_without_replacement_levels: ["DEF"]` plus a note; `board.json.def_supported` stays
`false`. Ingesting DST data is **not** planned.

**Trigger.** The front-end session reported the contradiction: `roster.starters` declares
`DEF: 1` while `replacement_levels` has no `DEF` key. A consumer reading `starters` alone would
reasonably expect a matching level.

**Why not just publish DEF10.** The replacement *rank* genuinely is derivable with no player data
(10 teams x 1 DEF starter — the same arithmetic that yields QB10), and that was the initial fix
attempted this session. It was reverted on the user's call. A published level invites a
downstream VBD, and the *points* half does not exist — no DST data is ingested. Publishing the
rank alone puts a number within reach of a consumer who cannot see which half is missing.
**Recorded explicitly so a future session does not rediscover the derivation and "fix" the
omission.**

The distinction being defended is the project's usual one: an absent dimension cannot be reported
at all (cf. ADR-031 on FTN alignment), and filling a field to make it look complete is the same
failure mode as inventing a number.

### ADR-040: Exports are strict JSON, enforced at write time

**Decision.** All three exporters write with `allow_nan=False`. A test parses every artifact with
`parse_constant` set to raise.

**The bug.** `league.json` shipped a bare `Infinity` token in `scoring.defense.points_allowed` —
valid Python, **invalid JSON** (RFC 8259). `JSON.parse` and `fetch().json()` both throw, so no
browser could load the file at all. It shipped for six commits, and the front-end session was
sanitising it at copy time to keep working.

**Why every Python test passed.** Python's `json` module accepts `Infinity`/`-Infinity`/`NaN` on
**both** read and write by default, so a Python round-trip is structurally incapable of catching
this. The test therefore makes the *reader* as strict as a browser, rather than checking for the
one token.

**Fix shape.** The open-ended tier is emitted as a `null` ceiling with an inline
`points_allowed_note`, because null means "not available" everywhere else in the contract and the
difference is load-bearing here. `float("inf")` stays in the scoring engine, which needs a
comparable bound; only the export drops it.

**Lesson, and it is ADR-028's again.** "The tests pass" is worth nothing when the test harness
shares the defect with the code under test. Both bugs were invisible to same-process,
same-language verification.

---

## 2026-07-26 (session 10)

### Diagnosis: consensus_rank mismatch is scoring-format, not staleness — DynastyProcess's mirror has no PPR dimension at all

**Trigger.** The board's `consensus_rank` doesn't match FantasyPros' current ECR. Diagnosed
against the live FantasyPros API (`.env` now populated), not fixed yet.

**Finding: (b), a scoring-format mismatch, is the primary cause — not (a) staleness.**
`nflreadpy.load_ff_rankings(type="all")` (the DynastyProcess mirror `src/ingest_rankings.py`
pulls from) exposes 44 `page_type` values and exactly **one** `ecr_type` value (`'ro'`) for
`page_type='redraft-overall'` — there is no half-PPR-specific, PPR-specific, or standard-specific
variant anywhere in the mirror. It is a single unparameterized "overall redraft" snapshot.

The live FantasyPros API, by contrast, genuinely supports `scoring=HALF` and returns a
materially different product for it (`type=ST&scoring=HALF` → "Draft Half PPR", `total_experts=92`).
Comparing the same player (Bijan Robinson) confirms the two are not identical: our stored row
(`adp_rank=2, adp_value=3.1, as_of_date=2026-07-24`) is close to but not the same as the live
half-PPR API's `rank_ecr=1, rank_ave=2.01` pulled one day later — close enough that (a) staleness
is a minor contributor (the board is ~1-2 days behind), but the *systematic* gap traces to
ingesting an unparameterized snapshot whose underlying scoring convention was never confirmed to
be half-PPR at all, not to the day-to-day lag.

**(c) positional-vs-overall confusion: ruled out.** `fetch_preseason_rankings()` sorts by the
single `ecr` column and assigns rank by that order alone; no positional/overall mixing is
possible in the current code.

**Switching to the live API is straightforward for the format problem, blocked for coverage.**
The API takes `scoring=HALF` directly and updates daily (`last_updated` field, confirmed same-day
for the ECR type). But — see `docs/deferred.md`'s FantasyPros entry — the free tier caps every
response at 10 players with no working pagination, so it cannot deliver a full ~580-player board
in any number of calls on this tier. **Fixing the format problem and fixing the coverage problem
are two different blockers; only a paid tier resolves both.**

**Not fixed this session** — diagnosis only, per instruction. `ingest_rankings.py` still pulls the
DynastyProcess mirror; `PAGE_TYPE = "redraft-overall"` is unchanged.

---

## 2026-07-26 (session 10, items 1-2) — Multi-league support

### ADR-041: LeagueConfig + DraftEngine, directory-per-league exports — IMPLEMENTED

**Decision.** `src/league_config.py` (`LeagueConfig`, versioned, JSON save/load, `CURRENT_LEAGUE`
= today's league as its first instance) + `draft_sim.DraftEngine` (a league-parameterized
equivalent of the module's free functions). Every export function now takes a `cfg`, defaulting
to `CURRENT_LEAGUE`.

**`DraftEngine` is a parallel implementation, not a refactor.** Every function above the
`DraftEngine` block in `draft_sim.py` is byte-for-byte untouched. A "wrap the existing functions"
design was considered and rejected: PR-003's numbers are ADR-028-verified byte-identically
reproducible, and even a behavior-preserving refactor of RNG-adjacent code risks changing call
order or floating-point accumulation in some way a test suite might not catch. Verified directly
(not just by test): `DraftEngine(CURRENT_LEAGUE)` reproduces `pick_order`/`opponent_pick`/
`legal_mask`/`strategy_bpa` output identically to the module-level functions on real 2026 season
data, and `availability.simulate_availability(engine=None)` -- the default -- is confirmed
byte-identical to before this change.

**Generalizes the single hardcoded "final round is DEF" rule to `reserved_rounds()`:** one
auto-filled, unsimulated round per starter position with no scoring engine (K, DEF -- no kicker
or DST stats are ingested for either). For the primary league this is exactly the old behavior.

**`NEED_TARGETS`/`MAX_AT_POSITION` stay the primary league's exact judgement-call numbers** for
`league_id="primary"` only. Any other league gets a mechanical formula
(`starters[pos] + flex_slots` for eligible positions) instead of an invented human-behavior
constant -- consistent with ADR-034's own reasoning for why the availability model prefers
mechanical need over a guessed one.

**Exports: directory-per-league, not an embedded dimension.** The primary league's six artifacts
stay at the unprefixed `data/export/` path -- the front-end session's sync is never disrupted.
Every other league's six artifacts land at `data/export/<league_id>/`, same filenames, same
shape, each carrying `league_id`. Rejected embedding a `{leagues: {id: {...}}}` dimension inside
each file: breaks the documented shape for every existing consumer immediately, balloons file
size with N leagues, and a one-league change risks a shared-file lock/partial-write.

**`nulls.json` findings do NOT carry across leagues.** PR-002/Hero-RB/elite-TE/QB-early/
board-vs-consensus are computed under the primary league's exact scoring rules and roster shape
(`spike_persistence.py`'s hardcoded 100/150/200 bonus thresholds; `draft_sim`'s STARTERS/scoring
engine). Presenting them under a different `league_id` would misrepresent them as measured for
that league. A non-primary league's `nulls.json` keeps each finding's identity/method but
replaces `result`/`plain_language_summary` with `"NOT_YET_RUN_FOR_THIS_LEAGUE"`. **Only the
alpha-detection closure (ADR-026) is structurally invariant** -- a function of how many consensus
seasons exist, not of any league's rules -- confirmed correct in the design-note pass and
unchanged here.

**Timing, measured, not estimated:** `board.json`+`league.json` ~7s; a full `availability.json`
recompute (3000 sims x 3 sigmas) ~45-60s; `strategies.json` (43,200 sims) ~13 min, unchanged by
league count since the cost is simulation count. Board+availability can support a
recompute-on-settings-change UI flow with a loading state; strategies stays a queued job.

**Verified content-preserving for the primary league at every step**, not just "tests pass": each
of `export_contract.py`/`export_static.py`/`run_availability.py`'s rewrites was diffed against
`git show HEAD` (ignoring `generated_utc`/`contract_version`) before proceeding to the next file.
Every diff was additive fields or explicitly-noted prose genericization (e.g. "the other nine
teams" -> "the other opposing teams", `2` shared flex slots -> generic phrasing) -- zero numeric
value changed for the primary league. Contract bumped 1.6.0 -> **1.7.0**.

### Item 2 -- Yahoo-standard 12-team mock league: generated a complete valid export set, two real gaps found and fixed, both named

Built `data/leagues/yahoo_standard_mock.json`: 12 teams, standard (0-PPR, no yardage bonuses)
scoring, K+DEF rostered, 1 flex (not 2), slot 6. Ran the full fast-tier pipeline
(`run_availability.py` -> `export_contract.py` -> `export_static.py`) against it with **zero
further code changes beyond the two fixes below**. Result: 6 strict-JSON-valid artifacts at
`data/export/yahoo_standard_mock/`, correct on inspection -- QB12/RB30/WR30/TE12 replacement
levels (12 teams, 1 flex, borrowed RB/WR split), `unsupported_positions: ["DEF","K"]`,
`roster.kicker: true`, 15 rounds, snake pick sequence starting `[6,19,30,43,...]`, 0-PPR/no-bonus
scoring correctly threaded through every player's score, 11 of 11 opponents correctly generic
(no named managers exist for a league that was never told any), `nulls.json` correctly showing
`NOT_YET_RUN_FOR_THIS_LEAGUE` throughout.

**Total regeneration time: ~47s** (41s availability + 6s board/league + 0.3s static) -- in the
same range as the primary league, confirming the design note's prediction that league count
does not change the fast-tier cost.

**Two real parameterization gaps found, both fixed (named per instruction, not silently
patched):**

1. **`make_board.py`'s `_season_actual_points()` always scored every player under the PRIMARY
   league's rules**, ignoring whatever league it was nominally building a board for -- there was
   no `scoring_cfg` parameter at all before this session. This is not cosmetic: without the fix,
   a Yahoo-standard board's VBD numbers would have been computed with the wrong PPR value and
   wrong (nonexistent) yardage bonuses, silently. Fixed by threading `scoring_cfg` through
   `_season_actual_points` -> `collect_observations` -> `fit_rank_curves`/`bootstrap_vbd_intervals`
   -> `build_board`, defaulting to `None` (-> the primary league's `scoring.LEAGUE`) everywhere, so
   the primary league's call sites are unaffected.
2. **`run_availability.py`'s summary generator hardcoded pick numbers `(18, 23)`** for the
   "headline" section -- the primary league's own `picks[1]`/`picks[2]`. Running against the
   12-team mock raised `KeyError: 18`, since pick 18 does not exist in that league's sequence at
   all. Fixed to `picks[1:3]` (verified to reproduce `[18, 23]` exactly for the primary league
   before accepting the fix).

**Deliberately NOT fixed, named instead of patched around:**

- **`backtest.py` has its own separate, hardcoded `STARTER_SLOTS`/`FLEX_SLOTS`/`FLEX_ELIGIBLE`/
  `ROSTER_PICKS`** (a pre-existing duplication of `draft_sim.py`'s constants, not introduced this
  session). Re-running the accuracy-track backtest harness per league -- refitting curves,
  re-locking holdouts -- is a materially larger task than "generate an export set" and was not
  attempted.
- **No kicker scoring engine exists**, and none was built. `_scoring_for_export` requires a
  `defense.points_allowed` structure but nothing analogous for kickers; K is handled exactly like
  DEF always has been (`unsupported_positions`), which is the right posture per ADR-039's own
  logic, not a workaround.
- **`RELEVANT_DEPTH` (`make_board.py`, curve-fitting depth per position) stays a fixed,
  cross-league constant.** It plausibly should scale somewhat with league size; not measured or
  parameterized this session.
- **`MAX_AT_POSITION` for a non-primary league is an explicitly-flagged, unmeasured heuristic**
  (`mechanical_need_targets + bench`), not a measurement -- the primary league's own numbers are
  themselves a judgement call with no formula behind them, so there was nothing to generalize
  from. Flagged in the export (`max_at_position_note`) rather than presented as derived.
- **`flex_split` for a new league is a borrowed placeholder** (the primary league's ADR-029
  measurement), flagged via `flex_split_measured: false` in both `board.json` and `league.json`.
  A real measurement requires re-running that 26-season analysis under the new league's own
  scoring rules, which was not attempted.

**23 new tests** (`test_league_config.py`, `test_draft_engine.py`, `test_multi_league_export.py`),
covering config validation, engine/primary-function parity, the mock league's structural
generalization, and export-function-level assertions (not just file inspection) for both leagues.
**288 tests passing project-wide.**

---

## 2026-07-26 (session 10, item 3 continued) -- Mock draft logging

### ADR-042: Mock draft validation instrument -- ingestion + full report (Levels 1-2, Tertiary, Brier-vs-baseline)

**Decision.** `src/ingest_mock_drafts.py` (file-based ingestion, matching the front end's schema
exactly) + `src/mock_validation_report.py` (Levels 1-2 of `mock_validation_protocol.md`).
Primary consumer, stated explicitly per instruction: **validating the availability model** --
every availability figure this project has shipped (ADR-034's mixture, the sigma schedule) has
been unvalidated against any real draft behavior until this exists.

**Schema exactly as specified, no additions**, since the point is ingestion needing no
translation from whatever the front end exports:

```
mock_drafts(mock_id, league_config_id, platform, drafted_at, source, is_mock)
mock_picks(mock_id, overall_pick, round, team_slot, mfl_id, player_name_raw,
           predicted_top, predicted_p, timestamp)
```

Plus `mock_pick_quarantine(mock_id, overall_pick, player_name_raw, mfl_id_supplied, reason,
quarantined_at)` -- not in the front-end schema, ours alone, for unresolved picks.

**Name resolution: `identity.resolve_name()` (new, public -- promoted from a private helper
already proven at 98.5% coverage in `coverage_report_for_board`).** Zero or ambiguous (>1)
matches go to quarantine, never a guess -- the same invariant `resolve()` already enforces for
ID-based lookups, extended to names. A supplied `mfl_id` is validated against
`players_canonical`, not trusted blindly.

**Both protocol discard gates now implemented** (bot-seat closed out in the same session by
ADR-043 below):

1. **Format-mismatch** (10-team/3WR-2FLEX/no-kicker/half-PPR) -- `format_conforms()`, checked
   against the mock's `league_config_id` at ingestion, stored per mock, never silently adjusted.
2. **Bot-seat gate** (>3 bot seats discarded) -- see ADR-043.

**Report: all four pieces built -- Levels 1-2, Tertiary, and the Brier-vs-baseline test.**
Level 1 (positional depletion at the primary league's own first 7 picks -- computed as
`ds.user_pick_numbers()[:7]`, confirmed to equal the protocol's literal [3,18,23,38,43,58,63])
and Level 2 (per-player calibration, 3 buckets not 5, per the protocol's own reasoning that the
board is fixed across mocks so effective N is ~40 players, not player x mock count) reuse the
already-shipped `data/availability_2026.csv` for predictions rather than re-simulating.

**Tertiary (`level3_dispersion_report`)** -- the protocol calls this "the highest-value output of
the whole exercise" -- runs a FRESH simulation at reduced `n_sims` (500, vs. production's
3000-4000) rather than approximating SD from the shipped CSV's percentile summary, because an
IQR-based SD estimate would assume near-normality the project has no basis for asserting. This
runs REGARDLESS of mock count: the model-side "implied SD" is a property of the model alone and
is always computable, so at 0 mocks the report still shows what the model currently predicts
dispersion to be, with the observed side correctly `None`. Failure criterion 4 (SS5) is checked
literally: observed SD outside `[0.5x, 2.0x]` of the implied SD **at sigma=10 specifically**, not
a comparison against the sigma=5/20 simulated SDs (which happen to sit near that same band by
construction of `SIGMA_SWEEP`, but the protocol's literal wording anchors the band to one
reference number).

**Brier-vs-baseline (`brier_vs_baseline_report`)** -- protocol SS1/SS5 criterion 2, **the actual
pass/fail gate**, not a secondary diagnostic. Fits `P(survive) = sigmoid(a + b*(pick - rank))` by
MLE (scipy, already a dependency) on the SAME conforming-mock pairs its Brier score is then
computed on -- not a train/test split, matching how `backtest.py`'s own baseline arms are
computed directly from the season being scored. **Note on the protocol's own text:** it labels
this "a one-parameter logistic" while showing a two-parameter formula (`a` and `b`); the explicit
formula was taken as authoritative over the prose label. Requires >=10 (player, pick) cells to
fit at all; below that, reports `NOT_EVALUATED_INSUFFICIENT_DATA_FOR_BASELINE_FIT` rather than a
degenerate fit.

**Both new checks correctly report "no measurement", not a fabricated number, at n=0 mocks** --
`_power_note()` scales language at 0 / <10 / <30 / >=30 mocks throughout the whole report,
matching the protocol's own power table.

**35 new tests** (`test_ingest_mock_drafts.py`, `test_mock_validation_report.py`) across this and
the prior session's pass, including seeded (non-zero) cases for depletion counting, bot-seat
filtering, the dispersion band, and the logistic fit's sign (not just convergence). **329 tests
passing project-wide.**

### ADR-043: Bot-seat gate -- `drafter_type` added as an optional per-pick field, decided not deferred

**Decision.** `mock_picks.drafter_type` (`'human' | 'bot' | 'unknown'`, nullable) is added to the
schema -- the ONE exception to "schema fixed to what the front end exports, no additions",
because without it the protocol's `>3 bot seats discarded` gate is permanently unenforceable, not
merely under-supported.

**Behavior, exactly as decided:**
- **No pick in a mock supplies `drafter_type` at all** -> `bot_seat_status='unknown'`. The whole
  mock is flagged, not silently included as passing or excluded as failing.
- **At least one pick supplies it** -> the number of DISTINCT `team_slot`s with `drafter_type=
  'bot'` is counted (a seat picking multiple times counts once, not once per pick) ->
  `bot_seat_status='conforms'` (<=3) or `'excluded_too_many_bots'` (>3, a HARD discard, same
  treatment as `format_conforms=0`).
- **`unknown` status mocks are INCLUDED in the report, with a caveat, not excluded.** Excluding
  every `unknown` mock would make the report permanently show zero usable mocks until a mock
  platform happens to expose per-seat bot/human status, which defeats the instrument's purpose.
  `mock_validation_report.py` states the count of `unknown`-status mocks used in every render,
  not as a footnote.

**Migration, not a rebuild.** `mock_drafts`/`mock_picks` are an accumulating log, unlike the
rebuild-from-source tables in `ingest_reference.py`/`identity.py` -- `ensure_tables()` now
`ALTER TABLE ADD COLUMN`s the two new fields (`mock_picks.drafter_type`,
`mock_drafts.bot_seat_count`) rather than dropping and recreating, so already-logged real mock
data is never destroyed by a schema change.

---

## 2026-07-26 (session 10, item 2) -- Player descriptions

### ADR-044: Archetype assignment + display-only player descriptions

**Decision.** `src/archetypes.py` (assignment) + `src/player_descriptions.py` (description
generation + export), per `archetype_taxonomy.md` (the Strategist's brief, supplied by the user).

**Implemented exactly as specified, not re-derived.** RB (5 of 6 labels -- see HANDCUFF below),
WR (5 labels), TE (4 labels), evaluation order as stated (BELL_COW -> PASSING_DOWN -> EARLY_DOWN
-> COMMITTEE for RB), confidence tiers (high >=12 games, medium 8-11, UNDETERMINED below 8),
t-1 labeling (archetype for draft season S computed from season S-1 actuals only), rookies
UNDETERMINED by construction, data floor at 2013 (offense_pct/snap_counts start then -- the
taxonomy's own "binding floor for any archetype using both targets and snaps").

**Thresholds are the taxonomy's stated conventions, not independently verified here.** The brief
says so itself: "I have not measured those breaks... plot the actual distributions... before
use." That verification pass was not performed. **Concretely visible in the live run:** Keenan
Allen (2025 season, ts=0.224, op=0.555, adot=8.42) falls through EVERY WR criterion --
HIGH_VOLUME needs op>=0.70 (fails), POSSESSION needs op>=0.60 (fails at 0.555), ROTATIONAL needs
op<0.55 (fails at 0.555, just over) -- landing in the exact mid-mass gap the taxonomy warned
about. Pinned as a regression test (`test_undetermined_mid_mass_gap`) rather than patched with a
tie-breaker, since inventing one would be exactly the "forcing assignment" the taxonomy's SS0
rejects.

**RB_HANDCUFF NOT IMPLEMENTED -- named, not silently dropped.** Needs a preseason depth chart,
which the taxonomy itself says is unavailable on any development season ("assignable live for
2026... not validatable... treat separately"). A player who would otherwise qualify (low
offense_pct, low volume) falls through to `RB_UNDETERMINED` rather than a guessed label.
`test_handcuff_not_implemented_falls_through_to_undetermined` locks this in.

**Data pipeline.** `carry_share`/`target_share` are SEASON-TOTAL ratios (sum player / sum team
across the same weeks), not an average of nflverse's own per-week `target_share` column --
chosen for consistency between the two shares (there is no equivalent pre-computed `carry_share`
column to average instead) and to avoid small-sample weekly-ratio noise. `offense_pct` comes from
`snap_counts` (already ingested, ADR from an earlier session), joined via the ADR-036 identity
hub's `gsis -> mfl_id -> pfr` double-hop -- collision-excluded on both legs, same invariant as
every other cross-source join in this project, not a shortcut through the raw `ff_playerids`
table.

**Live run, 2026 draft season (data season 2025):** 527 RB/WR/TE assigned, 237 high confidence,
86 medium, 204 undetermined. Sanity-checked by name: Christian McCaffrey -> RB_BELL_COW, Derrick
Henry -> RB_EARLY_DOWN, Travis Kelce/Zach Ertz -> TE_PRIMARY_RECEIVER -- all match the intuitive
read of their actual 2025 roles.

**Descriptions: deterministic templates, not a live language model call.** `license_tag=
'ai_generated'` describes the CONTENT's nature (synthetic, assembled from measured data, never
adapted from a real scout's text) -- not a claim that an LLM API was invoked at generation time.
A live call would make output non-deterministic, contradicting "regeneratable... never
hand-frozen" and "test-enforced": `test_description_is_deterministic_across_calls` asserts
byte-identical text (excluding the `generated_at` timestamp) across repeated calls on the same
assignment. This follows ADR-027's precedent directly: Layer 1 (facts) is pure and deterministic,
an LLM-based Layer 2 renderer was explicitly deferred there for the identical reason.

**UNDETERMINED produces NO description, enforced by tests, not just by the code path.**
`generate_description()` returns `None` outright for any `*_UNDETERMINED` (or generic
`UNDETERMINED`) archetype -- no placeholder sentence, no "not enough data" line attached to a
named player. `test_no_description_for_undetermined_players_in_real_run` cross-checks this
against a live `assign_for_season()` run, not just synthetic fixtures.

**Display-only, enforced by a static scan, same pattern as ADR-028's `hash()` ban.**
`TestDisplayOnlySeparationEnforced` fails if `narrate.py`, `scoring.py`, `make_board.py`,
`backtest.py`, `candidate_rankings.py`, `draft_sim.py`, or `availability.py` contain the string
`player_descriptions` or `archetypes` at all -- not "the field is unused," but "the import path
does not exist," which is the stronger guarantee ADR-027's Fact/Renderer wall already
established for narration. A second test asserts `narrate.py`'s `Fact.kind` enum never grows an
`archetype`- or `player_description`-shaped entry, so a description can never reach the Facts
pipeline that the front end's renderer is allowed to read from.

**Export: a standalone artifact, deliberately NOT wired into `export_contract.py`'s board
pipeline.** `player_descriptions.export_player_descriptions_json()` writes
`data/export/player_descriptions.json` independently -- "never a model input" is easier to keep
true when the description pipeline has no import path into the board-building code at all, not
merely a promise not to read the field once it's there. Verified byte-identical across two
independent runs against the same DB state (excluding timestamps) before committing, same
verification discipline as every export change this session.

**36 new tests** (`test_archetypes.py`, `test_player_descriptions.py`), including the static
enforcement scan, the mid-mass-gap regression case, and export determinism/strict-JSON checks
against the live DB.

---

## 2026-07-26 (session 11) — Live-availability adjustment, N_t(p) wired in, multi-config matrix

### ADR-045: Live-availability adjustment — hazard model, SS5(a) lambda measurement

**Decision.** `src/live_availability.py` implements the Strategist's
`live_availability_adjustment.md` spec in full: per-pick hazard back-out from the Prep-mode
marginal, roster-need term `N_t(p)`, positional-run term `R(p)`, global renormalisation, and
survival-by-product across the gap. `src/lambda_estimation.py` implements SS5(a) — the
conditional-logit measurement the spec required be run *before* writing any of the above.

**SS5(a) was run first, on real data, per instruction.** The one real draft this project has
(the actual 2025 league draft, 160 picks, 10 teams) was ingested via `ingest_mock_drafts.py` as
`mock_id='2025_league_draft_real'`, `is_mock=0` — the user supplied it as structured JSON
reconstructed from screenshots, now committed at `data/real_drafts/2025_league_draft.json`.
145 of 160 picks resolved to an `mfl_id`; the 15 that quarantined are exactly the expected
cases (9 team defenses, which have no player identity to resolve at all per ADR-039, plus 5
ambiguous historical-name collisions and one nickname mismatch — correct behavior, not a bug).
Ingesting this did not break `test_level3_dispersion_report_computes_real_implied_sd` (asserts
`NOT_EVALUATED_NO_MOCKS` against the real DB): with `n=1` conforming mock, observed-SD still
requires ≥2 mocks to compute a sample variance, so `n_checked` stays 0 and the status is
unchanged. Verified by running that test, not assumed.

**Why the regression reads the source JSON directly, not `mock_picks`.** `mock_picks` has no
`position` column (it stores identity, not position), and the 9 DEF picks — exactly the
near-hard-cap behavior SS2's own table is built on — have no `mfl_id` to join through at all.
Reading the source file loses nothing; reading the ingested table would silently drop the
positions this test most needs.

**Model: a conditional logit (McFadden), one shared covariate, no alternative-specific
intercepts** — `P(position taken=p) = softmax(beta * x_p)`, `x_p = log(share_t(p)/share_bar(p))`.
This is exactly the functional form `N_t(p) = (share_t(p)/share_bar(p))^lambda` implies for pick
choice under the need mechanism alone (ADP/rank preference is not in this regression — a stated
limitation of the test, not an oversight). Fit by MLE (scipy), cluster-robust SE by team (a
scalar M-estimator sandwich: `Var = (sum_c S_c^2) / H^2`, no numeric Hessian needed — a conditional
logit's Hessian is the fitted-softmax variance of `x`, a standard closed form). The MLE machinery
itself is verified on synthetic data generated from a known beta before trusting it on the real
draft (`test_conditional_logit_recovers_known_beta_on_synthetic_data`).

**Result: `lambda_hat = 0.352`, `se_clustered = 0.070`, `z = 5.04`, n=160 picks, 10 team
clusters.** Clearly nonzero and correctly signed — a saturated position's need share drops,
suppressing further picks there, exactly as SS2 predicts. **Adopted as `DEFAULT_LAMBDA`,
replacing the 0.5 prior**, per the spec's own decision rule ("either supports the need mechanism,
gives a data-derived lambda, or shows the effect is indistinguishable from zero"). **Explicitly
flagged, not oversold:** 10 clusters is a small-cluster regime where cluster-robust SEs are known
to under-cover (z=5.04 should not be read as a precise p-value), one season confounds need with
round (everyone has deficits early in every draft), and this is a *prior with a wide true
interval*, not a validated measurement — CLAUDE.md SS6.3's bar is not cleared by this alone.

**`delta=0.10` ships as the spec's own unvalidated prior, unchanged.** SS5(b) (run-detection
validation) needs mocks with **per-pick draft state logged**, which does not exist and was
explicitly out of scope this session (not to be added without a separate decision — the mock
schema is otherwise fixed to what the front end exports, per ADR-042). The spec's own decision
rule is recorded here so a future session does not need to re-derive it: **if ≥30 conforming
mocks with per-pick state accumulate and Arm 2 (need+runs) does not beat Arm 0 (the marginal) on
Brier score, set `lambda = delta = 0` and ship the marginal alone.**

**Checks #1 and #7b were written first, per instruction, as they are named as the two most
likely to catch a real bug.** Both passed on first implementation, along with #2–#9 written
immediately after in the same order as the spec's table. All are synthetic/self-consistent unit
tests (a fixture where `h0_true` sums to exactly 1 by construction), not integration checks
against the shipped Prep-mode CSV — **check #3 (`SUM h0(Y) ≈ 1` on the real marginal) cannot
currently be checked empirically**: `availability.json`/`availability_2026.csv` only track
per-player probabilities for the top ~80 players; the rest of the undrafted pool exists only as
tier-level aggregates, so the full-pool sum can't be reconstructed from the shipped artifact.
Noted as a real limitation, not silently worked around.

**Target vector verified before any code was written:** `{QB:1.0, RB:5.5, WR:7.0, TE:1.5,
DEF:1.0}` sums to exactly 16 (= roster size) — checked with a module-level assertion in
`live_availability.py`, not just eyeballed, so a future edit to `TARGET` cannot silently break
every `share_bar` denominator without the import itself failing loudly.

**13 new tests** (`test_live_availability.py`) + **8 new tests** (`test_lambda_estimation.py`).

### ADR-046: `N_t(p)` wired into the draft simulator's `strategy_balanced`

**Decision.** `draft_sim.strategy_balanced`'s flat "-8.0 if any STARTER slot is unfilled" step
function is replaced with `live_availability.n_need()`'s continuous, share-based `N_t(p)`,
evaluated against the same 2025-observed final-roster `TARGET` every other `N_t(p)` consumer
uses — not just the mandatory `STARTERS` minimum. The new adjustment is
`-NEED_ADJUSTMENT_SCALE * (N_t(p) - 1)` per position, `NEED_ADJUSTMENT_SCALE = 10.0`.

**This changes `strategy_balanced`'s simulated behavior for the WHOLE draft, not just the
opening rounds.** The old rule went silent the moment starters filled (round 2–3 for most
positions); the new one grades every remaining pick by how far the team's current composition
sits from the target *share*, so a team already 3-deep at RB is actively steered away from a 4th,
which the old step function could not express at all (it only ever asked "have I met the
minimum," never "have I taken too many").

**`NEED_ADJUSTMENT_SCALE=10.0` is an explicit, UNMEASURED proportionality constant** — same
posture as `NEED_PENALTY_PER_SURPLUS` and `MAX_AT_POSITION`, both already unmeasured judgement
calls in this file. No backtest calibrated it; it was chosen only to land in the same rough order
of magnitude as the flat -8.0 it replaces, so this is a considered starting point, not a claimed
improvement. A real calibration would compare roster-point outcomes under a swept `SCALE` against
the existing `bpa_consensus` baseline via `draft_sim.py`'s own simulator — not attempted this
session.

**`strategies.json`'s `balanced` arm is now stale relative to the code** the moment this landed;
regenerated in this same session (`python src/export_strategies.py`, ~13 min) so the shipped
artifact and the code do not silently diverge — see the session handoff for the refreshed
numbers.

**4 new tests** (`test_strategy_balanced.py`), including a tied-board fixture where the choice
between two identically-ranked players is decided purely by the need adjustment (confirms the
mechanism actually changes strategy behavior, not just its internal arithmetic) and a fresh-roster
case confirming the adjustment is exactly zero with no picks made (N_t(p)=1 everywhere, matching
check #1's null-parameter reasoning in ADR-045).

### ADR-047: Multi-config board/VBD matrix — team-size × scoring × roster-shape (first stage)

**Decision.** `src/generate_config_matrix.py` generates 24 `LeagueConfig`s and their `board.json`
+ `league.json` (no availability simulation, no strategies): 4 team counts (8/10/12/14) × 3
scoring variants (standard/half-PPR/full-PPR, reception value only) × 2 roster shapes
(ESPN-default, Yahoo-default). All 24 saved under `data/leagues/` and exported to
`data/export/<league_id>/`, same convention as ADR-041's Yahoo mock.

**Platform defaults used, from the researcher pass supplied 2026-07-26 mid-session:** ESPN
(QB1/RB2/WR3/TE1/FLEX1 RB-WR-TE/DEF1/K1, bench 7, roster VERIFIED, scoring unverified — bot
detection blocked the fetch) and Yahoo (QB1/RB2/WR3/TE1/FLEX1 **RB/WR only, no TE**/DEF1/K1,
bench 5, fully verified). **NFL.com and Sleeper deliberately excluded from this pass** —
NFL.com's roster is verified but its FLEX is W/R-only (a third, distinct shape, not a variant of
either included one) and its scoring is unverified; Sleeper has nothing platform-confirmed at
all (a possible 2-FLEX build is third-party-sourced only). Guessing either would have been
exactly the "leave platform variants for a later pass rather than guessing" the queued task
named as the fallback — except the fallback was not needed for ESPN/Yahoo, since real confirmed
shapes arrived before this item was reached.

**Scoring axis varies ONLY the reception value (0.0/0.5/1.0).** Yardage bonuses, TD values, INT,
and defense scoring are held at this project's existing `LEAGUE` ruleset (`scoring.py`) across
all 24 configs — which is not an arbitrary choice: it is *identical* to ESPN's confirmed bonus
structure (same +1/+1.5/+2 tiers at the same 100/150/200 rush/rec and 300/350/400 pass
thresholds). Yahoo's bonus structure was not confirmed by the researcher pass, so no
platform-specific bonus variant is claimed for it either — this matrix answers "how do team size,
PPR value, and roster shape move the board," not "what does Yahoo's board look like on Yahoo's
exact scoring," which remains unanswered pending a verified Yahoo bonus structure.

**Board-only, verified cheap.** ~7s/config confirmed (matches the ADR-041 timing measurement);
`availability.json` is written but carries empty `by_player`/`by_tier` (no CSV exists for a
config that was never run through `run_availability.py`) — the same "not yet run for this
league" state every fresh non-primary league starts in, not special-cased here.
`nulls.json`/`strategies.json` are not generated for any of the 24 at all.

**Spot-checked, not just executed:** `espn_12_full` → QB12/RB30/WR42/TE12 replacement levels
(12 teams, 1 flex), 17 rounds, `receptions=1.0`, `unsupported_positions=[DEF,K]`; `yahoo_14_standard`
→ QB14/RB35/WR49/TE14, 15 rounds, `flex_eligible=[RB,WR]` (no TE), `receptions=0.0`. Round counts
differ by roster shape as expected (ESPN 17 = 9 starters+1 flex+7 bench; Yahoo 15 = 9+1+5) and are
constant across team count within a shape, as they should be — round depth is a per-roster
property, not a league-size one.

**6 new tests** (`test_generate_config_matrix.py`), including a full-crossing check (all 24
`(platform, teams, ppr)` triples present, no duplicates) and one real-DB smoke export
(`espn_12_full`) confirming the whole `write_all` pipeline round-trips through strict JSON
without crashing.

## 2026-07-27 — ADR-046: Mock Lab live-logging store, event-sourced (thread 025 + 040 amendment)

**What.** `src/mock_lab_store.py`, new tables `mocklab_drafts` / `mocklab_picks`. Pick-at-a-time
live logging (create → append → undo → close) for the ~29 un-logged mocks the product's
calibration claim depends on, per thread 025. Separate from `ingest_mock_drafts.py` /
`mock_drafts` / `mock_picks`, which remain the batch, after-the-fact ingestion path — reconciling
the two (closed mocklab draft → batch JSON shape) is deliberately deferred, not silently merged.

**The design thread 025 specified was superseded before this was built, not after.** 025 asked for
write-once, immutable prediction storage. Thread 040's AMENDMENT (2026-07-27, same day) corrected
the PM's own earlier undo design and, with it, 025's premise: an availability prediction is a pure
function of board state at pick N, so recomputing it after an undo — with the SAME model version
that made the original call — reproduces exactly what live entry would have produced. That is not
hindsight contamination. The actual risk is regrading an old mock under a NEWER model, which would
inflate calibration for free without the model improving at anything.

So the store is event-sourced: `mocklab_picks` is an append-only, truncatable log and the only
source of truth. Predictions are derived on demand (`predict_next_pick` / `replay_predictions`),
never stored. `mocklab_drafts.model_version` is pinned at creation; `replay_predictions` raises
`ModelVersionMismatch` the moment the module's current `MODEL_VERSION` has moved past the pinned
value, and there is no override. That one comparison is the entire safeguard. Per the amendment,
there is deliberately **no** `voided_by_undo` flag and **no** undo counter — that bookkeeping
belonged to the retracted design and would misrepresent a now-ordinary action as costly.

Thread 040 item 2 (slot) is satisfied narrowly: `create_mock(..., slot, teams)` accepts any slot
1..teams, validated against the caller's own league config rather than assuming the founder's
slot 3. Deriving a full pick sequence from an arbitrary slot/team-count and wiring the *reviewed*
hazard model (`live_availability.py`, ADR-045) to it is **not** done here — see gap below.

**The gap, stated rather than papered over.** The reviewed hazard model predicts survival to a
future pick from a prep-mode Monte-Carlo marginal (P0) that today exists only for the founder's
own primary-league pick sequence (`data/availability_2026.csv`). A general P0 source for arbitrary
slots/configs is real modelling work, not wiring, and guessing it would be exactly the unmeasured
constant CLAUDE.md prohibits. What ships instead is ADR-D's own D-3 model-free baseline
(`baseline_id/MODEL_VERSION = "adp_rank_exp_v1"`): probability of being the next pick decays by a
fixed, **unfitted** exponential (`DECAY_K = 0.15`, chosen by fiat per ADR-D, not measured — zero
parameters estimated from any mock data, so no SE is owed) in the player's frozen consensus board
rank among the undrafted pool. This is not a stand-in pretending to be the hazard model; it is the
same baseline ADR-D already specs co-measuring alongside it. **Follow-up, not yet scheduled:** wire
the real hazard model in once a general P0 source exists, bump `MODEL_VERSION`, and old mocks stay
correctly frozen under their own pinned version rather than silently regraded.

**Brier scoring and calibration bucketing** (`brier_score`, `calibration_buckets`) are built over
the derived-baseline predictions, per thread 025 item 3. `calibration_buckets` skips (not errors on,
not silently pools) mocks whose pinned version no longer matches current `MODEL_VERSION`, returning
the skip count so a caller can see coverage was reduced.

**ADR-D's dwell/entry-mode/blind-arm instrumentation (thread 034) is explicitly out of scope here**
— that is frontend entry-surface + strategist statistical design, not storage, and remains a
separate open thread. This store's schema does not preclude adding those columns to
`mocklab_picks` later; it does not add them now.

**Tests written first**, per CLAUDE.md's non-negotiable ordering: `tests/test_mock_lab_store.py`,
20 tests, covering slot validation, duplicate-mock/duplicate-pick rejection, closed-mock rejection,
undo-truncates-not-voids, undo-then-reentry pick-number reuse, absence of any undo counter, the
model-version-mismatch refusal (and that it is silent/permitted when unchanged), Brier bounds and
a zero-Brier degenerate case, and calibration bucket skip-counting. All 20 pass in isolation
(`pytest tests/test_mock_lab_store.py`, not run against the full suite this session per instruction
to avoid DB contention with concurrent agents).

**No contract/export-schema change.** This is server-side storage with no export artifact yet;
Mock Lab UI wiring and any resulting `mocks.json`/similar export are follow-up work for whichever
session builds the UI against this store.

## 2026-07-26 — ADR-C: pre-registration convention, extended (thread 020)

Implemented `docs/adr-drafts/ADR-C-preregistration.md` in `src/preregistration.py` and
`src/holdout.py`, extending (not replacing) the existing `docs/preregistration/` tree —
PR-001..003 and the two `.jsonl` logs keep their filenames and schemas.

**What landed:**
- A second, richer registration format (`Registration` dataclass, `load_registration`,
  `require_confirmatory`) alongside the original flat `PreRegistration` loader: nine typed
  front-matter fields for confirmatory tests (`id`, `test_registry_id`, `family`, `mode`,
  `question`, `metric`, `threshold`, `data_scope`, `frozen`), four for exploratory
  (`id`, `mode`, `question`, `frozen`). `resampling_unit` defaults to `season` for
  confirmatory registrations and any other value requires a non-empty `power_note` — the
  default is the guardrail, not an option to configure around.
- **The one rule with teeth:** `record_amendment(..., data_seen=True)` irreversibly rewrites
  `mode: exploratory` into the file itself, with no override flag. `Registration.effective_mode`
  also demotes in memory even if a caller never re-checks the file, so a demoted registration
  cannot gate a confirmatory run either way (`require_confirmatory` raises).
- **Content-hash integrity** (`compute_content_hash`, `verify_content_hash`,
  `check_registration`): a registration mutated on disk without a matching `amendments:` entry
  fails `check_registration` — the mechanism the ADR calls out as necessary because "a silent
  edit is a valid commit and nobody re-reads history."
- **Family manifests** (`docs/preregistration/families/*.yaml`, `open_family`,
  `register_confirmatory_test`, `Family.m`/`status`) fix the BH denominator before tests run.
  Adding a confirmatory test to a `closed` family reopens it and increments `m` (recomputing
  and republishing prior BH adjustments in that family is a manual follow-up this session does
  not automate — flagged, not silently skipped). A `closed-unsealed` family
  (`close_family_after_unseal`) never reopens — "one look is one look."
- **`holdout.load_season(year, prereg_id)`** — the ADR's primary data-access guard. Raises
  `HoldoutViolation` if `year` falls outside the registration's `data_scope.seasons`, or if
  `year` is the locked 2025 holdout and `data_scope.holdout_unsealed` is not `true`.
  Defense-in-depth beyond the ADR's literal text: even a registration declaring
  `holdout_unsealed: true` is refused unless `docs/preregistration/UNSEAL_LOG.md` also carries
  a signed, named-approver entry for that `prereg_id` (`unseal_is_logged` /
  `append_unseal_log`) — the front-matter flag alone is a value anyone could flip; the log
  entry is the audit trail. A successful unsealed read is routed through the existing
  `HoldoutLock.final_evaluation` context, so it lands in the same, already-trusted
  `holdout_access_log.jsonl` rather than a second log.
- **`validate_exploratory_artifact`** rejects `p_value`/`ci_lower`/`ci_upper`/`significant` keys
  on any result reported under `mode: exploratory` — point estimates and plots only.

**Deliberately deferred, out of scope for this session** (restricted to
`src/preregistration.py` and the holdout guard while other agents worked other files in
parallel): the `prereg` CLI (scaffolding new registrations, `prereg check` as a pre-commit
hook/CI gate) and retrofitting PR-001..003 into the new front-matter fields. The ADR's
existing loader (`load_preregistration`/`require_preregistration`) and PR-001..003 are
untouched and still pass their own tests unchanged. Both deferred items are real gaps — there
is currently no enforcement stopping an analysis script from running without calling
`require_confirmatory` by hand — and should be the next thread if this convention is to have
its intended teeth rather than being available-but-optional.

**No YAML dependency available in the environment** (`import yaml` fails — no PyYAML
installed), so nested fields (`data_scope`, `frozen`, each `amendments` entry) are restricted
to single-line YAML *flow* style (`{k: v, k2: [a, b]}`) and parsed with a small hand-rolled
flow parser, rather than adopting multi-line YAML block mappings that would need a real
parser to get right. This is a real constraint on the format, not a stylistic choice, and
should be revisited if a `pyyaml` dependency is later added to the project.

Tests: 65 passed (`tests/test_preregistration.py` + `tests/test_holdout.py`, `-q`, targeted
run — full suite not run this session per instruction, to avoid DB contention with concurrent
agents).

### ADR-049: `league_builder.py` — real league creation from founder-facing parameters (thread 040 item 1)

**Decision.** Added `src/league_builder.py`: `create_league(name, teams, starters, flex_slots,
flex_eligible, bench, ir, user_draft_slot, ...)` builds and saves a `LeagueConfig` from plain
parameters (not a hand-built dataclass call), `export_league(cfg, out_dir, conn)` recomputes
board/league/availability/rosters for it via the existing `export_contract.write_all`, and
`create_and_export_league(...)` chains both. This is the missing capability thread 040 named:
before this, a "new league" meant either the founder's own hardcoded config or one of the 24
pre-generated combinations in `generate_config_matrix.py` — there was no path from a person
typing a name, team count, roster shape, scoring rules, and draft slot into a config that
actually recomputes.

**What was already correct and did NOT need fixing.** The thread's stated worry — that
replacement levels might get reused across leagues instead of measured per format — turned out
to already be handled. `scoring.ReplacementLevels.from_league_config()` (ADR-041) and
`export_contract.build_board_json(conn, cfg)` (ADR-041/047) already derive replacement levels
from whatever `LeagueConfig` is passed in, not from a module-level default; `tests/
test_multi_league_export.py` already covered this for the 24-config matrix. `league_builder.py`
does not touch that arithmetic at all — it only makes the *config* reachable from friendly
inputs. `tests/test_league_builder.py::test_replacement_levels_differ_by_format` and
`::test_create_and_export_league_board_uses_its_own_replacement_levels` (DB-backed) confirm
this directly: a 14-team, 1.0-PPR, 2-RB/2-WR/1-TE-starter probe league gets `QB14` (not `QB10`)
and a `board.json["replacement_levels_used"]` that is not `{"QB":10,"RB":30,"WR":40,"TE":10}`.

**`flex_split` is deliberately never passed in by `create_league`.** A new league's true flex
split has not been measured — ADR-029 measured the founder's specific league over 26 seasons
under its exact scoring. Omitting it means `from_league_config` takes its existing explicit
placeholder path (`measured=False`, primary league's split borrowed and flagged) rather than
this module silently baking a borrowed number into the saved config as if it were this league's
own.

**League-id slugging.** `slugify()`/`unique_league_id()` turn a display name into a filesystem-
and export-path-safe id (`data/leagues/<id>.json`, `data/export/<id>/`), reusing the same
directory convention ADR-041/047 already established, and disambiguate collisions with a
numeric suffix. The reserved `primary` id is refused — that identity belongs to
`lc.CURRENT_LEAGUE` specifically.

**What this explicitly does NOT build.** No API layer, no job queue/polling, no tier-1
(instant) vs tier-2 (~60s recompute) distinction, no shadow-recompute-then-apply state
machine — all of that is `docs/design-handoff/settings/SETTINGS-EDITOR-SPEC.md`'s contract for
the Settings editor UI, which no frontend agent is building this round. `export_league()` is a
synchronous, blocking call (~7-10s per the existing config-matrix timing, ADR-047) — the same
shape `write_all` already has for the 24 pre-generated configs. A future API layer wraps this
function in a job; this ADR does not attempt to guess that layer's shape.

**Scope note.** `create_league` accepts a `scoring_overrides` dict (shallow-merged into the
`offense` block of `scoring.LEAGUE`, deep-copied so the shared module constant is never
mutated) plus a `ppr` shortcut for reception value — enough to cover the Settings spec's
"Scoring rules" and "Yardage bonuses" editing surface (SS3) at the data layer. It does not
validate scoring values for football-plausibility (e.g. a negative passing-yards divisor) — the
existing `LeagueConfig.validate()` catches structural errors (roster/draft-slot/flex
consistency); a bad scoring number would currently only surface as an implausible board, not a
raised error. Flagged, not fixed here — same triage as the frontend contract requirements in
the spec's SS7, which are also unimplemented pending an API layer.

Tests: `tests/test_league_builder.py`, 19 passed (`-q`, targeted run; one `@pytest.mark.
requires_db` integration test, the rest pure/tmp_path-isolated). `tests/test_league_config.py`
+ `tests/test_multi_league_export.py` re-run targeted, 26 passed, no regression — confirms this
addition did not touch the existing per-config export path, only added a new entrypoint to it.

### ADR-048: `board.json`'s `player_id_gsis` populated — the join key for the history exports

**Decision.** `player_id_gsis` was a specified field the pipeline never populated — not a
structural impossibility. `src/export_contract.py::build_board_json` hardcoded
`"player_id_gsis": None` for every player (thread 052, raised by pm off a flag left in thread
017/039's own reply). Fixed by threading the id `make_board.build_board` already has in hand
straight through: `rankings.player_id` **is** a gsis_id (`src/ingest_rankings.py` joins
`fantasypros_id -> gsis_id` and inserts the result *as* `player_id` — see that file's own
`preseason ECR for season, joined to gsis_id` docstring), and it was simply being dropped on
the floor between `_consensus_board()`'s row and `BoardRow`. Added `player_id: Optional[str] =
None` to `BoardRow` (`src/make_board.py`), populated from `r["player_id"]` in `build_board()`,
and wired it into `export_contract.py`'s `player_id_gsis` field.

**Why gsis, not `mfl_id`, even though ADR-036 makes `mfl_id` the identity hub.** The thread-052
ask worried about recreating the identity-resolution problem with a second, competing scheme.
This is the opposite: `weekly_finishes.json`/`season_stats.json` (thread 017/039,
`src/export_history.py`) already key every row on `player_weekly_stats.player_id`, which is
nflverse's own gsis-format id — the same id space `rankings.player_id` already lived in before
this fix, untouched. Routing through `mfl_id` instead would mean (a) resolving board's gsis ids
through the ADR-036 hub's gsis spoke, which ADR-036 itself measured at only 62.1% crosswalk
coverage with 10 collisions, a strictly worse number than the direct join measured below, and
(b) adding `mfl_id` to `export_history.py`'s two files as a *second* key alongside their
existing `player_id`, which is exactly the "second identifier scheme" thread 052 warned against.
Using the id both sides already independently derive from nflverse is not a new scheme; it is
finishing the wiring of the one that was already there.

**Coverage, measured, not asserted.** Board regenerated (`data/export/board.json`, primary
league config): **378/378 (100%)** of board players now carry a non-null `player_id_gsis`.
Cross-referenced against `weekly_finishes.json`: **371/378 (98.15%)** of board `player_id_gsis`
values resolve to a `weekly_finishes.json` player. The remaining ~7 are players on the board
with zero rows in `player_weekly_stats` at all (no prior-season history — plausible for rookies
entering the 2026 draft class) — an honest null on the history side, not a join failure on the
key side. Not independently re-checked against `season_stats.json` (same `player_id` universe
as `weekly_finishes.json` by construction in `export_history.py`, so the number would be
identical or extremely close; flagged rather than silently assumed).

**Not a `CONTRACT_VERSION` bump.** `player_id_gsis` already existed in the schema at this name,
this type (`str|null`), this position — only the *value* changed, from always-null to actually
populated. `docs/data-contract.md`'s own convention (see its 1.9.0 entry) reserves version bumps
for shape changes; this is a data-quality fix to a field that was already contracted. Recorded
in `docs/data-contract.md`'s changelog as a labeled non-bump entry so it isn't mistaken for
silence.

**2025-in-exports holdout question, recorded DECIDED.** Thread 052 also asked backend to record,
not re-derive, whether including season 2025 in `weekly_finishes.json`/`season_stats.json`
touches the holdout lock. It does not — displaying historical facts is not model selection.
Written into `docs/decisions-needed.md` as **D-022, DECIDED**, with the reasoning and the
binding going-forward rule, specifically so a future session does not "fix" this by hiding 2025
from the UI.

**Tests.** Added `test_board_row_carries_player_id_field` (`tests/test_make_board.py`) before
the `BoardRow` field existed, and
`test_player_id_gsis_is_populated_and_matches_rankings_player_id`
(`tests/test_export_contract.py`) before `build_board_json` was wired — both red first, per this
project's sanity-check-before-implementation rule. `tests/test_make_board.py` +
`tests/test_export_contract.py` + `tests/test_export_history.py`: **71 passed** (targeted run,
not full suite — concurrent-agent DB contention this round per dispatch instructions).

### ADR-050: T9 team-code crosswalk, T5 freshness tripwire, T6 interim roster-status proxy, T4 interim suspension mechanism (fable-table-stakes-2026-07-27.md)

**Context.** Four work orders from the table-stakes review (FR-007: correctness floor before
edge, unconditionally), taken as one parallel round while a separate session does DB-writing
work on the half-PPR ECR swap. This round is `src/`+`tests/` only, no ingestion, no DB writes.

**T9 — team-code crosswalk, fully landed.** `src/team_codes.py`: a flat variant->canonical
mapping (canonical = current-era nflverse 2-3 letter code), covering every code variant this
project's own tables were found to actually carry — FantasyPros (`JAC`/`LAR`), era relocations
(`OAK`->`LV`, `SD`->`LAC`, `STL`->`LA`), and two different PFR-style abbreviation schemes found
in `draft_picks` and `adp_snapshots` (`GNB`/`KAN`/`NWE`/`NOR`/`SFO`/`TAM`/`PHO`/`RAI`/`RAM`/`SDG`
and `GBP`/`KCC`/`NEP`/`NOS`/`TBB`/`LVR`/`JAC`/`LAR` respectively) — 54 distinct codes total,
verified by a DB sweep test (`tests/test_team_codes.py::test_every_distinct_team_code_...`)
against `rankings`, `player_weekly_stats`, `snap_counts`, `draft_picks`,
`depth_charts_snapshots`, `injuries`, `adp_snapshots`. No `play_callers` table currently exists
in `nfl.db` despite being named in the review (the module `src/ingest_play_callers.py` exists
but its table isn't populated in this DB) — not swept, flagged rather than silently skipped.
`to_canonical()` raises `KeyError` on an unrecognized code (never guesses); `export_contract.py`
wraps it in a fail-open `_canonical_team()` at the one call site that must not crash a whole
board build over one bad code, so the existing T3 positive-coverage test remains the fail-loud
mechanism instead of an uncaught exception.

**Acceptance evidence.** `tests/test_floor_checks.py::test_t3_every_board_player_has_a_bye_week`
was pinned RED by an earlier session with the exact live symptom (22 players, JAC/LAR
unresolved). Wiring `team_codes.to_canonical()` into both sides of `export_contract.py`'s bye
lookup (the `byes` dict's keys via `_bye_weeks()`, and the lookup key via `team_of.get()`) and
regenerating `data/export/board.json` turns it green with no other change. This is measured, not
asserted: reran the test before and after, red then green.

**T5 — freshness tripwire, fully landed.** `src/freshness.py`: `snapshot_age_days()` (pure,
injectable `today` for testability), `check_freshness()` (non-raising, always-computed report:
`{as_of_date, age_days, max_age_days, stale}`), `require_fresh()` (raises `StaleSnapshotError` on
stale-or-absent). `league_config.LeagueConfig.freshness_max_age_days: int = 3` — labeled a
suggested default, not a measured constant, founder-tunable per league. Wired into
`export_contract.build_board_json()`: prints the freshness report unconditionally (age surfaced
even when comfortably fresh, per the work order's explicit ask) and raises before building if
stale. Deliberately NOT wired into `make_board.build_board()` itself — that function is also the
historical/backtest board-build path across training seasons, and gating it there would make
backtests over old seasons fail on "staleness" that is meaningless outside the live-season
context. The gate lives only in the live-board export path.

**T4 — interim suspension mechanism, built but NOT wired into the live board.**
`src/suspensions.py`: `load_suspensions()` (fixture loader), `adjust_for_suspension()`
(deterministic games-played deduction, `SEASON_GAMES=17`, floors at 0, only applies when
`appeal_status` is settled — `pending` flags without adjusting, an explicit
`not_adjusted_pending_appeal` reason rather than guessing at a games count that could still
change), `apply_suspension_flags()` (attaches flag/games/adjusted-points/reason to board-row-
shaped dicts, same four keys on every row regardless of suspension status). `tests/fixtures/
suspensions_2026.json` is **explicitly synthetic** — this session had no way to verify a real
2026 suspension list against the pipeline (post-training-cutoff, thread 057 still open on
whether any structured source exists), and fabricating one would violate the project's own "do
not fill gaps with plausible-sounding invention" rule. Given the fixture's gsis_ids are fake and
match no real player, wiring it into the live board would be cosmetic rather than meaningful, so
it was deliberately left disconnected from `export_contract.py`. **Blocked-on-thread-057** for
the real data; the mechanism is ready to receive it without further code changes once a real
list exists.

**T6 — interim roster-status proxy, fully landed on an existing signal, not a new ingest.**
`contracts.is_active` already existed in `nfl.db` from an earlier ingest, but it means "this
specific contract row is the player's current one," not "this player is on an NFL roster this
week" — verified this is NOT a usable active-roster flag directly (Josh Allen, an active
starter, carries `is_active=0` on his two older contracts and `is_active=1` only on the newest).
The usable derived signal: a player with **zero** `is_active=1` rows across their entire
contract history has no currently-active contract on file — verified against Tom Brady
(`gsis_id 00-0019596`, retired 2023): all ~9 of his contract rows read `is_active=0`, the same
shape a released/inactive player would show. `src/roster_status.py::contract_status()` returns
`active` / `no_active_contract_on_file` / `unknown_no_contract_data` (rookies/undrafted players
with zero contract rows — an honest "don't know," never inferred as retired). Wired into
`export_contract.build_board_json()` as a new `roster_status` field on every board row,
labeled in-code as a proxy, not a roster-status feed. **Full nflverse roster-status ingestion
(active/IR/practice-squad, per-week) is out of scope for this round** — it needs new DB writes,
which this session is deliberately not doing (parallel session doing DB-writing ECR-swap work).
Smallest schema addition data-ops would need for the real thing: a `roster_status_weekly` (or
similar) table from `nflreadpy.load_rosters()`/`load_rosters_weekly()`, keyed by
`(gsis_id, season, week)` with a `status` enum (`ACT`/`IR`/`RES`/`PUP`/... per nflverse's own
`status` column) and `as_of_date`.

**Contract version bumped 1.9.0 -> 1.10.0** (board.json rows gained `roster_status`). Handoff
thread opened to `frontend`. `tests/test_rosters_export.py::test_contract_version_bumped` updated
to match (was pinning the pre-bump value).

**Tests.** All four T-numbers' tests written before their implementation modules existed, per
this project's sanity-check-before-implementation rule (`tests/test_team_codes.py`,
`tests/test_freshness.py`, `tests/test_suspensions.py`, `tests/test_roster_status.py`), plus the
pre-existing `tests/test_floor_checks.py::test_t3_...` as the T9 regression pin. See session
report for the full pass count.

## ADR-051 — make_board.py rewired onto fantasypros_csv_2026draft; SOURCE/TRAINING_SOURCE split introduced (2026-07-27, backend, thread 053/067)

**What changed.** `src/make_board.py`'s live/display consensus board (`SOURCE`) moved off the old
`fantasypros_ecr` DynastyProcess mirror onto the founder's own FantasyPros Half-PPR CSV export
(`fantasypros_csv_2026draft`, ingested by `src/ingest_fantasypros_csv.py`, data-ops session earlier
this day). The old source was rank-only (no scoring format), effectively capped, and ambiguous
about which scoring format it reflected; the new source carries a confirmed `scoring_format` and
real `tier`/`bye_week`/`sos_season` columns.

**Why this needed a split, not a straight swap.** `fantasypros_csv_2026draft` is a single, one-off
2026 pull with no season history (`rankings` table: only `season=2026` under that source).
`make_board.py`'s rank-\>points curve (the thing that turns consensus rank into `projected_points`
and `vbd`) is fit on MULTIPLE PRIOR SEASONS — `fantasypros_ecr` has 2021-2025. Pointing the curve
fit at the new source would silently starve every position of training observations
(`collect_observations` returns empty per season, `_fit_one` returns `None` under 5 points, and
`build_board` drops every position from the board with **no error raised** — an empty board, not a
crash). This was caught before landing, not discovered after.

**Resolution:** two module constants, not one.
- `SOURCE = "fantasypros_csv_2026draft"` — the CURRENT-SEASON consensus board that is displayed,
  ranked, and reported in `board.json`'s `board_source`/`consensus_source`/`scoring_format` fields.
- `TRAINING_SOURCE = "fantasypros_ecr"` — stays the historical source the rank->points curve
  fits against (2021-2025), completely independent of which source is on display. This is a
  genuine, deliberate divergence between "what the board looks like" and "what the projection
  model was fitted on" — flagged so a future session doesn't "simplify" it into one constant
  without re-deriving multi-season history for the CSV source first.
- `_consensus_board`, `collect_observations`, `resolve_training_seasons`, `build_board`,
  `board_as_ranking` all gained an explicit `source` parameter (defaulting to the constant that
  was already implicit in each call site) so callers needing the historical source
  (`board_ranking_for_season`, the backtest baseline arm — **backtests run over historical
  seasons that only exist under TRAINING_SOURCE**) don't silently break against a 2026-only source.

**export_contract.py:**
- `board_source` / `consensus_source` updated to name `fantasypros_csv_2026draft`.
- New top-level `board.json` field `scoring_format`, read from `rankings.scoring_format` for the
  live source's rows (not hardcoded) — `null` if absent or mixed. This is the field the app header
  needs to show the confirmed Half-PPR format.
- The `team_of`/`positional_rank` lookup (previously hardcoded to `fantasypros_ecr` literally, a
  latent bug independent of `make_board.SOURCE`) now reads `make_board.SOURCE` so it stays in sync
  with whichever players `ours` actually contains.
- `CONTRACT_VERSION` bumped **1.10.0 -> 1.11.0** (new field). Handoff thread opened to `frontend`
  (see `docs/handoffs/OPEN.md`).
- `av.default_ranking_sources()`'s hardcoded `"fantasypros_ecr"` label (Monte Carlo opponent-model
  `ranking_sources` block in `build_availability_json`) was deliberately **not** touched — that
  subsystem's consensus source is independent of `make_board.SOURCE` and out of this rewire's scope;
  flagged for a future session if that model is ever pointed at the new CSV source too.

**Rebuilt boards, measured:**
| | Old (`fantasypros_ecr`) | New (`fantasypros_csv_2026draft`) |
|---|---|---|
| Primary league board player count | 378 | 511 |
| `ethans_expert_league` board player count | (not previously rebuilt this session) | 511 |
| 2026 rookies spot-checked (Jeremiyah Love / Carnell Tate / Jordyn Tyson) | present | present, real ranks (#33 / #70 / #84) |

**Tests:** two tests added pinning `make_board.SOURCE`/`TRAINING_SOURCE` to their expected literal
values (`tests/test_make_board.py`); four existing fixture-backed tests updated to pass
`source=make_board.TRAINING_SOURCE` explicitly since the shared fixture only seeds
`fantasypros_ecr` rows; `tests/test_rosters_export.py::test_contract_version_bumped` updated to
1.11.0. `tests/test_holdout_audit.py`'s `CONNECT_ALLOWLIST` gained `ingest_fantasypros_csv.py`
(same-shape ingestion script as the other allowlisted `ingest_*.py` files; this was a gap in the
allowlist from the earlier data-ops session, mechanical fix, not part of the rewire itself).

---

### ADR-052: Yardage bonuses verified to STACK — T2 closed, live scoring fixture added

**Decision.** T2 (`docs/reviews/ACTION-PLAN-2026-08.md`) and pre-mortem failure #4
(`docs/reviews/fable-draft-day-premortem-2026-07-27.md`) are **CLOSED**. CLAUDE.md §7's league
scoring table has been verified against the live Yahoo platform for the project's primary
league, "Westwood" (league ID 154693, 10 teams), and matches value-for-value.

**What was actually verified, and by what evidence — stated precisely because the two pieces of
evidence prove different things.**
- The scoring *tiers themselves* (25 yds/pt with +1/+1.5/+2 at 300/350/400 passing, same 10
  yds/pt shape with +1/+1.5/+2 at 100/150/200 for rushing and receiving, 4pt pass TD, -2 INT,
  0.5 PPR, 6pt rush/rec TD, etc.) are directly visible in `docs/screenshots/League Settings
  2.png`–`5.png`, dated 2026-07-27, and were cross-checked field-by-field against CLAUDE.md §7
  and `scoring.py`'s `LEAGUE` dict — an exact match.
- The **stacking mechanic** — that a player crossing multiple thresholds in one game gets *all*
  applicable bonuses added, not just the highest one — is **not** visible on the Yahoo settings
  screenshot. That page shows tier boundaries, not a worked multi-threshold example. The actual
  evidence for stacking is the founder's own statement, made directly to the PM session today,
  that this was confirmed by checking the live platform's behavior (not just its settings page).
  This ADR is honest about that distinction rather than implying the screenshot alone proves
  additive-vs-replacing.

**`scoring.py` reviewed, found already correct, not modified.** `score_offensive_game()` (`src/
scoring.py`) implements the bonus logic as three independent `for threshold, bonus in
off[...]["bonuses"]: if <yardage> >= threshold: score += bonus` loops — passing at lines 61–63,
rushing at lines 70–72, receiving at lines 80–82. Because each loop iterates every threshold
tuple and unconditionally adds the bonus for every one that the yardage total clears (there is
no `elif`, no `break`, no "take the max" reduction), a player who clears all three thresholds
gets all three bonuses added. This is structurally the stacking behavior the founder confirmed
on the platform. No change was made to this file — per the founder's own instruction, this
session's job was to verify the claim and add a test, not to "improve" already-correct code.

**Fixture added.** `tests/fixtures/league_scoring_live.json` — the live-verified offense scoring
table, sourced from the screenshots, dated 2026-07-27, tagged with league identity (Westwood,
Yahoo, primary, 10 teams), roster shape, and playoff structure. Includes a `_meta.note` stating
explicitly that the fixture proves the tiers, not the stacking mechanic (see above). Also
transcribes the defense/special-teams table for completeness (per the founder's instruction),
flagged as unconsumed by any code path (ADR-039, no DST scoring ingested).

**Two discrepancies found while transcribing, flagged rather than silently fixed or silently
ignored, both confined to the DEF side which nothing in the codebase consumes:**
1. `blocked_kicks`: screenshot value is 2, `scoring.py`'s `LEAGUE["defense"]["blocked_kicks"]` is
   1.
2. `points_allowed` tier boundaries are **off by one** at every threshold. Screenshot bands are
   0→10, 1–6→7, 7–13→4, 14–20→1, 21–27→0, 28–34→−1, 35+→−4 (upper-bound-inclusive). `scoring.py`'s
   `points_allowed` list `[(0,10),(7,7),(14,4),(21,1),(28,0),(35,-1),(inf,-4)]`, walked with a
   first-match `pa <= ceiling` loop, actually returns 7.0 (not 4.0) for `pa=7` and 4.0 (not 1.0)
   for `pa=14` — verified directly by calling `score_defense_game` (`{"sacks":0,
   "points_allowed": 7}` → 7.0; `{"points_allowed": 14}` → 4.0). Neither is fixed here: DEF
   scoring has zero consumers in this codebase (ADR-039), and this session's scope was offense
   verification without touching `scoring.py`'s logic. Left as a documented known gap in the
   fixture's `_blocked_kicks_discrepancy` / `points_allowed_tiers_note` fields for whoever
   eventually wires up DEF scoring.

**Team count and roster shape, closed as a side effect (feeds FR-012/CLAUDE.md §7 "known
gaps").** 10 teams; QB / WR / WR / WR / RB / RB / TE / W-R-T / W-R-T / DEF starters, 6 bench, 1
IR — read directly off `League Settings 4.png`'s roster-positions row and cross-checked against
`League Info 1.png`'s 10-team list.

**Playoff weeks — checked, no discrepancy found (resolves the open verification rider from
FR-009/ADR-E amendment E-A1).** `League Settings 3.png` states "4 teams - Week 16 and 17."
`src/league_config.py:56` already has `playoff_weeks: Tuple[int, ...] = (16, 17)`. These match
exactly. The "championships are weeks 15–17" phrasing that appears elsewhere in the docs
(`docs/adr-drafts/ADR-E-bottom-up-projection-framework.md`, `docs/reviews/ACTION-PLAN-2026-08.md`)
is not corroborated by this screenshot and should not be treated as authoritative over it.

**Tests.** `tests/test_scoring.py`: added `test_live_fixture_offense_matches_scoring_league`
(field-by-field fixture-vs-`LEAGUE` comparison), `test_live_fixture_metadata_sanity` (team
count, roster shape, playoff weeks), and `test_yardage_bonuses_stack_all_applicable_thresholds`
(425 rushing yards → 47.0, exercising all three rushing bonus tiers at once — a case that would
fail immediately under an `elif`/max-only implementation). All three written against the fixture
and the existing `scoring.py` before confirming they pass, per this project's
sanity-check-before-implementation rule. Full file: **19 passed** (`pytest tests/test_scoring.py
-q`).

## ADR-053 — T4 real interim suspension list wired into the live board; T5 freshness verified with real integration coverage (2026-07-27, backend, thread 057 partial close)

**T5 (freshness tripwire) — verified, not rebuilt.** Traced every call site: `export_contract.
build_board_json` calls `fr.require_fresh(conn, SEASON, make_board.SOURCE, cfg.
freshness_max_age_days, ...)` unconditionally (default `enforce_freshness=True`) before building
any board, and every league config funnels through this same function via `write_all` — there is
no per-league special case to go stale silently in. `tests/test_freshness.py` had thorough unit
coverage of the pure functions (`snapshot_age_days`/`check_freshness`/`require_fresh`) but no
integration test proving the real entrypoint (`build_board_json` against the real `data/nfl.db`)
actually raises. Added `TestBoardBuildActuallyRefuses` (2 tests): one forces staleness via the
`freshness_today` injection point against the real rankings table and confirms
`StaleSnapshotError` is raised; the other confirms the inverse (today's real, actually-fresh
snapshot does NOT raise), so the first test can't be trivially true from a "always raises" bug.
No code change was needed — T5 was already correctly wired for every league; this closes the gap
between "documented as fixed" and "proven fixed."

**T4 (interim suspensions) — real list built and wired, closing the "not wired into the live
board" gap CURRENT-STATE.md previously flagged.** Ran an exhaustive WebSearch/WebFetch research
pass (PED policy, personal-conduct policy, gambling policy angles; publication dates checked to
screen out stale index bleed-through from 2023/2024 suspensions resurfacing in 2026-dated
queries). Found exactly one real, current, unserved 2026 suspension: Charles Snowden (Cowboys
DE, 3 games, personal-conduct policy / 2024 DUI, announced 2026-07-14, effective Week 4) — not
included as a suspensions-mechanism entry because this board has no individual defensive-player
scoring at all (ADR-039; DEF replacement level is permanently None), so his suspension has zero
board consequence. Several other candidates surfaced and were confirmed NOT applicable: DK
Metcalf's 2-game suspension covered the final 2 games of the already-complete 2025 season;
Rashee Rice was explicitly ruled NOT suspended for 2026 (April 2026 NFL ruling); Jameson
Williams/Alvin Kamara hits were stale 2023/2024 suspensions, already fully served. Per the
project's "never fabricate or guess a name or game count" rule, none of these are listed as
entries — the real list (`data/suspensions_2026.json`) is honestly empty of suspension rows,
dated `as_of_date: 2026-07-27`, with every search source cited in `sources_checked`. This is a
verified state, not an oversight, and should be re-run periodically (thread 057 remains open for
the fuller structured-source question).

**Wiring:** `export_contract.build_board_json` now loads `SUSPENSIONS_PATH` (defaults to
`data/suspensions_2026.json`, overridable via a new `suspensions_path` parameter for testing) and
calls `suspensions.apply_suspension_flags` over every board row before returning, applied via the
same shared `write_all` path every league config uses — same "structural, not per-league"
reasoning as T5. Because the real list is currently empty, this is presently a no-op on every
board (every row gets `suspension_flag: False`), which is correct, not silent — the fields are
still emitted unconditionally on every row.

**Contract version bumped 1.11.0 → 1.12.0** (`CONTRACT_VERSION` in `src/export_contract.py`):
`board.json` player rows gain `suspension_flag` / `suspension_games` /
`projected_points_suspension_adjusted` / `suspension_adjustment_note` (previously entirely
absent). Handoff opened to frontend (thread 073) since this is a new field set, same convention
as ADR-050/051's `roster_status`/`scoring_format` additions.

**Tests:** `tests/test_freshness.py` (+2, `TestBoardBuildActuallyRefuses`, `@pytest.mark.
requires_db`), `tests/test_suspensions.py` (+6: `TestRealSuspensionList` covers the real list's
shape/dating/sourcing and confirms it's a correct no-op when applied; `TestRealListWiredIntoBuildBoardJson`,
`@pytest.mark.requires_db`, proves the wiring end-to-end against the real board — one test with a
temp fixture pointed at a real ranked player's gsis_id, confirming the flag actually propagates
through the full `build_board_json` pipeline into `board.json`'s player rows, not just that the
mechanism works in isolation). `tests/test_rosters_export.py::test_contract_version_bumped`
updated to assert `1.12.0`. Synthetic fixture (`tests/fixtures/suspensions_2026.json`) and its
test class are unchanged — still a valid unit test of the mechanism itself, per the task's
instruction not to delete it.

**T6 (roster status) — spot-checked, not rebuilt.** `tests/test_roster_status.py` (6 tests,
including the Tom Brady proxy-verification case) still passes unmodified; `src/roster_status.py`
unchanged. No gap found.

## ADR-054 — FFC half-PPR/non-PPR/PPR 10-team ADP ingester, daily capture wired into CI (2026-07-29, data-ops, FR-023/FR-026)

**Context.** The daily ADP capture has been MFL-only (`adp_source='mfl_proxy'`), and MFL's
`IS_PPR` flag is binary (0/1/-1) with no half-PPR option, so the project has been capturing
full-PPR ADP as a proxy for Westwood, a half-PPR league. Full-PPR ADP is receiver-forward relative
to half-PPR. FFC was recorded **blocked** in `docs/research/source-audit-2026-07.md` (ToS
unretrievable → conservative default). The founder contacted FFC directly on 2026-07-29 and
reported no restrictions on use, recorded in `docs/pm/MEMORY.md` §4 and
`docs/founder-requests/FR-023-ffc-is-unblocked-founder-confirmed-no-restrictio.md`. This is
broader than D-021's one-time historical-pull authorisation — recurring use is covered.

**Independently re-verified this session, not taken on trust:** `robots.txt` disallows `/api/`,
`/ajax/`, `/ajax-v2/`, `/import/`, `/adp/csv/`, `/draft/`, `/rate-my-team/results/`,
`/rankings/custom/`. The HTML pages this ingester fetches —
`/adp/<format>/<teams>-team/all/<year>` — are **not** on that list, and `/adp/csv/` is never
touched.

**What shipped.** `src/ingest_ffc_adp.py`: three formats, three `adp_source` values
(`ffc_non_ppr_10team`, `ffc_half_ppr_10team`, `ffc_ppr_10team`), all at 10 teams — the primary
league's own team count. Per CLAUDE.md §4's never-blend rule, platforms/formats are never merged
into a consensus number; each format is its own row set, own `adp_source`, own dated CSV under
`data/adp-snapshots-ffc/` (a directory distinct from MFL's `data/adp-snapshots/` on purpose — one
`YYYY-MM-DD.csv` per date would be ambiguous between sources; this ingester's filenames carry the
format tag, e.g. `2026-07-29_half_ppr.csv`).

Identity resolution goes through `identity.resolve_name()` (name + position, existing
suffix/punctuation normalization). A name that resolves to zero or more-than-one `mfl_id` is
quarantined to `ffc_adp_quarantine` with a reason (`no_name_match` /
`ambiguous_name_match:N_candidates`), never guessed. Measured 2026-07-29: non-PPR 171/188 stored
(91.0%), half-PPR 180/203 (88.7%), PPR 213/242 (88.0%). The bulk of quarantined rows are team
defenses — FFC lists "Seattle Defense" etc. as players; `ff_playerids`/`players_canonical` carries
**zero** DEF rows at all (verified this session), so that gap is structural, not a join defect,
and will not close without adding a DEF identity space to `ff_playerids` itself (out of scope
here).

CSV is the canonical archive (DB is gitignored, 813 MB); `--import-csv-dir` restores it into a
rebuilt DB, same pattern as `src/ingest_mfl_adp.py`. A same-day re-run (`--force`, or a scheduled
retry) `DELETE`s that day's existing rows for the same `(adp_source, period, teams, format,
as_of_date)` before inserting — found and fixed a real duplicate-row defect during this session's
own testing (a second same-day store call was appending, not replacing).

**CI.** `tools/ci_ffc_adp_snapshot.py` mirrors `tools/ci_adp_snapshot.py`'s fail-loud posture
(no DB / short `ff_playerids` / fetch or parse failure / zero rows / no CSV / under 100 rows all
exit non-zero) but with an **80%, not 90%, name-resolution floor** — MFL's 90% assumes a
near-lossless id-based join; FFC's is name-based against a crosswalk with a structural DEF gap, so
90% would fail every good run. `.github/workflows/adp-snapshot.yml` now captures MFL and all three
FFC formats in the same run, verifies all four CSVs exist before committing, and commits
`data/adp-snapshots/` and `data/adp-snapshots-ffc/` together.

**Historical backfill — deliberately not run this session.** `src/ingest_ffc_adp.py --period
<year>` can pull a past season, but FFC exposes no as-of date for historical years and there is no
way to confirm the sample predates that season's Week 1 rather than accumulating across the whole
year. Rows from a non-current `--period` are stamped `is_retrospective_aggregate=1` so nothing
downstream mistakes one for a real preseason board (CLAUDE.md §6.1 look-ahead bias). No historical
pull was executed this session — flagged as available, not done.

**Tests.** `tests/test_ingest_ffc_adp.py` (18 new), `tests/test_holdout_audit.py`
(`ingest_ffc_adp.py` added to `CONNECT_ALLOWLIST` — it is an ingestion module, same class as
`ingest_mfl_adp.py`).

**Not touched:** `src/export_contract.py`, `src/make_board.py`, `src/availability.py` — whether
FFC ADP feeds the board/availability model is a separate, deliberately open decision per the task
boundary.

## ADR-055 — `live_availability.py`'s structural assumptions are now LeagueConfig-derived, not frozen module constants

**Status:** decided, shipped 2026-07-29 (backend session, branch `claude/pm-agent-setup-gobxa0`).

**The defect.** `src/live_availability.py` carried module-level `TARGET`, `EPS`, `SHARE_BAR`,
`POSITIONS` -- the primary league's (Westwood) measured 2025 final-roster composition and roster
shape, with no way to substitute a different league's numbers. `LeagueConfig` (ADR-041) already
existed and already parameterizes `draft_sim.DraftEngine`, but `live_availability.py` was never
threaded through it. The model was correct for Westwood only because Westwood is the only league
anyone had run it against -- correct by accident, not by construction. No test asserted that two
different roster shapes produce different survival numbers; that gap is what made the accident
invisible.

**Why now.** Mock-draft collection starts imminently in public Yahoo rooms with a different roster
shape than Westwood's (standard scoring/shape vs. Westwood's 3 WR / 2 RB / 2 FLEX / no kicker) --
data collected against a frozen-to-Westwood model would teach the wrong league. Separately, FR-027
asks for generic support for the founder's other leagues; a model hardcoding one roster shape
cannot serve a second league honestly.

**What shipped.** `src/live_availability.py` gained four config-derived functions, mirroring the
primary-league-preserved / everyone-else-derived split `draft_sim.DraftEngine` already established
(ADR-041):

- `positions_for(cfg)` -- scoreable positions (QB/RB/WR/TE, whichever the league starts) plus any
  starter position with no scoring model (DEF, K, ...), generalizing the primary league's hardcoded
  `("QB","RB","WR","TE","DEF")`. An unscored position (K, same as DEF under ADR-039) stays IN the
  model as a real contested pick rather than being dropped.
- `target_for(cfg)` -- for the primary league, returns the SS2 measured `TARGET` dict **unchanged**
  (byte-identical, `==` not `approx`). For any other league: starters are allocated exactly
  (mandatory, arithmetic); flex slots via `cfg.flex_split` if the league has a measured one (ADR-029
  primary-league value) else split evenly across `flex_eligible` (explicit placeholder); bench slots
  allocated proportionally to each position's starters+flex share, which is the only allocation that
  both sums to `cfg.rounds` exactly and does not invent a number for any one position. **This is
  DERIVED, not measured** -- there is no draft history for a league with no prior season to measure
  a mean from, and the docstring says so explicitly rather than presenting it as equally well-founded
  to Westwood's number.
- `eps_for(cfg)` -- primary league unchanged; other leagues get an explicit unmeasured placeholder
  (0.25 for scoreable positions, 0.1 for unscored ones, mirroring the primary league's own pattern),
  flagged as a placeholder in its docstring, not a fitted rate.
- `share_bar_for(cfg)` -- `target_for(cfg)` normalized to sum to 1; exact primary-league `SHARE_BAR`
  when `cfg.is_primary`.

`need_share`, `n_need`, `run_z_scores`, `run_multiplier`, `_hazards_at_pick`, `live_survival`, and
`live_survival_excluding_drafted` all grew an optional `cfg: Optional[LeagueConfig] = None`
parameter. `cfg=None` (the default, and every pre-existing call site: `draft_sim.py`,
`lambda_estimation.py`) reproduces the exact pre-ADR-055 module-constant path -- **no Westwood
number moved**, verified by `test_primary_cfg_reproduces_module_constants_exactly` and
`test_primary_league_path_no_longer_bypasses_config` (the latter checks that calling WITH
`cfg=CURRENT_LEAGUE` produces numbers identical to calling with no `cfg` at all -- i.e. the primary
league now runs the same derivation code as every other league, rather than a hardcoded shortcut
that happens to match).

**The test that closes this.** `tests/test_league_config_availability.py`,
`test_two_roster_shapes_produce_different_survival_numbers`: runs the full hazard model
(`live_survival`) against `lc.CURRENT_LEAGUE` (Westwood) and `data/leagues/ethans_expert_league.json`
(Ethan's -- has a K starter Westwood entirely lacks, 1 FLEX vs. Westwood's 2, no measured
`flex_split`) with an identical synthetic scenario, and asserts the resulting survival numbers
differ. Also: `test_two_roster_shapes_produce_different_target` (K present in one league's derived
target and absent from the other's), `test_derived_target_sums_to_league_rounds` (the
sum-to-`cfg.rounds` invariant holds for a non-primary league too, not just the primary one's
hardcoded `== 16` check), and `test_unmeasured_derivation_is_flagged_not_silently_equal_footing`
(the flex-split placeholder actually runs, rather than raising or silently reusing Westwood's
measured split).

**Not changed.** `src/run_availability.py`'s CLI already threads `--league` through to
`draft_sim.DraftEngine` (ADR-041) for Prep-mode; that path was not touched. This session's scope
was `live_availability.py` (the LIVE-draft hazard-reweighting model) only, since that is where the
frozen constants and the missing test lived. Wiring a live-draft CLI/consumer to pass a real `cfg`
through to `live_survival` is a separate, not-yet-built piece of work (no live-draft-time consumer
of this module exists yet to wire).

**Evidence.** `../.venv2/bin/python -m pytest tests/ -q` (uv-managed venv, Python 3.12): 673 passed,
8 skipped, 1 pre-existing unrelated failure (`test_handoffs.py::test_mailbox_health`, thread
078's resolution missing its artifact -- not touched by or related to this change).
`tests/test_live_availability.py` and `tests/test_availability.py` (the two pre-existing suites
touching this module) pass unchanged, 22/22.

## ADR-056 — ID allocators widened to scan git refs, plus a hard duplicate-collision check (2026-07-29, backend)

**Problem.** Five collisions on the same root cause: `tools/handoffs.py` (thread IDs, ADR
numbers) and `tools/founder_requests.py` (FR numbers) all compute "next free ID" by scanning
files on disk in the *current working tree only*. A parallel branch, an unmerged worktree, or
another session is invisible to that scan, so two allocators independently return the same
number. Prior fixes (threads 043/049/053, ADR-048) were rules telling agents to use the
allocator -- which they did, and it still collided, because the allocator itself only sees one
branch. Confirmed live on this tree today: `docs/decisions.md` on `main` records ADR-054 as the
FFC ingester and ADR-055 as the kicker export artifact; the unmerged
`origin/backend/mock-calibration-kickers` branch records ADR-054 as the mock-draft snapshot
work and ADR-055 as the `live_availability.py` LeagueConfig change -- four distinct decisions
sharing two numbers, which will collide the moment that branch merges.

**Fix, two layers, per the founder's ask ("prefer a structural impossibility to a check, and a
check to a rule; three rules already failed here").**

1. **Widen allocation past the working tree.** `next_free_id()` (threads),
   `adr_next()` (ADRs), and `founder_requests.next_free_id()` (FRs) now also scan
   `docs/handoffs/`, `docs/decisions.md`, `docs/adr-drafts/`, and `docs/founder-requests/` as
   committed on every local + remote-tracking git ref (`git for-each-ref`, `git ls-tree`,
   `git show`), not just the working tree. This narrows the collision window (a branch this
   session has fetched is now visible) but cannot close it -- two sessions can still each
   allocate before either pushes. Degrades loudly: any git failure logs to stderr and falls back
   to the working-tree-only scan rather than allocating silently.

2. **A hard duplicate check, the actual backstop.** New `find_adr_collisions()` and
   `find_thread_id_collisions()` in `tools/handoffs.py`, and `find_fr_collisions()` in
   `tools/founder_requests.py`: compare the ID -> content (ADR header text; thread/FR slug)
   mapping across the working tree and every reachable ref. A number appearing with more than
   one distinct value anywhere fails the check. Wired into `tools/handoffs.py check` (now a hard
   failure, not a warning) and a new `tools/founder_requests.py check` subcommand. Both are
   detection-only by design -- **nothing is renumbered**; a real collision is a merge-time
   decision for a human/coordinator to make, not something an allocator should silently resolve
   by picking a winner.

**What the new check finds on this tree, today (2026-07-29):** two real collisions, exactly the
ones described above -- `ADR-054` and `ADR-055` each carry two different decisions across `main`
and `origin/backend/mock-calibration-kickers`. Left unresolved per explicit instruction (do not
renumber); this is now visible to `tools/handoffs.py check` instead of surviving silently to the
branch's eventual merge. Whoever merges that branch must renumber one side's ADRs before merge.

**Not done.** `next_id()` in `tools/handoffs.py` (the older back-compat helper, not
`next_free_id()`) was left unwidened -- it is unused by any current caller (grep confirms only
`next_free_id()` is called by `cmd_new`/`ingest_pending`), so widening it would be scope with no
consumer. FR-020's reported double-allocation (two sessions, two branches, same morning) was not
reproducible from the branches fetched in this session -- `origin/backend/mock-calibration-kickers`
does not contain a second `FR-020-*.md`; whatever branch carried the second allocation was not
available here. `find_fr_collisions()` is validated by fixture tests instead and will genuinely
detect the case if that branch is ever fetched.

**Constant?** None introduced. This is a data-integrity fix, not a modeling decision.

**Evidence.** `python3 -m pytest tests/test_handoffs.py tests/test_founder_requests.py -q`: 27
passed, 1 pre-existing failure (`test_mailbox_health`, thread 078 + the two collisions this ADR
documents -- both true positives, not test bugs; confirmed pre-existing via `git stash` that
078 alone already failed `check` before this session's changes). 9 new tests added:
`test_next_free_id_widens_past_local_tree_via_refs`,
`test_next_free_id_falls_back_when_git_unavailable`,
`test_adr_next_widens_past_local_tree_via_refs`,
`test_find_adr_collisions_flags_same_number_different_header`,
`test_find_adr_collisions_silent_on_identical_header`,
`test_find_thread_id_collisions_flags_conflicting_slugs` (`tests/test_handoffs.py`);
`test_next_free_id_widens_past_local_tree_via_refs`,
`test_find_fr_collisions_flags_conflicting_slugs`,
`test_find_fr_collisions_silent_when_no_conflict` (`tests/test_founder_requests.py`).

---

## ADR-059 — A claim checker for live documents, proved on planted faults (2026-07-29, backend)

**Context.** On 2026-07-29 five false claims in this project's own documents were found *by
accident* during unrelated work: FFC described as robots.txt-blocked on the morning it became
the primary daily capture; the cloud ADP capture described as "observed to succeed" and the
local Windows task as "now redundant" when no scheduled run had ever fired (acting on it would
have deleted the only working capture of an un-backfillable artifact); the Predictions tab
listed as absent while `frontend/ui/views/Predictions.tsx` shipped; `docs/handoffs/README.md`
stating design could not read the repo two days after it could, with the founder hand-relaying
files as a result; and rankings history called unrecoverable when it re-pulls row-for-row. The
founder personally caught six more the same day. Detection ratio ~6:1 in his favour and not
improving. `docs/pm/CHARTER.md` sets the threshold for him stepping back as "zero interruptions
**plus a detector that has caught planted faults**."

**Decision.** Build the detector as a **closed registry plus a closed document scope**, not as
prose analysis.

- `docs/state-claims.toml` registers each checkable fact with its verification: `[[artifact]]`
  (path on disk), `[[constant]]` (value read out of the defining source file), `[[status]]`
  (a named source/capability with a polarity vocabulary), `[[count]]` (measured from a file).
- `[scope].live_docs` names the ten documents that assert what is true *now*. Append-only logs
  — `docs/status.md`, `docs/status/`, `docs/decisions.md`, `docs/handoffs/NNN-*.md`,
  `docs/founder-requests/`, `SNAPSHOT-*`, `RUN-*` — are **never** scanned. Flagging a document
  for correctly recording history is the false-alarm pattern that gets a checker switched off,
  and this is the single biggest reason it stays quiet enough to be worth reading.
- A live document may still narrate a superseded belief, if it marks it: `~~struck through~~`,
  an `<!-- state-claims: ignore-block -->` region, or a named per-document suppression that
  carries a written reason.
- A `[[status]]` claim with **no** registered `truth` flags disagreement *between* live
  documents. That is the cross-document-contradiction class and it needs no ground truth — the
  honest form for a fact nobody has settled.

**Alternative rejected.** Natural-language detection of factual claims across all documentation.
It cannot be made precise here, and a checker that flags fifty things nobody acts on is worse
than none: this project already has documents nobody trusts. The registry deliberately puts the
cost of a claim on whoever writes it.

**Evidence — both directions, which is the acceptance condition.**
`tests/test_state_claims.py`, 21 tests. Six planted faults in `tests/fixtures/state_claims/`,
each reproducing a real 2026-07-29 false claim in roughly the words the real document used;
every one is caught, and every corrected counterpart passes clean. Fixtures substitute
`{{CONTRACT_VERSION}}`/`{{BOARD_PLAYERS}}` from the live repo so a correct fixture cannot rot
into a false one. Run against the real ten live documents, the checker found **eight live false
claims on its first run** — the Predictions-tab line, FFC described as blocked in two places,
`CONTRACT_VERSION` quoted as 1.13.0 against 1.14.0, the board stated as 511 players against 510
on disk (twice), design's read access, and one superseded rankings-history conclusion. All eight
corrected in this session; the checker now reports OK across ~4,000 lines of live prose with
**zero false positives** and one reasoned path allowance.

**Stated gap, asserted rather than described.** Whether a GitHub Actions *schedule* has fired is
not readable from a checkout, so failure #2 (the ADP capture) has no verifiable truth. It is
registered truth-less, which catches the two polarities coexisting across documents but would
**not** catch a single document asserting the false version alone.
`test_each_document_alone_does_not_fire_on_the_contested_claim` pins that limitation as a
measured property rather than a paragraph in a report nobody rereads.

**Constant?** None introduced. No statistical parameter, no model change.

**Anti-rot.** The registry is itself checked: a registered path whose existence flips, a missing
authority document, a suppression matching nothing, or a path allowance that has become
unnecessary all fail the test. A suppression that outlives its reason is how this class of tool
quietly stops working.
| component | VBD@QB1 | share |
|---|---|---|
| rush yds (base) | 35.5 | 31.2% |
| rush TD @6 | 28.7 | 25.3% |
| pass TD @4 | 26.5 | 23.3% |
| pass yds (base) | 24.4 | 21.4% |
| **pass yd BONUSES** | **2.4** | **2.1%** |
| interceptions | −2.4 | −2.1% |
| everything else | −1.3 | −1.1% |

**56.5% of the elite-QB edge is rushing**, which is scored at RB rates (10 yds/pt, 6 per TD) and is
untouched by the league's passing stinginess. Consensus top-3 QBs in 2021–2025 were Allen, Mahomes,
Hurts, Jackson and Daniels, with rushing shares of 13–47% and trending up. That is the mechanism.

**THE FINDING THAT MATTERS MORE, AND IT IS BAD NEWS.** The QB slope is not stable across the five
training seasons the curve pools with equal weight:

| season | b_QB | implied VBD@QB1 | b_RB | VBD@RB1 |
|---|---|---|---|---|
| 2021 | −66.6 | 153.4 | −34.9 | 118.8 |
| 2022 | −72.6 | 167.2 | −51.7 | 176.0 |
| 2023 | −58.6 | 135.0 | −41.4 | 140.8 |
| 2024 | −45.0 | 103.6 | −47.1 | 160.1 |
| **2025** | **−4.1** | **9.3** | **−77.9** | **265.1** |

A monotone collapse, with the most recent season essentially flat — 2025 says the QB1 slot was
worth **9 points** over QB10, not 114 — while RB moved hard the other way. 2025 is verified
complete (18 weeks, 18,521 rows, the largest season on file), so this is not truncation. It is
real: in 2025 consensus QB2 and QB3 (Jackson, Daniels) missed time while QB10/QB15/QB16/QB18 all
finished above 300 points.

`fit_rank_curves()` pools all five seasons **flat, with no recency weighting**, despite CLAUDE.md
§6.4 ("how far back to weight is an empirical question") and the schema principle that a
`season_weight` field exist from the start. **The shipped QB premium is therefore an average over a
regime that was disappearing during the training window.** Pinned by
`test_qb_curve_slope_collapsed_in_2025`.

**And the uncertainty already said so.** Allen's VBD is 113.7 with a bootstrap 95% CI of
**[57.0, 155.2]**. That interval overlaps the CI of **29 of the top 40 players**, spanning overall
ranks **1 through 31**. The board's own machinery already reports that "+20" is not distinguishable
from "consensus was right." The point estimate was being read without its interval.

**Secondary finding — the estimator is misspecified, asymmetrically across positions.** Fitting the
log-linear curve on sub-ranges shows RB and WR are strongly concave in log-rank while QB is not:

| pos | b on ranks 1–20 | b on deep ranks | ratio |
|---|---|---|---|
| RB | −33.0 | −87.0 (21–45) | 2.6× |
| WR | −31.2 | −63.5 (21–60) | 2.0× |
| QB | −44.2 (1–10) | −40.2 (11–20) | 0.9× |

A single log-linear fit overstates the top-of-board gap for RB/WR and does not for QB. Because the
board ranks positions **against each other**, an asymmetric misspecification is a real ordering
risk. Pinned by `test_rank_points_curve_is_misspecified_for_rb_and_wr`.

**Defects looked for and NOT found.** Bonuses are applied **per game**, not to season totals — the
leading defect hypothesis, checked at the engine level and against real 2024 QB seasons (Burrow
18.5 bonus points off 7 games ≥300; Jackson 2.0 off 2 games; a season-total bug would have paid a
flat 4.5 to every one of them). Bonuses stack correctly at thresholds per CLAUDE.md §7. Passing TD
is 4. Replacement is genuinely applied at QB10/RB30/WR40/TE10, and QB10 is the *most conservative*
choice in the plausible range — assuming streaming (QB12–QB18 replacement) moves Allen **up** to
#5–#3, not down. No units error, no look-ahead: training on 2025 for the live 2026 board is
explicitly sanctioned by `src/holdout.py` ("locking governs selection, not fitting"), so this is
**not** a HoldoutViolation.

**Constant?** None introduced. Every figure above is a measurement with a stated n: curve fits are
n=100 (QB), 225 (RB), 300 (WR) player-seasons over 5 seasons; R² = 0.158 / 0.263 / 0.266; CIs are
2000-draw season-level bootstraps on 5 units.

**Decision.** (1) The QB premium is **explained and is not a bug** — it is a rushing-QB regime
effect, correctly computed. (2) It is **not, on this evidence, a defensible edge**: the CI overlaps
consensus, and the single most recent season contradicts it outright. The board's QB ranking should
be treated as "consensus is probably fine here" rather than as a +20 signal to act on. (3) Two
methodology gaps are now documented and test-pinned but **deliberately not fixed here** — flat
season pooling with no recency weight, and the log-linear misspecification. Both are estimator
changes that require the Statistician + Red-team gate (CLAUDE.md §8), not a backend patch.

**Evidence.** `tests/test_qb_board_delta.py`, 9 tests, all passing. Diagnostics are reproducible:
`experiments/qb_board_delta_diagnostic.py` and `experiments/qb_board_delta_uncertainty.py`.

---

## ADR-058 — Non-primary leagues get their full six-artifact export set (2026-07-29, backend)

**Bug (founder-reported, live site).** Switching to "Ethan's Expert League" in the app failed:
*"Could not read leagues/ethans_expert_league/nulls.json (HTTP 200, non-JSON response)."*
`data/export/ethans_expert_league/` carried only 4 artifacts (board/availability/league/rosters)
against the primary league's 11. The HTTP-200-with-HTML-body framing is the deployed site's SPA
fallback for a missing file (a `wrangler.jsonc` concern, explicitly out of scope here, someone
else's fix in flight) — but the underlying file really was missing, which is this bug.

**Root cause.** ADR-041 requires six artifacts in every non-primary league's export directory
(board/availability/league/glossary/nulls/opponents), and `frontend/ui/data/load.ts` fetches and
`league_id`-checks all six unconditionally (only `rosters.json`/`strategies.json` are genuinely
optional — the loader has explicit fallback-to-null paths for exactly those two, confirmed by
reading `load.ts` directly rather than trusting a prior session's framing). But
`league_builder.export_league()` and `generate_config_matrix.py` both called only
`export_contract.write_all` (board/availability/league/rosters) and never
`export_static.py`'s glossary/nulls/opponents builders. Every one of the 24 pre-generated
config-matrix leagues had the identical gap — confirmed a real oversight, not documented scope:
`generate_config_matrix.py`'s own docstring only carves out `strategies.json`/Monte Carlo as
deliberately deferred, says nothing about the three prose artifacts.

**Fix.** Factored `export_static.py`'s inline `main()` payload construction into
`build_static_artifacts(cfg)` / `write_static_artifacts(out_dir, cfg)`, and call the latter from
both `league_builder.export_league()` and `generate_config_matrix.generate_all()`. Rebuilt all
affected exports: `ethans_expert_league` now carries 7 artifacts (was 4), all 24 config-matrix
directories now carry 7 (was 3), primary league unchanged at 11.

**Bug 2, same session (thread 042, `docs/backlog-triage-2026-07-29.md`).** `strategies.json` was
stamped `contract_version 1.7.0` against everything else at `1.14.0` — stale since a prior
contract bump, not a code bug (`src/export_strategies.py` already reads `CONTRACT_VERSION`
correctly). Re-ran `src/export_strategies.py`; now `1.14.0`.

**No `CONTRACT_VERSION` bump.** No artifact's shape changed, only which artifacts get generated
for non-primary leagues. No frontend handoff needed for a schema reason; thread 042 gets a reply
closing it out.

**Regression guard.** New `tests/test_export_directory_contract.py`: parametrized over every
`data/export/<league_id>/` directory found on disk, asserting the six required artifacts are all
present (plus a vacuous-pass guard so removing every league directory can't make this silently
pass), a primary-league full-set check, and a `strategies.json` contract-version-matches-source
check. Extended `test_create_and_export_league_board_uses_its_own_replacement_levels` in
`tests/test_league_builder.py` to assert the same six-plus-rosters set directly at the
`league_builder.export_league()` call site.

**Scope not taken.** Every subdirectory of `data/export/` becomes a switchable "league" in the
frontend (`sync-exports.mjs` treats any directory as a league, no allowlist) — this includes the
24 config-matrix combos, which is why their gap mattered too. `yahoo_standard_mock` is a real,
on-disk, working example of a league with only 6 artifacts (no `rosters.json`/`strategies.json`)
loading correctly, confirming those two really are optional rather than another hidden gap.

**Evidence.** `.venv/bin/python -m pytest -q`: 719 passed, 1 pre-existing failure
(`test_mailbox_health` — the ADR-054/055 collision ADR-056 already documents and left
unresolved by explicit design; unrelated to this change, reconfirmed via `git stash` equivalent
by checking the failure predates this commit). Commit `a88f041`.

---

## ADR-060 — ADP gets a glossary term and a Methodology section; two stale "no ADP" claims corrected (2026-07-29, backend, PM dispatch)

**Problem.** Contract 1.14.0 (thread 082) put real ADP fields on every board row and shipped them
to the prep board, draft screen, and player profile — but the term was defined nowhere.
`data/export/*/glossary.json` carried 13 terms and none of them was ADP; `Methodology.tsx` had
five sections and none mentioned it. A number with the largest caveat on the board (MFL proxy,
full-PPR capture against this half-PPR league, thin sample, ~230-player coverage ceiling) was
explained in exactly zero places a user could reach.

**Fix.**
1. `src/export_static.py::_GLOSSARY_BASE` gains an `"ADP"` term. `adp_min_pick`/`adp_max_pick`/
   `adp_selected_pct` are folded into this one entry via a parenthetical rather than given their
   own terms — same pattern as `confidence interval` covering `ci_low`/`ci_high`. The definition
   states the MFL proxy caveats up front (population, full-PPR-vs-half-PPR, thin sample, ~230-
   player ceiling) and states plainly that it does not feed the projection, VBD, tier, or any
   recommendation.
2. `frontend/ui/views/Methodology.tsx` gains an "ADP (market average draft position)" section,
   rendering `board.json`'s `adp_source_note`/`adp_match_rate_note` verbatim, with explicit
   display-only language naming the fields it does NOT touch (`projected_points`, `vbd`, tiers,
   availability, recommendations).
3. `frontend/ui/data/glossaryCategories.ts` maps `ADP` to a new-in-practice `draft` (Draft
   mechanics) category — that bucket existed in `CATEGORY_ORDER` since an earlier session but had
   no members until now — with `field: 'board.json:players[].adp'`.
4. Regenerated `glossary.json`/`nulls.json`/`opponents.json` (the three hand-authored artifacts
   `write_static_artifacts` emits together) for the primary league and all 26 saved league configs
   under `data/leagues/` — 27 `glossary.json` files total, all now carrying the ADP term. No `.db`
   connection needed for this path (`build_glossary`/`build_nulls`/`build_opponents` are pure
   functions of `LeagueConfig`), so this was possible without rebuilding `nfl.db`.
5. **Corrected two now-stale claims found sitting directly next to the new text**: the
   `consensus rank` glossary entry and `board.json`'s `consensus_source_note` (`export_contract.py`)
   both still said "no ADP source is legally obtainable (ADR-018)". False since ADR-035 partially
   superseded ADR-018 with the real (if thin, proxy) MFL ADP now on the board. Left the
   single-source/no-blend claim about *consensus* itself untouched — only removed the false
   "does not exist" framing about ADP and pointed at where the real thing is documented instead.

**ADP is confirmed display-only, not wired into anything the board computes.** Evidence, not
assertion: `_load_adp_snapshot()`'s own docstring in `export_contract.py` — "for DISPLAY only --
does NOT feed the model (`availability.load_mfl_adp_source` stays unwired by design)"; ADR-035's
own status note that `load_mfl_adp_source()` "exists, is tested, and is NOT wired into the shipped
default"; and thread 082's frontend reply confirming `AdpCell`/`AdpBlock`/`DraftRoomAdpCell` read
`row.adp`/`row.adpSource` exclusively, never merged into `consensus_rank` or its delta. Nothing in
this session rewired that — the new Methodology section states it, it does not create it.

**No contract version bump.** Every field used (`adp`, `adp_source_note`, `adp_match_rate_note`,
etc.) already existed at 1.14.0 (thread 082); this session only added prose that reads them.
`CONTRACT_VERSION` in `src/export_contract.py` is untouched, still `"1.14.0"`.

**Scoring-format caveat kept future-proof.** FR-042 (raised the same day this ADR was written)
will move the 24 preset leagues to standard scoring, leaving only the primary league (Westwood) on
the custom stacking-bonus ruleset — a separate, not-yet-built change. Neither the new glossary
entry nor the new Methodology section asserts anything about which leagues share which scoring
rules, so neither needs revisiting when FR-042 lands.

**Also fixed, found in the course of this work, not part of the ask.** Two files carried literal
leftover `<<<<<<< HEAD` / `=======` / `>>>>>>>` git-conflict markers: this file (`docs/decisions.md`,
around ADR-057/ADR-058) and `docs/handoffs/082-adp-fields-on-board-json-contract-1-14-0.md` (around
its two frontend replies). Confirmed both sides in each case were sequential, non-overlapping, already
correctly-headed content before touching anything — stripped only the three marker lines, changed no
prose. Did **not** touch the actual ADR-054/ADR-055 duplicate-header collision underneath — that is
ADR-056's decision, made and left unresolved on purpose (allocators widened instead); not this
session's call to re-open. See `docs/ideas-inbox.md`, 2026-07-29 backend entry, for the full
reasoning trail.

**Evidence.** Backend: `python3 -m pytest tests/ -q` — 688 passed, 29 failed, 9 errors, 3 skipped;
every failure/error is `nfl.db` being absent in this container (a documented, session-local GitHub
proxy 403 on `github.com/dynastyprocess/*` blocks `scripts/rebuild_database.py` step 4, per
`docs/can-we-rebuild-the-database.md` — reported, not re-solved, per that doc's own instruction) or
the pre-existing ADR-054/055 mailbox failure; none touch glossary/methodology code. With the DB
absent, `test_multi_league_export.py`/`test_export_contract.py`/`test_export_directory_contract.py`/
`test_league_builder.py` (the glossary-adjacent suites that don't need a live board build) run clean.
Frontend: `npm test` — 203 passed, 0 failed, 22 files; `tsc -b --noEmit` clean. Screenshots (Playwright,
`frontend/e2e/verify-adp-glossary-methodology.mjs`): `adp-glossary-2026-07-29.png`,
`adp-glossary-expanded-2026-07-29.png`, `adp-methodology-2026-07-29.png`,
`adp-methodology-scrolled-2026-07-29.png` in `frontend/e2e/artifacts/` — looked at directly, ADP
card renders under "Draft mechanics" and expands to the real MFL text; Methodology's new section
renders the real `adp_source_note`/`adp_match_rate_note` (147 of 225 `mfl_proxy` rows resolved,
snapshot 2026-07-29) beneath the "does not feed" language.

**Known limitation, not fixed here.** `data/export/board.json`'s `consensus_source_note` field
itself (the actual shipped artifact, not the Python source) still contains the OLD "ADR-018" text,
because regenerating `board.json` needs a live `nfl.db` connection this session could not establish
(same 403 as above). The source fix is real and will take effect the next time `board.json` is
rebuilt with a working database — until then, the live site's Methodology page will keep showing
the stale sentence in the "What the board does not claim" section even though the new ADP section
right below it is already correct (it reads a different field, `adp_source_note`, which was already
populated correctly before this session).

## ADR-062 — Standard scoring for presets and founder-created leagues, not Westwood's (2026-07-29, backend, FR-042)

**The defect.** `generate_config_matrix.py`'s 24 presets and `league_builder.py`'s
`create_league()` both built every non-primary league's scoring by `copy.deepcopy(scoring.LEAGUE)`
-- Westwood's verified custom ruleset (stacking yardage bonuses at 100/150/200/300/350/400,
ADR-052) -- with only the reception value swapped or explicitly overridden. A preset labeled
"ESPN-default, 12 teams, half scoring" was Westwood with a different name; any founder-created
custom league that didn't override every single offense/defense field silently inherited
Westwood's rules too. `generate_config_matrix.py`'s docstring also self-contradicted: it claimed
the bonus structure "happens to match ESPN's confirmed platform defaults exactly," twelve lines
after admitting the ESPN fetch was blocked by bot detection and never verified.

**Founder's ruling (FR-042), verbatim:** "All the other presets should be standard scoring (with
different PPR) not Westwood custom. Only Westwood should have the custom... Almost two separate
tracks."

**Decision.** New `src/standard_scoring.py::STANDARD_LEAGUE`, a genuinely separate ruleset object
(not a Westwood derivative):
- **Offense** -- the founder's own explicit definition, sourced directly to his words: 25 yd/pt
  passing, 4 pt passing TD, -2 INT, 10 yd/pt rushing/receiving, 6 pt TD, -2 fumble lost, **no
  yardage bonuses**. Receptions vary 0/0.5/1.0 across the three PPR presets.
- **Minor offensive categories not named in the ruling** (return-TD, two-point conversion,
  offensive-fumble-return-TD) kept at the same flat values Westwood uses, labeled a judgment call,
  not a platform fact -- these are near-universal flat values, not the "bonus structure" the
  founder was distinguishing Westwood by.
- **Defense** -- not addressed by the ruling at all, and not verified against any real platform.
  A conventional, explicitly UNVERIFIED placeholder, deliberately built as a *distinct* dict from
  Westwood's defense (different `blocked_kicks`, different `points_allowed` tiers) so this file
  cannot silently reintroduce the exact bug it exists to fix. Confidence level stated in the
  module docstring and in every export's new `scoring_ruleset_note` field.

`generate_config_matrix.scoring_variant()` and `league_builder.build_scoring()` (the more
consequential of the two -- every league the founder will ever create through the builder) both
now delegate to `standard_scoring.standard_scoring_variant()` / deep-copy
`standard_scoring.STANDARD_LEAGUE`. Only the primary (Westwood) league still uses `scoring.LEAGUE`
(`league_config.py::_current_league_scoring()`), and neither path can reach it --
`unique_league_id()`/`create_league()` both reject `league_id="primary"`.

`generate_config_matrix.py`'s docstring contradiction is resolved by removing the false claim
outright: standard scoring makes no platform-match assertion at all, so there is nothing left to
contradict the "ESPN fetch blocked, never verified" line, which is kept and clarified.

**Contract 1.14.0 -> 1.15.0 (additive).** `league.json` gains `scoring_ruleset_note: str` on every
league (primary and non-primary), stating on screen which ruleset that league actually uses --
the founder's explicit instruction, "state the assumption on the screen." Handoff thread 093
opened to frontend.

**Also fixed, found in the course of this work, not part of the literal "24 presets" ask.**
`data/leagues/ethans_expert_league.json` -- a real, previously-created custom league via
`league_builder.create_league()` (`scripts/rebuild_ethans_expert_league.py`) -- had its offense
yardage bonuses already zeroed by explicit `scoring_overrides` (whoever built it anticipated this
exact problem for the three yardage fields), but its **defense** block was still a silent copy of
Westwood's (`blocked_kicks=1`, Westwood's `points_allowed` tiers) because defense was never in
its overrides. Re-ran the existing rebuild script post-fix; its defense now correctly comes from
`STANDARD_LEAGUE`. No projection moved (DEF carries no replacement level/points in this project;
see `league.json.positions_without_replacement_levels`) -- this is a correctness fix to the stored
config, not a ranking change.

**Evidence -- before/after regeneration, `espn_10_half` (half-PPR ESPN-shape preset):**

| Player | Before (Westwood-derived) | After (standard) | Delta |
|---|---|---|---|
| Bijan Robinson (RB) | 303.16 pts, VBD 162.94 | 296.68 pts, VBD 158.20 | −6.48 pts (rushing-yardage bonus removed) |
| Ja'Marr Chase (WR) | 276.48 pts, VBD 146.52 | 267.48 pts, VBD 139.41 | −9.00 pts (receiving-yardage bonus removed) |
| Josh Allen (QB) | 359.01 pts, VBD 113.71 | 351.55 pts, VBD 111.20 | −7.46 pts (passing-yardage bonus removed) |

Every non-primary board's `projected_points`/`vbd`/`overall_rank`/tier moved by a comparable
amount for players who cross the removed bonus thresholds -- this is the expected, real effect of
removing stacking yardage bonuses, not noise. **The primary (Westwood) board is verified
byte-identical**: Bijan Robinson's Westwood-league points (303.16) and VBD (172.17) are unchanged
before and after this session's regeneration of the primary export -- `scoring.LEAGUE` itself was
never touched, only `CONTRACT_VERSION` (1.14.0 -> 1.15.0) and the new `scoring_ruleset_note` field
changed on the primary league's own `league.json`.

**All 24 presets + `ethans_expert_league` regenerated (not edited)**, plus the primary league's
`board.json`/`availability.json`/`league.json`/`rosters.json` (to pick up the contract-version
bump and the new note field; `scoring.LEAGUE` values inside are unchanged).

Also regenerated (the version bump makes every existing committed artifact stale, not just the
scoring-affected ones): `glossary.json`/`nulls.json`/`opponents.json` for the primary league
(`src/export_static.py`) and `strategies.json` (`src/export_strategies.py`, ~13 min real Monte
Carlo run, 600 sims x sigma sweep x 6 strategies x 4 seasons -- confirmed by diff to be a pure
metadata regeneration: every strategy margin (`bpa_consensus`=baseline, `hero_rb`=-13.9,
`zero_rb`=+26.4, `elite_te_early`=-96.1, `qb_early`=-116.5, `balanced`=+27.5) is byte-identical to
the pre-session committed file; only `contract_version`/`generated_utc` changed, as expected since
Westwood's scoring was never touched). Regenerating the primary board also incidentally closed a
gap ADR-060 had left open: `board.json.consensus_source_note` still carried stale "no ADP source
is legally obtainable (ADR-018)" prose because that session's `nfl.db` was unavailable; this
session's worktree has a working DB, so the already-fixed Python source finally reached the
shipped artifact -- unplanned, not part of this ADR's scope, noted for continuity.

**Real allocator race caught and resolved.** This ADR was first drafted as ADR-061 (the number
`tools/handoffs.py adr next` returned when this session started). Before committing, a fresh
`adr next` call returned 62 -- a concurrent session's ADR-061 ("Availability now covers every
draft slot...", FR-057) had landed on another branch in the meantime. Renumbered this entire
entry and every cross-reference to it (`docs/CURRENT-STATE.md`, `docs/founder-requests/FR-042-
...md`, this session's `docs/status/` file) to ADR-062 via the tool's own re-check, not by hand --
`python tools/handoffs.py check` confirms no ADR-061/062 collision remains. The pre-existing
ADR-054/055 duplicate-header collision is unrelated, already known, and deliberately left
unresolved per ADR-056 -- not touched here.

**Evidence.** Backend: `python3 -m pytest tests/ -q` -- final run **763 passed, 6 failed**
(worktree's copied `data/nfl.db` present, all `requires_db` tests ran for real, not skipped).
Every failure is pre-existing/unrelated to this change: the ADR-054/055 mailbox collision (above);
`tests/test_holdout_audit.py::test_no_new_direct_sqlite_connections_in_src` flagging
`src/ingest_sleeper_projections.py` (last touched in an unrelated, earlier commit `fdd4685`, not
part of this session's diff); and four tests in `test_ingest_ffc_adp.py`/
`test_ingest_sleeper_projections.py` that hardcode `as_of_date="2026-07-29"` and compare it
against `dt.datetime.now(...).date()` -- these started failing only in this session's *second*
full-suite run because the wall clock crossed into 2026-07-30 mid-session (confirmed: they fail
identically in isolation, with no DB or code dependency on this change; the first full-suite run,
before midnight UTC, did not have these failures). Pre-existing date-rollover fragility in those
two ingestion test files, not something this ADR's scope touches. New/changed test files:
`tests/test_standard_scoring.py` (new, 7 sanity checks written before the callers were changed to
use `standard_scoring`, per CLAUDE.md's non-negotiable ordering),
`tests/test_generate_config_matrix.py::test_scoring_variants_use_standard_ruleset_not_westwood`,
`tests/test_league_builder.py::test_build_scoring_uses_standard_ruleset_not_westwood`,
`tests/test_rosters_export.py::test_contract_version_bumped` (updated to assert 1.15.0).

---

## ADR-063 — Yahoo Fantasy Sports connector: adapter, OAuth2, fetch-on-demand only (2026-07-30, backend, FR-062)

**Context.** FR-062 asked what happens if a Yahoo API is unavailable. The researcher's answer
(`docs/research/yahoo-espn-league-connection-2026-07-30.md`, staged as unallocated thread 095,
`TO: pm`) found the premise mostly false: Yahoo's OAuth2 path appears open and self-serve; ESPN is
a clean, permanent no (Disney ToU SS2.B.x/SS2.A/SS3.H name automated/AI access by name, no
sanctioned channel exists to fall back to). The founder then promoted this to near-term work
directly ("add the yahoo connection work to our near term work... sooner than later"). This ADR
covers the connector built in response, dispatched straight to backend rather than through a
handoff thread.

**The constraint that shaped the whole build: no real Yahoo credential exists yet** (registration
is tied to the founder's account, undone at build time), and Yahoo hosts are not fetched by agents
(standing block, respected here too). Everything below is built against documented shapes and
tested against constructed fixtures, never a live response -- correctness of the parsing layer
cannot depend on having a credential; only the interactive one-time authorize step can.

**Decision 1 -- `yfpy` is not a runtime dependency, despite being the shape source.** The research
doc's biggest payoff claim (Yahoo's `Bonus(points, target)` class exposing Westwood's stacking
yardage bonuses from source-of-truth) rests on `yfpy`'s documented models. `pip install yfpy` was
attempted this session and **failed**: its OAuth dependency (`yahoo-oauth`) pulls in `myql` and
`rauth`, two unmaintained legacy Yahoo Query Language (YQL, retired years ago) packages whose
`setup.py` raises `AttributeError: install_layout` under current `setuptools`. Verified by running
the install, not assumed from a docstring or a version pin -- exactly the "a source swap is not a
substitution" check CLAUDE.md's non-negotiables require. **Decision:** `src/providers/yahoo*.py`
talks to Yahoo's OAuth2 + Fantasy Sports v2 REST endpoints directly via `requests` (already a
clean, satisfiable dependency), and defines its own `Bonus`/`StatModifier`/`RosterPositionSpec`
dataclasses (`src/providers/base.py`) matching `yfpy`'s verified field names, rather than vendoring
a library that does not currently install in this environment. If `yfpy`'s dependency chain is
fixed upstream later, swapping it in is a `providers/yahoo.py`-internal change; the interface
(`LeagueProvider`) and everything above it is unaffected.

**Decision 2 -- the response-parsing layer is signature-key-based, not fixed-path.** Yahoo's
`format=json` output encodes an XML document (deeply nested, index-keyed structures) that no
session here has ever read directly. `src/providers/mapping.py` never hard-codes an exact nesting
path; it recursively walks the whole payload and matches on the key-*set* a field is known to
carry together (`position`+`count` for a roster slot, `stat_id`+`value` for a stat, `points`+
`target` for a bonus). This degrades gracefully if the real nesting differs from any guess made
here, and every extraction failure is recorded in `LeagueSettings.parse_warnings` rather than
raised -- a partially-populated, inspectable result beats a crash on the first response this code
has ever seen. `.raw` always carries the full untouched payload for audit.

**Decision 3 -- fetch-on-demand only; nothing persists to `nfl.db` or `data/leagues/*.json`.** The
research doc's [SNIPPET]-tagged reading of Yahoo's developer terms: user data not explicitly listed
as storable indefinitely must be deleted within 24 hours, with the storable set reported as GUID +
authenticated token value only. **If that reading holds, "sync a league into `nfl.db`" is exactly
the design the terms forbid.** This was never independently re-verified against
`legal.yahoo.com` (not fetched, per the standing block) -- it is a snippet, not a verified clause,
and is treated as binding anyway because the downside of guessing wrong is a compliance problem,
not an inconvenience. Consequence: `src/providers/yahoo.py` has no write path to `nfl.db` at all
(and is correctly outside the `sqlite3.connect()` ingestion allowlist -- it never opens a
connection), and `scripts/yahoo_pull_league_settings.py` prints its report and exits by default;
`--out` writes a file only if passed explicitly, and even then it's a derived/human-authored report
(the kind of artifact this repo commits everywhere), not a raw Yahoo payload cache. The one
exception, deliberate: `TokenStore` (`src/providers/yahoo_oauth.py`) persists exactly the access
token, refresh token, and expiry to a gitignored `data/.yahoo_token.json` -- the one thing the
[SNIPPET] reading says is storable indefinitely. **Do not build a persistent league sync until gap
5 of the research doc (the exact, complete storable-indefinitely list) is closed against Yahoo's
actual Fantasy Sports APIs Terms of Use, which no session has read.**

**Decision 4 -- live draft-pick reading is designed for, never asserted, never depended on.** The
research doc's live-draft "yes" rests on a single, undated SDK docstring (n=1, unconfirmed by four
other wrappers). `YahooProvider.get_live_draft_picks()` exists, reuses the same
`league/{key}/draftresults` endpoint as the final-results call, and returns a `DraftResult` with
`is_live_estimate=True` and a `caveat` string stating the provenance and unknowns (latency,
throttling) explicitly -- every caller sees the caveat, none can mistake it for a verified
capability. **No write path exists anywhere in this connector**: no wrapper in any language
documents a draft-pick write endpoint, and a structural test
(`test_no_pick_write_capability_exists_on_the_provider`) asserts none was added, so a future PR
adding one has to justify it against that finding rather than sliding in unnoticed. The founder can
close the live-read gap for free with a Yahoo mock draft and a 5-second poll, per the research
doc's own suggestion -- this connector is what makes that test runnable.

**Decision 5 -- ESPN gets a real adapter that always fails, not a missing branch.**
`src/providers/espn.py::ESPNProvider` implements `LeagueProvider` and raises `ProviderUnavailable`
unconditionally, citing Disney ToU SS2.B.x/SS2.A/SS3.H by section number. This exists so any call
site written against the interface is honest about ESPN's status ("unavailable, permanently, for a
stated reason") instead of silently missing a case. If a founder league is on ESPN, its settings
stay manual entry (the pattern this project already used for Westwood/Ethan's Expert) unless the
founder decides otherwise -- his call, not this code's.

**Not resolved by this ADR, left open on purpose:**
- Whether a newly-registered Yahoo app still gets self-serve Fantasy Sports scope in 2026 (research
  doc gap 1) -- the founder settles this by attempting registration; no amount of code here can.
- The exact storable-indefinitely list (gap 5) and the fantasy-specific Terms of Use (gap 6),
  neither ever read by this project.
- The public-hosting question (Yahoo ToS clause (c), no competing-product / no income without
  permission, against an app now live on the open internet) -- flagged in the research doc as "a
  founder-and-possibly-lawyer question, not an agent one," explicitly not decided here.
- Whether `Stat.bonuses` actually populates for a football league with commissioner-set bonuses
  (gap 4) -- `diff_against_claude_md_westwood()` in `mapping.py` checks for exactly this and
  surfaces it in the pull script's report the first time real credentials exist.

**Evidence.** 58 new tests, all passing without any credential or network access:
`tests/test_providers_base.py` (7), `tests/test_providers_mapping.py` (16),
`tests/test_providers_yahoo_oauth.py` (19), `tests/test_providers_yahoo.py` (12),
`tests/test_providers_espn.py` (4). Fixtures
(`tests/fixtures/yahoo/*.json`) are explicitly labeled constructed-not-captured in a
`_fixture_note` field. Full suite: pre-existing failures only (missing `data/nfl.db` in this
worktree, and the already-known `ingest_sleeper_projections.py` sqlite-allowlist finding from
thread 094) -- none touch `src/providers/` or its tests.

**Founder's exact next steps** (also in `.env.example` and `scripts/yahoo_connect.py`'s docstring):
1. Log into the Yahoo account holding the leagues (Westwood 154693, Ethan's Expert 834236).
2. Go to `https://developer.yahoo.com/apps/create/`, choose "Installed Application," redirect URI
   `https://localhost:8080`, API Permissions -> Fantasy Sports -> Read, Create App.
3. Copy the Client ID / Secret into a `.env` file at the repo root (copy `.env.example`).
4. `python scripts/yahoo_connect.py` -- opens a URL to visit, prompts for the verification code
   Yahoo displays after clicking Allow, saves the token.
5. `python scripts/yahoo_pull_league_settings.py --discover` to find league keys, then
   `--league-key <key>` to pull settings and see the diff against CLAUDE.md SS7's Westwood table.
## ADR-061 — Availability now covers every draft slot, not just the founder's own (2026-07-29, backend, FR-057 part 1)

**Problem.** The draft-slot selector (FR-034) already changes the pick sequence everywhere in the
app — board, round grid, Predictions, draft room. Availability could not follow: `data/export/
availability.json`'s `by_player`/`by_tier` only carried rows for the founder's own slot's pick
numbers (`3, 18, 23, 38, 43, 58, ...`), computed by a single Monte Carlo run in `run_availability.py`.
Switching the selector to any other slot produced a DIFFERENT set of pick numbers with no matching
rows — the numbers went absent, not wrong, which is a worse failure mode because it looks like a
UI bug rather than a missing computation.

**Fix — the floor, not the browser recompute.** The founder asked for both ("the browser needs to
find a way to recompute them, python needs to run against all slots as well … I'd prefer the
browser can calculate, but we need good data too") and was right that they are not alternatives.
This ADR is the floor only: run the existing simulation for every slot and ship the lot. Client-side
recomputation conditioned on live picks (FR-057 part 2, his stated preference) is a separate, larger
build and is explicitly out of scope here.

**No new nesting level.** `pick_order()` — which team owns which overall pick number — does not
depend on which team is "the user" for a fixed team/round count; only the ROLE that team plays
(best-player-available vs. need-driven opponent) changes with slot. Consequently a given overall
pick number is tracked by exactly one slot's simulation, so sweeping every slot 1..`teams` and
merging the results into the EXISTING `by_player`/`by_tier` shape is a disjoint union, never an
overwrite. Verified structurally before any merge code was written
(`tests/test_run_availability_multi_slot.py`, 9 tests) — this is what keeps the contract change
additive (two new `metadata` fields) instead of a breaking restructure of an artifact `board.json`
and `narrate.py` also read.

**New in `availability.json.metadata` (contract 1.15.0, was 1.14.0):**
- `multi_slot_coverage: true`
- `picks_by_slot`: `{"1": [...], ..., "10": [...]}` — the canonical pick sequence per slot,
  computed by the same `pick_order()`/`DraftEngine` code the backend already uses. Shipped so the
  frontend has one source of truth instead of a second, independently-written snake-order
  implementation that could drift from this one (FR-057's own "two implementations must agree").

**Founder's own slot is unaffected.** `_engine_for_slot` keeps the exact pre-existing code path
for `cfg.user_draft_slot` (module-level free functions, `engine=None`, for the primary league) —
every other slot uses a `ds.DraftEngine` built from a copy of `cfg` with only `user_draft_slot`
swapped.

**Two real bugs found and fixed before this shipped, not after:**
1. The first version of the sweep added a slot-dependent seed offset to EVERY slot including the
   founder's own. Even though the algorithm path for that slot was unchanged, the different RNG
   stream moved 671 of 1280 checked cells at the founder's own pick numbers by 0.1–2.5 percentage
   points versus the pre-session committed `availability.json` — caught by diffing before/after,
   not by review. Fixed: the seed offset is `0` for `cfg.user_draft_slot`, non-zero only for the
   nine new slots. Regression-tested (`test_own_slot_numbers_unaffected_by_sweeping_other_slots`).
2. `board.json` embeds `by_player[player]` per row too (a separate consumer of the same CSV,
   `build_board_json`). Left un-filtered, it inherited the full multi-slot growth — measured
   1,020,368 → 2,276,988 bytes (2.2x) for an artifact loaded on every page view, for a feature
   FR-057 never asked `board.json` to carry. Fixed: `build_board_json` now filters its
   `by_player` read down to `cfg`'s own pick numbers only, the exact slice it carried before
   1.15.0. Regression-tested (`test_board_json_availability_embed_stays_own_slot_only`).

**Measured, not assumed:**

| | Before (1 slot) | After (10 slots) |
|---|---|---|
| `availability.json` | 161,100 bytes | 1,554,817 bytes (**9.65x**) |
| Sweep runtime (3000 sims × 3 sigmas) | ~45-60s (1 slot, prior doc estimate) | **628.8s (~10.5 min), ~63s/slot average, measured directly** |
| `board.json` | 1,020,368 bytes | **unchanged** (fix #2 above) |

**Scope: only the primary league (Westwood) got a real sweep this pass.** The 24 preset configs
and `ethans_expert_league` have never had a real Monte Carlo run at all — that is ADR-047's
deliberate cost-scoping, unrelated to this change, not something this session reopened. The CODE
PATH (`run_availability.py`, `export_contract.build_availability_json`/`_all_slot_pick_numbers`)
works identically for any `LeagueConfig` regardless of team count, so whenever a real sim IS run
for another league, it is multi-slot from day one with no follow-up fix needed.
`data/leagues/yahoo_standard_mock/availability.csv` (a labelled "mock, approximate" test fixture,
not one of the founder's real leagues) was left un-swept for the same reason. Recorded in
`docs/ideas-inbox.md`, 2026-07-29 backend entry.

**Known, measured, not root-caused:** every slot but the founder's own uses `ds.DraftEngine`
instead of the original hand-tuned primary-league free functions. A scratchpad comparison (200
sims, sigma 10, same seed, primary league at slot 3) found the two paths differ by up to ~0.02
absolute probability at late picks even though they SHOULD be numerically identical — almost
certainly a `legal_mask`/`picks_left` off-by-one between the two parallel implementations. Not
chased down here (contained, separate investigation); logged in `docs/ideas-inbox.md` rather than
shipped silently. Does not affect the founder's own slot's numbers.

**Recommendation given the measured numbers.** ~10.5 minutes and a 9.65x `availability.json` (to
1.55 MB) is workable as a floor for one 10-team league. It does not extend cheaply to every league
— a 14-team league scales roughly linearly with team count at the measured ~63s/slot rate, and
sweeping all 27 league exports (25 of which have no Monte Carlo data at all today) would be on the
order of hours. This is exactly the case client-side recomputation (FR-057 part 2) sidesteps: it
computes one slot's answer on demand instead of precomputing all of them, and already has its
inputs shipped (`client_simulation_parameters`, predates this ADR).

**Also fixed as a side effect, not the point of this session:** `board.json`'s
`consensus_source_note` field still carried ADR-060's stale "no ADP source (ADR-018)" text as of
that ADR's own "known limitation, not fixed here" note, because that session's `nfl.db` was
unreachable. This session's worktree had a real `nfl.db` copy, so regenerating `board.json` here
picked up the already-corrected source text automatically — `consensus_source_note` now reads
correctly in the committed artifact. No code change; confirmed by reading the regenerated file.

**Evidence.** Backend: `python3 -m pytest tests/test_run_availability_multi_slot.py -q` — 9 passed.
Full suite and commit hash in this session's `docs/status/` entry. Contract version 1.15.0 (was
1.14.0) — handoff thread 093 opened to frontend with the field-level contract and required
frontend-side change (read `picks_by_slot[str(slot)]` instead of assuming the founder's own).

## ADR-064 — Thread/FR IDs move to date+slug (`YYYY-MM-DD-slug`), retiring counter-based
allocation for new items (2026-07-30, backend, founder-approved)

**The counter is not the bug; the scheme is.** `tools/handoffs.py` and `tools/founder_requests.py`
allocated new IDs as `max(existing) + 1`, later widened to scan every local + remote-tracking git
ref (2026-07-29, thread 079/081) so a number claimed on an unmerged branch wouldn't be handed out
again. That widening narrowed the race; it could not close it, because two worktrees can each
compute a locally-valid "next free" number in the same window and only find out they collided when
someone reads the merged result — and because the two colliding files have *different filenames*
(`093-a.md` and `093-b.md`, say), git happily merges both with no conflict, so the collision does
not even fail loudly. It waits to be noticed. Six ID collisions happened this way on 2026-07-30
alone (threads 043/049/053, ADR-048, and — found by this session, not before it — 093/094/109/
110/111/112, ADR-054, ADR-055, FR-029, FR-030).

**Decision: new threads and founder requests are named `{date}-{slug}.md`
(`docs/founder-requests/` keeps the `FR-` prefix: `FR-{date}-{slug}.md`), not `{NNN}-{slug}.md`.**
No shared counter, no git ref scan, needed to allocate one — `new_thread_filename()` /
`new_request_filename()` (`tools/handoffs.py`, `tools/founder_requests.py`) claim
`docs/handoffs/{date}-{slug}[-N].md` via `os.O_CREAT | os.O_EXCL`, purely from (today's date, this
thread's own slugified subject), both already known locally with nothing to coordinate. Two agents
naming *different* things on the same day get different filenames for free. The one case that
can't be locally disambiguated — two separate worktrees independently choosing the identical
subject on the identical day — no longer collides silently either: the filename **is** the
identifier now, so two worktrees writing different content to the same path is an ordinary git
same-path merge conflict, which blocks the merge and forces a human/agent to resolve it, instead of
merging clean and hiding in the `ID:` field the way the old scheme's collisions did.

**Clock source: system clock, not passed in.** All worktrees for this project run in one
environment (`docs/environment.md`) with one clock; a day-granularity date has no meaningful skew
risk here. If this project ever runs across real timezone-separated machines, revisit — a UTC-day
boundary crossed mid-session could put two genuinely-same-day threads one calendar day apart, which
is a cosmetic ordering annoyance, not a correctness bug (filenames still never collide from it).

**Existing files are never renamed or renumbered.** ~135 numbered threads and ~120 numbered FRs are
cited by number throughout the repo (prose, commits, other threads, `CLAUDE.md` itself). All
`NNN-slug.md` / `FR-NNN-slug.md` files keep their filenames and their `ID:` frontmatter exactly as
they are; `load()` in both tools now matches either the legacy `\d{3}-` or the new
`\d{4}-\d{2}-\d{2}-` filename shape so old numeric threads keep resolving (`docs/handoffs/
119-*.md` still loads, sorts, and appears in `inbox`/`sync`/`check` output unchanged). Sorting by
`id` (a plain string sort) puts every legacy `NNN` thread before every date-shaped one, which is
also the correct chronological order in this repo's history.

**`next_free_id()` in both tools is kept, not deleted, but no longer used to allocate new IDs.**
It still answers "what's the highest legacy number anyone has claimed" honestly (still tested), and
`adr_next()` (ADR numbering, a separate, smaller space with far fewer concurrent allocators) is
**out of scope for this change** — it keeps its existing counter-plus-ref-scan-plus-backstop
design; this ADR does not touch it.

**Pre-existing collisions from before this change are not fixed, only accounted for.** `check` in
both tools now carries a frozen, dated exception registry (`KNOWN_LEGACY_ID_COLLISIONS` /
`KNOWN_LEGACY_ADR_COLLISIONS` / `KNOWN_LEGACY_FR_COLLISIONS`) naming the exact pre-existing
duplicates found while building this — full account, including the ADR-054/ADR-055 case (two
different real decisions recorded under one number, a content problem no filename fix can resolve)
in `docs/known-id-collisions.md`. This was the coordinator's addition mid-task, confirmed correct:
without it, `check` could never go green again regardless of this fix, and a genuinely new
collision would be lost in the noise of six already-known ones. The registries are pinned by test
(`test_known_legacy_collisions_registry_is_frozen`, `test_known_legacy_fr_collisions_registry_is_
frozen`) so growing them to hide a *new* collision is a visible diff, not a silent absorption — and
they match only on the specific pre-existing numbers, never on the new `YYYY-MM-DD-slug` shape,
which structurally can't produce the same failure mode in the first place.

**Evidence.** `python3 -m pytest tests/test_handoffs.py tests/test_founder_requests.py -q` — 36
passed (was 27/9 before this session's edits — some pre-existing tests describing the old counter
allocation behavior for *new* IDs were rewritten to describe the new date+slug behavior instead;
none of the legacy-ID-resolution or cross-branch-backstop tests changed). `python3 tools/
handoffs.py check` and `python3 tools/founder_requests.py check` both exit 0 against the real repo
(previously both failed — verified pre-existing via `git stash`, not introduced by this session).
Concurrency proven directly: `test_two_worktrees_different_subjects_same_day_cannot_collide`
reproduces thread 076's exact scenario (two isolated worktrees, no shared state) and asserts no
collision; `test_new_thread_filename_dedupes_same_day_same_slug_deterministically` proves the
same-slug-same-day case resolves deterministically rather than raising. Commit: see this session's
`docs/status/` entry.

## ADR-065 — `availability.json` exports the model's own consensus-rank provenance, plus a preparatory ADP block (2026-07-30, backend, thread 104/119)

**Decision.** Thread 104 (FR-066's resolution) asked backend to unblock a browser-side Monte Carlo
recompute of availability for an overridden draft slot, by exporting the per-player rank
`simulate_availability` actually runs its opponent model and the user's own `strategy_bpa` pick
against — a different, ECR-sourced ranking from `board.json:consensus_rank` (measured: 73 of the
top 80 players differ in order). Mid-session, thread 119 resolved: strategist recommended the
opponent model's central tendency move from `fantasypros_ecr` to FFC ADP
(`ffc_half_ppr_10team`) with per-player dispersion, and reformulated thread 104's ask from the raw
rank array to `{adp_pick, sigma_pick, coverage_flag}` per player — because with ADP + dispersion the
unconditional marginal becomes closed-form and a browser recompute needs no Monte Carlo port at all.

**What shipped, in `src/export_contract.py:build_availability_json` (now takes `conn`) and
`src/draft_sim.py`:**

1. `draft_sim.SeasonData` gains `consensus_rank_source`/`consensus_rank_as_of_date`, populated by
   `load_season` from the exact rows `consensus_rank` was read from (new module constant
   `CONSENSUS_RANK_SOURCE`, one edit point). `export_contract`'s `ranking_sources[0].name`/
   `as_of_date` read these fields rather than a second hardcoded literal, so a future repoint of
   `CONSENSUS_RANK_SOURCE` (e.g. thread 119's own recommendation, once it clears pre-registration)
   updates the export automatically. Proven, not asserted:
   `tests/test_export_contract.py::test_ranking_source_identity_matches_the_query_it_was_read_from`
   and `tests/test_availability.py::test_load_season_provenance_matches_the_rows_it_actually_read`
   independently re-query the DB and assert equality with what the export emitted.
2. `client_simulation_parameters.player_ranks` (the ECR array thread 104 originally asked for) is
   kept, not removed — it is still the accurate description of what the SHIPPED model runs on
   today; `simulate_availability` has **not** switched to ADP.
3. `client_simulation_parameters.adp_central_tendency` (new, additive) carries the reformulated
   shape: per player, `{adp_pick, coverage_flag}`, keyed to `by_player`'s own keys, sourced from
   `ffc_adp_snapshots` (adp_source `ffc_half_ppr_10team`, filtered to QB/RB/WR/TE, joined to the
   same gsis-keyed player universe `load_season` uses via `player_ids.mfl_id`). `status:
   "preparatory_switch_not_yet_shipped"` and an explicit `status_note` state that this is not yet
   the model's input.
4. **`sigma_pick` is deliberately NOT exported.** It is gated on M0
   (`docs/ranking/availability-opponent-model-precommit.md`) — FFC's `times_drafted` and
   `total_drafts_in_sample` columns do not reconcile on the committed snapshot (e.g. Bijan Robinson
   `times_drafted=90` against `total_drafts_in_sample=1254` on every row) — so no per-player
   sampling-variance weight is trustworthy yet. `sigma_pending_note` says so; no placeholder value
   ships.
5. **`adp_pick` is NOT axis-corrected (M4 in the precommit doc).** FFC's `average_pick` counts
   kickers/defenses and its sampled drafts run deeper than this league's 16 rounds; the isotonic
   calibration against `board.json` that fixes this is explicitly assigned to `strategist`, not
   invented here. `axis_note` states this loudly rather than silently passing raw values through as
   if they were Westwood pick numbers.
6. `algorithm_note` corrected: it previously claimed the user's own BPA pick runs off
   `board.json`'s unperturbed rank. It does not and never did — `ds.strategy_bpa` reads
   `data.consensus_rank`, the same array the opponent model's `ranking_sources` draws from. This was
   a real defect in the exported documentation, not a rewording.

**Coverage, measured against the real DB (2026-07-30):** 157 of 378 season-universe players resolve
an `ffc_half_ppr_10team` row (skill positions only); 79 of the 80 players actually tracked in
`by_player` are covered (`Marvin Harrison Jr.` is the one gap — honest, not fabricated). Every
`by_player` key has a corresponding `adp_central_tendency.by_player` entry with `coverage_flag`
explicit; `adp_pick` is non-null iff `coverage_flag` is true.
`tests/test_export_contract.py::test_adp_central_tendency_covers_every_by_player_key_honestly`
guards this.

**Contract version 1.16.0 → 1.17.0.** `docs/data-contract.md` updated in place (field table +
changelog). Handoff thread opened to `frontend` describing the new field and its preparatory status.

**Not done, and explicitly out of scope for this change:** the model itself has not switched to
ADP; `sigma_pick` is not computed; the M4 axis correction is not performed. All three remain gated
on the M0-M5 pre-registration in `docs/ranking/availability-opponent-model-precommit.md`, owned by
`strategist`.

**Evidence.** `data/export/availability.json`/`board.json`/`league.json`/`glossary.json`/
`nulls.json`/`opponents.json` regenerated against `data/nfl.db` (2026-07-30). Full test count and
commit hash in this session's `docs/status/` entry and the reply to thread 104.

## ADR-066 — Never-played ranked players in the backtest harness score the replacement deficit, not zero VBD (2026-07-30, backend, strategist finding on the primary-metric ruling)

**The defect.** `src/backtest.py`'s `_vbd_sum_for_ranking` and `top_k_starter_vbd` accumulated a
ranked player's contribution with `vbd.get(pid, 0.0)`. `vbd` is built by `_vbd_lookup` only over
players present in `_season_actuals` — i.e. players with at least one weekly stat row. A ranked
player with a resolved position but **zero weekly rows at all** (retired, cut, a season-ending
preseason injury, suspended for the year) still consumes a starting slot via
`build_position_lookup`'s "rankings win" query, and used to contribute exactly `0.0` — replacement
level. His true contribution is `0 − replacement_points[pos]`: he consumed a starting slot and
returned nothing, which is a materially worse outcome than "as good as the waiver wire." Found by
strategist while ruling on the primary evaluation metric
(`docs/adr-drafts/ADR-DRAFT-primary-evaluation-metric.md` §4.1), not by backend.

**The fix.** `_vbd_lookup` now also returns `replacement_points`, the per-position POINT value at
the replacement baseline (same index arithmetic `scoring.compute_vbd` already uses internally,
duplicated locally since `compute_vbd` does not expose it — this is an evaluation-harness change,
not a change to `scoring.py` or any ranking logic). A new `_slot_value(pid, pos, vbd,
replacement_points)` helper returns the real `vbd[pid]` when the player has one, otherwise
`-replacement_points[pos]`. Used by both `_vbd_sum_for_ranking` and `top_k_starter_vbd`.
Regression tests (`test_never_played_player_scores_the_replacement_deficit_not_zero_vbd`,
`test_never_played_player_in_starter_vbd_also_scores_the_deficit`) were written first, confirmed to
fail against the pre-fix code, then the fix landed. Commit `b567586`.

**Re-run of ADR-025.** ADR-025's published board-vs-consensus `starter_vbd` figures (+176.0 / −34.7
/ +113.4 / +83.8 for 2022-2025) were recomputed under the fix, both dev seasons and the sealed 2025
holdout (holdout access logged as a recomputation, not a fresh spend — see below):

| Season | Original (published, ADR-025) | Recomputed, current DB, same defective code | Recomputed, current DB, fixed code | Fix delta |
|---|---|---|---|---|
| 2022 | +176.0 | +174.60 | +174.60 | **0.0** |
| 2023 | −34.7 | −27.68 | −27.68 | **0.0** |
| 2024 | +113.4 | +94.10 | +94.10 | **0.0** |
| 2025 (holdout) | +83.8 | +79.54 | +79.54 | **0.0** |

**Two separate findings, not one.** (1) The fix itself changes **none** of these four numbers: zero
board- or raw-consensus-ranked players who filled a top-15 starting slot in 2022-2025 had zero
recorded games that season, so `_slot_value`'s new branch is never exercised for this specific
comparison. Directly verified by diffing the pre-fix and post-fix code against the same DB snapshot
and ranking objects (delta exactly `0.0` in all four seasons, both arms). (2) Separately, and
**not caused by this fix**, the numbers no longer exactly match ADR-025's originally published
values (174.60 vs 176.0, etc.) — this is `data/nfl.db` drift since 2026-07-25 (the DB is gitignored
and rebuilt/re-ingested repeatedly across sessions), confirmed by reproducing the drift with the
*unmodified* pre-fix code. **ADR-025's qualitative conclusion is unaffected either way**: 3 of 4
seasons positive, board advantage not statistically established at n=3/4 (CLAUDE.md §6.5,
§6.3) — unchanged in direction and magnitude class.

**The defect is real regardless — found a live instance.** `bpa_prior_season_points` (the weak
prior-season-points arm), which is exactly the class of backward-looking ranking most likely to
promote an injury-risk player, changed on `vbd_sum` (the deeper per-position metric, not
`starter_vbd`) by **−114.7 in 2022** and **−139.1 in 2025 holdout** — one player each season who
consumed a per-position slot with zero games, now correctly scored as a deficit instead of 0.0.
`starter_vbd` (top-15 budget) for this same arm was unaffected in all four seasons — the disaster
player in each case fell outside the top-15 picks, inside the deeper per-position cutoff. This
confirms the mechanism is real and fires exactly where predicted (weak/naive arms), just not on
the specific board-vs-consensus `starter_vbd` comparison ADR-025 reports.

**Blast radius — other results computed through this path:**

1. **ADR-025 board-vs-consensus `starter_vbd`** (the table above): re-run, unaffected by the fix.
2. **`bpa_prior_season_points` vs board, `vbd_sum`** (printed in the standard backtest report's
   DELTAS section, not previously published as a standalone headline in `docs/decisions.md`):
   changes materially (~$100-140 pts in 2 of 4 seasons) — the verdict was already "LOSES" against
   the board pre-fix; post-fix it loses by more. Direction unchanged, magnitude understated before.
3. **`docs/test-registry.md` #44/#45/#46 "headline" (−1,070 pts, BPA-by-2024-VBD vs FantasyPros
   consensus, scored on the real 2025 season via `src/candidate_rankings.py` +
   `_vbd_sum_for_ranking`)** — the same class of backward-looking arm shown in (2) to be sensitive to
   this defect, evaluated on the sealed holdout. **Not re-run here**: no committed script reproduces
   the original run, it reads the sealed 2025 season, and `docs/strategic-insights.md` already
   marks this exact figure "Discarded as superseded... do not cite" for unrelated methodological
   reasons (no CI, predates required per-position baselines). Flagging it as *additionally*
   contaminated by this defect, on top of already being deprecated, rather than re-running it
   myself. Escalated to `strategist`/`pm` — see handoff thread — since ADR-026 (alpha track closure)
   cites the same general ratio-of-evidence pattern this number was one input to.
4. **`docs/adr-drafts/ADR-DRAFT-oracle-ladder-disposition.md`'s planned durability test** was
   already blocked on this exact precondition (its own §"blocked on" cites precondition A by name).
   This fix unblocks it; no re-run needed since it never ran.
5. Everything else referencing `starter_vbd`/`vbd_sum` in the repo (`PR-002`, `PR-003`,
   `docs/deferred.md`, `docs/status.md`) restates the ADR-025 or ADR-020 figures above rather than
   reporting an independent number — not separately affected.

**Holdout access.** Recomputing ADR-025's figures under the fix reads the sealed 2025 season again.
Per the strategist's own ruling (§4.1): *"Re-computing an already-spent holdout number under a
corrected metric does not constitute a second holdout access... Log it as a recomputation with that
reason, do not treat it as a fresh spend."* The 2025 season was already unsealed for exactly this
decomposition (`docs/preregistration/holdout_access_log.jsonl` line 1, 2026-07-25, reviewed in
`tests/test_holdout_audit.py::REVIEWED_TIMESTAMPS`). This session's recomputation and diagnostic
re-verification (after an unrelated commit reshuffle by the shared session's other concurrent
agents required repeating the diff against the correct pre-fix parent commit) produced eight new
`FINAL_EVALUATION_OPENED` log entries, all citing this same recomputation reason. Added to
`REVIEWED_TIMESTAMPS` in `tests/test_holdout_audit.py` with this ADR as the justification note, per
that test file's own required procedure — no new registration id exists for this because it is a
recomputation of an already-reviewed access, not a new pre-registered test. No decision was made
from the holdout that was not already made in ADR-025; the fix is evaluation-only and this
recomputation confirmed rather than changed ADR-025's conclusion.

**Not in scope, deliberately.** No ranking logic, weight, or export field was touched — this is an
evaluation-harness-only fix. `test_no_new_direct_sqlite_connections_in_src`'s current failures
(`ingest_combine.py`, `ingest_contracts.py`, `ingest_ff_opportunity.py`, `ingest_officials.py`,
`ingest_participation.py`, `ingest_pbp.py`, `ingest_pfr_advstats.py`, `ingest_sleeper_projections.py`,
`ingest_trades.py`) are pre-existing, from concurrent sessions sharing this container, and unrelated
to this change — not fixed here, not this thread's scope.

**Evidence.** Commits `b567586` (fix + regression tests), plus this ADR and the
`REVIEWED_TIMESTAMPS` update. Full test count in this session's `docs/status/` entry. Handoff thread
opened to `strategist`/`pm` for item 3 above (the test-registry #44-46 figure).

---

## ADR-067 — #28 is NULL not HARMFUL, #29 is ungated and NULL, and the coordinator source is a preseason revision read

**2026-07-30, ranker.** Supersedes the `factor-batch-1-results.md` §1(2) reading of registry #28 and
the "GATED on coordinator data" status of #29/#30.

### Decision 1 — registry #28 moves from BLOCKED to NULL, and batch 1's HARMFUL grade is retired as
a data artifact

Batch 1 could only measure vacated opportunity from a Week-1 **depth chart** and graded #28 HARMFUL
at RB (+0.203 carries MAE). Re-run on `rosters_weekly` with everything else identical:

| | V1 depth chart | V2 real rosters | V2 − V1, paired, 11 seasons |
|---|---|---|---|
| RB `carries` | +0.2031 HARMFUL | −0.0123 NULL | **−0.2154 [−0.3003, −0.1384], p = 0.0006** |
| TE `targets` | +0.0448 HARMFUL | +0.0153 NULL | −0.0295 [−0.0552, −0.0043], p = 0.056 |
| WR `targets` | +0.0818 NULL | +0.0284 NULL | −0.0534 [−0.1557, +0.0507], p = 0.362 |

The V1 arm reproduces batch 1's published numbers to four decimals, so this is one harness measuring
two data sources. The mechanism batch 1 predicted is confirmed by the split it proposed: the RB harm
in the high-measured-vacancy bucket goes **+0.770 → +0.064**. The measures genuinely differ —
|V2−V1| > 0.05 on 32–35% of player-seasons, with the depth chart systematically *over*-stating
vacancy, exactly as predicted.

**Both halves are true and the row must carry both:** the harm was an artifact of the data source,
**and** the factor is NULL. Two further constructions (V3 absence share; V4 player-level
opportunity-vacated-*above*-this-player, the first genuinely player-level vacancy feature this
project has built) are also NULL. Nine cells, zero wins.

### Decision 2 — #29 and #30 are no longer gated; the source is Wikipedia staff-navbox revisions, not PFR

PFR remains 403 and is not the source. `experiments/bottomup/factors/coord_preseason.py` reads, per
club-season, the season article's revision before Week 1 (to learn which live staff navbox it pointed
at) and **that navbox page's own revision before the same kickoff**. Table
`play_callers_preseason`: 2012–2024, all 32 clubs, 803 OC+DC rows.

**Two things this establishes that were previously assumptions:**

- **The `coach_id` join works across team moves** — 53 of 126 named OCs (42.1%) appear for 2+ clubs,
  covering 243 of 400 club-seasons, **zero** same-season name collisions. `CLAUDE.md` §4's reservation
  of `coach_id` as a first-class dimension is vindicated by data rather than by argument.
- **Only 17.9% of OC changes bring in someone who was an OC elsewhere the prior season.** Any future
  tendency-following signal can reach at most one change in six. This bounds #30 before it is built.

**#29 itself is NULL**: WR −0.006 (p=0.71), TE −0.003 (p=0.87), RB +0.093 (p=0.29), with the
ADP-board metric positive at all three. Not underpowered — the OC changes for 46–48% of board
player-seasons.

### Decision 3 — `play_callers` and `play_callers_preseason` stay separate tables

`play_callers` stores `{{NFL final staff}}` — **end**-of-season. For a club that fired its OC in
November it names the replacement, and the firing is *caused by* the season going badly, so using it
as a preseason input contaminates in the **same direction as the hypothesis**. The only thing
distinguishing the two tables is which is safe to use as a preseason input; merging them destroys
exactly that. Schema ownership is data-ops' — thread
`2026-07-30-play-callers-is-not-in-nfl-db-and-end-of-season`.

### Decision 4 — the insight sentence the founder asked for is REFUSED for both factors

`FR-2026-07-30-bottom-up-causal-insights` asks the model to say *"new OC, expect routes up"* and
*"the starter from last year left."* The rule fixed before any result existed
(`factor-batch-2-precommit.md` §7): a sentence renders only if the factor **graded** and the feature
is **non-null for that player**. **Neither factor graded, so neither sentence renders.**

The cost of the alternative is measurable: `new_oc` is true for **46–48% of every ADP board**
(187/391 WR, 167/357 RB, 49/106 TE board player-seasons). Rendering it would have attached a
NULL mechanism to half of every draft board — the same failure the recommendation card was caught
committing, at ten times the surface area. Directional wording ("routes up") was never licensed:
nothing here measures routes, and route participation is not in `nfl.db`.

### A defect I introduced, disclosed rather than buried

My own pre-committed 2%-of-primary-error "this looks too good" trigger fired on the M1 arm and the
decomposition it forced overturned three arms including two SURVIVES. **95–97% of M1's effect is
`move_known` ("this player is on some club's Week-1 roster"), not `moved_club`.** `moved_club` does
nothing at any position (WR p=0.28, TE p=0.62, RB p=0.12). I added `move_known` as a companion flag
by analogy with batch 1's `vac_team_known`, which was computed but never entered a model; here it
entered the model and became the treatment. Registered grades stand as recorded with the correction
attached; **no claim about player movement may be drawn from them.** How to record them is a
`strategist` ruling, escalated on the open thread, not mine.

**Residue worth someone else's attention:** "is this player on an NFL Week-1 roster" is worth
**1.6–2.3% of component MAE** — larger than anything either factor batch produced — and the
availability sub-model does not use it. Handed over, not claimed.

**Evidence.** `docs/ranking/factor-batch-2-precommit.md` (content committed `851a6bb` before the
first fit; two amendments dated inside it, both pre-fit), `docs/ranking/factor-batch-2-results.md`,
commits `70bc893`, `fe3b66a`, `5d3e95e`, `df50e3b`, `da10906`, `dbc52a5`. 10 discipline tests
including bit-for-bit reproduction of batch 1's feature frame. Sealed 2025 holdout not opened.

## ADR-068 — Four selectable ranking sources: board order runs off any of three built sources, never blended; availability/opponent-model wiring deliberately deferred (2026-07-30, backend, FR-2026-07-30)

**Decision.** `docs/founder-requests/FR-2026-07-30-four-selectable-ranking-sources-driving-every-fe.md`:
"The draft board should be able to be fully functional off of consensus or my own rankings... App
should run based on any at user toggle." `ranking_source` (CLAUDE.md §4) already named the four
values; this wires the board layer onto it.

**`make_board.py`** gains `RANKING_SOURCE_SELECTIONS = ("expert_adjusted", "expert_raw",
"market_adp", "proprietary")` and a `ranking_source_selection` parameter on `build_board()`,
default `"expert_adjusted"` — regression-tested byte-identical to the pre-existing default
(`test_default_selection_is_expert_adjusted_byte_identical_to_old_default`). The value curve
(`fit_rank_curves`/`bootstrap_vbd_intervals`, fitted once on `TRAINING_SOURCE`) is applied under
every selection — it is a source-independent valuation lens, not itself a fifth blended source —
but board **order** is selection-specific and never re-derived from our VBD except under
`expert_adjusted`:

| Selection | Board order | Rows from |
|---|---|---|
| `expert_adjusted` (default) | our VBD, desc | `rankings[fantasypros_csv_2026draft]` |
| `expert_raw` | the source's own consensus rank, asc | same table, same rows |
| `market_adp` | FFC half-PPR/10-team ADP, asc by `average_pick` | `ffc_adp_snapshots`, resolved to gsis via the `player_ids` mfl_id↔gsis crosswalk (measured: 158/167 QB/RB/WR/TE rows resolve; unresolved rows dropped, never guessed) |
| `proprietary` | — | does not exist; `build_board()` raises `RankingSourceNotBuilt`, never falls back |

FFC half-PPR/10-team, not MFL proxy, is the `market_adp` source: it is the only ADP source whose
*format* matches this league (half-PPR, 10 teams) — see `ingest_ffc_adp.py`'s own docstring. MFL
proxy stays a display-only per-player field (`board.json:adp`/`adp_source`), unchanged, never
driving order — CLAUDE.md §4 forbids blending it with FFC into one "ADP" figure.

**Coverage is honestly thin for `market_adp`**: 158-167 rows vs. ~554 on the expert board. Reported,
not hidden — `describe_ranking_source()`'s `row_count`/`note`, and
`board.market_adp.json`'s own `ranking_source_row_count`.

**`export_contract.py` (contract 1.17.0 → 1.18.0):** `build_board_json()` gains the same
`ranking_source_selection` parameter and a `ranking_source_selection`/`_label`/`_built`/
`_as_of_date`/`_row_count`/`_note` field set on every board artifact — **each source carries its
own as_of_date and row count**, per the founder's explicit ask ("a user switching sources is
entitled to know what they switched to"). `_not_built_board_json()` gives `proprietary` an
explicit, empty, honestly-labeled shape (`ranking_source_built: false`, `players: []`) rather than
raising past the export boundary or silently substituting another source. New
`build_ranking_sources_json()` catalogs all four (built or not) in one file so a client can render
the full picker without probing each variant. `write_all()` now writes `board.json` (unchanged
name/default, `expert_adjusted`), `board.expert_raw.json`, `board.market_adp.json`, and
`ranking_sources.json` for the primary league. Non-primary league directories (the 24-config
matrix) are unchanged by this session — regenerating all of them for the two new sources was out
of scope; they still carry only the pre-existing `board.json`.

**What still runs off a single hardcoded source, and why that is not fixed here.**
`simulate_availability` (`src/availability.py`) drives both the opponent model's central tendency
and the user's own `strategy_bpa` pick off `draft_sim.load_season`'s single `CONSENSUS_RANK_SOURCE
= "fantasypros_ecr"` — confirmed live in this session, matching the founder's own diagnosis
(FR-2026-07-30: "the two live sources disagree on 73 of the top 80 players"). This is a **real,
audited silent-fallback gap**, not an oversight: an **open, unresolved thread**
(`docs/handoffs/2026-07-30-availability-adp-measurements-m0-m5.md`, strategist → backend) is
mid-flight on exactly this code path, gates M0-M5, and says explicitly *"Do not implement the
change yet — M0 is a gate and can stop half of it."* M0 already found FFC's `times_drafted` field
does not reconcile against its own documented denominator, and M1 found FFC ADP does **not** beat
the incumbent ECR baseline on MAE in 2 of 3 real mock drafts. Wiring `market_adp` into the
Monte Carlo's central tendency in this session — even behind an explicit user toggle — would ship
availability numbers under an "ADP" label with no calibrated dispersion (M2/M3 unmet), exactly the
"looks plausible while over-dispersing" failure M3 names. **Decided and logged, not escalated**:
availability/opponent-model wiring stays out of this pass; the board layer (order, VBD, tiers,
projected_points — everything `export_contract.build_board_json` drives) is fully wired across all
three built sources, and this gap is reported to the M0-M5 thread and to `docs/CURRENT-STATE.md`
by name rather than left implicit.

**Recommender fallback value.** `recommendation.ts`'s `g` term (value over the realistic fallback)
reads its ranking inputs from `board.json` — no server-side recommender code exists in `src/`. Once
frontend requests the source-matched board file (`board.json` / `board.expert_raw.json` /
`board.market_adp.json`) per the toggle, the recommender follows automatically; no backend change
was needed or made here.

**Tests.** `tests/test_make_board.py` +10 (ranking_source_selection enum, byte-identical default,
raw-order monotonicity, `RankingSourceNotBuilt` never-falls-back, `describe_ranking_source` for all
three built sources, the founder's own 73-of-80-disagreement measurement reproduced as a >5-player
floor against live data). `tests/test_export_contract.py` +6 (default selection field, proprietary
explicit-absence, raw vs. adjusted order differs, market_adp's own as_of/count, unknown-selection
`ValueError`, `ranking_sources.json` never hides the unbuilt option). Written before the
implementation (sanity-checks-first), confirmed failing pre-implementation, all pass now.

**Sealed 2025 holdout not touched** — this is export/contract plumbing over the live 2026 board,
no backtest or historical season read.

**Handoff:** `frontend` thread describing the new fields/files (contract version bump, per
CLAUDE.md's contract-change rule); reply appended to the M0-M5 availability thread noting the
interaction and this session's scope decision.

## ADR-069 — The bar is absolute quality, not edge over consensus: rankings are built independent of consensus and portable across league scoring (2026-08-01, pm, founder ruling)

**Status:** Accepted. Written into `CLAUDE.md` as new §2a, with a scope amendment to §6.5 and a new
schema principle in §4. Source: `docs/founder-requests/FR-2026-08-01-bar-is-absolute-quality-not-edge-build-rankings.md`.

**Context.** Fable's M2 review (`docs/fable/M2-findings.md` §F1-F7) ruled that the campaign's
measurement frame was asking a question it could not answer in the affirmative: "can we beat
consensus" was being asked of an object *derived from* consensus. The shipped board is consensus
re-scored — within-position identical to consensus, deviating only cross-positionally through four
slopes and four replacement ranks. ~90 factor nulls therefore carry far less information than they
appeared to, and the correction resurrects no dead factor.

The founder's response was not a better test. It was to stop deriving from consensus and stop
steering by it:

> "Our bar is not consensus. It's how good can our rankings be. When we think they are as good as
> they'll get ... then we can test vs the other three models like consensus, consensus adjusted and
> ADP etc."

**Decision — three binding consequences.**

1. **Consensus is not an input.** The ranking is built from player-level projections, not by
   re-scoring another party's order. The current board is replaced, not extended.
2. **Consensus is not the development signal.** Absolute quality against realised outcomes steers
   the build. §6.5's four baselines become a **release gate run once when a version is declared
   finished**, not a per-arm steering metric.
3. **Projections are stored and computed as stat lines, never as fantasy points.** Volume,
   efficiency and games per player; points derived by applying a league's scoring config; ranks by
   applying its roster shape to obtain replacement levels. Changing league scoring must re-score and
   re-rank **without re-fitting**.

**Why (1) and (3) are one requirement, not two.** A board whose within-position order comes from
consensus cannot respond to league scoring at all — consensus is produced for a generic 12-team
full-PPR room, so this league's half-PPR, stacking yardage bonuses (§7) and 10-team replacement
levels cannot reach the ordering by any route. Scoring portability is achievable only *through*
independence. The corollary matters for planning: the current board **structurally cannot** deliver
the portability the founder asked for, so this is not optional polish.

**§6.5 is not weakened.** A version that fails the four-baseline gate still has no edge and is still
reported as a failure in exactly the terms §6.5 requires. Only the *timing* of the question changed,
so that development is not implicitly optimising toward the benchmark it is meant to be independent
of. Overfitting protection during development remains the sealed 2025 holdout (§6.3), registered
thresholds, and the campaign-level `M` — the consensus gap never provided that protection and was
not doing so.

**Named risk, recorded in advance.** v1's rate projections are already at or better than market
parity; its entire measured deficit is one channel — **projected games** (Fable M2-1). That is also
where consensus's real advantage lies: it knows who is going to play. Independence therefore stands
or falls on building an own player-availability model from injury history, age, workload and
pre-Week-1 status (resolved vs ongoing absence — the Burrow/Hill defect class). **Distinct from
*draft* availability despite the shared word.**

**Consequences.** Core of the Monday Fable builder mandate
(`FR-2026-08-01-turn-the-keys-over-to-fable-to-build-the-next-bo`), priority order: stat-line
projection architecture, then player availability, then rates. PR-007 is unaffected. Any existing
document reporting a result as "no edge over consensus" during component development is now
mislabelled per §6.5's 2026-07-31 scope ruling and this one; corrections route through the owning
role, not by edit-in-place from whoever notices.

## ADR-070 — The factor inclusion decision rule for ranking v2: permutation nulls, sequential Monte Carlo p-values, and calibrated sign-consistency (2026-08-01, strategist, thread 2026-08-01-c1-the-registered-win-rule)

**Status:** Accepted. Full text: `docs/adr-drafts/ADR-070-factor-inclusion-decision-rule.md` (§4 is the
rule, §5 its cost, §6 how the next batch verifies it). Recorded here in summary; that file governs.

**Trigger.** Batch C1's registered placebo — a column of seeded noise that provably cannot carry
signal — returned a BH-robust WIN at TE (+0.0303, p = 0.0002) and the registered rule graded it
`INCLUDE`. Replication across 34 independent noise draws measured the harness false-positive rate at
**9.6% of cells against a nominal 2.5%**.

**Decision.** The estimator is **unchanged** — mean of per-season Spearman deltas. Changing the
estimand after seeing which arms nearly won is tuning, and every stored per-season delta re-grades
without a refit. What changes is the uncertainty:

- **Null:** a matched per-cell ensemble — joint within-season row permutation of *that arm's own
  column block*. Matches column count, marginals, within-block correlation and `*_known` coverage
  rate for free. The 1-column Gaussian placebo matched none of those for a 3-column arm.
- **p-value:** Besag–Clifford sequential Monte Carlo (h = 20, L = 3,000), two-sided. **No p below
  `2/(L+1)`, and no parametric tail fit.** Refusing a Gaussian/GPD tail fit is load-bearing: it would
  put F3-RB and F6-QB *over* the BH bar and the placebo *under* it, on an assumption nothing
  validates — the same error the bootstrap made in new clothes.
- **BH retained** on top, at cumulative campaign **M = 130**, and explicitly **not shrunk** — the
  "batches 1–7 tested a different primary model" argument was rejected in writing, because C1
  re-tested factors batches 3/5/7 had already tested.
- **Pre-committed error rates**, so batch C2 can verify them the way C1 verified its predecessor:
  HYPOTHESIS on a true null **≤ 5.0%**; any INCLUDE/EXCLUDE across an all-null 20-cell batch
  **≤ 1.3%**.

**Two changes originating from the founder, mid-task, both adopted.**

1. **Calibrated sign-consistency (§4.4a).** Strategist's first draft rejected a sign criterion for two
   correct reasons — the p-floor 2⁻⁷ = 0.0078 cannot reach a 7.7×10⁻⁴ threshold, and π₀ ≈ 0.77 at QB
   rather than 0.5. **Both objections vanish when `C = W⁺ − W⁻` is calibrated against the permutation
   ensemble instead of a binomial**, because the ensemble embeds both the 0.77 and the exact-zero
   mass. Costs zero extra draws, is integer and hand-auditable, and contains no resampling in its
   definition. Enters as a **required condition, never a second discovery route.** Stated consequence,
   accepted: this probably makes INCLUDE unreachable at QB, and at S = 7 that is the correct answer.
2. **HARM splits (§4.4b)** into **RE-SPECIFY** (BH-robust *and* sign-consistent — a column carrying no
   information cannot *consistently* degrade ordering) and **EXCLUDE (variance)**. Guardrail against
   "include it differently" becoming an unbounded search: **exactly one attempt, from a four-item menu
   fixed before it runs, named with its mechanism, entering the campaign denominator.** Falsification
   condition registered — if measurement M-1(B) shows noise routinely produces `C ≥ 4`, RE-SPECIFY is
   wrong and is withdrawn.

**Consequences.**

- **Batch C1 re-grades in full. The arms do not re-run** — only the null ensembles get built. Its six
  factor-level NULLs stand as *inclusion outcomes*; its **cell-level** results are `UNCALIBRATED`,
  not dispositioned. Ranker's argument that miscalibration only inflates false positives is right for
  what it covers and covers half the problem: the same discreteness has **no power** on mixed-sign
  vectors (placebo sd ≈ 0.003 at RB against a CI half-width of 0.020).
- **F6-QB's confirmatory test is refused and its "clears the placebo null" claim withdrawn** — F6 adds
  no column, so a column-addition placebo was never its null. Replaced by
  `docs/preregistration/PR-DRAFT-lag-weight-decay-profile.md`.
- **F3-RB** is a *suspended* registered cell, to be finished in its own family, but a `d` = 3 matched
  null runs first and may kill it for almost no compute.
- **Campaign correction:** BH flags are withdrawn as error-control claims on the old estimator, but
  **realised type-I exposure is nil** — zero inclusions in ~130 tests, and FDR is a property of
  discoveries. The live exposure is **type-II**, which is why no lower "provisional admit" tier was
  offered.
- **Batch B1 was deliberately not touched** (fable's registered batch). The ADR supplies the
  instrument and names the three load-bearing cells; **B1's WR HARM −0.0125, which rejected G1 and
  G1a, cannot be assessed until the ensemble's lower tail is published.**

**The structural finding, and the highest-value item on the list (M-4).** Every problem here reduces
to **S = 7**. At seven seasons **no exact season-level randomisation test can reach a BH threshold by
any method**; at twelve it can. How far back the target span can go is therefore worth more than any
individual factor currently queued.
