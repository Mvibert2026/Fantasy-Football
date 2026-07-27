# CURRENT STATE

**This file is the canonical answer to "where is the project right now."**
It is edited **in place**. When something changes, replace the affected line — never append a new
section, never leave the old value "for contrast." If you find yourself adding a second version of
a number that already appears here, you are doing it wrong.

Do **not** read `docs/status.md` to answer a current-state question. That file is an append-only
session log and contains superseded figures presented in the same voice as current ones. Same
hazard `docs/assistant-context.md` warns about for `decisions.md`. It is fine to read `status.md`
to learn *what happened*; it is not fine to read it to learn *what is true*.

**Last verified:** 2026-07-27, backend session (thread 064, narrowed scope) — build-state table
below is measured directly from `git rev-parse HEAD`, the real backend/frontend test-suite runs,
`CONTRACT_VERSION` in `src/export_contract.py`, and file counts in `src/`/`data/export/`. Nothing in
this pass was inferred by reading source to determine what is or isn't built — see the note at the
top of "Built and working" for that section's own verification status, which is separate and older.

---

## Build state

| | Value | Notes |
|---|---|---|
| Backend branch / commit | `master`, `c8738ed8cc8c3d8bfc4f7f23a2d771ecb85c33cf` | Local only — **no git remote configured** |
| Backend tests | **516 passing, 0 failures** | Full suite, `pytest -q`, single run, 199s. No concurrent DB contention observed this run (checked for another active backend session first). |
| Agent infrastructure | **Live** | Six subagents in `.claude/agents/` (backend, frontend, data-ops, strategist, researcher, librarian), `/inbox` command, mailbox tooling at `tools/handoffs.py` + `tools/sprint_status.py`, mailbox health enforced in the test suite (`tests/test_handoffs.py`) |
| Data contract | **1.9.0** | `CONTRACT_VERSION` in `src/export_contract.py`, read directly. |
| Frontend location | `frontend/` subdirectory of this repo | Merged from `frontend-prep` via `git subtree add`, full history preserved. No longer a separate working copy. |
| Frontend tests | **154 passing, 0 failing** (18 files) | Full suite, `npx vitest run`, single run, ~31s. |
| Python modules | **36** in `src/` | `ls src/*.py \| wc -l` |
| Export artifacts | **11** top-level files in `data/export/` | `ls data/export/*.json \| wc -l` |
| Config matrix | 25 dirs under `data/export/` | board + league + availability stub only; **hazard model not rerun per config**; count is a raw directory count, not inspected for which are real league configs vs. scratch |

## Statistical constants in force

| Constant | Value | Standing |
|---|---|---|
| `DEFAULT_LAMBDA` (roster-need weight) | **0.352** | Measured — 2025 real draft, n=160 / 10 clusters, clustered SE 0.070, z=5.04. One season, one draft. Keep the caveat attached. |
| `delta` (positional-run weight) | **0.10** | **D-004, defaulted:** keep at 0.10, visibly flagged as an unvalidated prior, honouring the pre-registered rule — if need+run does not beat marginal-only on Brier across ≥30 conforming mocks, `delta` goes to zero automatically. Not re-verified against code this pass. |
| `NEED_ADJUSTMENT_SCALE` | **D-001, decided: delete** | Founder decided 2026-07-27 to delete this parameter outright — do not adopt 10.0, do not fit a value. This is what the decision says; whether the code has been updated to match was **not checked this pass** (out of this session's narrowed scope). |
| Replacement levels | RB30 / WR40 / TE10 / QB10 | Measured over 26 seasons under this league's rules. TE10 is the solid part; RB/WR split moves ±1 rank by year selection. |
| DEF replacement level | **None, permanently** | No DST scoring ingested. Declared in `league.json`, not an oversight. |

## Decisions applied from `docs/decisions-needed.md` (this pass, narrow set only)

Recorded as what each decision *says*, not verified against implementation:

- **D-001** — delete `NEED_ADJUSTMENT_SCALE`. Do not adopt or tune a value.
- **D-003** — show rank numbers at TE/QB/DEF, but the unproven-ordering status must be structural
  (a visibly distinct treatment on the rank number itself, not a footnote) — founder departed from
  the rigorous tiers-only default. Re-evaluate when per-position n rises materially above ~20.
- **D-004** — see Statistical constants above.
- **D-006** — **CLOSED.** `nfl.db` is not tracked in git, `.gitignore` covers it. No history rewrite
  needed.
- **D-013** — **MOOT.** Single-user tool; the founder is the only league-settings editor. Reopens on
  any second user.
- **D-015 / D-016** — harvested drafts (e.g. FFC) and the founder's own drafts are both counted
  toward calibration, but reported as two separate numbers, tagged by population, and **never
  blended**. Other users' mocks are stored in the harvested pool, never silently merged into the
  personal pool.
- **D-020** — **CLOSED — no FantasyPros licence needed.** The product is private, personal, and
  displayed to nobody but the founder. Reopens on any second user, alongside D-021.
- **D-021** — **DECIDED — loosened.** Founder authorised harvesting Fantasy Football Calculator ADP
  history back to 2007 for private use, via the HTML endpoints (not the robots-disallowed CSV path),
  rate-limited, cached, pulled once per season-format. Void if the product ever ships to a second
  human.

No other entries in `decisions-needed.md` were applied this pass — this list is deliberately
narrower than earlier attempts at a full sweep.

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

**Alpha detection: CONTESTED between ~2028 and ~2029 in the docs.** `docs/CURRENT-STATE.md`
(previously) and `docs/dashboard.html` say ~2028 (ADR-026). `docs/decisions-needed.md` (D-001) and
`docs/adr-drafts/ADR-A-need-adjustment-scale.md` say ~2029. Both cite a sign-test-floor /
multiple-comparisons argument over consensus-history seasons, but the two documents were not
compared closely enough this pass to state with confidence whether they are the same claim at
different correction stringency or two different claims — flagging as `CONTESTED` per this
session's instruction to not sink real effort into resolving it. **Do not treat either figure as
settled until a session with the digging in scope confirms one.**

## Built and working

**Last verified 2026-07-26 — not re-verified.**

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
4. **FantasyPros licence decision — CLOSED (D-020).** No licence needed while the product stays
   private/personal/founder-only. Reopens on any second user, alongside D-021.
5. **`strategies.json` re-export** — stale at contract 1.7.0 while every other export artifact is
   1.9.0; app's version banner correctly flags this (thread 042, open to backend).
