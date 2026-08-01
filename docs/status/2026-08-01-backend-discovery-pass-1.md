# 2026-08-01 — backend — discovery pass 1 (reverse-identification hypothesis generation)

FR-2026-07-31-reverse-discovery, dispatched directly (not via handoff thread). Founder asked,
2026-08-01, for a way to "give us a hypothesis" instead of always testing one someone already
thought of — the same request he raised 2026-07-31 as "reverse identification via trend
analysis" after finding the Burrow-availability and Allen/Jackson-QB-tilt issues by eye.

## What was done

Residual analysis on `ranking_v2_G0_players.csv` (v2's pinned control arm, per `batch-C1`):
computed signed/absolute residual of realised vs. projected points (standardized within
season x position), split into a discovery sample (2018-2021, the only seasons analyzed) and
a confirmation sample (2022-2024, loaded but never touched). Three methods, in the dispatch's
priority order:

1. **Residual slicing** (10 slice variables, 30 real cells with n>=15) — the core method.
2. **Systematic screening** (62 real candidate columns + 1 noise control, x2 targets, x5
   slices = 630 correlational tests).
3. **RandomForest as a generator only** (6 model fits, permutation importance) — explicitly
   not a modeling decision, per `CLAUDE.md` §6.3's "start with weighted/regression, not ML."

Negative control (seeded N(0,1) column) run identically in every section. It never exceeds
|t|=1.90 in the slice screen (0 of 30 noise cells clear |t|=2, vs 13 of 30 real) and ranks
near the bottom of every correlation/importance table — a much cleaner separation than
`batch-C1`'s F0 placebo, which exploited a bootstrap-CI rule at n=7; this pass uses plain
magnitude comparisons at n in the hundreds to low thousands, which don't share that
small-n discreteness problem.

## What was found (all hypotheses, none tested/registered/adopted)

1. v2's games/points channel under-reverts toward the mean on prior-season games-played
   (0-4 games_1: +0.23 SD, t=9.3, n=595; 14-17 games_1: -0.29 SD, t=-8.8, n=707).
2. Same pattern isolated to unexpected-absence share specifically — population-scale version
   of the founder's own Burrow/Hill finding (heavy: +0.20 SD, t=10.6, n=1,004).
3. Week-1 depth-chart starter status, found only by the GBM generator as an interaction with
   prior-season games (invisible to the linear screen — pooled/per-position rho was weak and
   non-monotone), confirmed by a manual two-way slice: starters beat non-starters at every
   games_1 level by a consistent margin.

Bug found and fixed along the way: `depth_charts_weekly`'s `pos_rank`/`pos_slot` columns are
entirely unpopulated despite being named for exactly the starter/backup signal this pass
needed — `depth_team` is the field that actually carries it. `injuries` has no `PRE`
game_type rows at all, so the "preseason injury" indicator is documented as a Week-1-of-season
proxy instead. Both are the source-swap-is-not-a-substitution pattern `CLAUDE.md` calls out
by name for `src/ingest_rankings.py` — found the same way, by reading the table directly.

## Environment note

My worktree branch (`worktree-agent-a7d5127b279cd7e2b`) was several commits behind
`claude/pm-agent-setup-gobxa0` at session start — missing `batch-C1-results.md`,
`v2-build-log.md`, and the `ranking_v2_G0_players.csv` the dispatch named. Fast-forwarded
onto `claude/pm-agent-setup-gobxa0` before starting (clean ff-merge, no conflicts) rather
than escalating, since it was a pure fast-forward with nothing to reconcile.

## Deliverable

`docs/ranking/discovery-pass-1.md`. Scripts: `experiments/bottomup/discovery_pass1.py`,
`discovery_pass1_slices.py`, `discovery_pass1_screen.py`, `discovery_pass1_gbm.py`. None of
`experiments/bottomup/v2/factors_c*.py` or the campaign manifest was touched, per scope.

## Next step (not mine)

`strategist` pre-registers a confirmatory design for candidates 1-3 on 2022-2024 before any
of them is fit there. The 2025 holdout is untouched and stays that way.

Commits: `938f4c1` (base pipeline), `f79043a` (screening + noise control), `0c4dc94` (report,
slices, GBM, derived data).
