---
ID: FR-079
STATUS: IN PROGRESS
SOURCE: chat 2026-07-30, PM session (feedback batch)
RAISED: 2026-07-30
---

## Request
Last few seasons must render in the selected scoring format

Founder's own words:

> "Last few seasons should be in correct fomat as well"

## Why it matters

## Initial read
<Not the founder's own words -- PM's read on scope, constraints, sequencing.>

## Resolution (2026-07-30, frontend)

**Premise checked, not assumed wrong: it's correct, and the fix is not a frontend one.** Traced
`season_stats.json`/`weekly_finishes.json` back to their builder,
`src/export_history.py::build_season_stats`/`build_weekly_finishes` — both sum/rank
`player_weekly_stats.fantasy_points_ppr`, a fixed standard-PPR figure computed once, with no
`scoring_cfg` parameter at all (unlike `make_board.build_board`, which does take one). Separately
confirmed these two files aren't even exported per league — they live unprefixed at the top level
only (`ui/data/playerHistory.ts`'s own docstring already said so: "unprefixed, not per-league");
`data/export/espn_10_standard/` etc. carry no copy. So switching leagues cannot change these
numbers today, even in principle.

Per this project's rule against approximating scoring outside the pipeline, **did not** re-derive
fantasy points client-side from raw counting stats — that would be inventing a number, not fixing
one. Instead added an honest, static disclosure next to both the weekly-finishes heatmap and the
three-season table (`frontend/ui/components/PlayerDetail.tsx`): "Ranked by standard PPR scoring,
not this league's own ruleset ... does not yet vary by league." Screenshot:
`frontend/e2e/artifacts/fr079-player-card-westwood-history.png`.

Backend defect (the fixed-format gap itself) logged to `backend` for a real decision:
`docs/handoffs/NEW-adp-and-history-not-league-scoring-aware.md` (pending PM's ID allocation).
`npx tsc -b --noEmit` clean. Test count/commit: see session report in `docs/status/`.

## Resolution (2026-07-30, backend)

Root cause fixed. `player_weekly_stats.fantasy_points_ppr` was never this project's scoring
engine at all -- nflreadpy's own fixed full-PPR column, wrong for every league including
Westwood. `src/export_history.py` now re-scores every player-week from raw counting stats through
`scoring.score_offensive_game(stats, cfg.scoring)`, summed after per-game scoring so yardage
bonuses (game-level thresholds) are neither fabricated nor dropped. `season_stats.json`/
`weekly_finishes.json` are now built by `export_contract.write_all` and land under
`export_dir_for(cfg.league_id)` for every league, the same per-league pattern `board.json`
already used -- no longer unprefixed-only. Verified: the same player's 2022 season scores 283.2
under Westwood vs 271.7 under a standard 0-PPR preset.

**Contract 1.15.0 -> 1.16.0.** `season_stats.json`'s `fantasy_points_ppr` field is renamed
`fantasy_points` (not additive) plus a new `fantasy_points_available` bool. Full detail and the
per-league-artifacts-vs-read-time-application tradeoff:
`docs/handoffs/NEW-adp-and-history-not-league-scoring-aware.md` (backend's reply).

**STATUS left at IN PROGRESS, not SHIPPED** -- backend's part is done and tested, but frontend's
honest disclosure in `PlayerDetail.tsx` still needs to consume the renamed field and the new
per-league path before this is founder-visible as fixed; per this session's own instruction, that
disclosure was deliberately left in place rather than removed pre-emptively.
