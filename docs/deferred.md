# Deferred Decisions

## Normalized `players` dimension table

`CLAUDE.md` §4's core-tables sketch lists both `players` and `player_weekly_stats`. Only
`player_weekly_stats` was built (2026-07-25). A separate `players` table would require making
identity-resolution judgment calls (current team/position when they change mid-season or
year-to-year, name changes, etc.) with no current consumer — the raw fact table already carries
`player_name`, `position`, and `team` per row, which is sufficient for Step 1. Build it when the
scoring engine (Step 2) or ranking algorithm (Step 4) actually needs a stable per-player entity
to join against, not before.

## `player_season_stats` table

Also in `CLAUDE.md`'s sketch, not built. Season-level aggregates are a derived view over
`player_weekly_stats` (sum/avg by player+season) with no independent source data — better as a
SQL view or computed at read time once there's a real consumer, rather than a second cached copy
that can drift out of sync with the weekly table.

## Coaching staff, odds, ADP ingestion

Explicitly out of scope for this pass — the task was weekly player stats only. `coach_id`,
`odds_snapshots`, and `adp_snapshots` remain unbuilt. Per `CLAUDE.md`'s own flag: ADP snapshot
capture with `as_of_date` should start "immediately regardless of sequence" since it can't be
backfilled later — this is the next highest-priority ingestion gap, not weekly stats.

## True multi-source ADP (2026-07-25, attempted, blocked)

Requested sources: FFC, Yahoo, ESPN, Sleeper, Underdog. None ingested. Per-source finding:

- **FFC (Fantasy Football Calculator):** `robots.txt` explicitly disallows `/api/`, `/ajax/`,
  and `/adp/csv/`. No published API docs or ToS permitting programmatic access were found.
  `CLAUDE.md` §10 requires checking terms *before* building a scraper. Blocked, not attempted.
- **Yahoo / ESPN:** Would require OAuth and league-scoped access for any real draft data; no
  known public bulk ADP export. `CLAUDE.md` §10 explicitly discourages scripted-login workarounds.
  Not attempted.
- **Sleeper:** Has a public read-only league API, but no known public *aggregate ADP* dataset
  (as opposed to one league's own draft results). Not attempted — would need more research.
  Underdog: no known public API at all. Not attempted.

**What's actually available today:** FantasyPros Expert Consensus Rankings (ECR), via
`nflreadpy.load_ff_rankings()` → DynastyProcess.com's mirror — already ingested for 2025
(`src/ingest_rankings.py`, `source="fantasypros_ecr"`). This is expert opinion, not observed
draft position; the backtest harness (`src/backtest.py`) reports `consensus_adp` as explicitly
unavailable rather than substituting ECR under the ADP label. Test-registry.md's own tracked
status for "Multi-source ADP" (Tier 0 #1) was already `SPEC` (not started) before this pass —
this finding narrows the scope (FFC ruled out) rather than starting from zero.

**Next step if this becomes a priority:** get explicit authorization/API-key access to FFC (email
them — some hobby-analytics API access has historically been grantable on request even where
`robots.txt` blocks anonymous crawling), or have the user manually export ADP snapshots from
sites requiring login.

## FantasyPros preseason rankings for other backtest seasons (2021-2024)

Only the 2025 preseason snapshot was ingested (as literally requested). `load_ff_rankings(type=
"all")` already returns the full history back to 2020 in one call, so extending
`src/ingest_rankings.py` to backfill 2021-2024 preseason snapshots is a cheap follow-up (no new
data source, same function, just loop over seasons) — needed before the backtest harness can
evaluate any season other than 2025.

## Backtest harness: no draft-cost-sensitive comparison metric (2026-07-25, found while running #44)

`_vbd_sum_for_ranking()` (`src/backtest.py`) only tests whether a ranking puts the right players
*in* each position's startable pool (top-N by `ReplacementLevels`) — it's blind to the *order*
players are ranked in beyond that cutoff, and therefore blind to draft-slot opportunity cost.
Discovered running the Hero RB config (test-registry.md #44): boosting the value of RBs already
comfortably inside the RB28 cutoff produced an *identical* result to plain BPA, because the boost
never changed pool membership. This isn't evidence Hero RB is neutral — the test just can't see
what the strategy does.

Needed before any "pick X earlier than consensus" strategy (Hero RB, Zero RB, elite-TE-early,
etc.) can be tested for real: a metric sensitive to what you gave up elsewhere by reaching, e.g. a
draft-pick-slot simulation (take the ranking, assign players to picks in snake order, compare the
resulting roster's total value against a baseline roster built the same way) rather than a pure
value-over-replacement sum. Bigger lift than the current metric; not attempted this pass.

## Statistical guardrails compliance gaps (2026-07-25, found auditing #44/#45/#46 against the new doc)

`docs/statistical-guardrails.md` landed after the #44/#45/#46 runs. Auditing those runs against its
own pre-mortem checklist (full table in test-registry.md) surfaced concrete, fixable gaps — not
retracting the findings, but none of them are "validated" by that doc's standard yet:

1. **`backtest.py::_rank_correlation` computes correlation across all positions mixed together.**
   `statistical-guardrails.md` §6 requires it within position group (QB ranks vs. QB outcomes,
   not QB/RB/WR/TE pooled). Fix: group by position before calling `spearmanr`, return a per-position
   dict (and probably a position-weighted or separately-reported aggregate, not a single blended
   number — needs a design decision, not just a mechanical change).
2. **No confidence intervals anywhere in `backtest.py` output.** §7 requires season-level bootstrap
   resampling for any reported metric (correlation, vbd_sum delta). With 5 seasons of data, every
   point estimate reported so far (-1,070 pts, -226.4 pts, etc.) is, per that doc, "close to
   meaningless" without one. Needs a `bootstrap_seasons()` utility and a decision on how many
   backtest seasons are actually available to resample from (currently only 2025 has FantasyPros
   preseason data ingested — see the FantasyPros-backfill item above; bootstrapping single-season
   metrics needs a different resampling unit, e.g. players-within-season with a
   caveat, until multi-season data exists).
3. **No multiple-comparisons correction infrastructure.** Not urgent at 3 configs, but test #53 and
   any future factor sweep (Tier 1's ~20 items) will need Benjamini-Hochberg FDR correction
   (§3.2) before reporting "significant" factors. Build this before, not during, that sweep.
4. **No pre-registration workflow.** §3.4 requires writing down the exact metric/threshold that
   counts as confirmation *before* running a test, especially for folk-wisdom factors. No file or
   convention exists yet for recording a pre-registration. Needed before test #53 runs.

## Defense/DST scoring and ingestion

`scoring.py` ports `score_defense_game()` from the source code as given, but no ingestion
pipeline feeds it — `player_weekly_stats` and the `rankings` table are both skill-position-only
by construction (DST rows are dropped in `ingest_rankings.py` for lack of a `gsis_id`). The
league does have a DEF slot (`CLAUDE.md` §7 / test-registry.md league context). Out of scope for
this pass since it wasn't part of the requested narrow schema; the backtest harness currently
only evaluates offensive skill positions.
