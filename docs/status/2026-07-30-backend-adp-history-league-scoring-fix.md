# 2026-07-30 — backend — ADP note + season history made league-scoring-aware (FR-079/FR-083)

**Dispatch:** fix the root cause behind the founder's player-card complaint
("Why do player notes cards not show adp for the correct format for the league selected?" /
"Last few seasons should be in correct fomat as well"), traced by frontend to
`docs/handoffs/NEW-adp-and-history-not-league-scoring-aware.md`. Explicitly told not to allocate
a thread or ADR number this session.

## What shipped

Two real defects, both making the app assert something false about a league's scoring.

**1. `board.json:adp_source_note` was hardcoded Westwood prose for every league.**
New `export_contract._adp_source_note(cfg, adp_snapshot)` (plus `_ppr_format_description`)
derives the claim fresh from `cfg.scoring` on every call: which PPR value this league scores,
whether it matches MFL's binary `IS_PPR` flag (states a real match when one exists, not just a
mismatch warning), and whether the capture's `fcount` actually equals `cfg.teams` (previously
hardcoded `"(10-team, matching this league)"` unconditionally — wrong for any non-10-team
preset). Verified live against `espn_10_standard` (the exact league frontend's diagnosis used):
note now reads "...while THIS league ('espn_10_standard') scores standard (0-PPR, no points per
reception)..." — no "half-PPR" anywhere. Westwood's own board is unchanged in substance (still
correctly says half-PPR, now derived rather than hand-written).

**2. `season_stats.json`/`weekly_finishes.json` were never league-scoring-aware at all.**
Root cause was worse than "missing a `scoring_cfg` param": both files summed/ranked
`player_weekly_stats.fantasy_points_ppr`, a column nflreadpy ships as-is under its own fixed
full-PPR convention — never this project's scoring engine, never tunable. This was wrong for
**every** league including Westwood, not just presets. Fix: `export_history.py` now recomputes
every player-week's fantasy points from raw counting stats
(`db.player_week_scoring_inputs`/`db.SCORING_STAT_COLUMNS`, the same view make_board/backtesting
already read) through `scoring.score_offensive_game(stats, cfg.scoring)`, summed to a season total
**after** per-game scoring (yardage bonuses are game-level thresholds — summing raw yards first
and then scoring would fabricate or drop a bonus no single game actually earned). Ranking in
`weekly_finishes.json` moved from a SQL `RANK() OVER (...)` on the stored column to a Python
`_rank_desc` helper over the newly-scored points (same tie semantics), since the ranking basis is
now cfg-dependent and SQL can't see `cfg.scoring`.

**Shape decision, stated and justified per the dispatch:** per-league export artifacts, not
read-time application. `export_contract.write_all` now calls `export_history.write_all`
internally, landing `weekly_finishes.json`/`season_stats.json` under
`export_dir_for(cfg.league_id)` — the exact pattern `board.json`/`league.json` already
established — rather than inventing a new one. Rejected exporting raw per-week components for the
reader to score: the whole reason this thread exists is that scoring must never happen outside
this project's engine, and a raw-components artifact would hand the browser exactly that
temptation. Landing every artifact pre-scored keeps "frontend never computes scoring" true
structurally, the same guarantee `make_board.build_board` already gives by taking `scoring_cfg`
directly.

**Verified on two leagues, live (not just unit tests):** same real player, same 2022 season —
283.2 fantasy points under Westwood's ruleset vs 271.7 under a standard 0-PPR preset. Different
leagues, same underlying games, genuinely different numbers.

**Shared derivation, no more drift risk.** `league_config.scoring_ruleset_note_for(cfg)` is now
the single source of truth for "which ruleset does this league use," called by both
`export_contract.build_league_json` (`league.json:scoring_ruleset_note`, unchanged content) and
the new `export_history.py` envelope fields — the three artifacts describing a league's scoring
can no longer independently drift the way `board.json`'s `adp_source_note` and
`league.json`'s note already had.

## Contract bump

`CONTRACT_VERSION` **1.15.0 → 1.16.0** (`src/export_contract.py`). `docs/data-contract.md`
updated in place (version banner, regenerating commands, the `weekly_finishes.json`/
`season_stats.json` section rewritten, changelog entry added). Breaking for frontend:
`season_stats.json`'s `fantasy_points_ppr` field is **renamed** `fantasy_points` (not aliased —
old key gone) plus a new `fantasy_points_available` bool; both history files' envelopes gain
`league_id`/`scoring_note`/`scoring_ruleset_note`; both now exist per-league under
`data/export/<league_id>/`, not just the unprefixed top level. Handoff to frontend: appended a
reply to the same thread frontend opened (`docs/handoffs/NEW-adp-and-history-not-league-scoring-
aware.md`), `STATUS: RESOLVED` — same subject as the ask, not a new thread.

## Left undone, logged not decided away

Sub-ask 1b from frontend's diagnosis — whether `ffc_half_ppr_10team` (already ingested) should
replace `mfl_proxy` as Westwood's own ADP display source — is untouched. Real methodology call
(which leagues get which ADP source, if any) that needs strategist input, and per this project's
"a source swap is not a substitution" rule, `ffc_half_ppr_10team`'s actual coverage would need
verifying before treating it as a drop-in. Logged in the handoff reply for a future thread.

## Verification

- New sanity tests written before/alongside the implementation (per operating rules): 9 new cases
  in `tests/test_export_contract.py` (`_ppr_format_description`, `_adp_source_note` derivation —
  standard-0PPR-never-claims-half-PPR, Westwood-still-claims-half-PPR-honestly, two-leagues-get-
  two-different-notes, a real-match case, fcount-mismatch and fcount-match cases, league_id
  appears in its own note). `tests/test_export_history.py` fixture rewritten with full raw
  scoring-stat columns (matching `db.player_week_scoring_inputs`'s source shape); 6 new cases
  proving the identical raw stat lines score AND rank differently under two real league configs,
  and that the envelope names the league it was built for.
- `tests/test_rosters_export.py::test_contract_version_bumped` updated to assert `1.16.0`.
- Regenerated the primary league's committed `data/export/*.json` (all 6 artifacts,
  `export_contract.py` + `export_static.py`) against a real `data/nfl.db` copied into this
  worktree (gitignored, does not survive across worktrees per `docs/environment.md` §4).
- Ran `generate_config_matrix.py` to regenerate all 24 presets' `board.json`/`league.json`/
  `availability.json`/`rosters.json`/`weekly_finishes.json`/`season_stats.json` so the committed
  `data/export/<preset>/` directories don't ship the pre-fix bug. (See test count/commit below for
  whether this completed within the session or is a documented follow-up.)

Test count and commit hash: see final report.
