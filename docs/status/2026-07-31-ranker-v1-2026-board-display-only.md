# 2026-07-31 — ranker — v1's 2026 board, display only, holdout preserved

**Commits:** `50c36ba` (gate split), `c13a1b4` (board), `bb606b6` (review threads).
Branch `claude/pm-agent-setup-gobxa0`, main checkout, no worktree.

## What was asked

Produce ranking v1's 2026 board for display. The founder asked directly whether it burns the
holdout and framed it as "an independent math run."

## The constraint, and why it needed new code

`pos_eval.WalkForward.run()` trains on every pair whose outcome season is strictly before the
target. Pointed at 2026 it trains on **2025 outcomes** — the sealed holdout — and permanently burns
it. It also tries to read a season that has not been played.

Worse, the panel could not have produced a 2026 board at all: `SeasonPanel` carried a **single**
season bound (`HOLDOUT_SEASON = 2025`) used for both "may this be an input" and "may this be an
outcome", so `panel.before(2025)` — the feature read a 2026 projection requires — raised
`HoldoutViolation`. One bound, two questions.

**Fix:** split it into `feature_gate` and `outcome_gate` (`pos_data.py`). The production board runs
`feature_gate=2026, outcome_gate=2025`. Every other caller passes nothing and gets the old behaviour
byte-for-byte; `build_panel` refuses any `outcome_gate` above `HOLDOUT_SEASON`.

Added `WalkForward.project_target(target, train_outcome_max)` — the production path. `run()` is
untouched. `train_outcome_max` is required and asserted; there is no `outcome_components` call at
the target, so **there is no accuracy number by construction, not by discipline**.

## Result

`data/export/ranking_v1_2026.json`, 527 players; `v1` / `v1_pos_rank` / `v1_source` /
`v1_projected_points` on every row of `data/export/rankings_comparison_2026.json`, `v1_status`
flipped. Raw frame `experiments/bottomup/results/ranking_v1_2026_board.csv`.

Audit, per position: `observed_max_outcome_season = 2024`, `max_feature_cutoff = 2025`,
`n_outcome_reads_at_target = 0`, 13 training outcome seasons (2012–2024). 86 rookies pinned to
consensus, 441 model-ranked, 0 veterans without projectable history. DEF absent with a note.

The permitted 2025 features read is logged as `FEATURES_ONLY_READ` in
`docs/preregistration/holdout_access_log.jsonl`, stating explicitly that the fit was frozen at 2024
and that this is not a holdout spend.

## Decisions taken (also in `docs/ideas-inbox.md`)

- Overall order inherits **consensus's** cross-positional structure; v1's occupant of each positional
  slot takes that slot's consensus overall rank. v1's VBD channel is declared
  `measured_by_this_design: false` and applying it would be claiming it. Ruling requested from
  `strategist`.
- Consensus panel is `fantasypros_csv_2026draft` @ 2026-07-30 — exactly the 527 rows already in
  `rankings_comparison_2026.json`. FFC's 2026 half-PPR board covers only 166 of them; 2026
  `fantasypros_ecr` is `is_preseason_final = 0`.
- Pinned rookie rows carry **no** projected points. The model emits a number for them; it is not the
  number that placed them.

## Found, deliberately not fixed

Adjusting a model after seeing its output is tuning through a human.

- `pos_data._WEEK_SQL` admits only `position IN ('QB','RB','WR','TE','FB')`. **Travis Hunter played
  7 REG games with 45 targets in 2025 and is listed `CB`**, so the panel has never seen him; v1
  classes him a rookie and pins him at consensus WR64. Pre-existing; identical in every historical
  backtest. Exactly one such case in 527 rows.
- The panel counts REG rows only, so a playoff-only debut reads as never having played (Frank Gore
  Jr., Jordan James, Jarquez Hunter, Will Howard — all pinned).

## Pre-existing test failures, not caused here (only `experiments/` and `data/export/` were touched)

- `tests/test_holdout_audit.py::test_no_new_direct_sqlite_connections_in_src` — nine `src/ingest_*.py`
  files outside the allowlist.
- `tests/test_export_directory_contract.py::test_strategies_json_contract_version_matches_export_contract`
  — `strategies.json` stamped 1.15.0, `CONTRACT_VERSION` is 1.18.0.

## The sentence that travels with the artifact

The holdout remains unspent and this run measured v1's accuracy at nothing. v1's only measured
record is 2018–2024, where it **beat neither crowd at any position**.
