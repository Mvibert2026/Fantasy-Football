# 2026-07-29 — backend — live_availability.py takes LeagueConfig (ADR-055)

**Task:** correctness-floor item 1 -- `src/live_availability.py`'s structural assumptions (`TARGET`,
`EPS`, `SHARE_BAR`, `POSITIONS`) were hardcoded to the primary league (Westwood) rather than
derived from `LeagueConfig`, and no test checked that two different roster shapes produce different
survival numbers. Urgent because mock-draft collection (public Yahoo rooms, different roster shape)
starts imminently and FR-027 wants generic multi-league support.

**What I did.**

1. Read `docs/CURRENT-STATE.md`, `docs/environment.md`, `docs/founder-requests.md`, backend inbox
   (23 open threads, none of them this task -- left untouched, out of this session's scope).
2. Verified the defect directly: `src/live_availability.py` module constants confirmed hardcoded;
   `src/league_config.py` and `data/leagues/ethans_expert_league.json` confirmed real and already
   differently-shaped (K starter, 1 FLEX, no measured `flex_split`, INT -1). Found a useful existing
   precedent already in the codebase: `draft_sim.py`'s `DraftEngine` (ADR-041) already does exactly
   this split for Prep-mode (primary league untouched byte-for-byte, everyone else gets a
   `mechanical_need_targets_for(cfg)` / `default_max_at_position_for(cfg)` derivation, explicitly
   flagged as an unmeasured heuristic in its own docstring). Mirrored that pattern rather than
   inventing a new one.
3. Added `positions_for`, `target_for`, `eps_for`, `share_bar_for` to `live_availability.py`.
   Primary league: byte-identical to the old module constants (checked with `==`, not `approx`,
   in a dedicated test). Any other league: derived via starters (exact) + flex (measured split if
   present, else even placeholder) + bench (allocated proportionally to starters+flex share, the
   only allocation that both sums to `cfg.rounds` and doesn't invent a per-position number),
   explicitly flagged in the docstring as derived-not-measured.
4. Threaded an optional `cfg` parameter through `need_share`, `n_need`, `run_z_scores`,
   `run_multiplier`, `_hazards_at_pick`, `live_survival`, `live_survival_excluding_drafted`.
   `cfg=None` (default, and every pre-existing call site) is the unchanged primary-league path.
5. New test file `tests/test_league_config_availability.py` (6 tests): primary-cfg-equals-module-
   constants, primary-path-no-longer-bypasses-config (calling WITH `cfg=CURRENT_LEAGUE` matches the
   no-cfg call exactly), two-roster-shapes-produce-different-target, derived-target-sums-to-
   cfg.rounds, **two-roster-shapes-produce-different-survival-numbers** (the test the task named as
   the actual point -- runs `live_survival` against Westwood's and Ethan's real configs with an
   identical synthetic scenario and asserts the outputs differ), and the flex-split placeholder
   test.
6. Ran the full backend suite in a fresh `uv`-managed venv (`.venv2`, Python 3.12; the pre-existing
   `.venv` was missing `pandas`/`pytest`, unrelated to this task) plus the two pre-existing
   live-availability/availability suites individually.

**Result: no Westwood number moved.** `test_primary_cfg_reproduces_module_constants_exactly` and
`test_primary_league_path_no_longer_bypasses_config` both assert exact equality (not
`pytest.approx` for the dict-of-floats primary-league checks, since they should be literally
identical objects' worth of arithmetic), and pass. `tests/test_live_availability.py` and
`tests/test_availability.py` pass unchanged, 22/22.

**Full suite:** `../.venv2/bin/python -m pytest tests/ -q` -- 673 passed, 8 skipped, 1 failed
(`test_handoffs.py::test_mailbox_health`, thread 078's resolution missing its artifact -- pre-
existing, unrelated to this change, not in this session's file boundary to fix).

**Not done / explicitly flagged, not built speculatively:** no live-draft-time consumer of
`live_availability.py` exists yet (only `draft_sim.DraftEngine`'s Prep-mode path, already
config-aware since ADR-041) -- so nothing currently calls `live_survival(..., cfg=<non-primary>)`
in production. That wiring is future work once a live-draft consumer exists; noted in
`docs/ideas-inbox.md`.

**Export contract:** unchanged. No frontend handoff thread opened -- nothing here touches
`board.json` or any exported field.

**Commit:** see `git log` on `claude/pm-agent-setup-gobxa0` for the hash this file was committed
alongside (this session did not push).

**Files touched:** `src/live_availability.py`, `tests/test_league_config_availability.py`,
`docs/decisions.md` (ADR-055), `docs/ideas-inbox.md`, this file.
