# 2026-07-29 — backend — per-league export completeness

## Task
Founder-reported bug: switching to "Ethan's Expert League" on the live site failed with *"Could
not read leagues/ethans_expert_league/nulls.json (HTTP 200, non-JSON response)."* Plus a known,
smaller bug: `strategies.json` stamped at a stale contract version (thread 042).

## Root cause
`league_builder.export_league()` (the path that created `ethans_expert_league`) and
`generate_config_matrix.py` (the 24-config board/VBD matrix) both wrote only
board/availability/league/rosters via `export_contract.write_all`. Neither ever called
`export_static.py`'s glossary/nulls/opponents builders. ADR-041 requires all six
(board/availability/league/glossary/nulls/opponents) in every non-primary league's export
directory, and `frontend/ui/data/load.ts` fetches and `league_id`-checks all six unconditionally
— only `rosters.json`/`strategies.json` have real fallback-to-null/absent handling. Confirmed by
reading `load.ts` directly rather than trusting the prior framing that "some may be legitimately
absent" without checking which.

## Fix
- `src/export_static.py`: factored the inline `main()` payload dict into
  `build_static_artifacts(cfg)` / `write_static_artifacts(out_dir, cfg)`.
- `src/league_builder.py`: `export_league()` now also calls `write_static_artifacts`.
- `src/generate_config_matrix.py`: `generate_all()` now also calls `write_static_artifacts` per
  config (the docstring's "board-only at this stage" language only ever meant to scope out
  strategies.json/Monte Carlo — the three prose artifacts were an oversight, not a decision, so
  fixed rather than left as documented scope).
- Rebuilt `ethans_expert_league` (`scripts/rebuild_ethans_expert_league.py`) and all 24
  config-matrix exports (`src/generate_config_matrix.py`).
- Re-ran `src/export_strategies.py` (bug 2): `strategies.json` was at contract 1.7.0, now 1.14.0.

## Evidence — real artifact counts, measured after rebuild
| Directory | Artifacts | Notes |
|---|---|---|
| `data/export/` (primary) | 11 | unchanged |
| `data/export/ethans_expert_league/` | 7 | was 4; now board/availability/league/rosters/glossary/nulls/opponents |
| `data/export/{espn,yahoo}_{8,10,12,14}_{standard,half,full}/` (24 dirs) | 7 each | was 3 each (board/availability/league only) |
| `data/export/yahoo_standard_mock/` | 6 | untouched, pre-existing, confirms rosters/strategies really are optional (no load failure without them) |

Frontend load path (`frontend/ui/data/load.ts`'s `leagueIdsOf`/required fetch set) is satisfied
for every league directory found on disk: all six required artifacts present everywhere. Not
independently re-screenshotted this session (no frontend dev server run) — the assertion is
file-presence + `league_id` field correctness, which is what the loader actually checks before
rendering; the founder's exact failure mode (missing file, non-JSON SPA-fallback body) is
structurally impossible now that the file exists.

## Regression guard
New `tests/test_export_directory_contract.py`:
- Parametrized over every `data/export/<league_id>/` directory on disk; asserts all six required
  artifacts present. Includes a vacuous-pass guard (fails if zero league directories exist, so
  deleting every league dir can't silently pass).
- Primary league carries the full 8 (six + rosters + strategies).
- `strategies.json`'s `contract_version` matches `export_contract.CONTRACT_VERSION`.

Extended `tests/test_league_builder.py::test_create_and_export_league_board_uses_its_own_replacement_levels`
to assert the same six-plus-rosters set directly at the `league_builder.export_league()` call
site (catches this bug even without any files on disk, e.g. in a fresh clone before any export
has run).

## Not done / scope notes
- No `CONTRACT_VERSION` bump — no artifact shape changed, only which artifacts get generated for
  non-primary leagues. No frontend handoff needed for a schema reason.
- `sync-exports.mjs` treats every subdirectory of `data/export/` as a switchable league with no
  allowlist — this is why the 24 config-matrix combos had the same bug as Ethan's league and
  needed the same fix. Not otherwise touched; that's a frontend-owned file per this dispatch's
  boundary.
- The SPA-fallback-turns-404-into-200 behavior (why the error read "non-JSON response" instead of
  "not found") is a `wrangler.jsonc` fix explicitly owned by someone else this round, per the
  dispatch. Confirmed it doesn't change this diagnosis: the file really was missing either way.
- Did not work the other 22 pre-existing backend inbox threads (001, 002, 012, 021, 026, 032, 033,
  036, 037, 040, 045, 047, 050, 059, 060, 064, 067, 071, 072, 076, 077, 079) — out of this
  dispatch's scope, left for a future session.
- `tests/test_handoffs.py::test_mailbox_health` fails on this tree — pre-existing, unrelated to
  this change: `docs/decisions.md` ADR-056 already documents two real ADR-number collisions
  (ADR-054, ADR-055) across branches, deliberately left unresolved (a merge-time human decision,
  not something an allocator should silently resolve). Confirmed pre-existing by content, not
  introduced by this session's ADR-058.

## Environment notes for the next agent in this worktree
- `data/nfl.db` was absent in this worktree; `scripts/rebuild_database.py` failed at
  `ingest_rankings.py` (`403 Forbidden` fetching `dynastyprocess/data` raw parquet through the
  proxy — an external GitHub-side block, not a proxy policy denial). Worked around by copying the
  already-built `data/nfl.db` (854,700,032 bytes) from the main checkout
  (`/home/user/Fantasy-Football/data/nfl.db`) into this worktree — same fix `docs/environment.md`
  §4 already describes for the worktree-DB gotcha, just sourced from the main checkout instead of
  a sibling worktree.
- `uv venv --python 3.12 .venv` + `uv pip install -r requirements.txt --python .venv/bin/python`
  (needed `.venv/bin/python -m ensurepip` first — the bare `uv venv` python had no pip).

## Evidence
`.venv/bin/python -m pytest -q`: 719 passed, 1 pre-existing failure (`test_mailbox_health`, see
above). Commit `a88f041e98f8f2948adaaa3271c94d31a072d45d` on branch
`worktree-agent-aff79d3df50a140ce`, pushed. `docs/decisions.md` ADR-058. Thread 042 replied and
marked RESOLVED.
