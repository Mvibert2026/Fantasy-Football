# CURRENT STATE

**This file is the canonical answer to "where is the project right now."**
It is edited **in place**. When something changes, replace the affected line — never append a new
section, never leave the old value "for contrast." If you find yourself adding a second version of
a number that already appears here, you are doing it wrong.

Do **not** read `docs/status.md` to answer a current-state question. That file is an append-only
session log and contains superseded figures presented in the same voice as current ones. Same
hazard `docs/assistant-context.md` warns about for `decisions.md`. It is fine to read `status.md`
to learn *what happened*; it is not fine to read it to learn *what is true*.

**Last verified:** 2026-07-27, read directly from the working tree (backend session: thread 019
bootstrap-CI verification, thread 017/039 `weekly_finishes.json`/`season_stats.json` export
implementation (contract 1.9.0); frontend session: display-repair diagnosis, Opponents wiring
verification, mailbox duplicate-ID fix, thread 038/041; second frontend session, same day: thread
037 item 1 (`<1%` test literal), thread 029 (DraftRoom dot array + tier grouping, retargeted off
Board.tsx per its amendment), RETROFIT-5/thread 036 (Mock Lab TypeAhead back-port to DraftRoom pick
entry), plus mailbox hygiene — duplicate ID 043 and an orphaned no-`TO:` fragment file, both fixed);
third backend session, same day (9-way concurrent dispatch): thread 052's backend half —
`board.json`'s `player_id_gsis` join key populated (ADR-048), coverage measured, D-022 (2025
holdout-in-exports) recorded DECIDED.

---

## Build state

| | Value | Notes |
|---|---|---|
| Backend branch / commit | `master`, on top of `09391e4` (frontend WIP checkpoint) | Local only — **no git remote configured** |
| Backend tests | **423 passing, 0 failures** as of 2026-07-26, **+20 more** in `tests/test_mock_lab_store.py` added 2026-07-27 (thread 025), **+44 more** in `tests/test_preregistration.py`/`tests/test_holdout.py` added 2026-07-27 (thread 020, ADR-C), **+13 more** in `tests/test_export_history.py` added 2026-07-27 (thread 017/039) — all verified passing in isolation only. Full suite not re-run this session (concurrent-agent DB contention; instruction was to run targeted tests only), so the combined total is not yet independently confirmed | Re-measured 2026-07-26 (this session, `-m pytest -q`): **107-119s**, down from ~5.7 min — session-scoped caching of the expensive real-data archetype/description computation (thread 022). The prior "1 pre-existing failure" (`test_handoffs.py::test_mailbox_health`, duplicate thread ID 036 across two files) is fixed — thread 041 (frontend session) found a leftover, never-deleted `036-weekly-finishes-and-season-stats-exports-contrac.md` left behind when that thread was renumbered to 039 in an earlier session, and removed it. A NEW, separate `test_mailbox_health` failure exists as of this session (threads 020/023/025 resolved-with-no-artifact, 029 has no `TO:`) — not caused by the thread 017/039 work, not fixed by it either (out of scope: export path only) |
| Agent infrastructure | **Live** | Six subagents in `.claude/agents/` (backend, frontend, data-ops, strategist, researcher, librarian), `/inbox` command, mailbox tooling at `tools/handoffs.py` + `tools/sprint_status.py`, mailbox health enforced in the test suite (`tests/test_handoffs.py`) |
| Data contract | **1.9.0** | Bumped from 1.8.0 this session (thread 017/039: new `weekly_finishes.json`/`season_stats.json`, own `export_version`, not itself `CONTRACT_VERSION`-tagged — same pattern as `player_descriptions.json`). All six per-league `CONTRACT_VERSION`-tagged artifacts regenerated and verified matching 1.9.0. `strategies.json` is still stale at 1.7.0 pending backend re-running its export (thread 042, open, untouched this session). `assistant-context.md` still says 1.6.0 — fix on next touch |
| Frontend location | `frontend/` subdirectory of this repo | Merged from `frontend-prep` @ `7276a2d`..`d7cd321` via `git subtree add` (commit `2df3716`), full history preserved. No longer a separate working copy. |
| Frontend tests | **126 passing, 1 failing** (127 total, 16 files) | New this session: `format.test.ts` (+1, thread 037 item 1), `draft.test.ts` (+2, `entryMode`), new `draft-room-typeahead.test.tsx` (+9, RETROFIT-5). The 1 failure (`trace-fields.test.ts`, `TRACE_CONTRACT` pinned at 1.8.0 vs. `board.json` now 1.9.0) is **pre-existing contract drift from the concurrent backend session's thread 043 bump, not caused by this session** — flagged in a reply to that thread, not fixed here (real work: `TRACE_CONTRACT` bump + wiring `weekly_finishes.json`/`season_stats.json` into `PlayerDetail.tsx` §7/§8, out of scope tonight). `node_modules` is gitignored and must be reinstalled per checkout |
| Python modules | 35 in `src/` (`mock_lab_store.py` added 2026-07-27, thread 025; `preregistration.py`/`holdout.py` extended, not added, thread 020; `export_history.py` added 2026-07-27, thread 017/039) | |
| Export artifacts | 8 + `player_descriptions.json` + `weekly_finishes.json` + `season_stats.json` | `rosters.json` added (thread 016), wired into the Opponents tab and verified rendering live (thread 038/041). `weekly_finishes.json`/`season_stats.json` added this session (thread 017/039) — 1481 players, real `player_weekly_stats` data, 2003-2008 target-derived fields explicitly `target_data_unavailable`/`null`, never zeroed; NOT per-league (written once, unprefixed path only). All three of `player_descriptions.json`/`weekly_finishes.json`/`season_stats.json` version independently, by design |
| Config matrix | 24 dirs under `data/export/` | board + league + availability stub only; **hazard model not rerun per config**; each config's `write_all` now also emits `rosters.json` (empty-roster state, not yet regenerated for all 24 configs this session) |

## Statistical constants in force

| Constant | Value | Standing |
|---|---|---|
| `DEFAULT_LAMBDA` (roster-need weight) | **0.352** | Measured — 2025 real draft, n=160 / 10 clusters, clustered SE 0.070, z=5.04. One season, one draft. Keep the caveat attached. |
| `delta` (positional-run weight) | **0.10** | **Unvalidated prior.** Binding rule: if the need+run model does not beat marginal-only on Brier across ≥30 conforming mocks, set `delta = 0`. |
| `NEED_ADJUSTMENT_SCALE` | **10.0** | Unmeasured judgment call. Needs a swept-scale comparison vs `bpa_consensus`. |
| Replacement levels | RB30 / WR40 / TE10 / QB10 | Measured over 26 seasons under this league's rules. TE10 is the solid part; RB/WR split moves ±1 rank by year selection. |
| DEF replacement level | **None, permanently** | No DST scoring ingested. Declared in `league.json`, not an oversight. |

## Validation status — read this before quoting the product's core claim

The signature claim is **calibrated availability**. It is currently **not calibrated**.
**1 of ~30** required mock drafts is logged (and that one is the real 2025 draft, `is_mock=0`).
Until that number moves, availability output is an honest estimate, not a validated probability.
This is a data-volume fact, not a defect, and stating it plainly is required by Principle #2.

Mock-logging contamination control is **specified and must land before the first logged pick**
(ADR-D, thread 034): entry shortlist ordered by frozen board rank with no probabilities shown, a
seeded block-randomised blind arm of 10 of 30, `entry_mode`/dwell instrumentation, and a matcher
forbidden from consulting model output. Retrofitting discards mocks, so this precedes collection.
The realistic precision at 30 mocks is **±8 to ±10 points**, not the ±6 currently on the Mock Lab
screen — Wilson ignores intra-mock correlation. Absolute calibration will rest on the 10 blind mocks
(≈±14) because the sighted arm's absolute number is not contamination-free.

Alpha detection is **closed until ~2028** (ADR-026) — the season-level bootstrap floor sits above
the Benjamini-Hochberg threshold regardless of effect size. Do not reopen; it is a sample-size
result, not a modelling failure.

## Built and working

Board + VBD with format-corrected replacement levels · identity hub (`mfl_id`) with quarantine ·
live-availability hazard model · need-weighted `strategy_balanced` · mock-draft ingestion and
validation report · archetype assignment and display-only descriptions · multi-league config and
export routing · 24-config board matrix · deterministic narration Facts layer · FantasyPros ECR
preseason rankings 2021–2025 (`rankings` table, `is_preseason_final` flagged) · historical injury
reports 2010–2024 with enforced `as_of_date` (`injuries` table, `src/ingest_reference.py`; 2009
mostly undated at the source and dropped, 2025 has no `date_modified` column upstream yet) ·
**Opponents tab** (built this sprint, verified rendering live this session — thread 038/041;
`rosters.json`/`opponents.json`-backed, honest "not supplied"/"partial"/empty-roster null states,
5/5 tests passing) · league rosters export (`rosters.json`, mechanical starters/flex/bench/needs
from real draft picks on file; currently all-empty because the real 2026 draft hasn't started,
which is the correct state, not a bug) · **Mock Lab live-logging store** (`src/mock_lab_store.py`,
thread 025, ADR-046: `mocklab_drafts`/`mocklab_picks`, pick-at-a-time create/append/undo/close,
event-sourced per the thread 040 amendment — undo truncates and replays, no voided records, no
undo count; predictions derived on demand and guarded by a `model_version` pin, not stored;
Brier/calibration scoring built over an unfitted rank-decay baseline pending the real hazard model
being wired for arbitrary slots — see ADR-046 gap note; no UI, no export artifact yet) ·
**ADR-C pre-registration convention** (thread 020, `src/preregistration.py`/`src/holdout.py`,
additive to the original PR-001..003 mechanism): nine-field confirmatory / four-field exploratory
registration format, the data_seen-amendment-irreversibly-demotes-to-exploratory rule, content-hash
integrity checking, family manifests fixing the BH denominator, and `holdout.load_season(year,
prereg_id)` tying season reads to a registration's declared scope with a signed-unseal-log
requirement on top of the front-matter flag. **Not yet enforced at any entrypoint** — the `prereg`
CLI/pre-commit gate and the PR-001..003 retrofit are deferred, see thread 020 reply.

**Weekly finishes / season stats exports** (thread 017/039, `src/export_history.py`, contract
1.9.0): `data/export/weekly_finishes.json` + `data/export/season_stats.json`, real
`player_weekly_stats` data, 1481-player universe (`season >= 2018` at QB/RB/WR/TE), 2003-2008
target-derived fields explicitly `target_data_unavailable: true`/`targets: null` rather than
zeroed. **Join key fixed 2026-07-27 (thread 052, ADR-048):** `board.json`'s `player_id_gsis` was
hardcoded `null`; now populated from `rankings.player_id` (already a gsis id) threaded through
`make_board.BoardRow.player_id`. **378/378 board players carry it; 371/378 (98.15%) resolve
against `weekly_finishes.json`** (the ~7 misses are players with no `player_weekly_stats` history
at all — an honest null, not a join failure). No `CONTRACT_VERSION` bump — the field already
existed in the schema, only its value changed. Still not wired into `PlayerDetail.tsx`'s
consistency heat-map / three-seasons section — that is frontend's remaining half of thread 052 —
but the join key that blocked it now exists and is measured.

**DraftRoom pick-entry TypeAhead + availability presentation** (thread 029 retargeted off
`Board.tsx`, thread 037 item 1, RETROFIT-5/thread 036): `DraftRoom.tsx`'s available-player rows now
carry the same 10-dot frequency array as the player detail sheet / Availability Explorer, and rows
group under `TIER N — M players left` headers (restricted to a single position tab, since
`tier_label` is per-position — mixing under `ALL` would merge unrelated tiers sharing a label); row
height verified unchanged by live measurement. Pick entry backported from the Mock Lab
design-reference mockup (there is no Mock Lab application code — its UI remains unbuilt, only the
backend store above): digits 1-5 commit a shortlisted candidate directly, Backspace on an empty
field undoes the last pick, autofocus re-asserted on every input-node attach (not a one-shot guard),
default shortlist is the top 5 available by real board rank shuffled per pick (no fabricated
"predicted next pick" probability — this codebase has no model for that target), and every pick now
records `entryMode` (`'shortcut' | 'typed' | 'pasted'`), exported through `toDraftLog`. Deliberately
a smaller vocabulary than ADR-D's `mock_picks.entry_mode` (Status: Proposed, Mock-Lab-scoped) — not
yet reconciled with it; flagged in the thread 036 reply as needing deliberate resolution before
DraftRoom's exported log is treated as calibration input. `lib/format.ts::percent()`'s `<1%` branch
(thread 037 item 1) was already shipped in `09391e4`; this session only added the literal test case
the thread asked for and closed the reply loop. None of this is screenshot-verified — verified via
live DOM/state measurement in a real (non-screenshotting) browser session instead; see thread
replies for detail.

## Not built / null-stated

Predictions tab (**absent from the shipped app**) · Season mode entirely · Settings editor ·
Mock Lab UI (backend store now exists, thread 025 — see Built and working) · Compare tray ·
league creation / real multi-league slot support (thread 040 item 1, open) · live "Ask the
assistant" wiring · LLM prose renderer
(deliberately deferred — hallucination risk, reasoning stated in code) · `RB_HANDCUFF` archetype
(depth charts end 2024) · recompute progress streaming.

## Top open items

1. **Per-pick draft-state logging + ADR-D contamination instrumentation** — must land *before* mock
   collection begins, or the mocks collected cannot validate `delta` no matter how many there are,
   and cannot be defended against shortcut bias at all.
2. **ADP snapshot capture** — unrecoverable if delayed; a past date's snapshot cannot be backfilled.
3. **Mock drafts toward n=30** — gates the pre-registered availability decision rule.
4. **FantasyPros licence decision (D-020)** — the source audit (`docs/research/source-audit-2026-07.md`,
   2026-07-26) found FantasyPros now sells tiered **API** licences: Free = non-production/sample data,
   Premium $8.99/mo = personal & non-commercial, **Commercial = redistribution rights, price not
   public**. D-000 (no purchase, use the logged-in CSV export) settled *retrieval* and still holds;
   *displaying* ECR to anyone but the founder is unlicensed on every tier below Commercial.
5. **`strategies.json` re-export** — stale at contract 1.7.0 while every other export artifact is
   1.8.0; app's version banner correctly flags this (thread 042, open to backend).

## Hard dates

- **Late August** — board re-pull. Current board is `is_preseason_final = 0`; rankings will move.
- **Late Aug / early Sept** — the draft. Everything above is measured against this.
