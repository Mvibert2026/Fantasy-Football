# 2026-07-30 — backend — thread 104/119: availability.json 1.17.0, provenance-safe rank export plus preparatory ADP block

## What was asked

Thread 104 (FR-066's resolution): export the per-player rank `src/availability.py:simulate_
availability` actually runs its opponent model AND the user's own `strategy_bpa` pick against —
`board.json:consensus_rank` is a different ranking from a different source (73/80 top players
differ in order), and frontend correctly refused to build a browser-side recompute on it. The
dispatch specifically asked for the export to be self-describing (source name + `as_of_date`
derived from the model's own execution path, not hardcoded) so a future repoint of the model's
central tendency wouldn't silently make the export wrong.

## Mid-session redirect

While this was in flight, thread 119 resolved: strategist recommended the opponent model's
central tendency move from `fantasypros_ecr` to FFC ADP (`ffc_half_ppr_10team`) with per-player
dispersion — not adopted yet, gated on an M0-M5 pre-registration
(`docs/ranking/availability-opponent-model-precommit.md`) — and reformulated thread 104's ask from
the raw rank array to `{adp_pick, sigma_pick, coverage_flag}` per player, since with ADP the
unconditional marginal becomes closed-form and a browser recompute wouldn't need a Monte Carlo
port at all. The coordinator relayed this mid-task with explicit instructions: keep the
self-describing-source requirement (it's exactly what let the original build survive the
redirect), reformulate the shape, withhold `sigma_pick` since M0 hasn't cleared, handle or flag
the FFC/Westwood pick-axis mismatch, and do not implement the model switch itself.

## What shipped

**`src/draft_sim.py`.** New module constant `CONSENSUS_RANK_SOURCE = "fantasypros_ecr"` — the
single edit point for a future repoint. `SeasonData` gains `consensus_rank_source`/
`consensus_rank_as_of_date`, both fields, populated by `load_season` from the exact rows
`consensus_rank` was read from (added `as_of_date` to the SELECT, took `MAX()` over the rows
actually returned — same "newest row wins" convention as `freshness.snapshot_age_days`).

**`src/export_contract.py`.** `build_availability_json` now takes `conn` (was CSV-only before).
`client_simulation_parameters.ranking_sources[0]` gains `as_of_date`, both fields read from
`season_data` rather than hardcoded. New `player_ranks: {player_name: rank}`, keyed to `by_player`'s
existing keys — the array the shipped model runs on today. New `adp_central_tendency` block
(additive): `status: "preparatory_switch_not_yet_shipped"`, `{adp_pick, coverage_flag}` per player
sourced from `ffc_adp_snapshots` (skill positions only, joined via `player_ids.mfl_id` to the same
gsis-keyed universe `load_season` returns), `axis_note`/`sigma_pending_note`/`coverage_note`
stating the two known gaps loudly rather than silently. New helper `_load_ffc_skill_adp`. Also
corrected `algorithm_note`, which claimed the user's own BPA pick runs off `board.json` — it
doesn't and never did (`ds.strategy_bpa` reads `data.consensus_rank`, same array the opponents
use).

**`CONTRACT_VERSION` 1.16.0 → 1.17.0.** `docs/data-contract.md` updated (field table + changelog).
`docs/decisions.md` gains ADR-065. Handoff thread to frontend:
`docs/handoffs/2026-07-30-availability-json-1-17-0-adp-central-tendency-pr.md`. Thread 104 replied
and marked `RESOLVED`.

## What was deliberately NOT done

- The model has not switched to ADP. `simulate_availability` still runs entirely on
  `fantasypros_ecr`.
- No `sigma_pick`. FFC's `times_drafted`/`total_drafts_in_sample` columns don't reconcile on the
  committed snapshot (M0 in the precommit doc) — a placeholder would be a guess dressed as a
  measurement.
- No M4 axis correction on `adp_pick`. FFC counts kickers/defenses and samples deeper drafts than
  this league's 16 rounds; the isotonic-regression fix is assigned to strategist in the precommit
  doc, not invented here.

## Evidence

Coverage measured against the live DB: 157/378 season-universe players resolve an FFC row; 79/80
players actually present in `by_player` are covered (one honest gap: Marvin Harrison Jr., no FFC
row). New tests: `tests/test_export_contract.py::
test_ranking_source_identity_matches_the_query_it_was_read_from`,
`tests/test_export_contract.py::test_adp_central_tendency_covers_every_by_player_key_honestly`,
`tests/test_availability.py::test_load_season_provenance_matches_the_rows_it_actually_read`. All
regenerate the DB-backed exports directly and re-derive the same identity independently, rather
than asserting the export against itself.

All six primary-league export artifacts regenerated against `data/nfl.db`
(`python3 src/export_contract.py`, `python3 src/export_static.py`); `src/export_strategies.py`
also re-run to clear its own contract-version drift test.

Full test count, commit hash: see this thread's reply in `docs/handoffs/104-...md` and the final
report to the coordinator (background full-suite run was still in flight when this file was
written; check the reply for the final number if it differs).

## Handoffs touched

- `docs/handoffs/104-fr066-availability-ranking-source-export.md` — replied, `STATUS: RESOLVED`.
- `docs/handoffs/2026-07-30-availability-json-1-17-0-adp-central-tendency-pr.md` — opened, `TO:
  frontend`, `STATUS: OPEN` (no action required, notification only).
- `docs/handoffs/OPEN.md` — synced.
