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
