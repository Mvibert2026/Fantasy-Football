# CURRENT STATE

**This file is the canonical answer to "where is the project right now."**
It is edited **in place**. When something changes, replace the affected line — never append a new
section, never leave the old value "for contrast." If you find yourself adding a second version of
a number that already appears here, you are doing it wrong.

Do **not** read `docs/status.md` to answer a current-state question. That file is an append-only
session log and contains superseded figures presented in the same voice as current ones. Same
hazard `docs/assistant-context.md` warns about for `decisions.md`. It is fine to read `status.md`
to learn *what happened*; it is not fine to read it to learn *what is true*.

**Last verified:** 2026-07-27, backend session (thread 064) — full suites actually executed (not
copied from any thread reply), commit read via `git log -1`, modules/artifacts counted via `ls`,
D-001/D-003/D-006/D-020/D-021 checked against the working tree rather than assumed from
`decisions-needed.md`. See the corrections list at the end of this section for everything found
wrong in prior "current state" claims, including this file's own.

---

## Build state

| | Value | Notes |
|---|---|---|
| Backend branch / commit | `master`, `83170ccfc797471a853c1f7a7dbba3f65a5a0479` | Local only — **no git remote configured** (D-007 deferred by founder, PM to raise once more before the draft) |
| Backend tests | **512 passing, 0 failures** | Full suite (`pytest -q`), single run, no concurrent-agent contention this session, **201s**. This is a real measured full-suite number, not a sum of per-file claims — prior sessions had reported partial totals (423, then +20/+44/+13 in separate files) without re-running the combined suite; that combined run is what produced 512. |
| Agent infrastructure | **Live** | Six subagents in `.claude/agents/` (backend, frontend, data-ops, strategist, researcher, librarian), `/inbox` command, mailbox tooling at `tools/handoffs.py` + `tools/sprint_status.py`, mailbox health enforced in the test suite (`tests/test_handoffs.py`) |
| Data contract | **1.9.0** | `board.json`'s `contract_version` and `frontend/ui/data/trace-fields.ts`'s `TRACE_CONTRACT` both read `1.9.0` — the drift flagged in earlier sessions is resolved. `strategies.json` is still stale at **1.7.0** (verified directly, unchanged) — thread 042, still open, still backend's to re-export |
| Frontend location | `frontend/` subdirectory of this repo | Merged from `frontend-prep` via `git subtree add`, full history preserved. No longer a separate working copy. |
| Frontend tests | **154 passing, 0 failing** (18 files) | Measured this session via `npx vitest run`. The previously-reported single failure (`trace-fields.test.ts`, contract-version mismatch) is gone — contract versions now match on both sides. |
| Python modules | **36** in `src/` | Counted via `ls src/*.py` |
| Export artifacts | **11** top-level JSON files (`availability.json`, `board.json`, `glossary.json`, `league.json`, `nulls.json`, `opponents.json`, `player_descriptions.json`, `rosters.json`, `season_stats.json`, `strategies.json`, `weekly_finishes.json`) + **25** per-config directories under `data/export/` (24 real league configs + one `yahoo_standard_mock` scratch config) |
| Config matrix | 24 real configs + 1 scratch | board + league + availability stub only; **hazard model not rerun per config**; each config's `write_all` also emits `rosters.json` |

## Statistical constants in force

| Constant | Value | Standing |
|---|---|---|
| `DEFAULT_LAMBDA` (roster-need weight) | **0.352** | Measured — 2025 real draft, n=160 / 10 clusters, clustered SE 0.070, z=5.04. One season, one draft. Keep the caveat attached. |
| `delta` (positional-run weight) | **0.10** | **Unvalidated prior, founder-affirmed to ship this way (D-004, decided 2026-07-27).** Kept flagged, with the pre-registered binding rule intact: if need+run does not beat marginal-only on Brier across ≥30 conforming mocks, `delta` goes to zero automatically. Only 1 of ~30 required mocks is logged, so this will not run before the draft — 0.10 ships untested either way. `src/live_availability.py` comments this constraint; no code-level provenance tag was found beyond that comment. |
| `NEED_ADJUSTMENT_SCALE` | **10.0 in code, decision is to delete it** | **Founder decided 2026-07-27 (D-001) to delete this parameter, not adopt or tune it** — verified against the working tree, `src/draft_sim.py:284` still defines `NEED_ADJUSTMENT_SCALE = 10.0` and uses it at line 303. **The decision has not been implemented.** This is a real gap between `decisions-needed.md` (which records what was decided) and the code (which still runs the un-deleted parameter) — flagged here explicitly per the standing warning against conflating the two. |
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
The realistic precision at 30 mocks is **±8 to ±10 points**, not the ±6 originally on the Mock Lab
spec — Wilson ignores intra-mock correlation (D-019, defaulted). Absolute calibration will rest on
the 10 blind mocks (≈±14) because the sighted arm's absolute number is not contamination-free.
Per D-015/D-016 (decided 2026-07-27): harvested drafts (e.g. FFC) count toward calibration but are
never blended with the founder's own drafts — both numbers are reported side by side, tagged by
population, permanently.

**Alpha detection ("our ranking beats consensus") is closed until ~2028 — this is the correct
figure, and the 2029 figure elsewhere in the docs is a different, narrower claim, not a
contradiction of it:**

- **~2028 (ADR-026, general closure).** Beating consensus ADP/ECR requires consensus history, which
  covers 2021–2025 with one season held out. The exact two-sided sign test's minimum attainable p is
  0.125 at n=4 usable seasons, above 0.05 before any multiple-comparisons correction. The track
  reopens once the sign-test floor itself clears 0.05, which needs **n ≥ 6 development seasons**
  (floor 0.031) — on the current one-season-per-year accrual, **2028** (2021–2027, holdout still
  reserved). This is the figure that governs the general "can we claim an edge over consensus"
  question, and it is the one that belongs in this file.
- **~2029 (ADR-A, a stricter, parameter-specific figure).** This number came from a *different*
  question: testing `NEED_ADJUSTMENT_SCALE` specifically required surviving Benjamini-Hochberg
  correction across a 14-test family, which needs n ≥ 9 usable seasons (2021 + 9 = 2029). **D-001
  deleted `NEED_ADJUSTMENT_SCALE`** on 2026-07-27, so the question that produced the 2029 figure no
  longer has a live parameter attached to it. The figure was correct for the test it described; it
  was never a competing answer to the general 2028 question, and prior sessions conflating the two
  (this file included) were wrong to treat it as a discrepancy needing resolution in one direction.

**Bottom-up projection accuracy is a separate, unblocked track**, per thread 046: "our ranking beats
consensus" needs consensus history (blocked to 2028 as above), but "our projections are accurate
against outcomes" only needs `player_weekly_stats`/`player_season_stats`, which run back to 1999 —
measurable now, not gated by the 2028 figure at all. `docs/adr-drafts/ADR-E-bottom-up-projection-
framework.md` is the live proposal on this track (Status: Proposed, awaiting D-023).

## Built and working

Last verified 2026-07-26 — not re-verified.

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
   collection begins, or the mocks collected cannot validate `delta` no matter how many there are.
2. **ADP snapshot capture** — unrecoverable if delayed; a past date's snapshot cannot be backfilled.
   FFC ADP history harvest to 2007 is authorised (D-021, decided) but thread 055 is still `OPEN` —
   not yet executed as of this session.
3. **Mock drafts toward n=30** — gates the pre-registered availability decision rule.
4. **`NEED_ADJUSTMENT_SCALE` deletion** — D-001 decided to delete it 2026-07-27; the parameter is
   still live in `src/draft_sim.py`. This is now the top code/decision drift in the project.
5. **`strategies.json` re-export** — stale at contract 1.7.0 while every other export artifact is
   1.9.0 (thread 042, open to backend).
6. **D-023 (mixed-source board)** and **D-024 (simulation lookahead latency budget)** — both `OPEN`
   in `docs/decisions-needed.md`, both block further work on their respective ADR drafts
   (ADR-E, ADR-F).

## Corrections to prior "current state" claims found this session

Recorded because thread 064 asked for this explicitly as the most valuable output:

- The commit/test/contract figures in thread 064's own comparison table were themselves already
  stale relative to this file by the time thread 064 was written — this file had already been
  updated past that table's baseline. Do not use that table for anything going forward.
- **This file's own prior text was wrong in one place beyond the numbers**: "depth charts end 2024"
  is false as of this session — `depth_charts_snapshots` covers through 2026-07-26. The RB_HANDCUFF
  gap is a code gap (archetype not computed), not a data gap, and the two were previously
  conflated.
- **2028 vs 2029 is not a contradiction** — see Validation status above. Both figures are correct
  for what they each describe; they were never comparable claims.
- **D-001 (`NEED_ADJUSTMENT_SCALE` delete) is decided but not implemented.** `decisions-needed.md`
  records the decision; the code still runs the parameter. Treating a decision as done because it
  is marked `DECIDED`/`RESOLVED` in that file is exactly the failure mode the operating model warns
  about.
- Backend test count is a real full-suite run (512), not an assembled total from per-thread deltas
  reported without a combined re-run, which is what the prior entry explicitly admitted it was.
- Frontend's previously-reported single failing test (`trace-fields.test.ts`, contract mismatch) is
  resolved — both sides read 1.9.0 now. 154/154 passing.

---

*(The former "Hard dates" section — a late-August board re-pull and an early-September draft
deadline — is removed per D-009, decided 2026-07-26: the founder removed the draft deadline as a
constraint, and the operating model instructs it should no longer shape sequencing or appear in this
file as if it still gated anything. The board re-pull itself is not a date the founder retracted —
if it still matters operationally, it belongs in `docs/founder-requests.md` or a handoff thread, not
restated here as a "hard date.")*
