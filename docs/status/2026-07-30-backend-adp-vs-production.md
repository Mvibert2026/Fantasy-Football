# 2026-07-30 — backend — ADP vs production analysis (FR-072, thread 096)

Dispatch: founder's own words, "so now we can also look at ADP vs Production and try to establish
patterns." Explicit instruction: not "which players busted" (hindsight) — structural mispricings
identifiable *before* the draft. Explicitly told not to duplicate the ranker's concurrent RB/QB/TE
component-model work in a separate worktree — this measures the market, doesn't touch model code.

**Tier note.** This is statistical-methodology work; CLAUDE.md §9 says that belongs at Opus/high
effort. The dispatch didn't specify a tier. Flagged in the writeup and proceeded at the best tier
available rather than stopping to ask, per this session's own operating rules.

## What was built

- `analysis/adp_vs_production.py` — reproducible script, no network calls, ~15s runtime.
- `docs/analysis/adp-vs-production-2026-07-30.md` — full writeup: method, three caught-and-fixed
  design bugs (documented, not hidden), results ranked by confidence, honest null results.
- `data/qa/adp-vs-production-2026-07-30.json` — raw per-family/per-era/per-holdout tables.
- Thread 096 opened to `strategist` for Opus-tier methodology review before anything here reaches
  the ranking model.
- FR-072 filed and marked DONE for the analysis deliverable; two follow-on gaps noted inside it
  (no real 10-team historical ADP source anywhere in this project; `play_callers` coach-identity
  table has zero rows in this environment).
- `docs/ideas-inbox.md` entry with the three things decided without asking (below).

## Data source work, not just analysis

This worktree's `nfl.db` did not have the thread-055 FFC historical-ADP backfill
(`ffc_half_ppr_12team`/`ffc_non_ppr_12team`, 2018-2024/2013-2024) even though
`docs/CURRENT-STATE.md` said it had landed. `nfl.db` is gitignored and worktrees don't inherit it
(`docs/environment.md` §4) — loaded the 2,467 rows directly from the already-committed CSVs
(`data/adp-snapshots-ffc/*_12team_period*.csv`) into this worktree's DB copy. No network call, no
re-fetch — same data, same historical `as_of_date`s.

## Methodology — guardrails applied, stated explicitly

- **Look-ahead:** all "prior-season" features computed from season N-1 or earlier only; ADP's
  `as_of_date` is the historical mock-draft window's real end date (backfill script's own
  verification against nflreadpy schedules), not any run date.
- **Survivorship:** universe = players in that season's FFC ADP snapshot, decided pre-season.
  Busts retained at 0 points/replacement-floor VBD, never dropped.
- **Multiple comparisons:** six pre-registered families, one p-value each (season-clustered
  permutation test), Benjamini-Hochberg correction across the six.
- **Holdout:** 2024 held out, touched once at the end; 2025 isn't in this ADP source at all, so
  the project's locked holdout is untouched by construction.
- **Non-stationarity:** every family reported per-era (2018-2020 16-game vs 2021-2023 17-game).
- **Uncertainty:** season-clustered bootstrap 95% CIs on every reported effect size.

## Three design mistakes caught before publishing, documented rather than hidden

1. Per-position value curve makes every position's residual trivially ~0 by construction —
   caught before running the family test, redesigned to an overall cross-position curve.
2. Raw-points cross-position curve "found" QB underpriced by +146 pts/season — actually this
   league's 1-QB roster rule, not a market inefficiency. Redesigned to use value-over-replacement
   (`scoring.compute_vbd`, this project's own ADR-029 baselines), reusing what `backtest.py`
   already uses to evaluate rankings rather than inventing new machinery.
3. FFC's `rank` column includes kickers (dropped from this analysis), leaving gaps in the filtered
   universe's rank sequence; indexing the value curve by raw rank silently clamped every rank past
   the filtered length onto the same tail slot. Caught by adding an internal consistency check
   ("does residual sum to ~0 within a season, as the permutation design requires") and finding
   season 2022 alone summed to +1,465.76 points before the fix. Fixed by indexing on ordinal
   position within the filtered, sorted universe instead of the raw rank value.

## Results (see the writeup for full tables and confidence labels)

- **MODERATE:** early-round RB (1-3 of 12-team mock rounds) underperforms same-round peers at
  every other position by ~3x. Era-stable; the *unconditional* position-level framing (not
  round-conditional) did not clearly survive the 2024 holdout (RB flipped from -20.2 to +1.6 VBD
  pts) and is explicitly flagged as the weaker framing, not the one to carry forward.
- **MODERATE-HIGH:** young WR/TE (age <=23) outperform ADP by +34.6 VBD pts/season, holds
  directionally in both eras.
- **No reliable pattern (reported plainly, not buried):** prior-season games missed, team change,
  prior volume-vs-efficiency split. Sign flips between eras or CI crosses zero in every bucket.

## Decided without asking (logged, see docs/ideas-inbox.md for the full entries)

1. Loaded the historical FFC backfill from committed CSVs rather than re-fetching or blocking on
   the missing DB state.
2. Did not attempt coach/coordinator-identity ingestion (`play_callers` is empty here) — out of
   scope for a measurement-only dispatch, and CLAUDE.md §5 flags coaching-staff scraping as
   needing its own licensing check before building.
3. Did not open an ADR — nothing here is settled enough to change the ranking model yet; that's
   exactly what thread 096 asks `strategist` to determine.

## Verification

- `python3 analysis/adp_vs_production.py` runs clean, produces `data/qa/adp-vs-production-2026-07-30.json`.
- `pytest tests/test_holdout_audit.py` — 3 passed, 1 pre-existing failure
  (`test_no_new_direct_sqlite_connections_in_src`, `ingest_sleeper_projections.py`, thread 094,
  not touched this session).
- Full suite run in background this session; see commit message / final report for the count.

## Files touched

- `analysis/adp_vs_production.py` (new)
- `docs/analysis/adp-vs-production-2026-07-30.md` (new)
- `data/qa/adp-vs-production-2026-07-30.json` (new, generated — gitignored data dir, check before
  assuming this is committed)
- `docs/handoffs/096-adp-vs-production-methodology-review.md` (new, via `tools/handoffs.py new`)
- `docs/founder-requests/FR-072-adp-vs-production-analysis-run-on-12-team-mock-a.md` (new, via
  `tools/founder_requests.py new`)
- `docs/ideas-inbox.md` (appended)
- `docs/CURRENT-STATE.md` (edited in place)
- `docs/status/2026-07-30-backend-adp-vs-production.md` (this file)
