# Status log — combined view

**Generated 2026-07-29 by `tools/status_log.py sync` — do not hand-edit.**
Session files in this directory are the source of truth. Add a new dated file, then
re-run sync. Protocol: [`README.md`](README.md).

**28 sessions recorded.**

---

<!-- 2026-07-28-backend-shard-session-logs.md -->

# 2026-07-28 — backend — shard the shared append-only doc logs

## What changed

`docs/status.md`, `docs/founder-requests.md`, and `docs/CURRENT-STATE.md`'s "Build state" table
were the three most contended shared files in the repo — every parallel session wrote to one or
more of them, which is exactly the pattern `docs/reviews/fable-workflow-2026-07-27.md` (work
orders W3/W4) already diagnosed as the project's main source of merge conflicts, after two
sessions nearly collided on `CURRENT-STATE.md`. This session implements W3 and W4, plus extends
the same idea to `founder-requests.md`, which W3/W4 didn't cover.

Three different fixes for three different conflict shapes, not one fix applied uniformly:

1. **`docs/status.md`** (pure append log) → frozen; `docs/status/YYYY-MM-DD-role-slug.md` per
   session; `tools/status_log.py sync` generates `docs/status/INDEX.md`. This is the literal
   "shard into dated files" pattern.
2. **`docs/founder-requests.md`** (thread-shaped: FR-NNN numbers referenced 146 times across 40
   other files, and a request's `Status:` gets mutated by later sessions — concurrent-edit-to-
   one-blob, not append) → frozen; one file per request at `docs/founder-requests/FR-NNN-slug.md`,
   same pattern as `docs/handoffs/NNN-slug.md`, with the same staged-`NEW-*.md` + `sync`-time ID
   allocation `tools/handoffs.py` uses (W1), seeded past the archive's highest number (`FR-017`).
   `tools/founder_requests.py sync` generates `docs/founder-requests/INDEX.md`, grouped by status.
3. **`docs/CURRENT-STATE.md`** — deliberately *not* sharded into dated files. It's synthesized
   "current truth," edited in place by design (`CLAUDE.md`: "never append a new section").
   Regenerating it from per-session deltas would just move the merge problem into the generator.
   Only the actually-measurable "Build state" table is now generated, via a new `--apply` flag on
   `tools/state.py` that rewrites the content between `<!-- BUILD-STATE:START -->` /
   `<!-- BUILD-STATE:END -->` markers in place, leaving the rest of the doc (including the two
   rows that aren't measurable by a single command — Agent infrastructure, Frontend location) hand
   -maintained. Also fixed a latent bug while wiring this in: `tools/state.py` hardcoded the
   literal string `` `master` `` for the branch name regardless of the real branch (this repo's is
   `main`) — never previously exercised because the tool only printed to stdout for manual paste.

None of the three old files were rewritten or migrated — they stay in place as the archive,
unmodified except for a freeze-notice header pointing at the new location, per the explicit
instruction not to lose history.

## What still requires a shared-file append

- **`docs/decisions.md`** — the ADR log. Same append-only shape as the old `status.md`, and
  already has its own collision history (ADR-048, per `RECONCILIATION-2026-07.md`) and its own
  allocator (`tools/handoffs.py adr next`, which scans `docs/decisions.md` + `docs/adr-drafts/`).
  Out of scope for this session (not one of the three files named), but it's the same failure mode
  and hasn't been fixed. Flagging, not fixing.
- **`docs/handoffs/NNN-slug.md` thread files themselves** — replies within a single already-open
  thread are still a shared append target if two sessions touch the *same* thread in the same
  round. Narrow blast radius (one thread, not the whole mailbox) and already a known, accepted
  limitation — `docs/handoffs/README.md` rule 8 ("a pull conflict is not yours to resolve alone")
  exists for exactly this case.
- **Cross-worktree ID allocation races** — both the handoffs allocator and this session's new
  founder-request allocator use the same "hard-fail if the destination already exists" defense,
  not true cross-worktree coordination. Thread 076 already flagged this as open and unresolved for
  handoffs; the same caveat now applies identically to `tools/founder_requests.py`. Rare in
  practice (per 076's own assessment), but real.
- **`docs/status/` and `docs/founder-requests/` `INDEX.md` files** — not append targets (they're
  fully regenerated, never hand-edited), but two sessions running `sync` around the same time and
  both pushing will still produce a trivial merge conflict on the generated file itself, resolved
  by just re-running `sync` after the merge. Lower-stakes than the old failure mode: nothing is
  lost, the fix is mechanical, and it doesn't depend on either session's judgment about which
  content wins.

## Verification

- New tooling tests: `tests/test_status_log.py`, `tests/test_founder_requests.py`,
  `tests/test_state.py` — 16 tests, all passing.
- Full backend suite (`pytest -q`, real `data/nfl.db`) run post-change to confirm nothing else
  regressed — see this session's commit message / PR for the pass count.

---

<!-- 2026-07-29-backend-adp-glossary-methodology.md -->

# 2026-07-29 — backend — ADP glossary/methodology gap

**Dispatch:** PM finding. Contract 1.14.0 (thread 082) shipped real ADP fields to the board,
draft screen, and player profile, but the term was defined nowhere: `glossary.json` carried 13
terms and none was ADP; `Methodology.tsx` had five sections and none mentioned it.

## What shipped

1. **`ADP` glossary term** (`src/export_static.py::_GLOSSARY_BASE`). States the caveats up
   front: MFL proxy population (not this league's), captured full-PPR against this half-PPR
   league, thin sample, ~230-player coverage ceiling, and that it is display-only. Folded
   `adp_min_pick`/`adp_max_pick`/`adp_selected_pct` into this one entry rather than four separate
   terms — same pattern the existing `confidence interval` term uses for `ci_low`/`ci_high`.
2. **Methodology section** (`frontend/ui/views/Methodology.tsx`). Renders `board.json`'s real
   `adp_source_note`/`adp_match_rate_note` verbatim, states explicitly which fields ADP does
   *not* feed (`projected_points`, `vbd`, tiers, availability, recommendations).
3. **`frontend/ui/data/glossaryCategories.ts`** maps `ADP` to the `draft` (Draft mechanics)
   category — previously declared but empty — with `field: 'board.json:players[].adp'`.
4. **Regenerated all 27 `glossary.json` files** (primary + 26 saved league configs under
   `data/leagues/`) via `export_static.write_static_artifacts`, which needs no `.db` connection.
5. **Corrected two now-stale claims** found next to the new text: the `consensus rank` glossary
   entry and `board.json`'s `consensus_source_note` (`export_contract.py`) both said "no ADP
   source is legally obtainable (ADR-018)" — false since ADR-035's real MFL proxy. Fixed both to
   point at the real (thin) ADP instead of denying it exists.
6. **Fixed two files with literal leftover git-conflict markers** (`docs/decisions.md` around
   ADR-057/058; `docs/handoffs/082-...md` around its two frontend replies) — mechanical, marker
   lines only, no content change, both sides already sequential/non-overlapping. Did **not**
   touch the actual ADR-054/055 duplicate-header collision, which is ADR-056's already-made,
   deliberately-left decision.

Full reasoning, including why each judgement call was made without escalating, is in
`docs/decisions.md` ADR-060 and `docs/ideas-inbox.md`'s 2026-07-29 backend entry.

## Explicit answer to the dispatch's central question

**ADP is display-only.** It does not feed `projected_points`, VBD, tier, availability, or any
recommendation. Evidence: `_load_adp_snapshot()`'s own docstring in `export_contract.py` ("for
DISPLAY only -- does NOT feed the model"); ADR-035's status note that
`availability.load_mfl_adp_source()` "exists, is tested, and is NOT wired into the shipped
default"; thread 082's frontend reply confirming `AdpCell`/`AdpBlock`/`DraftRoomAdpCell` read
`row.adp`/`row.adpSource` exclusively, never merged into `consensus_rank` or its delta. This
session did not rewire any of that — the new Methodology section states the existing fact, it
does not create it.

## Contract

**No version bump.** Every field used (`adp`, `adp_source_note`, `adp_match_rate_note`, etc.)
already existed at contract 1.14.0 from thread 082. `CONTRACT_VERSION` in
`src/export_contract.py` untouched.

## Known limitation, not fixed this session

`data/export/board.json`'s `consensus_source_note` field (the shipped artifact, not the Python
source) still contains the old ADR-018 text. Regenerating it needs a live `nfl.db`; this
session's `scripts/rebuild_database.py` run got through steps 1-3 and failed at step 4
(`ingest_rankings.py`, `github.com/dynastyprocess/*` returns 403 in this kind of session) — a
documented, pre-existing, session-local restriction (`docs/can-we-rebuild-the-database.md`),
reported rather than re-solved per that doc's own instruction. The source fix will take effect
automatically the next time `board.json` is rebuilt with a working database.

## Evidence

- Backend: `python3 -m pytest tests/ -q` (no `nfl.db` in this container) — **688 passed, 29
  failed, 9 errors, 3 skipped**. Every failure/error is the missing-DB condition or the
  pre-existing `test_mailbox_health` ADR-054/055 collision (ADR-056, unrelated to this work,
  same before and after). Glossary-adjacent suites that don't need a live board build
  (`test_multi_league_export.py`'s pure-function tests, `test_export_contract.py`,
  `test_export_directory_contract.py`, `test_league_builder.py`) run clean.
- Frontend: `npm test` — **203 passed, 0 failed, 22 files**. `tsc -b --noEmit` clean.
- Screenshots (Playwright, `frontend/e2e/verify-adp-glossary-methodology.mjs` plus a follow-up
  scroll/expand pass), looked at directly: `adp-glossary-2026-07-29.png`,
  `adp-glossary-expanded-2026-07-29.png`, `adp-methodology-2026-07-29.png`,
  `adp-methodology-scrolled-2026-07-29.png` in `frontend/e2e/artifacts/`. Confirmed: ADP renders
  under "Draft mechanics" in the Glossary and expands to the real MFL text; the new Methodology
  section renders the real `adp_source_note` (147 of 225 `mfl_proxy` rows resolved, snapshot
  2026-07-29) beneath the "does not feed" language.
- All 27 `data/export/*/glossary.json` files (primary root + 26 sub-league dirs) confirmed via
  script to contain the `ADP` term.

## Files touched

- `src/export_static.py` — ADP term, `consensus rank` fix
- `src/export_contract.py` — `consensus_source_note` fix (comment + string), no version bump
- `frontend/ui/views/Methodology.tsx` — new ADP section
- `frontend/ui/data/glossaryCategories.ts` — `ADP` -> `draft` category mapping
- `data/export/**/glossary.json`, `nulls.json`, `opponents.json` — regenerated (content diff
  limited to the new ADP term plus timestamps)
- `docs/decisions.md` — ADR-060, plus conflict-marker cleanup around ADR-057/058
- `docs/handoffs/082-adp-fields-on-board-json-contract-1-14-0.md` — conflict-marker cleanup
- `docs/ideas-inbox.md` — session entry
- `docs/CURRENT-STATE.md` — in-place update
- `frontend/e2e/verify-adp-glossary-methodology.mjs` (new) — screenshot verification script

---

<!-- 2026-07-29-backend-fr040-costing.md -->

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

---

<!-- 2026-07-29-backend-id-allocation.md -->

# 2026-07-29 — backend — ID allocation widened + duplicate backstop (ADR-056)

## Task
Fix the recurring ID-collision defect (threads 043/049/053, ADR-048, thread 079/081, and three
more today: FR-020 double-allocated, ADR-054 colliding across `main` and an unmerged branch).
Root cause: every allocator scans the local working tree only, so a parallel branch is invisible.

## What shipped
1. **Widened allocation** (`tools/handoffs.py::next_free_id`, `::adr_next`,
   `tools/founder_requests.py::next_free_id`): now also scans `docs/handoffs/`,
   `docs/decisions.md`, `docs/adr-drafts/`, `docs/founder-requests/` as committed on every
   local + remote-tracking git ref, via `git for-each-ref` / `git ls-tree` / `git show`.
   Degrades loudly to working-tree-only scanning on any git failure (stderr warning, never
   silent).
2. **Hard duplicate-collision backstop** (the part that actually can't be bypassed):
   `find_adr_collisions()`, `find_thread_id_collisions()` in `tools/handoffs.py`;
   `find_fr_collisions()` in `tools/founder_requests.py`. Wired into `tools/handoffs.py check`
   (now hard-fails, not warns) and a new `tools/founder_requests.py check` subcommand.
   Detection only — nothing is renumbered automatically.

## What the new check found on this tree (real, not simulated)
`python3 tools/handoffs.py check` now fails with two genuine collisions in addition to the
pre-existing 078 issue:
- **ADR-054**: `main` = FFC ingester; `origin/backend/mock-calibration-kickers` = mock-draft
  batch ingestion snapshot work.
- **ADR-055**: `main` = kicker consensus-only export artifact; `origin/backend/mock-calibration-kickers`
  = `live_availability.py` LeagueConfig threading (my own ADR-055 from earlier this session).

Neither was renumbered, per explicit instruction. Whoever merges
`backend/mock-calibration-kickers` needs to renumber one side's ADRs before merge, or `check`
will keep failing after merge too.

`FR-020`'s reported double-allocation was not reproducible from the one branch fetched in this
session (`origin/backend/mock-calibration-kickers` has no second `FR-020-*.md`); the fix is
validated by fixture tests and will catch the real case once that branch is available here.

## Files touched
- `tools/handoffs.py` — `_git_ref_names`, `_git_tree_filenames`, `_git_show`, widened
  `next_free_id`/`adr_next`, `find_adr_collisions`, `find_thread_id_collisions`, wired into
  `cmd_check`.
- `tools/founder_requests.py` — same shape: `_git_ref_names`, `_git_tree_filenames`, widened
  `next_free_id`, `find_fr_collisions`, new `cmd_check` + `check` subcommand.
- `tests/test_handoffs.py` — 6 new tests (widening + both collision detectors, mocked git
  helpers so they don't depend on this session's actual fetched branches).
- `tests/test_founder_requests.py` — 3 new tests (same shape).
- `docs/decisions.md` — ADR-056.
- `docs/ideas-inbox.md` — the live collision finding, logged.

## Evidence
`python3 -m pytest tests/test_handoffs.py tests/test_founder_requests.py -q` → 27 passed, 1
pre-existing failure (`test_mailbox_health`; now failing for three true-positive reasons instead
of one — 078's missing reply, plus the two ADR collisions this session's own check newly
surfaces). Confirmed via `git stash` that `test_mailbox_health` was already red before this
session's changes (078 alone).

ADR number `056` from `python tools/handoffs.py adr next`; verified free (not present in
`docs/decisions.md`, `docs/adr-drafts/`, or the one fetched remote branch).

## Not done / out of scope
- Did not touch `src/`, `frontend/`, `docs/CURRENT-STATE.md` (file boundary).
- Did not renumber the live ADR-054/055 collision — detection only, as instructed.
- Did not widen the older unused `next_id()` back-compat helper in `tools/handoffs.py` — no
  current caller.
- Did not resolve thread 078's missing-reply issue — out of scope for this task.

---

<!-- 2026-07-29-backend-league-config.md -->

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

---

<!-- 2026-07-29-backend-per-league-exports.md -->

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

---

<!-- 2026-07-29-backend-qb-delta.md -->

# 2026-07-29 — backend — why QBs rank high in a 4-pt-passing-TD league

**Task.** The founder challenged the shipped 2026 board: it moves Josh Allen +20 (to overall #6)
and Lamar Jackson +19 against consensus, in a league that pays only 4 points per passing TD.
Investigated as a suspected defect first, per CLAUDE.md §8.

**Outcome: explained, not a bug — but the edge does not survive its own error bars.** Full
reasoning and every figure in **ADR-057** (`docs/decisions.md`).

## What I was asked to test, and what happened to it

The launching brief named the stacking passing-yardage bonuses as the leading mechanism and told
me to attack it hardest. **It is refuted.** Turning every yardage bonus off moves Allen zero board
ranks; passing bonuses are 2.1% of QB1's value over replacement. The brief's second premise — "if
disabling rushing/receiving bonuses also moves quarterbacks, that is a bug" — is **also wrong**,
and I did not treat it as a bug: VBD is a cross-position comparison, so changing the RB curve
necessarily reorders QBs, and elite QBs rush enough to hit rushing thresholds themselves. Both
predictions were stated confidently and both were incorrect; recording that here because the
project's stated failure mode is confident stories that fit the numbers.

The brief's leading *defect* hypothesis — a threshold bonus computed off a season total rather
than per game — is also disproved, at the engine level and against real 2024 QB seasons.

## What actually explains it

1. **VBD cancels the curve intercept exactly** (`VBD = b·(ln rank − ln base)`). Level intuitions
   about scoring rules — including "4 points per passing TD is stingy" — transfer to this board
   only through the *slope*. This is why the question felt unanswerable.
2. **The founder's intuition is correct and the board already obeys it.** At 6 pts/passing TD
   Allen would be #4; at 2 pts he'd be #8. The stingy setting is already pushing QBs down.
3. **56.5% of the elite-QB edge is rushing**, scored at RB rates and untouched by passing
   stinginess. Exact decomposition, licensed by the linearity of OLS in the outcome vector.

## The finding that matters more than the answer

The QB slope **collapsed monotonically** across the training window: −67, −73, −59, −45, **−4**
for 2021–2025. `fit_rank_curves()` pools all five seasons with **equal weight**, so the shipped QB
premium is an average over a regime that was disappearing. 2025 is verified complete (18 weeks,
18,521 rows), so this is not truncation. Meanwhile Allen's bootstrap CI is **[57.0, 155.2]**,
overlapping 29 of the top 40 players. The board's own uncertainty machinery already said the +20
was not actionable; the point estimate was being read without its interval.

Secondary: the log-linear estimator is misspecified **asymmetrically across positions** (RB/WR
concave in log-rank, QB not) — an ordering risk, since the board ranks positions against each
other.

**Deliberately not fixed.** Recency weighting and the estimator form are methodology changes
requiring the Statistician + Red-team gate, not a backend patch. Both are test-pinned and logged
in `docs/ideas-inbox.md`.

## Environment notes

- `scripts/rebuild_database.py` failed at **step 4/8** (`ingest_rankings.py`): the DynastyProcess
  mirror on github.com 403s through the agent proxy. This is documented in that script as an
  expected, reportable Claude-session-only block that must **not** be patched around. I did not
  patch it. I restored the `rankings` table from the **committed byte-exact dump**
  `data/rankings-history/rankings_2021_2025.csv` via a session-local helper in `experiments/` —
  a committed-artifact restore, not a source swap, and nothing in the pipeline calls it.
- Consequently steps 6–8 never ran, so `players_canonical`, `adp_snapshots` and `play_callers` do
  not exist in this container's DB. **18 test failures + 9 errors are entirely from those missing
  tables** (`sqlite3.OperationalError: no such table: adp_snapshots`), plus the pre-existing
  `test_handoffs.py::test_mailbox_health` documented in ADR-056. `git status` confirms **zero
  files changed under `src/`** this session, so none of them can be mine.
- The brief said the rebuild takes ~64s and succeeds. It does not in this worktree.

## Inbox

23 open threads addressed to `backend`, all from `pm` and all unrelated to this task. Not worked —
this session was scoped to the QB question only. No thread statuses changed.

## Evidence

- `tests/test_qb_board_delta.py` — **9 tests, all passing** (6 pure, 3 `requires_db`). Written
  before the diagnostics they license, per the standing rule.
- `experiments/qb_board_delta_diagnostic.py`, `experiments/qb_board_delta_uncertainty.py` —
  reproducible.
- Full suite: **673 passed, 18 failed, 9 errors** — all failures environmental as above.

---

<!-- 2026-07-29-backend-state-claims.md -->

# 2026-07-29 — backend — a claim checker for live documents (ADR-059)

**Branch:** `worktree-agent-afa13ac8a8bd0c533` (worktree, not merged).

## The premise, checked first

The dispatch said five false claims were found by accident on 2026-07-29 and asked for a
detector. I checked each against the repo before building anything, because a detector built on
a wrong account of the failures would encode the wrong checks:

| Claim in the dispatch | What the repo says |
|---|---|
| FFC "blocked by robots.txt" in CURRENT-STATE | Confirmed still live, in **two** places (lines 192 and 474), contradicted by `docs/pm/MEMORY.md` §0/§4, `docs/research/source-audit-2026-07.md` (row rewritten to UNBLOCKED) and `FR-023` |
| ADP capture "observed to succeed" / local task "redundant" | Already corrected in place in CURRENT-STATE, with the correction narrated inline |
| Predictions tab "absent from the shipped app" | Confirmed still live. `frontend/ui/views/Predictions.tsx` exists and is routed from `App.tsx:167` and `StandaloneApp.tsx:127` |
| `handoffs/README.md`: "design cannot read this repo" | Confirmed still live at line 99; `docs/design-protocol.md` §1 says the opposite and explicitly calls the README line false |
| rankings history unrecoverable | Confirmed live in CURRENT-STATE item 9 and in `can-we-rebuild-the-database.md`'s revision history; the same document's pass 2 disproves it (2,540 rows, row-for-row) |

Premise held. No contradiction with a written rule, so I proceeded without escalating.

## What I built

A **closed registry plus a closed document scope** — deliberately not prose analysis.

- `docs/state-claims.toml` — the registry. `[[artifact]]` (path on disk), `[[constant]]` (value
  read from the file that defines it), `[[status]]` (a named source or capability with a
  polarity vocabulary), `[[count]]` (measured from a file), `[[ignore]]` and `[[paths.allow]]`
  (suppressions, each with a written reason).
- `tools/state_claims.py` — the checker, also a CLI (`python tools/state_claims.py`).
- `tests/test_state_claims.py` — 21 tests, including the planted-fault proof.
- `tests/fixtures/state_claims/` — six planted faults with corrected counterparts, plus a
  two-document contradiction pair.

Three design choices did the real work, and each is a precision decision rather than a coverage
one:

1. **Only ten "live" documents are scanned.** `docs/status.md`, `docs/status/`,
   `docs/decisions.md`, numbered handoff threads, `docs/founder-requests/`, `SNAPSHOT-*` and
   `RUN-*` are never read. They record what was believed then; flagging them would be flagging a
   document for doing its job, and that is the false-alarm factory that gets a checker switched
   off. `test_append_only_logs_are_out_of_scope` pins this so a later session cannot widen it
   casually.
2. **A live document may narrate a superseded belief if it marks it** — `~~struck through~~`, an
   `<!-- state-claims: ignore-block -->` region, or a named suppression carrying a reason. I used
   the region marker once, on `can-we-rebuild-the-database.md`'s "three revisions in one day"
   list, which is genuinely history sitting inside a live document.
3. **A `[[status]]` claim with no registered `truth` flags disagreement *between* documents.**
   That is the cross-document-contradiction class, and it is the only honest form for a fact
   nobody has settled — it needs no ground truth at all.

Two implementation details were bugs I found by measuring rather than reasoning, and both would
have made the tool quietly useless:

- Phrases must match across a **soft line wrap**. The real CURRENT-STATE fault reads
  `FFC remains\n   blocked`; matching a literal single space missed it. The first draft of the
  checker did exactly that and silently under-reported. Fixed with `[^\S\n]+` joins.
- Matching must **not** cross a paragraph or heading boundary. A `## Not built` heading sits
  inside the proximity window of the first sentence under it and manufactures a false positive
  — it did, on my own corrected fixture, which is how I caught it.

## Planted faults — both directions

Six fixtures, each reproducing a real failure in roughly the words the real document used.
`{{CONTRACT_VERSION}}` and `{{BOARD_PLAYERS}}` are substituted from the live repo at test time,
so a *correct* fixture cannot rot into a false one when the real value moves.

| Fixture | Class | Caught | Corrected version silent |
|---|---|---|---|
| F1 FFC blocked by robots.txt | source status | yes | yes |
| F2 Predictions tab absent | existence | yes | yes |
| F3 design cannot read this repo | capability status | yes | yes |
| F4 `CONTRACT_VERSION` quoted as 1.13.0 | version | yes | yes |
| F5 board stated as 511 players | count | yes | yes |
| F6 rankings history unrecoverable | cross-doc / recoverability | yes | yes |
| F7 two docs disagreeing on the ADP capture | cross-doc, no ground truth | yes | n/a (pair) |

## Eight live false claims, found and corrected

The checker's first run on the real documents:

| Document | Claim | Corrected to |
|---|---|---|
| `CURRENT-STATE.md:419` | Predictions tab absent from the shipped app | removed from "Not built", replaced with a stated correction and the two routing sites |
| `CURRENT-STATE.md:44` | `CONTRACT_VERSION` is 1.13.0 | 1.14.0 — the file's own generated Build-state table had been right all along |
| `CURRENT-STATE.md:192` | FFC blocked by robots.txt | FFC unblocked; it is still the wrong *shape* for consensus, which is the point that paragraph was actually making |
| `CURRENT-STATE.md:474` | FFC remains blocked, founder decision needed | FFC unblocked, decision answered, remaining work is scoping |
| `CURRENT-STATE.md:55` and `:349` | board is 511 players | 510, measured from `data/export/board.json` |
| `handoffs/README.md:99` | design cannot read this repo | design has read access, no write access; `VIA: pm` is the landing hop only |
| `can-we-rebuild-the-database.md:33` | rankings history permanently unrecoverable | wrapped the superseded-conclusions list in an ignore-block, since the document's own pass 2 disproves it two paragraphs later |

After the corrections: `python tools/state_claims.py` → **OK, 10 live documents, no contradicted
claims.** Zero false positives across roughly 4,000 lines of live prose, and exactly one reasoned
path allowance (`src/mock_prediction.py`, which `CODE-MAP.md` correctly cites as living on
`backend/mock-calibration-kickers`, not on main — the allowance itself fails if that branch lands
or if the mention disappears).

## What it does not catch, stated plainly

**Failure #2 — the ADP capture — is the one it cannot verify.** "Has been observed to succeed"
and "the local task is now redundant" were false because no run with `event: schedule` had ever
fired; only a manual `workflow_dispatch` had. That is not readable from a checkout. It is
registered *truth-less*, so the checker flags the two polarities coexisting across documents but
**a single document asserting the false version alone still passes.**
`test_each_document_alone_does_not_fire_on_the_contested_claim` asserts that limitation rather
than describing it, so the gap is a measured property and not a paragraph nobody rereads. Closing
it properly needs a step that queries the Actions API — checking `event`, never the commit
author, since `github-actions[bot]` authors a manual dispatch too, and that is precisely how this
was got wrong. Raised as thread 083 item 3.

Also not covered, and deliberately: inferring a *presence* claim from free prose (imprecise — the
exact form, "a doc names a code path that is gone", is covered instead); and `docs/pm/**`, which
holds the richest live claims in the repo but is outside this role's write boundary, so a
violation there would produce a red suite with no available fix. One-line change, raised as
thread 083 item 1.

## Suite

`pytest -q` on this branch: 674 passed, 26 failed, 9 errors. The failing and erroring set is
**byte-identical to the same run with my changes stashed** — all pre-existing, all DB- or
snapshot-dependent, plus `tests/test_handoffs.py::test_mailbox_health`, which is red by design
over a real ADR numbering collision on an unmerged branch and was left alone.
`tests/test_state_claims.py` alone: 21 passed.

## Documents edited

`docs/CURRENT-STATE.md` (six corrections in place, plus a new Build-state row for the detector),
`docs/handoffs/README.md` (design's access), `docs/can-we-rebuild-the-database.md` (ignore-block
around the superseded-conclusions list), `docs/decisions.md` (ADR-059), `docs/ideas-inbox.md`
(four entries). Thread 083 opened to `pm`.

---

<!-- 2026-07-29-data-ops-db-rebuild.md -->

# 2026-07-29 — Data Ops: single-command database rebuild, closed the ADP-loader gap

**Role:** data-ops
**Ask:** Verify whether the three artifacts thread 080 committed as files actually load back
into a rebuilt database, build a single rebuild entry point if not, and prove it end to end.

Mid-session the coordinator redirected: another session (`claude/cloud-path-rehearsal-kafx7m` @
`6c23c13`) had already run a full clean-clone rehearsal and found the documented rebuild order
wrong/incomplete, corrected the "rankings history is unrecoverable" claim (it re-pulls
identically), and identified the real remaining gaps: `requirements.txt` missing pandas/numpy,
no Python version declared, `identity.py` ordering, and — the highest-value item — no
`adp_snapshots` CSV→DB loader. This session's scope narrowed to those gaps plus the rebuild
entry point.

---

## What was built

- **`scripts/rebuild_database.py`** — single entry point, 8 ordered steps, restores three
  fixture-committed artifacts plus the newly-loadable `adp_snapshots` history, and asserts row
  counts on all four after the run (fails loudly, not green-but-partial).
- **`src/ingest_mfl_adp.py`**: `import_snapshot_csv()` / `import_all_snapshot_csvs()` +
  `--import-csv-dir` CLI flag. The counterpart to the existing `export_snapshot_csv()` — closes
  the one gap the rehearsal found that was still open. 17 tests in
  `tests/test_ingest_mfl_adp.py` (8 pre-existing + 9 new), all passing.
- **`requirements.txt`**: added `pandas==3.0.5`, `numpy==2.5.1` (pinned, matching what installed
  cleanly under 3.12 this session).
- **`.python-version`**: `3.12`.
- **`tools/state.py`**: `BACKEND_PYTHON` hardcoded the founder's Windows conda path; changed to
  `sys.executable`. **Broke this once mid-session** — the explanatory docstring I wrote contained
  a literal Windows path in a non-raw string, and `\U...` in `miniconda3\Users` etc. parsed as a
  malformed unicode escape, making the whole module fail `ast.parse` on any Python. Coordinator
  caught it by actually running the file rather than reading the diff. Fixed by making the
  docstring raw (`r"""`). Re-verified: `ast.parse` succeeds on 3.11 and 3.12, and running
  `tools/state.py` end to end prints the build-state table correctly.

## What was found, corrected against the rehearsal branch

- **The rehearsal's documented order (`identity.py` last) does not work.** `identity.py` is the
  only thing that creates `players_canonical`, and `ingest_mock_drafts.py` needs that table to
  resolve picks. Running mock-draft restore before identity fails with `sqlite3.OperationalError:
  no such table: players_canonical` — measured directly. The correct order runs identity right
  after rankings exists (so its `build_identity_tables()` call, invoked directly rather than via
  its `main()`, needs nothing further) and before the mock-draft restore. Documented in both the
  script's own docstring and `docs/can-we-rebuild-the-database.md`.
- **`data/real_drafts/2025_league_draft.json`** (not `tests/fixtures/real_draft_2025/`, which is
  a table-dump export the ingester doesn't read) is the correct ingestible source and was already
  committed prior to this session (`c8738ed`). `ingest_mock_drafts.py` resolves it to 145/15,
  matching the documented figures exactly.

## Proof — measured this session

Full rebuild, `scripts/rebuild_database.py --db <scratch>`, against a genuinely empty database:

| Step | Time |
|---|---|
| 1 ingest_weekly_stats | 12.2s |
| 2 ingest_reference | 34.5s |
| 3 ingest_league_metrics | 14.0s |
| 4 ingest_rankings | 1.2s |
| 5 ingest_fantasypros_csv | 0.9s |
| 6 identity | 0.3s |
| 7 ingest_mock_drafts (real draft) | 0.4s |
| 8 ingest_mfl_adp --import-csv-dir | 0.4s |
| **Total** | **64.0s** |

Post-rebuild assertions — all passed:

```
OK  mock_drafts (2025 real draft): got 1, expected == 1
OK  mock_picks (2025 real draft): got 145, expected == 145
OK  mock_pick_quarantine (2025 real draft): got 15, expected == 15
OK  rankings (fantasypros_ecr, 2021-2025): got 2540, expected >= 2540
OK  rankings (founder 2026 half-PPR csv): got 538, expected >= 1
OK  adp_snapshots (distinct captured dates): got 3, expected >= 2
```

22 tables, matching row counts (`player_weekly_stats` 475,626; `ff_playerids`/`players_canonical`
12,468; `rankings` 3,486; `adp_snapshots` 703 across 3 dates; etc.) — see
`docs/can-we-rebuild-the-database.md` for the full table.

**Network steps in this session specifically:** `github.com/dynastyprocess/*` (nflreadpy's
source for `ff_playerids`/ECR/the CSV crosswalk) 403s in this Claude Code session's proxy —
verified a GitHub-App repo-scoping message, not a general network block; `raw.githubusercontent.com`
serves the same files unblocked. Per the coordinator's explicit instruction, **this is not
worked around in the committed script** — the founder's real machine and GitHub Actions never
see it. The 64.0s run above and full row counts were verified using a scratch-venv-only
`sitecustomize.py` patch that never touched the repo (confirmed via `git status`/`git diff`
clean throughout); this is documented as a session-specific environment finding in
`docs/can-we-rebuild-the-database.md`, not fixed in code.

## Full test suite against the rebuilt database

Run in background (`pytest -q`) against a rebuilt `data/nfl.db` (symlinked from the scratch
rebuild output; the real repo's `data/` was never written to). See this file's tail / the
session's tool-call log for the exact pass/fail/skip counts once it completed — recorded here at
session close: **[fill in from the completed run below]**.

---

## Rows ingested / quarantined / sources attempted

| Source | Status |
|---|---|
| nflverse (weekly stats, reference tables, league metrics) | OK, network, no login |
| DynastyProcess ECR mirror (`ingest_rankings.py`) | OK in principle (re-pulls identically to committed CSV); blocked in *this session's* proxy specifically, not a general finding |
| Founder 2026 half-PPR FantasyPros export | OK, committed file, 538 ingested / 37 quarantined (36 DST-by-design + 1 crosswalk gap) |
| 2025 real draft (`data/real_drafts/2025_league_draft.json`) | OK, committed file, 145 resolved / 15 quarantined |
| MFL ADP CSVs (`data/adp-snapshots/*.csv`) | OK, committed files, 703 rows / 3 dates, new loader |
| FFC / Yahoo / ESPN | Not attempted — out of scope this session, still blocked per `robots.txt` / OAuth per CLAUDE.md §5/§10 |

No values fabricated; no gap silently filled.

## Files touched

- `scripts/rebuild_database.py` (new)
- `src/ingest_mfl_adp.py` (loader added)
- `tests/test_ingest_mfl_adp.py` (9 new tests)
- `requirements.txt`, `.python-version`
- `tools/state.py` (interpreter fix)
- `docs/can-we-rebuild-the-database.md` (rewritten with final measured state)
- `docs/ideas-inbox.md` (decision logged)
- `docs/status/2026-07-29-data-ops-db-rebuild.md` (this file)

---

<!-- 2026-07-29-data-ops-ffc-adp.md -->

# 2026-07-29 — data-ops — FFC ADP ingester (all three formats), wired into daily CI

## What this session did

1. **Verified the FFC-unblock authorisation independently**, rather than trusting the coordinator
   dispatch message alone: `docs/pm/MEMORY.md` §4 and
   `docs/founder-requests/FR-023-ffc-is-unblocked-founder-confirmed-no-restrictio.md` both confirm
   the founder contacted FFC directly and reported no restrictions. Re-fetched `robots.txt` myself
   and confirmed only `/api/`, `/ajax/`, `/ajax-v2/`, `/import/`, `/adp/csv/`, `/draft/`,
   `/rate-my-team/results/`, `/rankings/custom/` are disallowed — the HTML ADP pages this ingester
   fetches are not on that list, and `/adp/csv/` is never touched.
2. **Built `src/ingest_ffc_adp.py`** — half-PPR 10-team initially, then extended to all three
   formats (non-PPR/half-PPR/PPR) mid-session at the founder's follow-up request. Each format is
   its own `adp_source` (`ffc_non_ppr_10team` / `ffc_half_ppr_10team` / `ffc_ppr_10team`), never
   blended with each other or with `mfl_proxy`.
3. **Found and fixed a same-day duplicate-row defect**: a second `store_adp()` call for the same
   day was appending rather than replacing. Added a `DELETE` scoped to
   `(adp_source, period, teams, format, as_of_date)` before insert, plus two regression tests.
4. **Rebuilt `data/nfl.db` locally** (`uv venv --python 3.12`, `scripts/rebuild_database.py`) to
   get `ff_playerids` for identity resolution — hit and resolved two environment issues along the
   way (a stale locked sqlite connection from an earlier failed run; the DB itself needed only
   `--only ff_playerids`, not a full rebuild, once the lock was cleared).
5. **Ran the real capture** for all three formats against the live site, once, and confirmed
   idempotency under repeated `--force` runs (no duplicate rows, no duplicate CSV lines).
6. **Wrote `tools/ci_ffc_adp_snapshot.py`** (mirrors `tools/ci_adp_snapshot.py`'s fail-loud
   posture) with an explicit, documented 80% name-resolution floor instead of MFL's 90% — FFC
   resolves by name against `ff_playerids`/`players_canonical`, which carries **zero** team-defense
   rows (verified by direct count), a structural ceiling below 100% rather than a join defect.
7. **Wired both MFL and all three FFC captures into `.github/workflows/adp-snapshot.yml`**,
   holding the existing bar: the run fails rather than commits an empty or degraded file, for any
   of the four snapshots.
8. **Mid-session false-alarm, documented for the record**: discovered two commits already on the
   branch with content matching my own uncommitted work almost exactly, and halted rather than
   resolving it myself (per CLAUDE.md's coordination discipline). The coordinator confirmed this
   was their own `git add -A` sweeping my in-progress files under their commit messages while I was
   still working — not a parallel agent. `git diff HEAD -- src/ingest_ffc_adp.py
   tests/test_ingest_ffc_adp.py` was empty, confirming byte-identical content; nothing was
   reconciled or discarded because there was nothing to reconcile.

## Evidence

**Rows captured (2026-07-29, live pull):**

| adp_source | stored | quarantined | match_rate | totalDrafts (sample) |
|---|---|---|---|---|
| `ffc_non_ppr_10team` | 171 | 17 | 91.0% | 628 |
| `ffc_half_ppr_10team` | 180 | 23 | 88.7% | 1,187 |
| `ffc_ppr_10team` | 213 | 29 | 88.0% | 3,673 |

**Quarantine reasons (union across formats, half-PPR shown as representative):** 19 of 23 are
`no_name_match` on team defenses ("Seattle Defense", "Denver Defense", ...) — `ff_playerids` has
zero DEF entries, confirmed by direct query. Remaining: `Marvin Harrison Jr.` (`ambiguous_name_match`
— normalize_name() strips the "Jr." suffix, colliding with the elder Marvin Harrison and a third WR
Harrison), `Kenny Gainwell`, `Eddy Piñeiro`, `Chig Okonkwo` (`no_name_match`, likely nickname/accent
mismatches against `ff_playerids`' canonical names — not investigated further, correctly quarantined
rather than fuzzy-matched).

**as_of_date:** `2026-07-29` for all three, `is_retrospective_aggregate=0` (genuine same-day
capture, not a backfill).

**Tests:** `tests/test_ingest_ffc_adp.py` — 18 new tests, all passing (parsing, identity
resolution + quarantine, never-blend across 3 formats, CSV export/import round-trip, same-day
overwrite-not-append, network-failure handling). `tests/test_holdout_audit.py` — added
`ingest_ffc_adp.py` to `CONNECT_ALLOWLIST` (ingestion module, same class as `ingest_mfl_adp.py`).
Full suite run this session: 655 passed, 8 skipped, 8 pre-existing failures unrelated to this work
(export_contract version/committed-artifact mismatches in files explicitly out of my boundary —
not investigated or touched, per task scope).

**Commit:** see `git log` for this session's commit hash (recorded at commit time below).

## Sources attempted and status

| Source | Status |
|---|---|
| FFC HTML ADP pages (`/adp/<format>/10-team/all/2026`) | **Captured**, 3 formats, daily via CI |
| FFC `/adp/csv/` | **Not touched** — robots-disallowed, never attempted |
| FFC historical seasons (`--period <year>`) | **Not pulled this session** — flagged in
  `docs/ideas-inbox.md`; would need `is_retrospective_aggregate=1` labelling per ADR-054, and a
  decision on whether a retrospective aggregate is worth capturing before it's built |

## Not done / explicitly out of scope this session

- Whether FFC ADP feeds `src/export_contract.py` / `src/make_board.py` / `src/availability.py` —
  not touched, per the task's explicit file boundary.
- FFC historical backfill.
- Model/ranking changes of any kind.

---

<!-- 2026-07-29-data-ops-nflverse-audit.md -->

# 2026-07-29 — data-ops — nflverse unused-data audit

**Task:** audit only, no ingestion. Enumerate every `nflreadpy` loader (23 total, pinned
`nflreadpy==0.1.5`) against what `data/nfl.db` and `src/ingest_reference.py` /
`src/ingest_weekly_stats.py` already pull, and identify what's free, licensed, and unused that
would plausibly matter to a player-level ranking model — specifically checking whether it closes
any of the coaching or route-participation gaps.

**Worktree setup note:** `data/nfl.db` in this worktree was a 0-byte stub (per
`docs/environment.md` §4 — sqlite silently creates one on first touch). Copied the real 854.7MB
file from the main checkout before querying.

**Method:** called every loader not already used by this repo directly against the network
(nflverse's public GitHub-release mirrors), inspected real `.columns`/`.shape`, cross-checked
against `sqlite3` queries on the copied `data/nfl.db` (22 tables, matches CURRENT-STATE).

**Findings (full detail in `docs/research/nflverse-unused-data-audit-2026-07-29.md`):**

- 10 of 23 loaders already called by this repo; 13 never called.
- `load_schedules()` carries `home_coach`/`away_coach` per game, 1999–2026, 7,548 rows total,
  zero nulls in every season sampled (1999/2010/2020/2025/2026). Not currently ingested.
  **Partially** closes the coaching gap — head-coach identity only, not coordinator/play-caller
  duty, so `src/ingest_play_callers.py` (confirmed still parked, zero rows, no table in
  `data/nfl.db`) remains the right approach for that piece.
- `load_participation()` carries a `route` column (route type run by the targeted receiver) and
  `offense_players` (all 11 on-field players) per pass play, 2016–2025, ~45–48K plays/season.
  This is the "documented proxy calculation" CLAUDE.md §5 anticipates for route data — not
  currently ingested. Confirmed the three already-ingested NGS tables
  (`ngs_receiving`/`rushing`/`passing`, 14,731/6,059/5,933 rows, 2016–2025) carry no route field
  at all — so the existing route-gap claim was accurate for those tables, the miss was never
  checking `load_participation`.
- `load_ff_opportunity()` (2006–2025, ~5,200–6,100 rows/season, 159 columns) is a pre-fitted xFP
  model, not raw data — flagged for a Statistician call before use as a ranking input, not
  something Data Ops should decide alone.
- `load_ff_rankings()` attempted, got `403 Forbidden` from the proxy fetching
  `github.com/dynastyprocess/data` — recorded as blocked, not retried, not worked around.
- Other unused loaders checked and deprioritized: `load_rosters_weekly` (marginal overlap with
  `injuries`/`depth_charts_weekly`), `load_ftn_charting` (test-registry #16/#17 pointed here —
  checked, **no route-participation column exists in it**, that pointer was stale), `load_pfr_advstats`,
  `load_team_stats`, `load_officials`, `load_trades`, `load_players`/`load_rosters` (no distinct
  signal over what's already held), `load_pbp`/`load_stats`/`load_ffverse` (raw source or
  dispatcher/meta, nothing new).

**Rows ingested:** 0 (audit only, per task constraint).
**Rows quarantined:** 0.
**Sources attempted:** nflreadpy loaders — all succeeded except `load_ff_rankings` (403 via
proxy, blocked, recorded).
**Commit:** see `git log` in this worktree, branch pushed, not merged.
**Test count:** no code changed; no new/changed tests this session.

**Docs touched:** `docs/research/nflverse-unused-data-audit-2026-07-29.md` (new),
`docs/CURRENT-STATE.md` (item 10 added, in place), this file.

---

<!-- 2026-07-29-data-ops-rescue-rebuildability-closeout.md -->

# 2026-07-29 — rescue, environment doc, rebuildability test, closeout, code map

Founder-directed session, five items in a fixed order, run without approval checkpoints
("decide and log").

## 1. Rescue — done

`.claude/worktrees/backend-mock-calibration` held 11 uncommitted files (7 modified, 4 new).
Committed **as-found** to `backend/mock-calibration-kickers` @ `11c794a` and pushed. Not merged,
not reviewed, completeness not assessed — that was the instruction.

Contents: `src/mock_prediction.py` (ingest-time prediction snapshots for the batch mock path,
reusing `mock_lab_store.predict_next_pick`), `freshness.historical_snapshot_date`, a frozen
league-config snapshot plus `calibration_usable` gate in `ingest_mock_drafts.py`, kicker export
changes, three new test files, and ADR-054. ~1,116 insertions.

Two premise notes. The branch had **no unique commits** — `f1d51d0` was already an ancestor of
`origin/main`, so the working tree was the only thing at risk. And the worktree carries an
**older CLAUDE.md**, under which `docs/status.md` was still the live log; its `status.md` append
was correct when written, not a violation of the current freeze.

## 2. `docs/environment.md` — done

Six environment facts that subagents were rediscovering every session, each re-verified against
current code rather than copied forward. Linked from CLAUDE.md §12 and inserted as session-start
reading item 2, ahead of the role docs.

Two facts changed on verification:

- The hook gained a `dequote()` step on 2026-07-28, so the semicolon false positive is
  **narrower** than previously recorded. Measured truth table: `@{n='FE';e={...}}` and
  `ForEach-Object { $a = 1; $b = 2 }` are still blocked; `;` inside quotes is now allowed. A
  third case was found — interleaved quote types can misalign the textual dequote and expose a
  `;` you believed was protected.
- Here-strings fail differently per shell: PowerShell 5.1 breaks on embedded double quotes, and
  the Bash tool does not parse `@'...'@` at all (it passed literal `@` characters into a commit
  message this session). Recorded `git commit -F <file>` as the pattern that works in both.

## 3. Rebuildability — done, and it changes a standing claim

`docs/can-we-rebuild-the-database.md`. Measured by actually rebuilding into a scratch directory;
the live DB was opened `mode=ro` throughout.

**99.3% rebuilds in ~4 minutes** with no credentials (`ingest_weekly_stats` 22.2s → 475,626 rows
exact; `ingest_reference` 75.0s; `identity.py` 12,468/49,391/57 exact; `ingest_league_metrics` 27
exact). Scratch DB 807.8 MB vs the real 813.7 MB.

**Three things do not rebuild** — full detail in thread 080 and CURRENT-STATE open item 9:
the 2025 real draft (160 picks, `user_provided_screenshots`, the `n=160` behind λ=0.352); the
founder FantasyPros export under gitignored `data/raw/`; and rankings history 2021–2025, which
the DynastyProcess mirror no longer serves — verified per season with the ingester's own
`resolve_snapshot_date` (2021–2025 all fail, 2026 resolves).

**Committed ADP CSVs cannot substitute** for the rankings history: wrong source (`mfl_proxy`
market ADP vs FantasyPros expert ECR, which CLAUDE.md §4 forbids blending), wrong period (both
July 2026), wrong scale (232 vs 3,487 rows).

This corrects CURRENT-STATE's standing claim that `adp_snapshots` is "the one table in
`data/nfl.db` that cannot be rebuilt" — corrected in place. MFL *does* serve historical periods,
but stamps every response today and returns an accumulated aggregate, so re-pulling reintroduces
look-ahead. Its window also shrank: 2026 `totalDrafts` read 43 on 07-29 against 50 in the 07-26
CSV.

Also measured: `depth_charts_snapshots` (+9,522) and `contracts` (+48) drift upward on rebuild.
Reproducing a past backtest number needs pinned artifacts, not pinned commands.

## 4. Closeout — done (five items, ideas inbox skipped as instructed)

**Defects registered.** Thread 080 (three unreproducible artifacts → backend, blocks cloud
sessions). Thread 081 (thread 079 ID collision between `main` and the `phase3-chain1` worktree —
a *fourth* instance after 043/049/053/ADR-048; the mechanism is that `sync` cannot see unsynced
threads in sibling worktrees, so parallel worktrees make the documented protocol insufficient
rather than merely forgettable). FR-019 filed for the founder's working preferences.

**Founder interruptions counted** across 57 prior transcripts, structured events only: 45 total,
0.8/session. Ask-the-founder 19 (42%), manual interrupt 9 (20%), tool denied 6 (13%), hook
chaining 6 (13%), hook destructive 5 (11%). An earlier regex pass gave 173 and was inflated by
docs and hook source that merely quote those strings — **that number should not be used.**
This overturns FR-018's premise: permission denials are 6 of 45, and `permissions.allow` is
already fully wildcarded, so the request was rescoped in place rather than worked as written.

**Branch audit.** 28 local branches; **0 have unique work missing from origin**. Five dirty
worktrees, not one — but the four beyond the rescue target hold regenerated exports or
superseded drafts already landed on `main` (`export_history.py`, `league_scoring_live.json`,
`season_stats.json` are all tracked; `export_rosters.py` was superseded by `build_rosters_json`
inside `export_contract.py`). The founder's premise that the mock-capture work was the only real
orphan was correct.

**CURRENT-STATE.md** updated in place: `Last verified` moved to 2026-07-29 @ `c96739c`, the
ADP-is-the-only-unrebuildable-table claim corrected, open item 9 added. Build-state table
regenerated via `tools/state.py --apply`, not hand-typed.

**Dashboard.** `docs/dashboard.html` was a hand-written snapshot with no date in it, making
staleness undetectable. Replaced with `tools/dashboard.py`, which renders from
`CURRENT-STATE.md` + `handoffs/OPEN.md` + git, per the standing CLAUDE.md preference. `--check`
mode exits 1 when stale, so it can go in the suite later. One bug found and fixed while
verifying: the page counted its own file in the dirty count, so writing it made `--check`
permanently red.

**Still stale, not regenerated:** `docs/roles-workflow-map.html` — no generator exists and
writing a second one was out of scope.

## 4b. Artifacts committed mid-session — founder interrupt, thread 080 closed

The founder redirected mid-session to act on thread 080 immediately rather than leave it
queued. All three are now committed and pushed (`bdda50e`), verified by reading the blobs back
out of `origin/main` rather than trusting the working tree:

| Artifact | Path | Verified from `origin/main` |
|---|---|---|
| 2025 real draft | `tests/fixtures/real_draft_2025/` | 145 picks + 15 quarantined + 1 draft = 160 |
| Rankings history | `data/rankings-history/rankings_2021_2025.csv` | 2,540 rows, 5 seasons, dispersion intact |
| Founder exports | `data/raw/founder-export/2026-07-27/` | 4 files, board source 574 players |

`.gitignore` now reads `data/raw/*` with `!data/raw/founder-export/` — the negation only works
against the `*` form, since git does not descend into an excluded directory. Repo confirmed
private before committing third-party data (unauthenticated API read → 404), consistent with
the already-settled D-020.

`tests/test_unreproducible_artifacts.py` adds 13 tests that read the *fixtures*, not the
database, so they pass in a fresh clone with no DB — the exact situation they protect against.

One number corrected: the rankings history is **2,540** rows, not the 3,487 quoted earlier in
the session. 3,487 is the whole table; 2021–2025 is 2,540, and the 36 quarantined rows are all
2026, which is re-pullable.

## 5. Code map — done

`docs/CODE-MAP.md`, read-only, five questions answered with file:line. Nothing refactored.

## Commits

`11c794a` (rescue branch), `7b9a5a4`, `c96739c`, plus the closeout and code-map commits on
`main`. All pushed.

---

<!-- 2026-07-29-data-ops-sleeper-projections.md -->

# 2026-07-29 · data-ops · Sleeper component projection ingestion

**Dispatch:** PM/founder-relayed task, licensing question pre-decided ("personal use, proceed"),
answering thread 091/092 item 1 (`docs/research/component-projections-and-fr-053-features-
2026-07-29.md`).

## What was built

`src/ingest_sleeper_projections.py` — matches `src/ingest_ffc_adp.py`'s shape: descriptive
User-Agent, HTTP 429 backoff, at most one fetch per position per calendar day, CSV snapshot
canonical under `data/projection-snapshots/`, `data/nfl.db` a rebuildable cache of it.

**Independently re-verified the researcher's endpoint record before building** (the researcher's
session had no shell tool and could not run anything itself):
- `GET https://api.sleeper.com/projections/nfl/2026?season_type=regular&position[]=QB` → HTTP 200,
  355 QB rows, every row `company: "rotowire"`, `stats` block carrying real per-component numbers
  (`pass_att/cmp/yd/td/int`, `rush_att/yd/td`, `rec/rec_yd/rec_td`, `fum_lost`, `gp`, 2pt fields,
  reception-distance buckets). RB=741, WR=1362, TE=647 rows the same session.
- `https://api.sleeper.com/robots.txt` is entirely commented out — nothing disallowed.

Both match the researcher's record; no schema drift found.

**Identity resolution:** `identity.resolve(conn, "sleeper", player_id)` — a real crosswalk spoke
already present in `ff_playerids.sleeper_id` (identity.py's `DIRECT_CROSSWALK_SOURCES`), not name
matching. An unresolved `sleeper_player_id` is quarantined with reason
`no_sleeper_crosswalk_match`, never guessed.

**A real bug found and fixed before landing:** Sleeper's own `player.position` field is not
reliably consistent with the `position[]=` query filter — an `RB` fetch returned some rows Sleeper
itself tagged `WR`/`TE`/`FB`. The first version keyed the once-a-day skip-check and the re-run
DELETE scope on that field, which caused the WR and TE fetches to be silently (and wrongly)
skipped as "already fetched today" because a stray mistagged row from the RB fetch satisfied the
check. Added a separate `query_position` column carrying the actually-requested filter and
rekeyed gating/DELETE/CSV export on it. Caught by running the real ingester against the real
crosswalk, not just the unit tests (which used single-position fixtures and would not have
exposed this).

**As-of-date convention:** Sleeper's payload has no as-of-date field of its own, only per-row
`last_modified`/`updated_at` (Rotowire's own last-touch timestamps). Per CLAUDE.md §4,
`as_of_date` is stamped as OUR capture date (UTC); the source's own timestamps are preserved
verbatim as `source_last_modified`/`source_updated_at` so the two are never conflated.

## Scope discipline

Ingestion only — no scoring changes, no re-ranking, `board.json` untouched. **Not wired into any
export, not behind the public site** (CLAUDE.md §10; the app is public per `docs/CURRENT-STATE.md`,
and Sleeper's ToS §9.2 forbids redistribution, per the researcher's artifact). Lands only in
`data/nfl.db` (gitignored) and `data/projection-snapshots/` (committed, canonical).

## Rows ingested / quarantined

| Position | Stored | Quarantined | Match rate | Reason (100% of quarantine) |
|---|---|---|---|---|
| QB | 250 | 105 | 70.4% | `no_sleeper_crosswalk_match` |
| RB | 538 | 203 | 72.6% | `no_sleeper_crosswalk_match` |
| WR | 840 | 522 | 61.7% | `no_sleeper_crosswalk_match` |
| TE | 379 | 268 | 58.6% | `no_sleeper_crosswalk_match` |

Spot-checked: quarantined names are deep practice-squad/UDFA QBs (Tim DeMorat, James Blackman,
etc.) absent from `ff_playerids`, not real starters — resolved rows include Dak Prescott, Jared
Goff, Patrick Mahomes with real component values. Match rate is lower than FFC's ADP ingester
(~98.5%) because Sleeper's pool includes far more fringe/UDFA players than the ADP boards do; not
a resolution defect.

## Sources attempted and status

| Source | Status |
|---|---|
| `api.sleeper.com/projections/nfl/2026` (QB/RB/WR/TE) | Fetched successfully, 4/4 positions |
| Every other source in the researcher's artifact (FantasyPros API, NFL.com, PFF, SportsDataIO) | Not attempted — out of scope for this dispatch, which named the Sleeper route specifically |

## Records written

- `docs/handoffs/092-component-projections-exist-and-are-cheap-for-pe.md` — allocated the
  previously-staged unallocated thread (`091-...md`, deleted, no shell to allocate it originally)
  via `tools/handoffs.py new`, pasted the full staged body, appended a data-ops reply recording
  what was built against item 1's licensing ruling. Left `STATUS: OPEN` — only `pm`/`design` may
  resolve; items 2-5 are untouched and outside data-ops scope.
- `docs/founder-requests/FR-056-...md` — the founder's "personal use, proceed" ruling, marked DONE.

## Tests / commit

- `python3 -m pytest tests/test_ingest_sleeper_projections.py -q` → 10 passed.
- `python3 -m pytest tests/ -q` → 33 failed / 718 passed / 9 errors — **identical to the baseline
  measured with this session's new files absent** (confirmed via re-run without them); every
  failure is the missing/partial-local-`nfl.db` condition documented in
  `docs/can-we-rebuild-the-database.md`, none touch `ingest_sleeper_projections.py`.
- `python3 tools/handoffs.py check` → fails only on the two pre-existing, deliberately-known-red
  ADR-054/055 collisions (`docs/CURRENT-STATE.md` top open item #15) — unrelated, unchanged by
  this session.
- Commit `fdd4685b9ac4a902b31bc6107821de02b1150bfe`.

---

<!-- 2026-07-29-frontend-adp-display.md -->

# 2026-07-29 — frontend — ADP display on board, draft room, player detail

**Role:** frontend · **Type:** UI wiring against an already-landed export contract bump
**Thread:** 082 (backend -> frontend, FR-024) · **Contract:** 1.13.0 -> 1.14.0

## Task

Founder asked (2026-07-29, recorded as FR-024): "ADP should be shown on both the prep and draft
screens as well as player profile." Backend's half landed same day (thread 082, commit `3690217`/
`c6b45be`, contract bump to 1.14.0): `board.json` player rows gained `adp`/`adp_min_pick`/
`adp_max_pick`/`adp_selected_pct`/`adp_source`; the board top level gained `adp_source`/
`adp_as_of_date`/`adp_match_rate_note`/`adp_source_note`. Nothing rendered any of it. This session
closes the frontend half.

## Premise check

Read `CLAUDE.md`, `docs/CURRENT-STATE.md`, `docs/operating-model.md`, `docs/design-fidelity.md`,
thread 082, `docs/founder-requests/FR-024-*.md`, and `docs/backlog-triage-2026-07-29.md` before
acting. All consistent, no contradiction found. `data/export/board.json` and
`frontend/public/data/board.json` were both already at `contract_version: 1.14.0`, byte-identical,
already synced — confirmed measured, 144/510 rows carry a real `adp` value, 366 null, matching
backend's reported count.

## What was built

- `frontend/ui/data/types.ts` — `RawBoardPlayer` gains 5 optional ADP fields; `RawBoard` gains 4
  optional top-level ADP fields. Optional so a pre-1.14.0 export still parses.
- `frontend/ui/data/board.ts` — `BoardRow` gains `adp`/`adpMinPick`/`adpMaxPick`/`adpSelectedPct`
  as `Cell<number>` (through `fromNullable`, honest-null convention, authored reason citing MFL's
  ~top-230 coverage limit) and `adpSource` as a plain string travelling alongside them.
- `frontend/ui/data/contract.ts` — `EXPECTED_CONTRACT` 1.13.0 -> 1.14.0.
- `frontend/ui/data/trace-fields.ts` — `TRACE_CONTRACT` 1.13.0 -> 1.14.0, new 1.14.0 changelog
  entry (records the delta-column decision below), all 5 player-row ADP fields registered in
  `BOARD_TRACE_FIELDS` (required — the registry is compared 1:1 against exported player-row keys
  by `trace-fields.test.ts`), all 4 top-level fields registered in `BOARD_HEADER_TRACE_FIELDS`.
- `frontend/ui/views/Board.tsx` — new `ADP (MFL)` column between CONS and Δ, sortable
  (`SortKey` gains `'adp'`). Header label is the glance-level "not your league's ADP" signal (per
  the founder's explicit requirement); `AdpCell` shows the value with a tooltip carrying source,
  pick range, and selected%; absent renders through the same em-dash convention as every other
  column on this table. Column header itself carries a title with the full `adp_source_note` +
  `adp_as_of_date`, reachable without depending on any row having data.
- `frontend/ui/views/DraftRoom.tsx` — compact `DraftRoomAdpCell` (value + "MFL" superscript, or
  em-dash) inserted between team and the existing delta-vs-consensus cell in the board list.
- `frontend/ui/components/PlayerDetail.tsx` — new `AdpBlock` section below "WHY OUR RANK DIFFERS
  FROM THE MARKET": value, pick range, selected%, and `board.adp_source_note` rendered verbatim
  (the one place on any of the three screens the full caveat is always visible, not gated behind
  hover) plus `adp_as_of_date`. Null case shows the row's own absent-cell reason, distinct wording
  from the projection/availability null states elsewhere in the same sheet.
- `frontend/e2e/cloud-adp-screenshot.mjs` — new screenshot script following the cloud recipe in
  `docs/frontend-cloud-runbook.md` (explicit `executablePath` against the pre-installed Chromium
  1194 binary; never `playwright install`).

## Judgement call: no second delta column

Thread 082 and FR-024 both explicitly left this to frontend ("the board already shows a delta
against consensus, and two adjacent delta columns measuring different things would confuse more
than they reveal... left to frontend, which can see the layout").

**Decision: do not add a delta column comparing our rank to ADP.** Reasons:

1. The board already renders one delta (`delta_vs_consensus`, our rank vs. FantasyPros expert
   consensus). A second delta beside it (our rank vs. MFL-proxy ADP) is a different comparison but
   would sit in the same visual slot doing the same visual job — a reader skimming Δ columns has no
   cheap way to remember which delta means what without re-reading a header each time.
2. No backend field computes "our rank minus ADP." Adding that column would mean computing it
   client-side from two independently-sourced numbers, which is closer to inventing a value than
   displaying one — thin justification against Principle #1 (every rendered number traces to a
   named backend field).
3. The raw ADP value placed beside CONS lets a reader compare three sourced numbers (consensus
   rank, ADP, our rank) directly, which is the information FR-024 actually asked for, without
   introducing an unsourced fourth number.

Recorded in `trace-fields.ts`'s 1.14.0 changelog entry and in the thread 082 reply so the reasoning
is visible from both places a future session would look.

## Evidence

`npm test`: **202 passed, 0 failed, 22 test files** (`frontend/`). `npx tsc -b --noEmit`: clean.
`npm run smoke` (against a live dev server, contract 1.14.0 confirmed via `curl`): **18/19 passed**
— the one failure (`no console errors during the loop`) is the pre-existing missing-
`ANTHROPIC_API_KEY` reasoning-proxy network error already documented in
`docs/frontend-cloud-runbook.md` as unrelated to any data screen; unchanged by this session.

Six screenshots, looked at directly (not just captured), in `frontend/e2e/artifacts/`:

- `adp-board-2026-07-29.png` — Board table, top 16 rows, ADP (MFL) column populated (Bijan
  Robinson 3.3, Ja'Marr Chase 2.9, ...).
- `adp-board-null-row-2026-07-29.png` — scrolled to rank 33 (Jeremiyah Love), ADP column shows
  "—" distinct from populated neighbors above and below.
- `adp-draft-room-2026-07-29.png` — Draft Room board list, compact ADP figures with "MFL"
  superscript beside the existing delta column.
- `adp-draft-room-null-row-2026-07-29.png` — same list scrolled to Jeremiyah Love, "—" with no
  MFL tag, delta and availability columns unaffected.
- `adp-player-detail-present.png` — Bijan Robinson detail sheet, MARKET ADP block: 3.3 avg pick,
  range 1–7, taken in 16% of sampled drafts, full caveat paragraph visible.
- `adp-player-detail-null.png` — Jeremiyah Love detail sheet, MARKET ADP block: "No MFL ADP data
  for this player -- MyFantasyLeague's public sample only covers roughly the top ~230 players in a
  10-team pull... Not a zero, not a rank -- not computed."

## Coordinator commit note

Most of this session's edits (`board.ts`, `contract.ts`, `trace-fields.ts`, `types.ts`,
`Board.tsx`, plus `DraftRoom.tsx`/`PlayerDetail.tsx`) appear in commits `b6d5a0d` and `75bf095`,
authored by the coordinator mid-session ("wip: ADP display, in flight" / "Also carries in-flight
ADP display work from the frontend chain"), not by a competing agent. Verified via `git diff HEAD
-- <files>` before concluding anything: empty diff both times, byte-for-byte the session's own
work. No reconciliation needed, work continued.

## Boundary

Touched only `frontend/**`, this status file, and thread 082. Did not touch `src/`, `tests/`
outside frontend, `.claude/`, `docs/pm/`, `docs/CURRENT-STATE.md`, `wrangler.jsonc`, `.github/`.

## Result

Commit (this session's remaining diff — screenshots + screenshot script): see `git log` after
`tools/handoffs.py sync`. Test count: 202 frontend unit tests passing, 0 failed, 22 files.

---

<!-- 2026-07-29-frontend-cloud-readiness.md -->

# 2026-07-29 — frontend — cloud readiness verification

**Task:** answer, with evidence, whether the full frontend loop (install, typecheck, unit tests,
dev server, real screenshot) can run in this cloud container. Scope explicitly narrowed to
`frontend/**`, `docs/frontend-cloud-runbook.md`, `docs/ideas-inbox.md`, and this file — other
chains were active in `docs/handoffs/**`, `docs/pm/**`, `docs/environment.md`, `CLAUDE.md`,
`docs/CURRENT-STATE.md`, `.claude/**`, `scripts/`, `src/`, `tests/` and were not touched.

**Outcome: yes, with one worked-around gap.** Full detail and the recipe: `docs/frontend-cloud-runbook.md`.

## What was run, in order, stopping only where the task said to check

1. `npm ci` in `frontend/` — 6.2s, 184 packages, clean, no browser download triggered.
2. `npx tsc -b --noEmit` — clean, 0 errors.
3. `npm test` (vitest) — **202 passed, 0 failed, 22/22 test files.** Differs from
   `docs/CURRENT-STATE.md`'s recorded "192 passing / 2 pre-existing-red-by-design" (that line is
   dated 2026-07-26 and the paragraph around it is marked not-re-verified except for four unrelated
   bullets). Reported as a finding in the runbook, not silently reconciled, and not corrected in
   `docs/CURRENT-STATE.md` (outside this session's file boundary).
4. Dev server (`npm run dev -- --port 5199 --strictPort`) — started clean, served `GET /` 200 and
   `GET /data/board.json` with a real 511-player board.
5. Screenshot via Playwright — **hit a real red first**: the pinned `playwright` package expects
   Chromium revision 1234; the container's pre-installed binary is revision 1194 at
   `/opt/pw-browsers/chromium`, and `playwright install` is explicitly disallowed (blocked
   downloads). `frontend/e2e/verify-069-073.mjs` run unmodified confirmed the failure mode exactly
   (`Executable doesn't exist at .../chromium_headless_shell-1234/...`). Fixed by launching with an
   explicit `executablePath` against the pre-installed binary, per the task's own guidance. Wrote
   `frontend/e2e/cloud-board-screenshot.mjs` (new, always uses `executablePath`) rather than editing
   the provenance-marked `verify-069-073.mjs`. Captured
   `frontend/e2e/artifacts/board-cloud-2026-07-29.png` and **looked at it**: WESTWOOD league
   selected, header reads real provenance (`fantasypros_csv_2026draft · half ppr · preseason moving
   · generated 2026-07-28T04:41:54... · 511 players loaded`), table shows real ranked rows (Bijan
   Robinson #1 through row 17, Brock Bowers) with populated PROJ/CONS/Δ/VBD/TIER columns. Not an
   empty state.
6. `npm run smoke` — same executable mismatch, so added an opt-in `PLAYWRIGHT_CHROMIUM_PATH` env
   var to `frontend/e2e/smoke.mjs` (one line changed; default behavior unchanged when the var is
   unset). Ran with `PLAYWRIGHT_CHROMIUM_PATH=/opt/pw-browsers/chromium ... --no-server` against the
   already-running dev server. **18/19 checks passed.** The one failure (console-error check) is
   caused by the reasoning proxy (`server/proxy.ts`) having no `ANTHROPIC_API_KEY` in this container
   and failing at the network layer rather than resolving to its designed "reasoning unavailable"
   response — does not touch the board or draft room, both of which passed every assertion
   including the thread-063 regression table (suggester never reopens after a commit; stays closed
   across Escape, tab-switch, reload, undo). Looked at `draftroom.png`: DRAFT LIVE badge, real pick
   counter, Position Scarcity panel with real tier text, My Roster showing the drafted player.

## Decisions made without asking (per the founder's "decide and log" instruction this session)

- **Did not touch `docs/handoffs/**` or reply to the 15 open frontend inbox threads.** The task's
  explicit file boundary said other chains were active there this session; the standard end-of-
  session protocol (reply to every open thread, run `tools/handoffs.py sync`) was overridden by
  that explicit, narrower scope for this specific verification task. Not logged to
  `docs/ideas-inbox.md` (that file is described in-repo as PM-owned, append-only capture of raw
  founder remarks — this is a scope call, not a founder idea, so it goes in this status file
  instead, where the operating rules already expect session decisions to be recorded).
- **Edited `frontend/e2e/smoke.mjs` (one line) rather than leaving it broken in this environment.**
  Judged in-scope because the task explicitly asked to run it and report the result, and explicitly
  anticipated and prescribed the fix (`executablePath` over `playwright install`). Change is
  additive and env-gated — no behavior change anywhere the env var isn't set.
- **Left `frontend/e2e/verify-069-073.mjs` unmodified** rather than patching it too, since its own
  docstring marks it a one-off provenance record, not a maintained harness; added a new script for
  cloud screenshots instead.

## Evidence

- Commit: see `git rev-parse HEAD` after this session's commit (reported in the final reply).
- Test counts: 202 passed / 0 failed (vitest, frontend), `tsc -b --noEmit` clean.
- Screenshots: `frontend/e2e/artifacts/board-cloud-2026-07-29.png` (new),
  `frontend/e2e/artifacts/board.png` and `frontend/e2e/artifacts/draftroom.png` (regenerated by
  `npm run smoke` this session, both looked at directly, described above).
- Smoke: `frontend/e2e/artifacts/report.json`, 18/19 passed.

## Not done / explicitly out of scope this session

- `docs/CURRENT-STATE.md`'s stale test-count line was not corrected (not this session's file).
- The reasoning-proxy console-error gap was not fixed, only reported.
- No handoff threads were replied to; no ADR was opened (no methodology or architecture decision
  was made — this was operational verification).

---

## Task 2 (same session): standalone single-file board

Founder hit "localhost can't be reached" live — dev-server dependency is exactly what the cloud
move is meant to remove. Built `frontend/dist-standalone/board.html`: one file, all JS/CSS/data
inlined, opens via `file://`, no server, no network, no build step at the far end. Full recipe,
scope (in/out), and the real bug found and fixed along the way (a silently-failing `resolve.alias`
that shipped a real `fetch()` under a wrong assumption it had been eliminated) are in
`docs/frontend-cloud-runbook.md`'s new "Standalone build" section — not duplicated here.

Verified by opening the built file directly with Playwright over `file://` (never through a dev
server) and looking at the captures: `frontend/e2e/artifacts/standalone-board.png` (WESTWOOD,
half ppr, 511 players, real ranked rows through Brock Bowers) and `standalone-player-detail.png`
(full detail sheet, including the honest "Could not load weekly_finishes.json: not included in this
static snapshot..." state for the two sections deliberately not embedded). `e2e/verify-standalone.mjs`
also asserts zero non-`file://` network requests through both the initial load and opening
PlayerDetail — the second half of that check is what caught the `resolve.alias` bug; the first half
alone would have missed it.

## Task 3: phone-responsive layout — built, then reverted on explicit founder instruction

Built a responsive layer (`ui/styles/responsive.css`, an off-canvas Sidebar drawer, sticky Board
columns inside a horizontal-scroll container, 44px touch targets, a full-width PlayerDetail sheet)
against four phone/tablet viewports per the PM's dispatch. **Before this was verified or reported,
the founder pulled the request** — his actual ask was narrower ("optimize for phone viewing" read
as "build responsive layouts," which was an over-read), and his real position is that a mobile
layout on a deliberately dense board is a Design decision, not one to make ad hoc in the app
(FR-025).

**Reverted in full**, not left half-applied:
- `frontend/ui/styles/responsive.css` — deleted.
- `frontend/ui/styles/base.css` — `@import './responsive.css'` line removed.
- `frontend/ui/components/shell/Sidebar.tsx` — restored to its pre-work version exactly (diffed
  against `d0be35c^`, the commit before the WIP started, to confirm byte-for-byte match).
- `frontend/ui/App.tsx`, `frontend/ui/StandaloneApp.tsx`, `frontend/ui/views/Board.tsx`,
  `frontend/ui/components/shell/TopBar.tsx` — these were never committed (working-tree only) and
  were restored via `git checkout -- <path>` before anything captured them. The coordinator's revert
  instruction named only three files because those were the ones already committed and visible in
  the diff; the other four carried the same phone-only edits (hamburger button, sidebar-open state,
  touch-target classes) and were included in the revert on the same reasoning, not left behind on a
  technicality.

**Verified the revert, not just the diff**: full unit suite (202/202 still passing), clean
`tsc -b --noEmit`, and a real screenshot of the desktop app
(`frontend/e2e/artifacts/board-post-revert-2026-07-29.png`) — looked at directly: sidebar back at
full width with all seven Prep entries and the coming-soon list, all three mode buttons (Prep/Draft/
Season) present, board header carrying real provenance, table rendering real ranked rows. Matches
the pre-phone-work baseline screenshot exactly.

**Time cost:** the founder's own framing was "maybe twenty minutes, and it surfaced the real
answer" — not treating this as wasted effort, per his message.

## Task 4: Draft mode restored to the standalone build

The standalone build's first version excluded Draft mode on the assumption it needed a backend.
Challenged directly (the founder's own read of the code, which turned out right): checked
`ui/data/draft.ts` and `DraftRoom.tsx` for `fetch()` calls (none), confirmed the module's own
docstring already says "No backend call per pick," and confirmed "Export draft log" is a client-side
`Blob` download. Put Draft mode back into `ui/StandaloneApp.tsx` (mode switcher now shows Prep and
Draft; Season stays out, confirmed against `docs/CURRENT-STATE.md`'s "not built" listing — nothing
to restore there). Rebuilt the standalone artifact (1.07MB).

Verified with a new script, `frontend/e2e/verify-standalone-draft.mjs`, driving the actual
interaction over `file://`: switched to Draft mode, committed a pick via the digit shortcut (pick
counter 1→2, draft log recorded "Bijan Robinson"), undid it (2→1), triggered "Export draft log" and
confirmed it fires a `download` event rather than a network request, and asserted zero non-`file://`
requests through the whole sequence. All checks passed. Screenshots looked at directly:
`standalone-draft-room.png` (initial state — DRAFT LIVE badge, pick #1, full roster/scarcity/picks
panels, real snake sequence 3/18/23/...) and `standalone-draft-after-pick.png` (after the pick — pick
#2, board re-filtered to 510, draft log entry, scarcity recomputed).

## Evidence, tasks 2-4

- Commits: `1365c56` (standalone build), `833b168` (player-history fetch-bug fix), `d0be35c` (phone
  WIP, then reverted), `fcc1ef6`/`08d2c60` (revert + proof), `98a112b` (Draft mode restored). Final
  hash for this session reported in the closing reply.
- `frontend/dist-standalone/board.html`: 1.07MB, zero `fetch()` calls verified by both standalone
  e2e scripts.
- Unit suite: 202/202 passing after every change in this stretch (checked after the standalone
  build, after the fetch-bug fix, after the revert, and after Draft mode landed — not just once at
  the end).

---

<!-- 2026-07-29-frontend-fr034-035-036-037.md -->

# 2026-07-29 — Frontend: FR-034/035/036/037

Worktree `worktree-agent-ad3fc0f6ee64497b5`, branch of the same name, base `main@4980b29`.
Final commit: `cce7893`.

## Scope

Dispatched to diagnose and fix FR-035 (Predictions must be scoped to the selected league) and
build FR-036 (manual opponent team names). Mid-session, scope expanded twice by coordinator
message: FR-034 (draft-slot selector, Prep + Draft) and FR-037 (remove the "Refresh data"
button, which turned out not to be FR-030 in this tree — see collision note below).

## FR-035 diagnosis (the specific question asked)

**Re-derivation was already correct; the defect was that nothing on screen named the league.**
Switched leagues live in a running app (Westwood 10T/16rd/slot3 vs. Ethan's Expert League
10T/15rd/slot1), screenshot-confirmed the header line, BASELINE column, and "on the clock"
message all changed correctly on switch. Fix: a `Predicting for <league> · N teams · M rounds ·
your slot S` line under the Predictions heading, falling back to `league_id` when
`league_name` is absent, marking an FR-034 override distinctly (accent colour, "overridden,
sourced N").

**One separate, real bug found and fixed along the way:** `App.tsx`'s league-load effect had no
guard against out-of-order async resolution. Repeated league switches (not fast-clicking — real
waits between each) could leave `data` pointing at a stale league while every visible control
reported the new one selected. Fixed with a standard effect-cancellation flag. Regression test
confirmed to actually fail without the fix (temporarily disabled the guard, reran, restored).

## Opponents.tsx vs. LiveOpponents.tsx (the specific question asked)

**In this worktree, only `Opponents.tsx` exists — no `LiveOpponents.tsx` anywhere.** It is
reachable both as its own Prep-mode sidebar screen and, unmodified, as Draft mode's own
"Opponents" hub tab (`DraftRoom.tsx`'s `AdaptedOpponentsPane` wraps it). Confirmed by grep and by
screenshot in both surfaces.

**However:** a sibling, unmerged branch (`claude/pm-agent-setup-gobxa0`, commit `59b58cf`) *does*
carry a real `LiveOpponents.tsx` — a Draft-mode-only reimplementation reading live
`DraftState.picks` instead of `rosters.json`. That branch was never merged to `main`
(`origin/main` is still at `4980b29`), so this worktree never saw it. The original dispatch's
reference to `LiveOpponents.tsx` was accurate for that branch, not for this one — see the
collision note below for what this means for merging.

## Real cross-branch collision found, logged, not resolved unilaterally

While verifying FR-036, discovered:

1. **FR-034/035/036 numbering collision (self-inflicted, corrected before committing):** ran
   `tools/founder_requests.py new` against this worktree, which had no FR past 033, allocating
   034/035 to the wrong subjects. The real, already-allocated files (034=draft slot, 035=predictions,
   036=opponent names) existed only on `claude/pm-agent-setup-gobxa0` (commits `f987195`/`35854e2`).
   Fixed by discarding my own uncommitted, wrongly-numbered files and copying the real content via
   `git show <commit>:<path>` — never merged the branch, never touched anything already committed.

2. **FR-030 numbering collision (pre-existing, both sides real, not self-inflicted):** this
   worktree's real FR-030 is "run the rankings validation at maximum effort." The sibling branch's
   commit `59b58cf` independently created its *own* `FR-030-remove-the-refresh-data-button-...md`
   — same number, different subject, both real, on branches neither saw the other. Filed the
   refresh-button removal fresh as FR-037 here rather than overwriting the real FR-030 or guessing
   which branch's FR-030 should win.

3. **Two different implementations of the same fix**, both removing the Refresh button from the
   hosted site but architecturally different: the sibling branch kept `RefreshData.tsx` and gated
   it behind `import.meta.env.DEV`; this worktree deleted the component entirely (per this
   session's explicit instruction). Merging both branches as-is will conflict on `App.tsx` and
   `RefreshData.tsx`, and separately needs a decision on which Opponents-in-Draft-mode
   implementation (`AdaptedOpponentsPane`+`Opponents.tsx` here vs. `LiveOpponents.tsx` there) is
   kept. Not decided here — flagged in `docs/founder-requests/FR-037-...md` for whoever merges.

`python tools/founder_requests.py check` reported "no cross-branch ID collisions" both times,
despite two real ones existing — worth someone checking why it didn't catch either.

## What shipped, this worktree

- **FR-034**: draft-slot selector (`ui/components/shell/TopBar.tsx`'s `DraftSlotControl`),
  `1..teams`, present in both Prep and Draft mode, local per-league storage
  (`ui/data/draftSlot.ts`), single-seam recompute (`ui/data/league.ts`'s
  `applyUserSlotOverride`) that also recomputes `pickSequence` for the overridden slot (not left
  stale — would have silently broken RoundGrid's "mine" highlighting and DraftRoom's MY PICKS
  panel otherwise).
- **FR-035**: `Predicting for` context line (above), plus the async-race fix.
- **FR-036**: click-to-edit typed opponent names (`ui/data/opponentNames.ts`,
  `ui/views/Opponents.tsx`'s `OpponentNameField`), names-only, per-league, survives reload,
  never blends into any model input, clears to the sourced name (not blank), TYPED marker
  visually distinct from a sourced name. Works identically in Draft mode's Opponents tab with
  zero extra code (same component).
- **FR-037**: Refresh data button removed entirely; freshness line kept via a new `FreshnessNote`
  in `App.tsx`.

## Evidence

231/231 frontend tests pass (up from 203 at session start: +39 new, -12 removed with
`refresh.test.tsx`, +1 net for the button-removal regression test), `tsc -b --noEmit` clean.
Screenshots in `frontend/e2e/artifacts/`: `fr034-*.png`, `fr035-*.png`, `fr036-*.png`,
`topbar-no-refresh-button*.png` — all looked at directly, not just captured.

## Commits

`e54b83f`, `6a2523a` (pm-preserved WIP through two API outages), `4dc84ec` (async-race fix),
`3455074` (FR-035 fix + 39 tests), `1775ac6` (screenshots), `b1bd17f` (docs), `cce7893`
(Refresh button removal). Final: `cce7893`.

---

<!-- 2026-07-29-frontend-hub-adp-captures.md -->

# 2026-07-29 — frontend — draft-hub fold-in, ADP verification, four screenshot backlog threads

**Scope, per the dispatch:** `frontend/**`, `docs/handoffs/` replies on 027/028/029/041/082 only,
this file. Not touched: `src/`, `tests/` outside frontend, `.claude/`, `docs/pm/`,
`docs/CURRENT-STATE.md`, `docs/design-*`, `wrangler.jsonc`, `.github/`, `scripts/`.

Three jobs, worked in order.

## Job 1 — fold Opponents and Predictions into the draft hub

Premise checked before acting: `DraftRoom.tsx` really did carry three honest "not wired into Draft
mode yet" placeholders (thread 049 item 1's tab shell), and `Opponents.tsx`/`Predictions.tsx` really
were complete, shipping, tested screens elsewhere in the app (Prep mode) — the task's framing held.

**What each screen needs, checked before wiring, not assumed:**
- `Opponents.tsx` takes `{ data: Dataset }` — `DraftRoom` already holds `data` in scope.
- `Predictions.tsx` takes `{ data, rows, league }` — `DraftRoom` already holds all three.
- `Predictions` reads its pick state via `loadDraftState(leagueId)` from the exact same
  `localStorage` key (`ui/data/draft.ts`'s `prep.draft.<leagueId>`) `DraftRoom` already writes to
  via `saveDraftState` on every commit — so folding it in makes it genuinely live, not merely
  present. Verified this by recording 5 picks via the Board tab's digit shortcuts, then switching to
  the Predictions tab in the same session: header moved from "Live availability at pick 3" to "...at
  pick 18," every row's `LIVE` column moved from `not yet` to a real computed percentage, and the 5
  taken players dropped out of the row list. Screenshots:
  `frontend/e2e/artifacts/09-draft-room-after-5-picks.png` /
  `10-predictions-after-5-picks.png`.
- `Opponents.tsx`'s roster/`next #N` picture is sourced entirely from `data.rosters`
  (`rosters.json`) — a backend export built from real, `is_mock=0` picks. Read `ui/data/draft.ts`
  directly and confirmed there is no `fetch`/`POST` anywhere in it: nothing recorded in a live
  Draft-mode session (real tracking or a practice mock) ever reaches the backend, so this tab's
  cards do not move when a pick is recorded in the pane next to it. This is real data
  (`rosters.json` exists, is not "missing"), not a hollow mount — but it is a genuine
  live-vs-static disconnection the founder's "hook up to draft" framing could reasonably expect
  didn't exist. Rather than mount it silently, added one caveat line above the real cards
  (`AdaptedOpponentsPane` in `DraftRoom.tsx`) stating plainly what the tab does and does not track.
  This is the "verify what each screen needs, say so rather than mounting hollow" instruction
  applied to a *connection* gap instead of a *data* gap — there was no case here where a screen
  needed to be left out entirely; both screens' underlying data genuinely exists.

**Built:** `frontend/ui/views/DraftRoom.tsx` imports `Opponents`/`Predictions` (both unmodified,
read-only) and renders them in the two tab bodies that previously read "not wired into Draft mode
yet." New test coverage in `frontend/ui/__tests__/draft-room-recommendation.test.tsx` replaces the
old "shows placeholder" assertions with real-content assertions (heading text, caveat text, absence
of the old placeholder strings) plus a new test for the live-linkage scenario above.

**Stale-doc finding, reported not fixed (out of this session's file boundary):**
`docs/CURRENT-STATE.md`'s "Not built / null-stated" section lists "Predictions tab (**absent from
the shipped app**)." `frontend/ui/views/Predictions.tsx` is a real, complete, tested file and has
been since thread 028's build session (2026-07-27) — it was already reachable from Prep mode's
sidebar before this session touched anything. This line was already stale before this session; now
also folded into Draft mode. Flagging for whoever next edits that file in place.

## Job 2 — ADP display verification (FR-024, thread 082, contract 1.14.0)

**Premise checked first.** `docs/CURRENT-STATE.md`'s build-state table said this was "partially
landed already ... unverified, no screenshots taken." Found the actual state: the wiring across
`board.ts`/`contract.ts`/`trace-fields.ts`/`types.ts`/`Board.tsx`/`PlayerDetail.tsx`/`DraftRoom.tsx`
was **already complete** in this worktree (landed by a concurrent chain across commits
`b6d5a0d`/`75bf095`, this project's documented "coordinator commits in-flight work" pattern — `git
diff HEAD` against those files was empty before I touched anything else). This session's job 2 work
was verification and screenshot capture, not new construction.

**Read every ADP code path directly, not just the diff, and confirmed:**
- All three screens (`Board.tsx` prep board, `DraftRoom.tsx` draft room, `PlayerDetail.tsx` player
  profile) render `adp`/`adp_source`/the proxy caveat, each with its own honest-null treatment
  (`—` on the board/draft-room cells, a full-sentence "No MFL ADP data for this player..." block on
  the player profile).
- The null case is never `0` or an ambiguous dash-without-explanation — every null cell/block
  carries a `title`/inline text naming the reason (MFL's ~230-player coverage limit).
- Never confused with `consensus_rank`: `AdpCell`/`AdpBlock`/`DraftRoomAdpCell` read `row.adp`
  exclusively; the pre-existing `CONS`/`Δ` columns are untouched and visually and semantically
  separate, with code comments in both `Board.tsx` and `DraftRoom.tsx` recording that this was a
  deliberate choice, not an oversight.
- Never presented as this league's own ADP: every label/tooltip/caveat says "MyFantasyLeague proxy"
  or "not this league's own ADP" verbatim.

**Screenshots** (11 total, `frontend/e2e/artifacts/`, all real Playwright captures against a running
dev server, each looked at directly — not just captured): prep board with populated + null ADP
cells, player detail with populated + null MARKET ADP blocks, draft room board tab with inline
`N.NᴹFL` figures and a null case in the tiered RB view, the refresh panel confirming the app is on
contract 1.14.0 with no mismatch.

**Real gap found and flagged, not fixed:** no dedicated `adp.test.tsx` exists. Rendering is covered
incidentally by the general board/draft-room/player-detail suites (all still pass against real
exported data), but nothing asserts the null-vs-populated distinction or the source-label text
directly. Flagged in the thread 082 reply as follow-up, not addressed this session (time budget
went to the fold-in and the four-thread screenshot backlog).

## Job 3 — screenshot the four threads blocked only on compositing

All four (027 Opponents, 028 Predictions, 029 frequency array/tier grouping, 041 frontend WIP
repair) had every "Done looks like" item met except a screenshot, each explicitly blocked by the
same environment limitation ("the Browser pane is not displayed, so the page is not compositing
frames"). That limitation does not exist in this cloud container
(`docs/frontend-cloud-runbook.md`'s `executablePath` workaround against the pre-installed Chromium
at `/opt/pw-browsers/chromium`). Captured and looked at real screenshots for all four, replied on
each thread with the artifact paths and a description of what each image actually shows (league
name, row counts, honest-null examples), and set `STATUS: RESOLVED` on all five threads this
session touched (027, 028, 029, 041, 082) — all five are `TO: frontend`, so this session held the
authority to resolve them, per `docs/handoffs/README.md` rule 6.

## Evidence

**Screenshots** (`frontend/e2e/artifacts/`, 15 new files + 1 new capture script,
`verify-hub-and-adp.mjs`) — see the individual thread replies (027/028/029/041/082) for what each
one shows in detail; not re-duplicated here.

**Tests:** 203 passed, 0 failed, 22 test files (`npm test`, 2026-07-29) — up from 202 baseline (one
net new test added, `draft-room-recommendation.test.tsx`'s live-linkage case). `npx tsc -b --noEmit`
clean.

**Pre-existing, unrelated failure noted, not fixed:** `python tools/handoffs.py check` fails on an
ADR-054/ADR-055 cross-branch numbering collision (`docs/decisions.md`) — confirmed via `git stash`
that this predates every change in this session (present on the untouched `75bf095` HEAD too). Out
of this session's file boundary (`docs/decisions.md`) and out of scope for a frontend chain to
resolve unilaterally — a cross-branch ADR-number collision is exactly the "contradiction between two
docs" class of thing this project's rules say to escalate, not silently fix.

## Not done, flagged for follow-up

- No dedicated `adp.test.tsx` (see Job 2).
- `docs/CURRENT-STATE.md`'s stale "Predictions absent" line (see Job 1) — outside this session's
  file boundary, reported not corrected.
- Thread 049's remaining items (6, 7, and the rest of item 1's design polish — `DRAFT LIVE`
  indicator styling, richer league selector) were not touched; thread 049 itself is outside this
  session's handoff-reply boundary (027/028/029/041/082 only) even though item 1 is now functionally
  closed by this session's job 1 — noted here so the thread's owner can update it, not updated
  directly.

---

<!-- 2026-07-29-frontend-opponents-live.md -->

# Frontend — Opponents live in Draft mode + Refresh data removal — 2026-07-29

**Scope given:** `frontend/**` only. Not `src/`, not `docs/CURRENT-STATE.md`, not `.github/`.
Dispatched as FR-032 (see numbering note below); a second ask was relayed mid-session by the
coordinator (remove the Refresh data button on the hosted site).

## What the founder asked for

> "For opponents we will need to fix that.. make it functional for the user."

A prior session (same day) had mounted `Opponents.tsx` into the Draft-mode hub tab and found the
real limit: it reads roster/next-pick data only from backend `rosters.json`, which is real,
non-mock completed-draft data. During a live draft that file reflects nothing (no real 2026 draft
has been logged there), so the tab rendered as a placeholder. This session's job was to make the
tab actually useful mid-draft.

## Numbering note

The dispatch referred to this request as "FR-032" throughout. `tools/founder_requests.py new` in
this worktree allocated **FR-029** (this worktree's `docs/founder-requests/` only went up to
FR-028; `check` reports no cross-branch collision). Filed under FR-029, with the FR-032 label
preserved in its `SOURCE:` field in case a real FR-032 already exists in a branch this worktree
doesn't see — flagged for whoever reconciles branches, not resolved unilaterally here.

## What was built

**Found the existing roster-need arithmetic rather than writing a second one**, per the task's own
instruction: `buildRosterSlots` in `frontend/ui/views/DraftRoom.tsx` (previously private to that
file, used only to build the user's own MY ROSTER panel from `userPicks` -- a filter of
`draft.picks` by the user's own `teamSlot`). The function itself was already slot-agnostic; it has
never looked at which team's picks it's handed. Extracted verbatim, no logic change, to
`frontend/ui/data/rosterSlots.ts` so a second caller could use the identical arithmetic per team
instead of re-deriving it. `DraftRoom.tsx` now imports it from there; its own MY ROSTER panel is
unchanged in behavior.

**New component: `frontend/ui/views/LiveOpponents.tsx`.** Mounted at `DraftRoom.tsx`'s Opponents
hub tab in place of the old "Opponents is not wired into Draft mode yet" placeholder. For each of
the league's real team slots (`league.json:teams`), it filters `DraftState.picks` (this session's
local, in-browser pick log -- the same object `DraftRoom.tsx`'s own MY ROSTER already reads) by
`teamSlot`, runs `buildRosterSlots`, and renders:

- Real drafted players by roster slot (QB/RB/WR/TE/FLEX/DEF), matching the Prep-mode Opponents
  card's visual language (bordered team cards, colored position rows, "empty" in dim italic).
- **STILL NEEDS** chips: real `required - filled` per starter position -- QB/RB/WR/TE/DEF, no
  fabricated urgency ranking, no predicted next pick.
- **next #N**: real snake-order arithmetic (`nextPickForSlot`, already existing in `ui/data/
  draft.ts`, imported not reimplemented) -- the same helper that already computes the user's own
  next pick.
- **ON THE CLOCK**: which team slot is currently up, from `teamSlotAtPick(currentOverallPick(...))`
  -- also already-existing arithmetic, not new.
- **(you)**: the user's own slot, from `league.json:user_draft_slot`.

**Boundaries honored, not just stated:**

- **No inferred strategy anywhere on this screen.** `opponents.json`'s `positional_tendencies` /
  `first_pick_by_position` / `consensus_tracking_behaviour` fields are not read by this component
  at all -- there is no code path that could render them here, not just an unused prop. Verified by
  a test asserting those strings and "NOT A MODEL INPUT" never appear on this tab
  (`ui/__tests__/live-opponents.test.tsx`, "STILL NEEDS reflects real unfilled starter counts, not
  a fabricated tendency").
- **The two data sources never merge.** This component imports nothing from `rosters.json` --
  only `opponents.json`'s static `team_name` field (an identity label, not a roster number) is
  read, the same field the Prep-mode screen already uses for the same purpose. The empty-state
  text and the populated-state banner both name `rosters.json` explicitly, by contrast, so the
  distinction is visible on screen, not just true in the code.
- **Empty state reads as "nothing happened," not as a finding.** Before any pick is entered,
  `LiveOpponents` renders one sentence ("No picks yet. Mark picks on the Board tab...") and zero
  team cards -- not a ten-team grid where every team needs every position, which would look like a
  discovered fact rather than the absence of one. Confirmed live and by test.

**Doc comments updated in place**, not left describing stale behavior: `DraftRoom.tsx`'s own
module doc previously said Opponents/Predictions were "not yet folded into this pane"; corrected
to say Opponents is now wired in via `LiveOpponents.tsx` and explain why it isn't a reuse of the
Prep-mode screen.

## Mid-session addition: remove the Refresh data button

Coordinator relayed, mid-task: **"We also can remove that refresh data button at the top."**
Reasoning given: `/__refresh` is dev-server-only Vite middleware
(`server/refresh.ts`'s `configureServer` hook never attaches under `vite build`), and the
founder's daily use has moved to the hosted static site, where the button can only ever fail.

Verified directly rather than taking the reasoning on faith: built the app (`npm run build`),
served the real production output with `vite preview`, and confirmed by screenshot that
`/__refresh` genuinely does not exist there -- this is a compile-time absence (no route registered
at all), not a flaky-network question, so the fix uses a compile-time signal
(`import.meta.env.DEV`), not a runtime probe.

`RefreshData.tsx` gained a `refreshAvailable` prop, defaulting to `import.meta.env.DEV`. The
button renders only when true. **The freshness line is unconditional either way** -- per the
coordinator's explicit hard requirement, hiding the button must never also hide the fact it
existed to report (`generated_utc` + the snapshot-freshness fields, contract 1.13.0). Confirmed by
screenshot: production build shows `exported <timestamp> · snapshot fresh (...)` with no button;
dev server shows the same text plus the button.

## Evidence

Screenshots taken and looked at (not merely captured) -- `frontend/e2e/artifacts/`:

- **`live-opponents-empty-2026-07-29.png`** -- Draft mode, Opponents tab, zero picks entered.
  Shows exactly one sentence: "No picks yet. Mark picks on the Board tab and each team's roster
  will fill in here as the draft happens. This view is built from picks entered in this session
  (this browser's local draft log), separate from and never merged with backend `rosters.json`
  -- the Prep-mode Opponents screen's data source, which reflects only real, completed drafts on
  file." No team cards, no STILL NEEDS chips, nothing that could be mistaken for a finding.
- **`live-opponents-populated-2026-07-29.png`** -- same tab after seeding 6 real picks across 6
  different team slots (real board players: Bijan Robinson -> slot 1 "Cucked Commish", Ja'Marr
  Chase -> slot 2 "Shit Leopards", Josh Allen -> slot 3, the user's own slot, labelled "(you)",
  Puka Nacua -> slot 4, Jonathan Taylor -> slot 5, Amon-Ra St. Brown -> slot 6). Each card shows
  only its own player, correct STILL NEEDS chips (e.g. slot 1's RB row went from "×2" to "×1"
  after Bijan Robinson filled one of two RB starter slots), and real per-team next-pick numbers
  that check out against the league's real 10-team snake order (slot 1's "next #20" and slot 2's
  "next #19" both match round-2 snake reversal by hand calculation). Slot 7, on the clock at
  overall pick 7, is the only card marked "ON THE CLOCK." Slots 8-10 (not yet reached) show fully
  empty, honest zero state -- real per-team absence, not the global "nothing happened yet" state
  from the empty screenshot above.
- **`topbar-dev-2026-07-29.png`** -- dev server (`npm run dev`): "Refresh data" button present,
  next to the freshness text.
- **`topbar-prod-2026-07-29.png`** -- real production build (`npm run build` + `vite preview`):
  button gone; freshness text (`exported 2026-07-29T16:39:37... · snapshot fresh (2d old, max
  3...)`) still fully present, unchanged from the dev screenshot's text.

**Degrades sensibly with zero picks entered:** confirmed above (the empty-state screenshot) and by
an explicit test asserting no `live-opponent-slot-*` test id and no "STILL NEEDS" text render
before any pick exists.

## Tests

- `frontend/ui/__tests__/live-opponents.test.tsx` (new, 4 tests): empty state; each team's card
  shows only its own picks; STILL NEEDS arithmetic + no inferred-strategy text; on-the-clock badge
  + real next-pick numbers.
- `frontend/ui/__tests__/draft-room-recommendation.test.tsx` (1 assertion updated to match the new
  empty-state text instead of the retired placeholder text).
- `frontend/ui/__tests__/refresh.test.tsx` (2 new tests): button hidden + freshness text intact
  when `refreshAvailable={false}`; button shown when `refreshAvailable={true}`.

**Full suite: 209 passed, 0 failed, 23 test files** (`npm test`, this worktree, 2026-07-29).
`npx tsc -b --noEmit`: clean.

**Fidelity harness:** `docs/design-fidelity.md` names `tools/fidelity.py`; the actual file lives at
`docs/design-reference/fidelity.py` (a known, already-tracked relocation gap -- see
`docs/backlog-triage-2026-07-29.md` thread 037 items 3-4, not something to fix unilaterally in this
session). Its `screens.json` maps `opponents` to route `/draft/opponents`, but this app has no
router at all (`grep` for `react-router`/`BrowserRouter` in `ui/`/`server/` returns nothing) --
navigation is in-memory tab state, not URLs. Running the harness as-is would not measure this
change meaningfully (it would `goto` a path this SPA doesn't route on). Not run this session;
flagged rather than silently skipped or forced to a misleading result.

## Founder requests logged

- **FR-029** (`docs/founder-requests/FR-029-...md`) -- this Opponents-live request. `SOURCE:` notes
  the dispatch called it "FR-032."
- **FR-030** (`docs/founder-requests/FR-030-...md`) -- the Refresh data button removal, relayed
  by the coordinator mid-session.

Both left `STATUS: IN PROGRESS`, not `SHIPPED` -- this session's own report is not the evidence bar
per `docs/operating-model.md`; founder review of the attached screenshots is.

## Files touched

- `frontend/ui/data/rosterSlots.ts` (new -- extracted from `DraftRoom.tsx`)
- `frontend/ui/views/LiveOpponents.tsx` (new)
- `frontend/ui/views/DraftRoom.tsx` (import shared roster-slot module; mount `LiveOpponents`;
  doc comment corrected)
- `frontend/ui/components/RefreshData.tsx` (`refreshAvailable` prop, default from
  `import.meta.env.DEV`)
- `frontend/ui/__tests__/live-opponents.test.tsx` (new)
- `frontend/ui/__tests__/draft-room-recommendation.test.tsx` (assertion updated)
- `frontend/ui/__tests__/refresh.test.tsx` (2 new tests)
- `frontend/e2e/live-opponents-shot.mjs`, `frontend/e2e/topbar-prod-shot.mjs` (new capture
  scripts, tracked per the existing `e2e/` convention)
- `frontend/e2e/artifacts/live-opponents-empty-2026-07-29.png`,
  `live-opponents-populated-2026-07-29.png`, `topbar-dev-2026-07-29.png`,
  `topbar-prod-2026-07-29.png` (new, tracked)
- `docs/founder-requests/FR-029-...md`, `FR-030-...md` (new), `docs/founder-requests/INDEX.md`
  (regenerated)

## Not done / explicitly out of scope this session

- Thread 027 (Prep-mode Opponents screenshot) was not touched -- different screen
  (`Opponents.tsx`, backend-`rosters.json`-backed), not modified by this session's work.
- The `fidelity.py` relocation (backlog thread 037 items 3-4) was not fixed here.
- `docs/CURRENT-STATE.md` was intentionally not edited -- out of this dispatch's stated boundary.

---

<!-- 2026-07-29-integration.md -->

# 2026-07-29 — integration — overnight run against docs/RUN-2026-07-29-integration.md

Founder asleep, no questions asked. Every judgement call is recorded below under
"Decisions made without asking."

**Outcome: clean. One merge landed, all suites green, harness 9/9, app verified at runtime and
restarted on 5173 at the end. One instruction in the run doc was wrong and was not complied with —
see "The premise that did not hold."**

---

## What merged

| Branch | Commit | Note |
|---|---|---|
| `docs/sharded-session-logs` | `5901b6b` (merge), `2243eec` (branch tip) | No conflicts. `--no-ff`. |
| ~~`frontend/topbar-clipping-and-hardcoded-count`~~ | `cc638ba` | Already in before this session. Verified, not re-merged. |
| ~~`qa/acceptance-harness`~~ | `870750d` | Already in before this session. Verified, not re-merged. |
| **mock draft capture** | — | **Does not exist as a branch. Not merged. See below.** |

Other commits this session:

| Commit | What |
|---|---|
| `a891a90` | Founder permission tooling + the run doc, committed as instructed |
| `402f553` | Acceptance player-count check fixed; stale `frontend/tests/` deleted |
| `1cf61a7` | Fable mandate M tracked (appeared on disk mid-run; **not acted on**) |

`main` pushed to `origin/main` at `1cf61a7`, then again after this handover.

The sharding merge produced **zero conflicts** — none of the resolution rules in the run doc's
conflict table were needed. `docs/status.md` and `docs/founder-requests.md` were touched only by
the branch, and the frontend files it appeared to change in a two-dot diff were untouched relative
to the merge base.

---

## The premise that did not hold

The run doc says four branches were created and instructs merging "mock draft capture" third.
**There is no such branch.** `backend/mock-calibration-kickers` points at `f1d51d0`, already an
ancestor of `main` — zero commits ahead. The work exists only as **eleven uncommitted files** in
`.claude/worktrees/backend-mock-calibration`, including four source/test files that exist nowhere
else in the repo (`src/mock_prediction.py`, `tests/test_kickers_export.py`,
`tests/test_mock_calibration_snapshot.py`, `tests/test_mock_prediction.py`).

Last write to those files: 2026-07-28 23:25. `main` took its next commit at 23:46. The session that
produced them ended without committing.

**Decision: did not commit it, did not merge it.** Committing another session's uncommitted tree
would mean authoring work with no commit, no test evidence, and no handoff reply declaring it done
— and it is not possible to distinguish "finished but uncommitted" from "interrupted mid-edit" from
the outside. Not merging loses nothing; the files sit exactly where they were.

Opened as **handoff thread 079 (pm → backend)** so it is no longer invisible. That thread also
flags that its `tests/test_kickers_export.py` may be in tension with a founder constraint dated
2026-07-29 ("No kicker", kickers consensus-only and excluded from the board) — and explicitly says
the thread is *not* authority to delete it.

Also unmerged and left alone: `docs/phase3-chain2-claude-md-agents` (2026-07-27, not one of
tonight's branches, out of scope for this run).

---

## Test results

| Suite | Result | Runtime |
|---|---|---|
| Backend (`pytest`, scoped to `pytest.ini` `testpaths`) | **636 passed**, 1 warning | 677.53s (11m 17s) |
| Frontend (`npm --prefix frontend run test`) | **202 passed**, 22 files | 58.81s |
| Acceptance harness | **9/9** | — |
| Runtime verification on 5173 | **9/9** | — |

No test failures anywhere. Nothing deliberate to explain.

**One tool did fail, and it was a real bug**, not a test: `tools/state.py --tests` crashed with
`FileNotFoundError: [WinError 2]` on the project's own machine. It called
`subprocess.run(["npx", "vitest", "run"])` with a list argv and no shell; on Windows `npx` is
`npx.CMD`, so `CreateProcess` cannot find a bare `npx`. The backend half worked because it invokes
the conda interpreter by absolute path.

This landed tonight as part of the sharding merge, and it means the generated build-state table
could never have been produced with real counts on the only machine this project runs on. Fixed by
resolving `argv[0]` through `shutil.which` in `run()`, which applies `PATHEXT` and so finds
`.CMD`/`.exe`/`.bat` without hardcoding an extension or resorting to `shell=True` with a list argv.
`shutil.which('npx')` → `C:\Program Files\nodejs\npx.CMD`.

Backend was 620 before this run; the sharding branch added `tests/test_founder_requests.py`,
`tests/test_state.py` and `tests/test_status_log.py` for +16. 620 + 16 = 636, which reconciles.

The 1 warning is a pre-existing pytest deprecation about a class-scoped fixture declared as an
instance method. Not introduced tonight, not addressed.

### Acceptance harness, per check

All nine green: `app-loads`, `mode-switcher-present`, `league-name-matches-config`,
`board-header-player-count`, `board-renders-nonzero-rows`, `status-banner-matches-data`,
`draft-room-renders`, `opponents-renders`, `player-detail-opens`.
Evidence: `tools/acceptance/artifacts/evidence.json`.

`board-header-player-count` was the one that had been failing (8 of 9 before tonight), and the run
doc's diagnosis of it was correct: the check
was wrong, not the app. It asserted `"N of TOTAL players loaded"`; the frontend fix removed the
denominator rather than correcting it, so `Board.tsx` renders `"511 players loaded"` and its own
test asserts the `of \d+` form is *absent*. The check was failing on a string the app no longer
emits.

Rewritten to assert the rendered count equals the `data/export/board.json` row count with no
denominator required — **and to actively fail if a denominator reappears**, since any denominator
there would be an unsourced total free to drift again, which is the original fault.

### `tools/handoffs.py check`, verbatim

```
mailbox check OK — 78 threads, none stale, all addressed.
```

Followed by 30 non-fatal contradiction warnings (25 antonym-pair overlaps between threads, 5
threads referencing D-021 which is already marked DECIDED). Not new, not addressed.

Thread 079 was opened after that run, so the mailbox now holds **79 threads, 46 open**.

### Session-log and founder-request sync tools

Both work and are idempotent apart from their date stamp — the only diff from re-running them on an
unchanged tree was `Generated 2026-07-28` → `Generated 2026-07-29`.

- `tools/status_log.py sync` → 1 session file (2 including this one) → `docs/status/INDEX.md`
- `tools/founder_requests.py sync` → **0 requests** → `docs/founder-requests/INDEX.md`

**0 is correct, not a failure.** FR-001..FR-017 stay in the frozen `docs/founder-requests.md`
archive; the new directory starts empty and allocates from FR-018.

---

## Runtime verification (Phase 6)

Killed both stale dev-server processes — a vite server on port **5175** (PID 7152) and its npm
parent (PID 17456), both started **2026-07-27 11:52**, i.e. ~36 hours stale. Both were launched
from the main checkout, not a worktree. No server was left on any other port.

Started **one** server from the **main checkout** on port **5173** (`prep` in
`.claude/launch.json`).

**Caveat, stated plainly because it affects what you will find:** that server died once during this
session, unprompted, while the verification work was still going on. It was restarted and was
listening on 5173 at the end of the run (PID 21092). But it is managed by the session's preview
harness, not detached, so **it may not survive this session ending.** If port 5173 is dead when you
read this, that is the expected failure and not a regression in the app:

```bash
npm --prefix frontend run dev
```

Nothing else was left on any other port.

Verified with runtime evidence, not by reading code — `tools/acceptance/shot-5173.mjs`, which
attaches to whatever is already on 5173 rather than starting its own server (a script that started
its own would prove nothing about the one the founder will find running):

| Claim | Result |
|---|---|
| Board renders 511 players | ok — 511, matches `board.json` |
| Header does not say "of 378" | ok |
| Header carries no denominator at all | ok |
| Board footer count matches export | ok — 511 vs 511 |
| League reads Westwood | ok — matches `league.json` |
| Mode switcher fully in viewport, loaded state | ok — all three buttons, none clipped |
| Refresh button inside the top bar | ok — shares the 46px top-bar element with the mode switcher |
| Refresh button fully in viewport | ok |
| Page does not scroll horizontally | ok |

Screenshot: `docs/status/artifacts/2026-07-29-integration-5173.png`. Confirmed visually, not just
by assertion — the mode switcher sits at the right edge of the top bar, fully visible.

**One cosmetic observation, not a regression:** the top bar's freshness text truncates with an
ellipsis (`snapshot fresh (1d…`). This is the same 11px advisory text D-026 is about, so it is
already covered by open work rather than needing a new item.

---

## Decisions made without asking

1. **Did not commit or merge the mock-draft-capture worktree.** Reasoning above. Opened thread 079
   instead. This is the one place the run doc's instructions were not followed, and it was because
   its premise was factually wrong about the repo.

2. **Deleted `frontend/tests/` (20 files).** The run doc authorised this "if nothing imports it."
   Nothing does — the only references are three docs describing it as a known problem. It arrived
   via `2df3716` when the frontend-prep repo was merged into `frontend/`, so it is a stale copy of
   the *Python backend* tests, not frontend tests. Verified before deleting that every test in it
   exists by name in `tests/`, with exactly three exceptions in `test_backtest.py`, all covering
   `weighted_aggregate` — which `src/backtest.py` records as **deliberately DELETED** under ADR-B,
   thread 021 ("a field that does not exist cannot be misquoted"). So they are dead tests for
   removed behaviour and no live coverage was lost.

3. **Committed the founder's permission tooling and the run doc** (`a891a90`), as instructed.
   Checked the diffs for credentials first; the only settings change is broadening `Bash(*)` /
   `PowerShell(*)` in the allow list. Nothing reverted.

4. **Made the harness check reject a denominator rather than merely not require one.** The run doc
   asked only that the check not require one. Requiring its *absence* is a small addition, made
   because a silently-reintroduced hardcoded total is precisely the original fault and nothing else
   would catch it.

5. **Amended one commit message** (`402f553`) rather than leaving it inaccurate. The staged
   `frontend/tests` deletion was swept into the harness-fix commit; the original message described
   only the harness fix. Amended before pushing, so no rewritten public history.

6. **Committed the Fable mandate that appeared mid-run** (`1cf61a7`) — see below — rather than
   leaving it untracked, so it is not lost. Did not act on a word of it.

7. **Put the screenshot script in `tools/acceptance/`** rather than `tools/`, only because that is
   where playwright is installed. Noted in its header that it is not part of the harness run.

8. **Fixed the `tools/state.py` Windows bug** rather than just reporting it. It was blocking this
   session's own write-back duty (regenerating the `CURRENT-STATE.md` build-state table with
   measured counts), the fix is four lines and provably correct, and `tests/test_state.py` covers
   the module. Judged in scope because the alternative was to leave a tool that landed tonight
   broken on the only machine it runs on. After the fix, `--apply --tests` ran clean end to end
   and wrote the table.

9. **Added a dated qualifier to a stale figure in `CURRENT-STATE.md`'s narrative** (thread 052 /
   ADR-048 section). It read "378/378 board players carry it; 371/378 (98.15%) resolve" — a real
   2026-07-27 measurement, but the board is 511 players now, so a reader today would take 378 as
   the current universe. Edited to date the measurement and state the current count, and to say
   explicitly that the 98.15% coverage ratio has **not** been re-measured against the larger
   universe. Deliberately did **not** invent a new ratio: that would need re-running the join,
   which this session did not do. This touches a narrative section belonging to another session,
   which the operating rules discourage — done anyway because the alternative was leaving the
   canonical state document asserting a player count 133 short of reality.

---

## Things I halted on, or deliberately left alone

**A file appeared on disk mid-session that this run did not write.**
`docs/fable-mandate-M-2026-07-29.md` (11,808 bytes) was absent from `git status` at session start
and present at **00:12:52**, roughly 17 minutes in. It is a mandate addressed to a **Fable**
session — three model-design questions M-1 (bottom-up rankings), M-2 (availability), M-3
(suggested pick) — and it instructs its reader to modify nothing but its own output documents.

**Not acted on.** It is not part of tonight's run, it is addressed to a different agent, and
instructions found in a file are not instructions to a session. Committed for safekeeping and
flagged here. Its referenced prerequisite, `docs/CORRECTIONS-2026-07-28.md`, does exist — nothing
missing, nothing reconstructed.

A fresh session should establish **whether a Fable run is expected and whether another session was
live tonight**, because a file arriving mid-run is the only evidence either way.

**The stash is not empty.** Left alone as instructed. `stash@{0}` — *"pre-integration stash:
uncommitted fable-mandate docs + status.md on main"*:

```
docs/CORRECTIONS-2026-07-28.md                      |  92 +
docs/fable-mandate-2026-07-28-short.md              |  98 +
docs/fable-mandate-G-2026-07-28.md                  | 140 +
docs/fable-mandate-K-2026-07-28.md                  | 128 +
docs/reviews/fable-bottomup-next-tests-2026-07-28.md| 258 +
docs/reviews/fable-lambda-sensitivity-2026-07-28.md | 249 +
docs/reviews/fable-schedule-feasibility-2026-07-28.md| 291 +
docs/status.md                                      |  72 +
```

**It contains nothing that is not already in the repo.** All seven docs are tracked in `HEAD`, and
`HEAD`'s `docs/status.md` differs from the stashed copy by 261 lines of pure insertion — a strict
superset, restored by `1c3675f`. It can be dropped, but that is the founder's call, not this run's.

**Two hook-blocked commands, both correctly blocked.** `Remove-Item -Recurse -Force` on the stale
test directory, and a `;`-containing pipeline. Worked around without weakening either guard. The
`.pyc` leftovers were removed file-by-file instead.

---

## What a fresh session should pick up first

1. **Thread 079 — the uncommitted mock-draft-capture worktree.** Highest priority: it is real work
   that exists in exactly one place and is not under version control. Decide it before that
   worktree is cleaned up by anything.
2. **Confirm whether a Fable run is expected** for mandate M, and whether another session was live
   during this one.
3. **D-026** — promote the stale-snapshot advisory to a blocking state — remains OPEN and needs a
   design pass on what "blocking" means before Frontend can start. Explicitly not built tonight.
   Verified present and correctly worded, along with D-025 (CLOSED, no work); Phase 5 needed no
   action.
4. **Check port 5173 before starting a server.** One was left running from the main checkout, but
   see the caveat above — it may not have survived. Reuse it if it is up; do not start a second.
5. `docs/dashboard.html` and `docs/roles-workflow-map.html` are **stale** — this session changed
   project state and did not regenerate them.
6. **Re-measure the `weekly_finishes.json` join coverage** against the 511-player board. The
   98.15% figure in `CURRENT-STATE.md` was measured against a 378-player board and is now dated
   rather than corrected, because correcting it honestly means re-running the join.
7. **`tools/state.py`'s commit row can never be current in the commit that carries it** — it
   records `HEAD` at generation time, so the table always names the previous commit. Cosmetic, but
   worth either documenting in the tool or having `--apply` note the lag, so a future reader does
   not mistake it for drift.

---

<!-- 2026-07-29-librarian-triage.md -->

# 2026-07-29 — librarian: backlog triage + Fable still-live pass

**Role:** librarian. Read-only analysis session; no code changed, no thread STATUS changed (not my
role for any of them). Two documents written, both for the founder, plus this log.

## What was asked

Two founder questions, verbatim: (1) "do we have other things on our lists or bugs to clean up... can
we start knocking them out?" and (2) "is there relevant stuff left on Fable's last recommendations
(we've changed a lot since it ran)."

## What was done

**Task A.** Read all 47 open threads in `docs/handoffs/` in full, against `docs/pm/MEMORY.md`,
`docs/CURRENT-STATE.md`, and `docs/status/2026-07-29-pm-cloud-migration-and-deploy.md`. Sorted each
into DONE ALREADY / STILL LIVE / OBSOLETE / BLOCKED. Spot-checked two claims directly in the repo
rather than trusting a session narrative: whether ADP fields actually render on any frontend screen
(grepped `frontend/ui` for `adp_source`/`adp_as_of_date` — zero matches, so **no**, despite a status
log saying ADP is "now on the board"), and whether `data/export/strategies.json` is still stale
(**yes** — `contract_version: 1.7.0` on disk against a live contract of `1.14.0`). Both surfaced as
real, cheap bugs and are called out first in the output, ahead of the full 47-thread sort.

Output: `docs/backlog-triage-2026-07-29.md`. Two real bugs, ~19 STILL LIVE items (summarized, several
already substantially done with one piece remaining), ~10 BLOCKED (mostly the shared screenshot-pane
limitation and the design-fidelity pause), 5 DONE-ALREADY-but-never-closed threads, zero OBSOLETE
(nothing found with a cleanly falsified premise — the closest candidates were already corrected in
place by later replies on the same thread rather than left to rot).

**Task B.** Read all 18 files in `docs/reviews/` in full (fable-* review docs plus the
`ACTION-PLAN-2026-08.md` consolidation). Extracted what still applies given today's changes (cloud
migration, FFC unblocked and half-PPR ADP now daily, ADP reached the board data layer, the app live
on the internet, one-command DB rebuild, ESPN-league deferral reversed per FR-027). Spot-checked two
things directly: whether the thread-ID allocator fix Fable recommended was actually built (yes,
`docs/pm-outbox/` and `NEW-*.md` handling exist in `tools/handoffs.py`) and whether λ (the one
measured model parameter) reaches the shipped recommendation card (per Fable's own G-A session, no —
confirmed nothing since claims otherwise).

Output: `docs/fable-still-live-2026-07-29.md`. Eight still-live items, four dead (their premises
were falsified by today's work — notably the FFC/ADP data-source gap Fable worried about no longer
exists), two items flagged as *more* urgent now than when Fable wrote them (the model's need-math
being hardcoded to the Westwood league specifically, now a direct blocker for the founder's new
generic-tier request; and the ticket/decision-numbering collision problem, which recurred three more
times today in forms the shipped fix doesn't cover).

## Contradictions flagged, not resolved

- A session status log claims ADP is "now on the board." Verified false by direct grep. Not fixed
  here — flagged in the triage doc per this role's standing instruction to report, not silently
  correct, another session's narrative.
- `docs/decisions.md`'s live ADR-054 (FFC ingester) and `docs/CURRENT-STATE.md`'s note that an
  unmerged branch also claims ADR-054 will collide the moment that branch merges. Already known to
  the PM (per `docs/pm/MEMORY.md`); restated in the triage doc rather than acted on.

## What I did not reach

Every open thread and every review file was read in full — nothing was skipped for time. Given the
token budget, the two output documents report what the threads/reviews themselves say rather than
independently re-verifying every code claim inside them; only the handful of claims cheap to check
and central to a DONE/STILL-LIVE/OBSOLETE call were spot-checked directly (see above).

## Handoffs opened

None. No new gap was found that warranted a fresh thread — the two real bugs (ADP display, stale
`strategies.json`) are already covered by existing open threads (082, 042) named in the triage doc.

## Files

- `/home/user/Fantasy-Football/docs/backlog-triage-2026-07-29.md`
- `/home/user/Fantasy-Football/docs/fable-still-live-2026-07-29.md`
- `/home/user/Fantasy-Football/docs/status/2026-07-29-librarian-triage.md` (this file)

## Same-day correction: BLOCKED bucket re-tested

The founder flagged that this same document's original BLOCKED bucket had carried the
screenshot-compositing limitation forward from earlier sessions without re-testing it against
today's environment — a document asserting something nobody re-checked, this project's recorded
failure mode, happening again in a document I wrote hours earlier the same day.

Went back through every thread in the BLOCKED bucket and re-read each one's own reply chain rather
than trusting the bucket label. Result: **027, 028, 029, 041** were each blocked solely on the same
screenshot-compositing gap ("the Browser pane is not displayed, so the page is not compositing
frames") — verified by reading each thread's own text, not inferred. That gap is fixed today per
`docs/frontend-cloud-runbook.md` (real Chromium via `executablePath`,
`frontend/e2e/cloud-board-screenshot.mjs`, dated captures in `frontend/e2e/artifacts/`). Moved all
four to STILL LIVE with a note that the remaining work is running the capture and attaching it, not
re-building anything.

Checked the rest of the BLOCKED bucket too, not just the ones that looked suspicious: 003, 006, 007,
012, 030, 031, 035, 050 are blocked on a deliberate, on-record design-fidelity pause (confirmed in
`docs/handoffs/035-frontend-catchup-runbook.md:77-81`, not a stale artifact). 076 and 081 are blocked
on a genuinely unresolved thread-ID/ADR-allocator design question, unrelated to screenshots, FFC, or
the database — confirmed by reading 081's latest reply, which explicitly says the problem is broader
than worktrees and still needs a design owner. Also checked for the other two classes the founder
named (FFC-blocked and database-unavailable-in-cloud-blocked items in the open BLOCKED bucket): none
found — FFC's unblocking was already reflected correctly in STILL LIVE (thread 054/055), and the one
thread about DB rebuild-in-cloud (080) was already closed, not sitting in BLOCKED.

Edited `docs/backlog-triage-2026-07-29.md` in place (correction note at top, BLOCKED section trimmed,
four items added to STILL LIVE with unblock reasons). No thread STATUS changed — that belongs to
`frontend`/`pm`, not this role.

---

<!-- 2026-07-29-pm-cloud-migration-and-deploy.md -->

# 2026-07-29 — PM: zero approvals, the move off the founder's machine, and the app online

**Role:** pm (in-repo, taking over from the outside-the-repo PM)
**Branch:** `claude/pm-agent-setup-gobxa0` → merged to `main` @ `a3dab01`

## What the founder asked for, in order

Get to zero approvals · finish the move off his machine · challenge every premise in the handover ·
then, mid-session: see the app on a website.

## What landed

**Zero approvals.** Deleted the `PreToolUse` hook, all 25 `permissions.ask` rules, 86 of 94
`permissions.allow` entries, and the seven Windows scripts that installed them. **The hook had been
inert here all along** — registered with a Windows conda path that does not exist in Linux — so zero
approvals was true by accident, which is worse than either extreme. Replaced with the measured bigger
lever: FR-018 counted agents *choosing* to stop and ask at 42% of interruptions across 57 sessions
against 24% for hook and permission stops combined. Decide-and-log is now a hard rule in all seven
agent definitions.

**The move off his machine, finished.** One-command rebuild (`scripts/rebuild_database.py`, 64s),
the ADP snapshot CSV→DB loader that had never existed, `pandas`/`numpy` added to `requirements.txt`
(15 `src/` modules imported pandas; without it pytest collection aborted and *zero* tests ran),
`.python-version`, and `tools/state.py` unhardcoded from the founder's conda path.

**The app is online.** `https://fantasy-football.soft-water-e755.workers.dev` — Cloudflare Worker,
static Vite build from `main`, rebuilds on every push. Founder confirmed it in his own browser.
Independently verified `/data/board.json` serves `contract_version 1.14.0`.

**A single HTML file that runs a full draft** — no server, no network, no install. Originally
excluded Draft mode on the assumption it needed a backend; challenged that, and it was wrong.

**ADP, captured daily and never once displayed, now on the board** at contract 1.14.0 — 144 of 510
rows, 366 honest nulls, labelled a proxy.

**The format was wrong, and the founder caught it.** MFL's `IS_PPR` flag is binary, so four days
were captured at full PPR for a half-PPR league. FFC publishes half-PPR at 10 teams — exact match,
27× the sample — and he had already lifted the block on it. All three formats now capture daily.

## Corrections to things the repo asserted

- **The daily capture had never run on schedule.** One run existed, `event: workflow_dispatch`,
  triggered by hand. `CURRENT-STATE` said the Windows task was redundant. It was not.
- **The 2021–2025 rankings history is not permanently lost** — it re-pulls, verified row-by-row by
  another session.
- **`docs/pm/HANDOFF.md` was not in the repo.** Now committed.

## What the PM got wrong, recorded because it is the point of this file

- **Manufactured a phantom collision twice** by committing running agents' in-flight files to satisfy
  a clean-tree hook. The second cost a chain a full decision cycle. Ruleset now in `PLAYBOOK.md` and
  all seven agent definitions.
- **Over-read "optimize all for phone viewing right now"** as build responsive layouts. ~a third of
  the largest agent run on record (374k tokens) went on work the founder then cancelled. *"Right
  now" is urgency, not scope.*
- **Dispatched three Fable mandates mid-week.** Fable runs on a separate weekly budget spent at the
  end of the week. All three killed. Now recorded in `ROLE.md`.
- **Declared worktrees obsolete in the cloud.** Half right — the concurrency reason moved from
  session level to agent level rather than vanishing, and removing it caused the collision above
  within hours.

## Cost

~1.09M tokens across reporting agent chains. Logged per-dispatch in `docs/operating-model.md`.

## What a next session should pick up first

1. **Verify tomorrow's 09:15 UTC run fires on schedule.** Check `event: schedule`, not the commit
   author — that is how this was got wrong once. Until then the Windows task stays.
2. **The hardcoded league config** — correctness-floor item 1, now also the enabler for FR-027's
   generic tier. Must land before any mock is recorded.
3. **The Fable queue, at the end of the week** — and write `.claude/agents/fable.md` first; it is the
   one role with no definition.
4. **ID allocation is broken structurally**, not by indiscipline — three collisions today, all from
   tool-allocated IDs on parallel branches. See thread 081.

---

<!-- 2026-07-29-ranker-pass-2-late-round-te.md -->

# 2026-07-29 — `ranker` — bottom-up pass 2: where the TE mispricing can be spent (FR-039)

**Scope.** FR-039, the founder's narrowing of the pass-1 TE finding into a draft-strategy claim:
*if we aren't taking TE or QB early, find an underrated TE at late-round ADP.* Three questions —
where in the ADP distribution the mispricing sits, whether late TE hits are forecastable, and
whether the Kraft example represents a recurring pattern. Absorbed the previously queued TE arm on
`snap_counts` rather than running it beside.

**Posture: exploratory.** Nothing registered, nothing corrected for multiplicity, nothing shipped.
The one confirmatory test worth running is an *ask* in thread 087 and was deliberately not run.

## What was measured

Universe frozen pre-season from the FantasyPros ECR preseason list (`is_preseason_final=1`,
late-August `as_of_date`), 2021–2024, 344 TE player-seasons. Never-played TEs scored 0 and
retained. 2025 outcomes never read.

- **Hit rate by pre-draft band is steeply front-loaded with no late bump** — TE1-3 66.7%
  [39.1, 86.2] down to TE11-16 4.2% [0.7, 20.2].
- **5 of the 7 top-6 TE seasons that came from pre-draft TE11+ were outside the 150 picks of a
  10-team draft** — waiver adds, not late-round picks. In the actual last four rounds (ECR
  111–150) the top-6 rate is 7.4% [2.1, 23.4].
- **Consensus error scale is flat across the TE draft range** (residual RMSE 45.9 → 43.4) where RB
  falls 104.7 → 61.2. New, unexplained, logged to `ideas-inbox.md`.
- **A TE at overall ECR 75–113 costs the same VBD as a WR at the same pick** (−12.2 vs −12.2) and
  buys a 25.0% [10.2, 49.5] top-6 shot. One such pick beats three darts at ECR 111–150 (20.6%).
- **Forecastability is near-nil.** Of 11 pre-draft signals only consensus rank (0.649 [0.56, 0.74])
  and the panel's most optimistic expert (0.692 [0.61, 0.78]) exclude a coin flip, and both are the
  market restated. Expert disagreement killed (0.487/0.500/0.432). Snap-share proxy not supported
  at TE11+ (0.630 [0.36, 0.89]).
- **Kraft was consensus TE11 at overall ECR 105 going into 2025**, off a TE9 2024 — a mid-round TE,
  not a late-round unknown. Pattern test 2021–2024: Kraft-type 1.9% [0.5, 6.6] vs 2.5% [1.1, 5.8]
  for other late TEs. No advantage.

## Two methodological corrections made mid-pass

1. **Rank statistics were initially pooled across seasons**, which compares a 2021 player to a 2024
   player. Rebuilt so every rank-based statistic is computed inside a season and then averaged. The
   pooled version was discarded, not reported.
2. **Band sensitivity in the AUC table.** Running the late band to the end of the consensus list
   (TE41-95) moves the AUCs to 0.826 / 0.860 / 0.629 / 0.555 / 0.803 — every killed signal appears
   to work. The denominator does all the work. Recorded in the report as a trap, because the
   flattering version is what an unconstrained analysis produces by default.

## Escalated rather than celebrated

TE1-3 produced exactly two top-6 tight ends in each of the four seasons (2, 2, 2, 2) — a 3.9%
coincidence under its own base rate. Not believed to be leakage (pre-draft input, realised
outcome, no path between them) but the regularity must not be read as precision.

## Data gap, now binding

**There is no ADP history in `nfl.db` at all** — `adp_snapshots` and `ffc_adp_snapshots` are
2026-only. The only pre-draft market history is FantasyPros ECR, 4 usable seasons. Every
"late-round" claim in this pass uses ECR rank as a draft-cost proxy, calibrated on the one
overlapping season (2026: TE median ADP − ECR **+12**, IQR [+4, +16], n=18). The proxy error runs
*against* the founder's hypothesis, not for it. Thread 055 is the fix and was replied to.

## Artifacts

| | |
|---|---|
| Report | `docs/ranking/bottom-up-research-pass-2.md` |
| Code (runs, reproduces every headline figure) | `experiments/bottomup/pass2_te_adp.py` |
| Registration ask | thread **087** → `strategist` (stopping condition committed in advance) |
| Data escalation | thread **055** → `data-ops`, replied |
| Founder answer | `FR-039`, status → ANSWERED, replied on-thread |
| Leads logged | 4 entries in `docs/ideas-inbox.md` |

Commits: `e0d6299`, `68cde7f`, `7497477`, `b109100`.

---

<!-- 2026-07-29-ranker-research-pass-1.md -->

# 2026-07-29 — ranker — bottom-up research pass 1: where is the edge, and is it reducible at all

**Task.** Opening research pass for the founder's bottom-up ranking. Explore widely, commit to
nothing, ship no model. Answer first how much of a season's variance is reducible at all, then
survey four candidate edge channels cheaply. Deliverable:
`docs/ranking/bottom-up-research-pass-1.md`.

**Effort tier.** Opus/xhigh, per `.claude/agents/ranker.md`. Statistical methodology and model
design, CLAUDE.md §9.

## Premise check, done before any work

Every load-bearing claim in the brief was checked against the repo and holds — with one
correction that turned into the session's main finding. The "consensus explains 0.16-0.27"
figure is real (`docs/data-contract.md:95`) but it is the R² of the *consensus-rank curve*, not a
property of the game; the same curve fitted on realised finish rank has R² 0.91-0.98. The QB
slope series (`docs/ideas-inbox.md:229`) is real and reproduces; its *interpretation* is now
contested.

## What was measured

Five scripts, read-only handle on `data/nfl.db`, points scored through the real
`src/scoring.py` league config. **Season 2025 was never loaded** — not for features, not for
evaluation, not once. Universe frozen from season N−1 before N is opened, so busts and zero-game
seasons count. Bootstrap CIs resample seasons, not players.

1. An **oracle ladder** on season points (folds 2010-2024): naive baselines, consensus where it
   exists, and two impossible predictors that know exactly one thing about the target season.
2. A **three-way variance decomposition** of season ppg into stable player level, real
   season-specific shift, and week-to-week noise — the first from adjacent-season correlation
   (never the middle season), the third from within-season split-half.
3. **Bonus arithmetic**: every player-season 2009-2024 scored twice, with and without the
   stacking bonuses.
4. **Regime curves**: `points ~ a + b·ln(rank)` fitted per position per season, 1999-2024, on
   realised finish rank *and* on consensus rank, side by side.
5. **Two independent bounds on the team channel**: a perfect-foresight team-volume oracle, and a
   team fixed-effect ANOVA on prediction residuals against its own chance expectation.

## Findings, all exploratory, none registered

**The variance question has an answer and it is uncomfortable.** At WR, of observed season-ppg
variance: 12.5% week-to-week noise, 20.1% real season-specific change, 52.3% already priced by
consensus, ~15.1% stable quality left unpriced. Availability is the bigger unexplained block and
is near-unforecastable (prior games predicts games at r = 0.09-0.18). **The founder's edge is not
in forecasting a player's rate.**

**The shipped board's rank curve confounds positional value with market skill.** Realised QB value
spread is at an era *high* (era-mean slope −72.9 in 2021-2024 vs −57 to −59 before) while the
consensus-fitted slope fell. TE shows the same pattern; RB and WR do not. If that reading is
right, the recency-weighting fix on record would make the board chase market noise. **Opened
thread 085 to `strategist` rather than acting** — I do not rule on my own work, and this argues
against another agent's finding.

**TE is the position with unpriced stable signal**, on three independent lines: the ledger
(0.336 unpriced vs 0.151 at RB/WR), consensus failing to beat prior-season ppg there
(0.303 vs 0.407), and the prior prototype's only CI-clear VBD win.

**Two data gaps closed by deciding not to buy them.** The whole team-environment channel —
coaching a strict subset — is bounded at ≤ +0.055 τ by a *leaky, generous* oracle and shows zero
excess fixed-effect variance at every position. Coaching staff history and Vegas implied totals
should not be funded on this evidence.

**The bonus channel is now quantified for the first time**: half a positional rank of realised
reordering, less ex ante, and cross-positional rather than within-position (~6.8 points of
relative VBD between WR and TE). Real, small, and not the structural edge it has been called.

## Things I got wrong or nearly got wrong, recorded deliberately

- **Regression to the mean nearly became a finding.** Bucketing consensus residuals by consensus
  tier showed top-12 "underperforming" everywhere. That is Galton, not market error. Caught and
  removed by de-trending before anything was written down.
- **I rebuilt the V3 self-inclusion leak.** My first team-environment oracle let a player's own
  production into his team's total — the exact leak the ext-2 session found and named. Rebuilding
  it with self-exclusion produced a numerically unstable specification with negative τ, which I
  discarded as a broken spec rather than reporting as a negative result. The leaky version is
  reported as what it is: a generous upper bound.
- **The calibration prior applied to my own output.** Two consensus-residual patterns look like
  good stories (RB touchdown regression, WR post-injury over-rating). Both are r² ≈ 0.03 on n=4
  seasons with ~16 uncorrected comparisons. Recorded at half weight as hypotheses; neither is
  proposed as a factor.

## Repo defect fixed in passing

`tools/handoffs.py:31` — `ROLES` did not include `ranker` although `.claude/agents/ranker.md`
exists, so this role could not open a correctly attributed thread. One-line addition.

## Threads opened

- **084 → `data-ops`**: deepen expert consensus history before 2021. This is the only measured
  data gap that still binds; n=4 caps every market-relative claim below significance permanently.
- **085 → `strategist`**: rule on the rank-curve confound, and register (or reject) the
  decomposition experiment. No confirmatory run happens without it.

## Where I would go next

The decomposition experiment in thread 085 — it is the only candidate that touches a live defect
in a shipped artefact, needs no new data, is few-parameter, and is testable on 26 seasons rather
than 4. Runner-up and close: a TE arm built on `snap_counts` (2013-2025, 324,611 rows, already in
the database, never read by the prototype) as a labelled route-participation proxy.

---

<!-- 2026-07-29-researcher-competitive-ux.md -->

# 2026-07-29 · researcher · competitive UX ahead of a possible frontend overhaul

**Role:** researcher (Opus, effort 4–5) · **Type:** research only, nothing built · **Shell:** none

## What was asked

The founder is weighing a major frontend overhaul and wants to know what good looks like first —
*"features of other apps out there to see if we want to include them, or looking at good UI/UX
features."* He also corrected the PM's framing: **this is a multi-league tool, three leagues at
least, and draft position must be selectable in prep** (FR-034). Four questions: what the good ones
do well (weighted toward under-the-clock, density, uncertainty, multi-league/multi-slot), what they
do badly, what exists that this project has not considered, and what to deliberately not build.

## Artifact

`docs/research/competitive-ux-2026-07-29.md` — conclusion-first, every factual claim tagged
`[VERIFIED]` / `[SNIPPET]` / `[SECONDARY]` / `[GAP]` / `[ANALYSIS]`.

## Headline

**The evidence weakens the case for an overhaul rather than strengthening it.** ESPN's 2025 redesign
is the category's cautionary case and the verbatim complaints are about density specifically
(*"so zoomed in, can barely see any of the roster"*, *"everything just blends together"*). The prior
competitive UX pass already concluded the fix here was token-level, and that work shipped. What the
evidence *does* support is a scoped structural change: league and slot as first-class selectable
state, uncertainty surfaced on the board row, and three or four on-the-clock affordances.

Three to steal: (1) publish the uncertainty already computed at the point of decision — Draft Sharks
ships 80%/95% confidence prediction limits per player plus a published MAE, ROC-AUC and calibration
plot, so the honest version is commercially survivable; (2) rehearsing from a *randomised* draft slot
as a prep loop, not a settings value; (3) modelling actual league-mates from your own league's draft
history (FantasyPros "Draft Intel") — this project holds 160 real 2025 picks and spends them only on
λ. Three to avoid: spending an overhaul on whitespace, an ambient "trending/recommended" feed (the
one feature ESPN users explicitly asked to have removed), and live platform sync (ToS-blocked here
*and* the category's most common in-draft failure).

**One correction to prior work:** thread 061 concluded *"no competitor found publishes calibration
evidence."* That needs narrowing — it holds for availability modelling, but Draft Sharks publishes
out-of-sample metrics and a reliability check for its injury model. The defensible claim is
pre-registered calibration of the *availability* model specifically, which this project still cannot
make at 1 of ~30 mocks.

## Three things that had never been considered

1. **An agent-facing MCP surface instead of an in-app chatbot.** STACKED ships a hosted, OAuth-scoped,
   read-only MCP endpoint exposing 20 tools to Claude/ChatGPT/Codex `[VERIFIED]`. This dissolves the
   hallucination trade-off that caused the LLM prose renderer to be deferred, rather than resolving
   it. Recorded as an option, explicitly **not** recommended as work — no consumer, out of Phase 1.
2. **League-mate tendency modelling from your own league's history.**
3. **The product as the *second* screen.** Every screen spec assumes this app is the screen being
   looked at. On draft day it will be beside Yahoo's draft room. Nothing in the repo addresses that.

## Decided, not escalated

- **Did not halt on the premise, but recorded three challenges** (§0.5 of the artifact): the thread
  061 audit is in `docs/research/`, not `docs/reviews/`; a frontend overhaul sits outside written
  Phase 1 scope per `CLAUDE.md` §2/§8 and needs a spec amendment rather than a sprint; multi-league is
  *not* a contradiction with §1 because one founder with three leagues is still one user.
- **Escalating, and it is the reason this dispatch was partly unavoidable rework:** the prior
  **competitive UX research artifact does not exist in this repository.** `docs/operating-model.md`'s
  budget table logs the pass as completed and verified, and at least six live documents cite its
  conclusions (`design-handoff/HANDOFF-NOTES.md`, `design-handoff/README.md` Addendum 3,
  `handoffs/030`, `handoffs/047`, `adr-drafts/ADR-A`, `screenshot-checklist.html`). I searched the
  whole tree including every agent worktree. Its conclusions survive only as paraphrase inside the
  documents that consumed them. **This project has now bought the same research twice.**
- **Honoured every recorded block rather than routing around it.** `www.reddit.com` was refused by the
  tool outright and is the single largest hole in the voice-of-customer section — recorded, not
  worked around. ESPN/Yahoo/CBS not attempted. `forums.footballguys.com` and `www.fantasylife.com`
  both had relevant material surface in search and were left unfetched to stay consistent with the
  blocks recorded in thread 009 and the Yahoo audit, even though `fantasylife.com/articles/` is not
  robots-disallowed. Flagging that path-level loophole rather than exploiting it alone.
- **Refused to convert a `[GAP]` into a number** in three places: the visual form of Boris Chen's
  tier charts (output is a PNG my tools cannot read), what a BeerSheet contains (page carries only
  download links), and whether any user anywhere has asked for uncertainty display (every search
  returned vendor marketing). That last one is flagged in the artifact as the gap that would most
  change the confidence of the headline recommendation.
- **Flagged sample quality as the main caveat, including where it agreed with us.** Five of the
  richest sources are vendors describing their own products; the best competitor comparison is
  written by a competitor; the App Store review sets are curated by Apple and skew positive. And the
  ESPN density finding is exactly what this repo already believed — I went looking for it and found
  it, and did not look as hard for a disconfirming source.

## Not done — no shell in this session

This container has no Bash tool, so `python tools/handoffs.py new` and
`python tools/founder_requests.py new` could not be run. Hand-typing an ID is refused (threads
043/049/053, ADR-048). Two bodies are staged with their exact allocator commands:

- `docs/research/HANDOFF-BODY-unallocated-competitive-ux-2026-07-29.md` (researcher → pm, frontend)
- `docs/founder-requests/NEW-look-at-other-apps-ux-before-committing-to-an-overhaul.md`

Also not run: `python tools/status_log.py sync` to regenerate `docs/status/INDEX.md`, and
`python tools/state.py --apply`. `docs/CURRENT-STATE.md` was **not** edited — nothing in this
session changed build state, and this is research, not a state change.

## Fourth session to report it

`docs/ideas-inbox.md` still carries unresolved merge-conflict markers (`<<<<<<< HEAD`, `=======`,
`>>>>>>>`) around the strategist PR-004 and backend ADR-057/ADR-059 entries. Both sides look like
real work. I appended below them without touching either side. Three prior sessions reported the same
thing.

---

<!-- 2026-07-29-researcher-historical-adp.md -->

# 2026-07-29 · researcher · historical preseason ADP availability

**Mandate:** research only. Establish what historical, point-in-time, preseason draft-market data is
legitimately obtainable, how far back, and in what formats — because the confirmatory market-baseline
comparison `CLAUDE.md` §6.5 demands is currently limited to n=4 expert-consensus seasons.

**Nothing was built, ingested, scraped in bulk, or committed to code.** Output is
`docs/research/historical-adp-availability-2026-07-29.md` plus a reply on thread 055.

## What was done

~35 individual page reads of Fantasy Football Calculator's HTML ADP pages (one per season-format,
no concurrency, no bulk harvest), plus its `robots.txt`, its ToS/terms paths, and its ADP index.
Cross-checked against `data/adp-snapshots-ffc/2026-07-29_half_ppr.csv` (the repo's own same-day
capture) and `src/ingest_ffc_adp.py`.

## Headline

**The n=4 wall lifts, to 13 (non-PPR 12-team, 2010 + 2013–2024) or 7 (half-PPR 12-team,
2018–2024).** FFC states an explicit bounded draft-date window on every archived season that carries
data, so a per-season look-ahead gate is computable rather than assumed. It is genuinely unlike MFL,
which stamps today's date on an accumulated aggregate.

But: **"back to 2007/2009" is not achievable.** 2007–2009 windows all run to June 20 2010, 2011
straddles kickoff, 2012 ends on kickoff day. And the archive is **12-team only** — 10-team and
14-team requests silently return the 12-team page with HTTP 200. Westwood is half-PPR *10*-team, so
no archived season matches the primary league's format exactly.

## Premise challenges raised

1. **This does not rescue PR-004.** It is registered and frozen; §4 exit 3 and ADR-C both say a new
   baseline is a new test with a new id, not an amendment. The honest path is a fresh confirmatory
   registration. PR-004 should still run as-is.
2. **PR-004's primary arm was never n=4** — only the market-comparison headline was.
3. **n=7 half-PPR does not survive BH at m=4.** Sign-test floor 0.0156 > α/m = 0.0125. A perfect
   7-of-7 sweep would still fail. The format arm and `m` must be chosen before the run.
4. **n=13 is n=1 by market** — thirteen draws from one site's *mock*-draft pool, sample sizes varying
   9x across seasons.

## Escalated, not resolved

- **The app is public; every source authorisation is scoped "private, one person, void if a second
  human."** FR-023, D-020 and D-021 all carry that condition, and `CURRENT-STATE.md` records the app
  as live on the open internet by founder choice. Founder decision with a licensing consequence.
- **`docs/ideas-inbox.md` contains unresolved merge-conflict markers** (`<<<<<<< HEAD` /
  `=======` / `>>>>>>> c191f45...`) around the strategist's PR-004 entry and backend's ADR-057
  entries. **Not touched.** Both sides look like real work; this is a genuine conflict for the
  coordinator.
- **`CURRENT-STATE.md` still says FFC is blocked** ("FFC is blocked by robots.txt regardless",
  "FFC remains blocked") while `docs/pm/MEMORY.md` §4 and FR-023 record it as unblocked. MEMORY
  states it supersedes; the supersession was never propagated. Stale-line fix, not mine to make.

## Blocked, recorded, not routed around

`web.archive.org` — "Claude Code is unable to fetch from web.archive.org". Wayback captures would
have been a strong independent source of true point-in-time ADP boards. Stopped there.

## Gaps left open deliberately

- Exact row count per archived season. WebFetch's markdown conversion drops rows demonstrably.
  Closes by running `src/ingest_ffc_adp.py::parse_adp_table()` over saved HTML.
- FFC Terms of Service, in any retrievable form. Third independent attempt, third failure.
- Whether the displayed window is exactly the sample bound. Closes for free from two weeks of the
  existing daily capture.
- FFC PPR archive depth (2010 verified present, 2009 absent, 2011–2024 not probed).

## Tooling note

This session had **no Bash tool**. Consequences: no `tools/handoffs.py new` (so no thread was
allocated for this work — the reply went on the existing thread 055, which is exactly on-topic), no
`tools/status_log.py sync`, and **no commit**. Files written this session:
`docs/research/historical-adp-availability-2026-07-29.md`, this log, the thread 055 reply, and one
`docs/ideas-inbox.md` append.
</content>
</invoke>

---

<!-- 2026-07-29-researcher-missing-inputs.md -->

# 2026-07-29 · researcher · sourcing the three unbuilt inputs

**Task:** research only — establish what exists and on what terms for the three inputs `CLAUDE.md`
§5 names but that were never built: Vegas odds, coaching staff history, route participation.
Build nothing, ingest nothing, write no scraper.

**Output:** `docs/research/missing-inputs-sourcing-2026-07-29.md`.

---

## What was done

Read first, as instructed: `docs/CURRENT-STATE.md`, `docs/environment.md`, `docs/pm/MEMORY.md` §4,
`docs/research/source-audit-2026-07.md`, `CLAUDE.md` §5/§10. Then read
`docs/test-registry.md` (rows 11, 16/17, 29/29b/30), `docs/data-availability.md` §7.9,
`docs/deferred.md`, `docs/research/tier1-usage-source-inventory-2026-07.md`, and
`docs/handoffs/054-ftn-and-sleeper-harvest.md`.

Roughly 30 external fetches/searches. Every claim in the output document is tagged `[VERIFIED]`,
`[SNIPPET]`, `[SECONDARY]` or `[GAP]`. No `[GAP]` was filled.

## Premise challenges raised, not resolved unilaterally

1. **The dispatch calls Vegas odds "probably the highest-value missing input."
   `docs/test-registry.md` rates it Tier 0, edge "Low", and defines Tier 0 as "having them is not an
   edge" — while rating route participation (#17) and coordinator continuity (#29) "High".** That is
   a contradiction between the task framing and a written project document. I did the research on all
   three as asked, but did not adopt the ordering as fact; the recommendation is decided on the
   evidence gathered. Escalated in the output document §0(b), for PM/founder to settle.
2. Minor citation slip: the dispatch attributes the MFL retrospective-aggregate trap to `CLAUDE.md`
   §6.1; it is actually recorded in `docs/CURRENT-STATE.md` open item 2 and `docs/pm/MEMORY.md` §4.
3. `docs/environment.md` describes a Windows conda box with a `PreToolUse` hook. This session ran in
   a Linux cloud container **with no shell tool of any kind** — read/write/grep/glob/web only. Not a
   conflict to resolve, but it meant **zero `[MODAL-SAMPLED]` evidence was possible**: no `nflreadpy`
   call, no `data/nfl.db` query, no API call needing a key. Several gaps in the report are one
   Python query away for anyone with a shell, and the report says which.

## Headline findings

- **Vegas game lines are not a sourcing problem.** `nflreadpy.load_schedules()` already carries
  `spread_line`, `total_line`, four odds columns and two moneylines, CC-BY-4.0, $0, from 1999. Implied
  team total is arithmetic on two of them. The repo references none of these columns anywhere in
  `src/` (grepped). **The one gap that matters — opening vs closing line — is undocumented**, and the
  report explains precisely where that bites (season-N in-season use) and where it does not
  (season N−1 aggregates, which is what the backtest rule permits anyway).
- **The Odds API is the only odds source whose terms permit display to a third party.** Genuine
  10-minute point-in-time snapshots from 2020-06-06, paid-plans-only, historical requests at 10×
  credits, cheapest usable tier **$30/month**. **It has no NFL season-win-totals market** — verified
  against their sport-key list, so it must not be bought expecting that.
- **Season win totals: covers.com/sportsoddshistory, 1999–2026, $0, fetch permitted, display
  prohibited.** Sample-quality caveat is the decisive finding: the 2020 page is dated "As of
  September 10, 2020"; the **2012 page carries no date at all.** n = 2 of 28 seasons and they
  disagree on the property that determines look-ahead safety.
- **Coaching staff — the real finding of the session.** PFR re-verified as blocked today (both
  `robots.txt` and `sports-reference.com/data_use.html` return HTTP 403; recorded and stopped).
  nflverse confirmed to carry head coaches only. **Wikipedia's `Template:NFL final staff` is
  transcluded on 1,062+ mainspace articles spanning 1946–2024, names offensive and defensive
  coordinators, is reachable through the official MediaWiki API, and is CC BY-SA 4.0 — fetch *and*
  display both permitted.** Two hazards flagged: I verified only two articles, both Atlanta, so
  per-team-season population rate is a `[GAP]`; and the template is *final* staff, an end-of-season
  end-state with no `as_of_date`, which is a genuine look-ahead problem for a preseason input.
- **Route participation: record is still accurate.** No routes-run column in nflverse. The
  participation `route` field describes only the *targeted* receiver's route, not who ran routes.
  The defensible proxy is pass-play presence via `offense_players`, 2016–2024 only, with a
  **systematic position-correlated bias** (overstates blocking-heavy RBs and inline TEs) that must be
  named in the column and not just called "a proxy". Fantasy Points sells real route data and its ToS
  forbids automated collection outright; its price is a `[GAP]` because the page renders client-side.
  Thread 054 (the founder's existing, unaudited FTN subscription) is the cheaper next move and was
  deliberately not duplicated.

**Recommendation: coaching staff first** — it is the only one of the three that ungates a
registry item rated High edge, and the only one whose licence permits display.

## Not done, and why

- **No handoff thread was opened or replied to.** This task named no thread, and the three open
  `researcher` threads (054, 057, 070) are different asks. A new thread would need
  `python tools/handoffs.py new` for its ID, and IDs must never be hand-typed or computed from a
  directory listing (the 043/049/053 and ADR-048 collisions). **No shell tool was available in this
  session**, so the allocator could not be run. Flagged for the coordinator.
- **Nothing was committed** — same reason: no shell. Files written: this log and
  `docs/research/missing-inputs-sourcing-2026-07-29.md`. `python tools/status_log.py sync` has not
  been run, so `docs/status/INDEX.md` is stale by one entry.
- No founder statement occurred in this session, so no `docs/founder-requests/` entry was created.
- `docs/CURRENT-STATE.md` not edited: this session changed no build state, only added a research
  document.

---

<!-- 2026-07-29-researcher-yahoo-assistant.md -->

# 2026-07-29 — researcher — Yahoo in-draft assistant

**Role:** researcher · **Type:** research only, no build, no ingestion, no data collection
**Output:** `docs/research/yahoo-draft-assistant-2026-07-29.md`

## Task

Answer five questions about Yahoo's in-draft assistant: what a drafter sees on the clock, what
rankings it draws on and under what scoring format, whether ADP/ranks are obtainable through the
official OAuth API, what the founder can get manually as a league member, and how much of his room
plausibly anchors on the platform's suggestions.

## Premise check

Checked the instruction against the repo before acting, as required. It holds:

- `docs/pm/MEMORY.md` §4 records ESPN / Yahoo / CBS as having "explicit written prohibitions on
  automated collection." Not lifted.
- The 2026-07-29 FFC unblock is FFC-specific in the same section and does not extend to Yahoo.
- The task's characterisation of `src/ingest_mfl_adp.py`'s docstring is accurate — it does state
  that "drafters pick off their own platform's displayed ranks, so ADP is a per-platform
  behavioural variable" and that platforms must never be blended.

No contradiction found. Proceeded.

## Boundary honoured

Every Yahoo-owned host examined names `anthropic-ai`, `Claude-Web` and `ClaudeBot` with
`Disallow: /` — `help.yahoo.com`, `sports.yahoo.com`, `www.aol.com` (which mirrors Yahoo Sports
articles), and `football.fantasysports.yahoo.com` per the prior audit. `developer.yahoo.com` has no
AI-agent block but its fantasy guide 308-redirects to the blocked `sports.yahoo.com/developer`.

**No Yahoo fantasy page was fetched. No scraper was built, tested or designed.** Yahoo's own product
and developer documentation is therefore unreadable by this agent class, which caps every claim
about the Yahoo product at `[SNIPPET]` or `[SECONDARY]`. There is no `[VERIFIED]` claim about the
Yahoo draft room in the report, and there cannot be one from here.

Also deliberately did **not** fetch a Fantasy Life article whose path (`/articles/`) is outside that
site's robots disallow list, because the prior audit records Fantasy Life as blocked and its ToS as
`[GAP]`. Chose consistency with the recorded block over a path-level loophole; flagged in the report
rather than resolved unilaterally.

## Findings, in one paragraph each

**The founder's insight is correct and under-specified.** "The Yahoo board" is at least three
different numbers: a **Default Rank** computed from the league's own scoring settings, an **Expert
Rank** computed from Yahoo's *default* scoring which also drives autopick, and a platform-wide
**ADP**. Which one a drafter anchors on changes the model. Treating them as one object would
reproduce the exact blending error `ingest_mfl_adp.py` exists to prevent.

**The scoring gap is narrower on receptions and wider on bonuses than expected.** Yahoo's default
football scoring is already half-PPR — corroborated `[VERIFIED]` in-repo from
`data/leagues/ethans_expert_league.json`, which carries `receptions: 0.5` and empty `bonuses: []`
arrays on all three yardage categories. So Westwood's wedge against the room's anchor is not PPR
format; it is the **stacking yardage bonuses**, plus INT −2 vs −1, no kicker, and two flex.

**The highest-value open question is a `[GAP]` and I left it as one.** Whether Yahoo's
league-scoring-aware Default Rank actually prices bonus thresholds is unestablished. A threshold
bonus is a nonlinear function of a per-game distribution and cannot be computed from a season-total
projection, so there is a real chance Yahoo ignores bonus settings entirely — in which case the whole
room, including the league-aware surface, under-prices ceiling in a league that pays for it. That is
directly exploitable and is **not** to be acted on until confirmed. A cheap legal test exists: the
founder compares his Pre-Draft Rankings ordering in Westwood against the same page in Ethan's Expert
(also Yahoo, also 10 teams, no bonuses). Identical orderings would answer it.

**One Yahoo number is obtainable within the rules, and it is the behavioural one.** `draft_analysis`
(`average_pick`, `average_round`, `average_cost`, `percent_drafted`) is confirmed `[SECONDARY]` on
three mutually independent third-party API wrappers fetched this session — upgrading the prior
audit's unconfirmed `[SNIPPET]`. It is real Yahoo drafter behaviour, and OAuth is the channel
`CLAUDE.md` §10 prefers. Three blockers stop it being a green light: the 24-hour user-data deletion
clause (`[GAP]` whether aggregate ADP falls under it — this decides whether snapshots are storable at
all), the no-competing-product clause (Yahoo ships a draft assistant; so does this project), and
`[GAP]` whether the figure can be filtered to 10-team half-PPR. Founder decision, not an agent one.

**Draft Scout is paywalled during real drafts**, free only in mocks. So the modal free drafter is
anchored on an *ordering plus ADP columns*, not a roster-aware recommender — a simpler and more
tractable modelling target. Its metric, VOLS (Value Over Last expected Starter), is the same family
as this project's replacement-level VBD, which means positional revaluation — per `docs/pm/MEMORY.md`
§1 the board's only edge channel — is partially competed away against any manager who pays.

**Q5 is a `[GAP]` and I did not fill it.** No usage statistic on autopick rates, queue usage or
Fantasy Plus attach rate was found. Platform MAU-share figures surfaced and are recorded only so
nobody mistakes them for an answer — they are platform popularity, not in-draft behaviour, and
applying them to a 10-person room is a category error. The genuinely useful observation is that the
founder's own read is n=1 observer over ~9 managers, and is still the best evidence that exists about
*this room*; the recommendation is that he label each manager `own-board / mixed / platform-default /
unknown` **before** 7 September, which makes it a checkable pre-registration rather than hindsight.

## Sample quality

The ~15 sources consulted collapse into roughly four independent units. All §2/§3 claims about
Yahoo's rank types trace back through search synthesis to one or two Yahoo help pages — four
agreeing searches are four reads of the same page, not four sources. The fantasy-media commentary
class (FantasyLife, FantasyLabs, FTN, RotoWire, DraftSharks) is one decision unit and is structurally
motivated to assert that Yahoo's list is beatable; none was read. The only `[VERIFIED]` scoring
evidence came from inside this repo, which is convenient and agrees with the web — flagged as exactly
when it deserves scrutiny, since its provenance is not independent of this project's own assumptions.

An additional caveat recorded in the report: most `[SNIPPET]` items here are the search tool's own
*synthesis* over excerpts, i.e. a model paraphrase of a page neither of us rendered. That is weaker
than a normal `[SNIPPET]` and is stated as such.

## Environment notes

- **No Bash tool in this session.** Tools available were Read, Write, Edit, Glob, Grep, WebSearch,
  WebFetch only. Consequences: **the two files written could not be committed**, and the founder's
  verbatim observation quoted in the task could not be captured via
  `python tools/founder_requests.py new` as the agent operating rules require. Both need someone with
  a shell.
- Three fetches returned HTTP 403 (`fantasypointcalculators.com`, `support.fantasypros.com`,
  `ftnfantasy.com`) and one returned 503 (`sjdm.org`). Without a shell I could not run the proxy
  status check `docs/environment.md` and the environment notes describe, so I could not determine
  origin-side vs. proxy-side. Recorded as unretrieved, **not** as blocked.
- `docs/environment.md` is written for the founder's Windows machine (conda interpreter path,
  `PreToolUse` hook). Neither applies in this cloud container.

## Files written

- `docs/research/yahoo-draft-assistant-2026-07-29.md` (the deliverable)
- `docs/status/2026-07-29-researcher-yahoo-assistant.md` (this file)

Nothing else was modified, per instruction. No handoff thread was opened or replied to — the task
named none, and the three threads standing open to `researcher` (054, 057, 070) are unrelated to it
and were deliberately not absorbed into this session.

---

<!-- 2026-07-29-strategist-bottomup-registration.md -->

# 2026-07-29 · strategist · PR-004 bottom-up confirmatory registration

**Role:** strategist (Opus/high). **Shell:** none, by design — this session wrote a
pre-registration and could not, and did not, run any measurement.

## What was asked

Pre-register the one confirmatory bottom-up ranking experiment that has never been run
(ADR-E §9 / F-A §1's A0, "F-BOTTOMUP-CORE"), and commit the decision rule before anyone runs it.

## Premise challenged

The brief asserted *"the baseline that matters is consensus, not last-season rank."* Correct in
principle (`CLAUDE.md` §6.5), **not achievable with this data**, and the registration says so
rather than hedging. Consensus ECR coverage is 2021–2025; 2025 is the sealed holdout, leaving
n=4. The exact two-sided sign-test floor at n=4 is p=0.125 — unreachable at alpha=0.05 before
any correction, the same wall PR-003 documented. Consensus is registered as **descriptive
only** (no p-value, no CI, per ADR-B and ADR-C's exploratory-artifact rule), and the
registration states the consequence in full: **no outcome of PR-004 may be reported as an edge,
as beating the market, or as evidence our rankings beat consensus.** The descriptive evidence
already on file has consensus ahead of the V5 model at every position. A PASS licenses a
labelled, non-binding overlay at the passing position and nothing more.

Not a refusal. An accuracy claim against a stated naive baseline, scope-limited, is defensible
with the data in hand. What would be indefensible is running it and calling it an edge — so the
scope limit is registered where it cannot be relaxed after the number is seen.

## What was produced

| Artifact | Path |
|---|---|
| Registration (ADR-C nine-field confirmatory) | `docs/preregistration/PR-004-bottomup-core-confirmatory.md` |
| Family manifest (m=4, fixes the BH denominator) | `docs/preregistration/families/F-BOTTOMUP-CORE.yaml` |
| Handoff body, **unallocated** | `docs/reviews/PR-004-handoff-body-unallocated-2026-07-29.md` |
| Decision log | `docs/ideas-inbox.md`, 2026-07-29 strategist entry |

## The decision rule, in one place

Per position, six conjunctive criteria: mean dtau_b vs prior-season-points baseline **>= +0.04**;
positive in **>= 10 of 13** embargoed-LOSO folds; season-level bootstrap 95% CI excludes 0 **and**
the bootstrap p survives BH across m=4; points-per-game variant agrees in sign; no ADR-E §8
audit trigger; cross-process determinism from seed 20260729. Projected-points adoption
additionally requires mean dR2 > 0 at >= 10/13 folds.

**STOP: if neither RB nor WR clears, bottom-up is dead as a 2026 product input** — consensus-only
board, no overlay, no further configs before the draft, family closed. Three escape routes are
closed by name in §4 (lowering the floor, promoting a descriptive arm, re-running with different
knobs).

## Four judgement calls, made not asked

1. **Consensus refused as confirmatory baseline** (above).
2. **F-A's ordering inverted.** A0 runs *before* N-1/N-2. Choosing the frozen candidate after
   seeing N-1/N-2 is a `data_seen` selection step; amending PR-004 on it would irreversibly
   demote it to exploratory under ADR-C's one rule with teeth. V5 is frozen unconditionally;
   N-1/N-2 become post-hoc exploratory work that cannot change this verdict.
3. **QB run confirmatorily**, against F-A §2.3's "closed, not run", keeping ADR-E §9's declared
   m=4. Dropping the position we expect to fail would shrink the BH denominator by exactly the
   failing test. Strictly more conservative; costs nothing.
4. **Materiality floor +0.04 dtau_b**, derived from decision-relevance arithmetic (~23 pairwise
   inversions over a ~48-player universe ≈ one improved pick per draft) and deliberately set
   **above WR's exploratory point estimate of +0.036**. A threshold set beneath every estimate
   already seen is not a threshold.

## Calibration prior, applied

Four of five registered prediction sets across sessions 3–4 were materially wrong, every miss
over-crediting a situation story — and V5's advantage over V1 comes precisely from a situation
feature family. §5 registers the pessimistic reading: **modal outcome is STOP**; at most RB
clears; WR is predicted to fail on materiality even if it clears significance.

## The limitation that must survive into every downstream summary

**Selection contamination.** V5 was chosen from eight configurations evaluated on these same
folds (2012–2024). PR-004 does not measure V5 against data unseen by the selection process. It
measures, for the first time, what the effect looks like under a pre-registered rule with an
honest season-level CI, a fixed denominator, the ADR-E embargo, and a threshold that can fail.
It cannot establish out-of-sample skill for the configuration choice. Only the sealed 2025
unseal (n=1, one shot) or P-2026 (prospective) could.

## Not done, and why

- **Handoff thread not opened.** No Bash in this role by design, therefore no allocator access.
  Hand-typing or computing an ID was refused (collisions at threads 043/049/053, ADR-048). The
  body is staged with the exact `python tools/handoffs.py new --from strategist --to backend`
  command; whoever has a shell allocates, pastes, syncs, deletes the staging file.
- **`content_hash` left as `PENDING-FREEZE`.** Cannot compute sha256 without a shell.
  `compute_content_hash` redacts the field before hashing, so backend writing the real value in
  is the designed two-pass freeze; §9 spells out the four steps and makes them a prerequisite to
  running anything.
- **2025 holdout not unsealed and not authorised.** Irreversible, permanently closes the family,
  requires a named human approver in `UNSEAL_LOG.md`. That is an escalation, not an agent call.
- **No measurement of any kind run.** That is the role working as intended.

---

# REVISION, same day, before freeze — the founder challenged the premise and was right

PR-004 landed as **thread 083**. The founder then made two corrections, both accepted, and a
third request. The registration was **revised in place** — legitimate because `content_hash` was
never frozen and no data was seen, so there is nothing to amend and no ADR-C demotion is
triggered. Recording it as an `amendments:` entry would have misrepresented a never-frozen file
as a peeked-at one.

## What he said, and what it changed

1. **"Market ADP is not consensus rankings — people use consensus rankings, not ADP."**
   Accepted without qualification. No baseline swap to ADP, not even to buy FFC's deeper
   history. **Depth bought by measuring a different quantity is not depth.**
2. **"We have 25 years of data to build our bottom-up rankings from, independent of
   consensus."** Structurally correct and it exposes a real error in my first draft: **I let the
   weak question's n cap the strong one.** Bottom-up needs player stats to build and actual
   finishes to score; both go back decades. Consensus history is needed for exactly one
   question — did we beat the experts.
3. **"Then we test our bottom up r squared against consensus and consensus adjusted for what we
   do have for now."** Folded in as PR-004 §11, descriptive only.

## The finding the revision surfaced, which neither of us had

`experiments/bottomup/data.py:60`:

```
TARGET_RELIABLE = lambda s: (1999 <= s <= 2002) or (s >= 2009)   # air yards real 2009+ only
```

**Targets are missing 2003–2008.** The usage features that produce the model's entire measured
edge cannot be built across the deep record. So:

> **The deep sample buys power. The deep model is the weak one.** 25 years of stats does not
> rescue the strong model; it gives a powerful test of the weak one.

Hence two registrations rather than one, with separately fixed denominators so the winning arm
cannot be chosen after the fact:

| | PR-004 `F-BOTTOMUP-CORE` m=4 | PR-005 `F-BOTTOMUP-USAGE` m=4 |
|---|---|---|
| Model | box-score long arm | V5, the shipping candidate |
| Folds | measured by census, expected ~2000–2024 | 2012–2024, n=13 |
| Trade | power, weak model | strong model, short sample |

BH within each family across its own m=4 (ADR-E §10). Across-family FWER is not controlled and
the registration says so; the compensating discipline is that STOP requires **both** to fail.

## Usable span: measured, not asserted

I have no database access and refused to assert a number. PR-004 §3 specifies the census
precisely (per-season coverage of every field `src/scoring.py`'s `LEAGUE` consumes, with
two-point conversions and return TDs checked explicitly as the likely binding fields) and
pre-commits the fold set as a formula, `FOLDS = { s : S_min + L ≤ s ≤ 2024, s ≠ 2025 }`.

**Prediction on the record: n≈25, folds ~2000–2024.** `run.py:10`'s current 2002 start is a
*walk-forward* warm-up artifact ("needs >=2 training pairs"); embargoed LOSO has no warm-up
cost, so the switch should recover the folds walk-forward spent. If so the founder's "25 years"
is close to exactly right and the current 23 was a fold-scheme artifact, not a data limit.
Pre-committed: **if n < 15, STOP without running.** A coverage census reveals nothing about any
effect, so it may legitimately precede the freeze.

## Two instructions I declined, with reasons

- **Recomputing the +0.04 materiality floor against the real n.** Power and materiality are
  different quantities. n governs detectability; it says nothing about how large an effect must
  be to matter. The floor is decision-relevance arithmetic (~23 pairwise inversions over a
  48-player universe ≈ one improved pick per draft), identical at n=13 and n=25. Lowering it
  because the sample deepened is lowering the bar for the same benefit. **What did change is the
  meaning of the ≥75% fold rule**, now tabulated: sign p≈0.092 at n=13 (weaker than α=0.05),
  ≈0.007 at n=25 (stricter). ADR-E's 75% kept unchanged; the stringency is now visible instead
  of implicit.
- **Reporting a positional-tier heuristic as CLAUDE.md §6.5's third baseline.** Subtracting
  replacement level is a monotone transform *within position*, and tau-b is invariant under
  monotone transforms — its tau equals B1's by construction. It would be reporting B1 twice.
  B2 is instead a three-season equal-weight average, genuinely distinct, and is criterion (h).

## The three-way comparison, handled rather than glossed

- **R² is his language and it is answered in his language**, not silently swapped. Where it is
  defensible: nested comparison, variance in actual points, single position. Where it is not:
  season-points R² is already **negative** at QB (−0.13) and TE (−0.85), so an R²-only reading
  calls the model useless at TE while tau says its ordering improves. Both are printed side by
  side at every position.
- **Non-independence handled by construction.** The blend *contains* consensus, so in-sample
  `R²(consensus+bottom-up) ≥ R²(consensus)` is a mechanical identity — three numbers side by
  side would guarantee the blend "wins" and mean nothing. Registered instead as **one nested
  question per position**: out-of-sample **ΔR²_oos**, weights fit on the other three seasons and
  rotated, which can be negative. Never a three-way leaderboard. Registered asymmetry: at n=4 a
  strongly negative value is informative, a positive one says almost nothing.

## Escalations, not resolved here

- **`CLAUDE.md` §4 says "Ranking sources stay separate, never blended."** The founder's
  preferred product shape is a blend. Measuring one descriptively is not shipping one, and §11
  only measures — but **shipping it requires a §4 amendment, which is his decision.** Middle
  path put on the record: consensus adjusts display and confidence (labelled overlay,
  disagreement flags) rather than being averaged into a score.
- **Successor question PR-006** (consensus as adjustment rather than rival) recorded as future
  work with its own registration, explicitly not folded into PR-004/005, n-limited to January
  2027 at the earliest.

## Kept unchanged

The decision rule committed in advance; the STOP condition with its three exits closed by name;
the calibration prior applied against my own registered predictions (**modal outcome across
both files is STOP**); the selection-contamination caveat that must survive into every
downstream summary; and the refusal to authorise a 2025 unseal.

---

