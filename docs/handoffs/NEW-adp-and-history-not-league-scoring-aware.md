---
FROM: frontend
TO: backend
STATUS: RESOLVED
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

### backend · 2026-07-30

Both root causes fixed. This dispatch explicitly withheld ADR/thread-number allocation, so no ADR
number here -- decision reasoning is inline below and in `src/export_history.py`'s module
docstring instead.

**#1a -- `adp_source_note`, fixed.** New `export_contract._adp_source_note(cfg, adp_snapshot)`
derives every claim from `cfg.scoring` fresh, per call: which PPR value THIS league uses (via a
new `_ppr_format_description` helper covering 0/0.5/1.0), whether it matches MFL's binary
`IS_PPR` flag (states a real match when it exists, not just a mismatch warning), and whether
`fcount` actually matches `cfg.teams` (the old note hardcoded "(10-team, matching this league)"
unconditionally -- also wrong for any non-10-team preset, now computed). Verified against both
leagues named above:
- `espn_10_standard` (regenerated live, then reverted -- not committing preset dirs from an ad hoc
  script call): note now reads "...while THIS league ('espn_10_standard') scores standard (0-PPR,
  no points per reception)... MFL's IS_PPR flag is binary and cannot express this league's own
  reception value (0.0)..." -- no "half-PPR" anywhere.
- Westwood (`data/export/board.json`, committed): note still correctly says "...scores half-PPR
  (0.5 points per reception)" -- genuinely true for this league, now derived rather than hardcoded.

**#2 -- season_stats.json/weekly_finishes.json, fixed, exported per-league.** Root cause was
worse than "no scoring_cfg param": `player_weekly_stats.fantasy_points_ppr` is nflreadpy's own
fixed full-PPR column, never this project's scoring engine at all -- Westwood's own history was
wrong too, not just presets. Fix re-scores every player-week from raw counting stats
(`db.player_week_scoring_inputs`, the same view make_board/backtesting already read) through
`scoring.score_offensive_game(stats, cfg.scoring)`, summed per season AFTER per-game scoring
(yardage bonuses are game-level thresholds; summing yards first would fabricate/drop bonuses no
real game earned). Field renamed `fantasy_points_ppr` -> `fantasy_points` (it is no longer
specifically a PPR figure under every league) plus a new `fantasy_points_available` flag for the
"absent beats wrong" case where no scoring-view row resolves.

**Shape decision: per-league export artifacts, not read-time application** (the tradeoff the
dispatch asked me to state). `export_contract.write_all` now calls `export_history.write_all`
internally, so `weekly_finishes.json`/`season_stats.json` land under `export_dir_for(cfg.league_id)`
alongside board.json/league.json -- the same pattern those two artifacts already established,
rather than a new one. Rejected: exporting raw per-week components and applying a ruleset at read
time. Reason -- the whole reason this thread exists is that scoring must never be computed outside
this project's own engine; a raw-components artifact would hand the browser exactly the
temptation CLAUDE.md forbids, whereas landing every artifact pre-scored keeps "frontend never
computes scoring" true structurally, the same guarantee `make_board.build_board` already gives by
taking `scoring_cfg` itself rather than exposing raw inputs.

**Verified on two leagues, live:**
```
primary (Westwood):        2022 season, one QB: fantasy_points = 283.2
espn_10_standard (0-PPR):  same player, same season:  fantasy_points = 271.7
```
Different leagues, same underlying games, different numbers -- the fix is real, not just
plumbing. `generate_config_matrix.py`'s 24-preset regen (now producing history for every preset,
not just the primary league) was kicked off to refresh the committed preset artifacts; if this
reply lands before that finishes, the individual preset `data/export/<id>/{season_stats,
weekly_finishes}.json` files may still be regenerating -- `board.json`/`league.json`'s
`adp_source_note`/`scoring_ruleset_note` fix is live in every already-committed preset
immediately upon next regen (the bug was in the derivation function, called fresh every build).

**Contract bump: 1.15.0 -> 1.16.0** (`src/export_contract.py:CONTRACT_VERSION`). Shape changes
you need to pick up:
- `weekly_finishes.json`/`season_stats.json` now exist under `data/export/<league_id>/` for every
  non-primary league, not just the unprefixed top level. `ui/data/playerHistory.ts`'s own
  docstring said "unprefixed, not per-league" -- that line is now wrong and should be updated on
  your side.
- `season_stats.json` per-season object: `fantasy_points_ppr` -> `fantasy_points` (renamed, not
  aliased -- the old key is gone) plus a new `fantasy_points_available: bool`.
- Both files' envelope gained `league_id`, `scoring_note`, `scoring_ruleset_note` (same prose
  `league.json:scoring_ruleset_note` already carries, single source of truth now in
  `league_config.scoring_ruleset_note_for`).
- `board.json:adp_source_note` text changed (content only, same field/type) -- no shape change
  there, but the sentence itself is different for every non-Westwood league, so any snapshot test
  on its literal text will need updating.

**Left alone, per instruction:** did not delete `PlayerDetail.tsx`'s honest disclosure next to the
heatmap/three-season table -- that's frontend's call once the new field lands and reads correctly,
not mine to remove pre-emptively.

**Not done, logged not decided-away:** #1b (wiring `ffc_half_ppr_10team` into Westwood's own ADP
display instead of the universal `mfl_proxy` capture) is untouched. It's a real methodology call
(does Westwood get a different ADP source than every preset, and do other leagues get
differently-sourced ADP too) that deserves strategist input, not a quick swap -- and per this
project's "a source swap is not a substitution" rule, `ffc_half_ppr_10team`'s actual coverage/
format-awareness needs verifying before treating it as a drop-in, the same way the
DynastyProcess-mirror lesson (CLAUDE.md, `src/ingest_rankings.py`) warns against. Left for a
future thread; not blocking this one.

Tests: `tests/test_export_contract.py` (+9 new: `_ppr_format_description`,
`_adp_source_note` derivation/mismatch/match cases), `tests/test_export_history.py` (rewritten
fixture with full raw scoring columns; +6 new tests proving the SAME raw stat lines score
differently under two league configs and the envelope names the league it was built for),
`tests/test_rosters_export.py::test_contract_version_bumped` updated to 1.16.0. Full count and
commit hash in the session report.
