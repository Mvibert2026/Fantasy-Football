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
