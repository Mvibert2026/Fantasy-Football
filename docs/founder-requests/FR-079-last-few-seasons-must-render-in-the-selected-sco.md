---
ID: FR-079
STATUS: NEW
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
