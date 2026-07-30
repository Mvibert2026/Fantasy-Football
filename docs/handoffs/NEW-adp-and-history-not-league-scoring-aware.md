---
FROM: frontend
TO: backend
STATUS: OPEN
BLOCKS: none
---

## Ask

FR-083/FR-079 ("Why do player notes cards not show adp for the correct format for the league
selected?" / "Last few seasons should be in correct fomat as well") traced to two backend
data-generation gaps, not a frontend routing bug. Frontend already reads whichever league's
`board.json` is currently loaded correctly (`ui/data/board.ts` has no cross-league caching); the
underlying export fields themselves aren't league-scoring-aware. Two separate, independently
fixable problems:

**1. `board.json:adp_source_note` hardcodes Westwood's own ruleset in its prose, for every league.**

`src/export_contract.py:279` calls `_load_adp_snapshot(conn)` with no `cfg` argument, so every
league (Westwood and all 24+ presets alike) gets `adp_source='mfl_proxy'` — the one universal,
full-PPR-ish MFL proxy capture. Separately, and worse: the note text itself
(`src/export_contract.py:531-547`) is hand-written prose that says, verbatim, "MFL's IS_PPR flag
is binary and this league scores half-PPR" — literally false for every non-Westwood league.
Reproduced live this session: `espn_10_standard`'s board.json (a STANDARD, 0-PPR league per
FR-042/ADR-062) carries this exact sentence unchanged. Screenshot:
`frontend/e2e/artifacts/fr083-player-card-standard-league-adp-block.png` — the backend's own note
claiming "half-PPR" sits directly above frontend's new `league.json:scoring_ruleset_note` display,
which correctly says "STANDARD ruleset (FR-042)... no stacking yardage bonuses." The two visibly
contradict each other on screen now, which is the honest state given what's fixable from
frontend, but the root fix is here.

Two sub-asks, and they may have different owners/timelines:
- (a) The `adp_source_note` prose should read `cfg.scoring`/`cfg`'s real ruleset and only assert
  what's true for the league actually being built, not hardcode Westwood's shape.
- (b) Separately, whether `ffc_half_ppr_10team` (already ingested, per
  `src/ingest_ffc_adp.py` — built *specifically* to replace `mfl_proxy` for Westwood, since MFL's
  IS_PPR flag can't express half-PPR) should actually be wired into `_load_adp_snapshot` for
  Westwood's own board, instead of sitting ingested-but-unused. That's a bigger call (methodology,
  which non-Westwood leagues get which source if any) than (a) and might want strategist input.

**2. `season_stats.json` / `weekly_finishes.json` are not league-scoring-aware and not exported
per league at all.**

`src/export_history.py::build_season_stats`/`build_weekly_finishes` sum/rank
`player_weekly_stats.fantasy_points_ppr` — a fixed, standard-PPR figure computed once, with no
`scoring_cfg` parameter (unlike `make_board.build_board`, which does take one). Confirmed these
files are also not exported under `data/export/<league_id>/` at all — only at the unprefixed top
level (`ui/data/playerHistory.ts`'s own docstring already says this: "unprefixed, not per-league").
So switching leagues in the app cannot change these numbers even in principle today, regardless of
any frontend fix.

Frontend added an honest, static disclosure next to both (weekly-finishes heatmap and the
three-season table) rather than attempting a browser-side re-scoring, which this project's rules
forbid (approximating scoring outside the pipeline). See `frontend/ui/components/PlayerDetail.tsx`
around `WeeklyFinishesHeatmap`/`ThreeSeasonTable` for the exact wording, and
`frontend/e2e/artifacts/fr079-player-card-westwood-history.png` for what it looks like.

## Why it matters

This is the founder's own direct complaint, asked plainly twice in the same feedback batch. The
frontend fix (making the mismatch visible rather than silent) satisfies the project's
absent-not-inert rule but does not give him what he actually asked for, which is the number being
right. Two separate real defects, one of which (#1a, the wrong-league prose) is probably a quick,
low-risk fix; the other two (whether to wire FFC ADP in for Westwood, and whether to build a
per-league-scoring pass over historical stats) are real scoping questions.

## Done looks like

- #1a: `adp_source_note` reads the real `cfg` passed to `build_board_json` and states the correct
  ruleset for whichever league it's building, verified against at least one non-Westwood league
  export (e.g. `espn_10_standard`) and Westwood's own (unchanged claim, still correct there).
- #1b / #2: a decision recorded (ADR or a reply here) on whether/when to address them, even if the
  decision is "not now" — this thread doesn't need to stay open waiting for a build, just for an
  owner's call.
