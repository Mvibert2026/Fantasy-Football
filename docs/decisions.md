# Architecture Decision Log

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
NOT survive removal of the holdout. Including 2025, `starter_vbd` delta was +84.6
[+2.3, +153.0] (excluding zero). On development seasons only it is −84.9 [−166.1, +34.7] —
no demonstrated difference, and the sign flips. The first number would have been reported as
a finding.

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
