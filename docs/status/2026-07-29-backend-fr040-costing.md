# Backend — FR-040 spec/costing pass, 2026-07-29

Dispatched as a spec/costing pass on FR-040 (custom league option). Explicit constraints: no
`src/export_contract.py` changes beyond reading, no contract version bump — a second backend agent
was working in a separate worktree the same session. Two founder rulings landed mid-session and were
folded in: FR-042 (presets must use standard scoring, only Westwood keeps the custom ruleset) and
FR-043 (audit for unused capability, fed by this session's `league_builder.py` findings).

**Everything under "verified by running" was actually run** — `data/nfl.db` was copied from the main
checkout into the worktree per `docs/environment.md` §4 (worktrees do not inherit it), and
`league_builder.create_and_export_league()` was called twice with real, non-Westwood scoring
overrides: once with a malformed bonus shape (crashed, real defect found — see below), once
corrected (succeeded, 7 real artifacts, genuinely re-scored `board.json`).

**Findings, full detail in `docs/specs/FR-040-custom-league-settings-costing.md`:**

1. **The backend for arbitrary custom leagues mostly exists, with two real bugs.**
   `league_builder.build_scoring()` starts from `scoring.LEAGUE` (Westwood's ruleset) and only
   overrides fields explicitly passed — the identical defect FR-042 just corrected in
   `generate_config_matrix.py`, present a second time, never previously exercised (no caller besides
   `scripts/rebuild_ethans_expert_league.py`). It also validates override *keys* but not nested
   *shape* — a bonus passed as `{"threshold": 250, "bonus": 3}` (the natural form a settings form
   would submit) crashes deep inside `scoring.py` with an opaque `TypeError`.
2. **Component projections do not exist.** Traced `make_board.py`: `board.json`'s
   `projected_points` is `curve.predict(consensus_rank)` — a single per-position rank curve
   (`points ≈ intercept + slope·ln(rank)`), never a per-player, per-stat forward projection. The
   "ship components so the browser can re-score any format" idea from FR-040's initial read is dead,
   confirmed by source trace, not assumed.
3. **Client-side team-count/roster-shape recompute is real but incomplete.** `board.json` already
   ships `replacement_levels_used` and every player's `positional_rank`, so VBD for the
   *currently-exported* config needs no recompute at all. A *changed* team count/roster shape needs
   `flex_split` (the RB/WR/TE flex allocation, `scoring.py`, ADR-029) to compute a new replacement
   count, and that value is never exported anywhere in the contract.
4. **`docs/design-handoff/settings/SETTINGS-EDITOR-SPEC.md` §7 specifies a job-queue backend API
   that cannot exist against the current static Cloudflare Worker deploy.** Real, previously
   unflagged contradiction between two live documents — flagged to `frontend`/`pm`, not resolved
   here.
5. **Resolved a docstring self-contradiction** in `generate_config_matrix.py` (also present in
   `docs/decisions.md`'s ADR-047 entry itself): the "ESPN's confirmed platform defaults exactly"
   claim is unsupported — the same file and the same ADR entry separately say ESPN scoring was
   "unverified, bot-detection blocked the fetch." No citation anywhere supports "confirmed."

**Not fixed, deliberately** (spec/costing scope only, per the dispatch): the two `league_builder.py`
bugs, the `flex_split` export gap, the docstring/ADR-047 contradiction text itself. All logged —
`docs/ideas-inbox.md` (bugs), this doc + the spec doc + thread 084 (everything else).

**Infrastructure note, not a project finding:** the original worktree
(`.claude/worktrees/agent-a1e9b46c312d8548a`) lost its git-worktree registration mid-session (an
apparent side effect of the API outage this session hit) — `.git` link file and the corresponding
`.git/worktrees/agent-a1e9b46c312d8548a/` admin directory were both gone, and the branch had been
deleted. The already-written spec file survived on disk (git-worktree removal doesn't delete
directory contents by itself unless forced with a discard) and was copied into a fresh worktree
(`backend/fr-040-costing-spec`, branched from `main` at `4980b29`) rather than reconstructed from
memory. No content was lost; the recovery is why this session has two worktree paths in its history.

**Thread 084** opened to `frontend`,`pm` — full ask in the thread body, not duplicated here.

## Commit / test count
See parent report — this pass did not run the Python test suite (spec/costing pass, no `src/` code
changed; the one code path exercised was via a scratch script, not a test file). `git rev-parse
HEAD` in the worktree at time of commit is the source of truth for what shipped.
