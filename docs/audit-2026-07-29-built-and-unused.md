# Audit — capability already built and sitting unused (FR-043)

**Date:** 2026-07-29 · **Role:** librarian · **Method:** repo-wide, evidence-based. No building,
no refactoring, no deleting. One disposition per item: **USE / FINISH / DELETE / LEAVE**.

Founder's own words, the reason this exists: *"Probably should see if anything else is built
sitting around we can use."* Full request: `docs/founder-requests/FR-043-audit-for-capability-
already-built-and-sitting-u.md`.

Evidence method for item 1: every `src/*.py` module (42 files) checked for real import references
(not comment mentions) across `src/`, `scripts/`, `tools/`, `experiments/`, and `tests/`
separately, plus a second pass for subprocess-style invocation (`scripts/rebuild_database.py`
shells out to several ingesters by path, which a plain `import`-grep misses — corrected below).
Script: not committed (scratch tooling), rerunnable as the grep commands quoted per item.

---

## 1. Python modules in `src/` with no caller

| Module | Real caller | Disposition | Evidence |
|---|---|---|---|
| `league_builder.py` | `scripts/rebuild_ethans_expert_league.py` (real, non-test) + `tests/test_league_builder.py`. **No UI, no API, no Settings-screen consumer.** | **Already tracked — do not duplicate.** This is the module that triggered FR-043. FR-040 already found it (`docs/founder-requests/FR-040-*.md`); a separate agent is establishing what it can/cannot do this same round per this session's dispatch note. | `grep -rn "league_builder" src/ scripts/ tools/` |
| `narrate.py` | **None.** No import anywhere in `src/`, `scripts/`, `tools/`, `experiments/`. No `__main__`. No `json.dump`/`write_text` call — it produces nothing that reaches `data/export/`. Only `tests/test_narrate.py` exercises it directly. | **LEAVE**, but flag explicitly. Documented in `CURRENT-STATE.md` as "deterministic narration Facts layer" under "Built and working," which is true but understates the gap: this isn't "no UI," it's **unreachable from any entrypoint at all**, CLI included. It is Layer 1 of a two-layer design; Layer 2 (LLM prose composition) is deliberately deferred for hallucination risk, per its own docstring and `CURRENT-STATE.md`'s "Not built" list. Correctly parked, not a surprise — but worth stating plainly since nothing currently reads a single `Fact` this module produces. | `grep -rn "^import narrate\|from narrate import" src/*.py scripts/*.py tools/*.py` → 0 hits |
| `mock_lab_store.py` | Tests only (`tests/test_mock_lab_store.py`). | **LEAVE** — known, already documented (Mock Lab backend store, no UI, `CURRENT-STATE.md`). See item 2. |
| `generate_config_matrix.py`, `export_history.py`, `player_descriptions.py`, `mock_validation_report.py`, `regimes.py`, `run_draft_sim.py`, `export_strategies.py`, `spike_persistence.py`, `lambda_estimation.py`, `candidate_rankings.py` | Each has a `__main__` block and is documented in `docs/data-contract.md` / `docs/decisions.md` / `docs/can-we-rebuild-the-database.md` as a manually-run CLI. Not imported by any other `src/` module (confirmed per-module below), so "no caller" in the automated sense, but each produces a real, cited artifact (an export file, or a one-off statistical measurement feeding an ADR/constant) and is run by hand on purpose. | **LEAVE** — working as designed. These are intentionally manual tools (research CLIs, artifact regenerators), not dead code. `export_strategies.py` and `generate_config_matrix.py` in particular are actively re-run (thread 042 close, FR-042 rewrite in progress). |
| `ingest_league_metrics.py`, `ingest_weekly_stats.py`, `ingest_reference.py`, `ingest_rankings.py`, `ingest_fantasypros_csv.py`, `ingest_mock_drafts.py`, `ingest_mfl_adp.py` | **Correction to a first-pass false negative:** a plain `import`-grep shows zero callers for most of these. They are in fact invoked by `scripts/rebuild_database.py` via `subprocess.run([python_exe, str(SRC_DIR / "<module>.py"), ...])` (`scripts/rebuild_database.py:136-198`), which an import-grep cannot see. **All seven are real, live callers.** | **LEAVE** — in use, not orphaned. Recorded here because the false negative is itself a finding: an import-only caller search under-counts real usage in this repo, and any future audit should also grep for `SRC_DIR /` / subprocess dispatch. |
| `ingest_play_callers.py` | **None** — zero callers, zero tests. | **LEAVE.** Its own docstring: `"PARKED. Play-caller ingestion — schema only, no data."`, with a named completion trigger (ESPN's annual 32-team play-caller roundup, due late August). Independently reconfirmed by `docs/research/nflverse-unused-data-audit-2026-07-29.md`: no `nflreadpy` loader supplies play-calling duty, so nothing closes this gap yet. Deliberately parked twice over — not a hidden orphan. |
| `preregistration.py` / `holdout.py`'s ADR-C convention | Imported (`run_draft_sim.py`, `holdout.py` cross-imports), but **"not yet enforced at any entrypoint"** — `CURRENT-STATE.md`, thread 020 reply. | **Already tracked**, not new — listed here because it's a third instance of the same pattern as Mock Lab and `narrate.py`: built, tested, and structurally disconnected from anything that runs it automatically. |

**All other `src/*.py` modules** (`archetypes`, `availability`, `backtest`, `config`, `db`,
`draft_sim`, `export_contract`, `export_static`, `freshness`, `identity`, `ingest_ffc_adp`,
`league_config`, `live_availability`, `make_board`, `roster_status`, `scoring`, `suspensions`,
`team_codes`) have real, multiple `src/`-internal callers. No finding.

### The crossed check the coordinator asked for specifically

`src/generate_config_matrix.py` (about to be rewritten, FR-042) and `src/league_builder.py` (FR-040,
audited separately this round) both build a per-config `LeagueConfig` by `copy.deepcopy()`-ing
`scoring.LEAGUE` and swapping only the reception value, holding every other rule (TD values,
yardage bonuses, INT, defense) at Westwood's ruleset regardless of the target config. I searched
for a **third**, undiscovered instance of the same fault class:

```
grep -rn "deepcopy(scoring\|deepcopy(LEAGUE\|deepcopy(_BASE_LEAGUE\|scoring.LEAGUE\b\|from scoring import LEAGUE" src/*.py
```

Result: only those two files copy `LEAGUE` as a mutable default (`export_contract.py` and
`league_config.py` import `LEAGUE` too, but as the primary league's own real scoring, not a
borrowed default for another config — `league_config.py:163`'s `_current_league_scoring()` backs
`build_current_league()`, the actual Westwood config). **No third occurrence exists.** This is a
negative finding worth stating plainly rather than leaving implied: the fault is contained to the
two places already known and already being worked, not spread further.

### Item 1 × backlog — no other undiscovered match found

Beyond `league_builder.py` × FR-040 (known) and the `scoring.LEAGUE`-copy pattern × FR-042 (known),
I checked several open threads against `src/` for a hidden existing solution and found none:

- **Thread 026** (recompute progress streaming) — no streaming/progress/websocket infrastructure
  exists in `src/`; no FastAPI app exists in the repo at all despite `CLAUDE.md` §4 naming it as
  the eventual API layer. Nothing to surface.
- **FR-033 (bottom-up ranking "from zero")** — `experiments/bottomup/` (model.py, data.py,
  metrics.py, situation.py, run.py, `REPORT.md`, `VARIANTS.md`) is substantial and real, but this
  is **not** a hidden find — it is the `ranker` role's active, ongoing work
  (`docs/ranking/bottom-up-research-pass-1.md`, threads 084/085), already known to whoever raised
  FR-033. Not an audit finding.

---

## 2. Backend capability with no UI

| Capability | Evidence | Disposition |
|---|---|---|
| **Mock Lab live-logging store** (`src/mock_lab_store.py`) | `CURRENT-STATE.md`: "no UI, no export artifact yet." Confirmed — zero references outside tests. | **FINISH** (already an open build item; not new) |
| **`narrate.py` deterministic Facts layer** | See item 1. Not merely "no UI" — no consumer of any kind. | **LEAVE**, blocked on the deliberately-deferred LLM prose layer (Layer 2). Worth naming as a second instance of the same shape as Mock Lab. |
| **ADR-C pre-registration convention** (`preregistration.py`/`holdout.py`) | "Not yet enforced at any entrypoint" — `CURRENT-STATE.md`, thread 020. | **Already tracked**, third instance of the pattern. |

Three "built, tested, structurally disconnected from anything live" capabilities now exist in this
repo (Mock Lab, `narrate.py`, ADR-C enforcement). None is new information on its own, but the
recurrence is worth naming as a pattern rather than three unrelated facts — see Escalation below.

---

## 3. Data ingested and unused

**Already fully covered — cite, don't repeat.** `docs/research/nflverse-unused-data-audit-2026-07-29.md`
(data-ops, same day) measured this directly: 10 of 23 `nflreadpy` loaders are called by this repo.
I re-checked the FR-043 anchor claim against that audit rather than trusting the paraphrase:

- **`load_schedules()`'s `home_coach`/`away_coach`** (1999–2026, 7,548 rows, zero nulls) — real,
  but the audit is explicit this is a **partial** close of the coaching gap: verified **head-coach**
  identity only, not coordinator/play-caller duty, which is what `src/ingest_play_callers.py`
  actually exists for. The FR-043 anchor's phrasing ("carries coaches 1999-2026") risks reading as
  a full close; it is not one. `src/ingest_play_callers.py` staying parked is still correct.
- **`load_participation()`'s `route` column** (2016–2025 only, not before) — a real, documented
  proxy for route-participation, closing "a real chunk" of the gap per that audit's own wording,
  not all of it (no pre-2016 coverage).
- Both loaders remain **not ingested** — the audit measured them without writing to `data/nfl.db`.

**`CLAUDE.md` §5 is now stale against this finding**, and I am flagging rather than editing it —
see Escalation. It currently states coaching data is "Not in nflverse" and route data "not
directly in nflverse — needs NGS or a documented proxy calculation" with no acknowledgment that
`load_schedules`/`load_participation` partially answer both, and that the test-registry's pointer
to FTN charting for route data is confirmed wrong (`load_participation`, not FTN, is the real
proxy — FTN has no route field at all, per the same audit).

**`data/nfl.db` tables:** all 24 tables have at least one real read or write reference in `src/`.
Several (`injuries`, `depth_charts_weekly`/`_snapshots`, `snap_counts`, `ngs_receiving`/`_rushing`/
`_passing`, `draft_picks`, `combine`) are written by their ingester but have no read-side consumer
in the ranking/export pipeline yet — this matches Phase 1's documented scope (ingestion
infrastructure ahead of the ranking algorithm, `CLAUDE.md` §3) and is already tracked via open
threads 057/070 and open items T6/T7 in `CURRENT-STATE.md`. Not a new finding.

---

## 4. Documents cited but absent (the inverse case)

**Already found and reported same-day, by researcher, thread 086** (`docs/handoffs/
086-competitive-ux-the-overhaul-case-is-weaker-than.md`) — I am not duplicating that
investigation, only acting on the part addressed to librarian/PM. The missing artifact:
`docs/operating-model.md`'s budget table logs a completed "Competitive UX + platform + Reddit
research" pass (pre-2026-07-26 row) whose file does not exist anywhere in the repo or any agent
worktree. Thread 086 names six citing documents: `docs/design-handoff/HANDOFF-NOTES.md`,
`docs/design-handoff/README.md` Addendum 3, `docs/handoffs/030`, `docs/handoffs/047`,
`docs/adr-drafts/ADR-A`, `docs/screenshot-checklist.html`.

**Corrected in place this session** (the two carrying the disputed numeric scores, which is where
the real risk is — a number with no evidence behind it is worse than a paraphrase with no evidence
behind it):

- `docs/operating-model.md` — the budget-log row itself now states plainly it is unverifiable.
- `docs/design-handoff/HANDOFF-NOTES.md` — the "5/10 visual polish, 4/10 light mode" line now
  carries a correction note: unverifiable, treat as an unconfirmed prior, and points at the
  2026-07-29 re-run (`docs/research/competitive-ux-2026-07-29.md`) which reached the same
  token-level (not redesign) conclusion independently, on evidence that does exist.

**Not touched, left for PM/frontend per thread 086's own disposition** (avoiding duplicated work
on a thread already open and addressed elsewhere): `docs/design-handoff/README.md` Addendum 3,
`docs/handoffs/030`, `docs/handoffs/047`, `docs/adr-drafts/ADR-A`, `docs/screenshot-checklist.html`.
None of these carry a disputed number the way HANDOFF-NOTES.md did; they cite the pass's
conclusion only, not its scores.

No other phantom-citation pattern was found in the time available — this was not an exhaustive
sweep of every document citing a research pass, only the one thread 086 already surfaced.

---

## 5. Exports written and never read

Checked `data/export/board.json`'s real top-level and per-player keys (56 fields) against every
`.ts`/`.tsx` file under `frontend/ui` excluding generated data bundles (which embed the JSON
verbatim as a string and produce false-positive matches on every field name).

**Genuinely invisible to the frontend — not even declared in `frontend/ui/data/types.ts`:**

- `replacement_levels_flex_split_measured`
- `replacement_levels_flex_split_note`

**Declared in `types.ts` (or registered in `trace-fields.ts`) but never rendered by any component:**

- `attribution_identity`
- `attribution_is_additive`
- `published_levels_compared_against`
- `consensus_source_count`
- `unsupported_positions` / `unsupported_positions_note`

Evidence: `grep -rl "<field>" frontend/ui --include=*.ts --include=*.tsx | grep -v generated`,
cross-checked against `frontend/ui/data/types.ts` directly for the two fields with zero hits at all.

**Disposition: LEAVE, flag for frontend.** These are honest, sourced fields already in the
contract (some brand-new — `replacement_levels_flex_split_*` backs the flex-split placeholder
noted in `league_builder.py`'s own docstring). Not a defect on their own; worth a frontend thread
if any of them should surface (in particular `unsupported_positions_note`, which is exactly the
kind of "why is DEF missing" explanatory text the product already values elsewhere on the board).
Not opening that thread here — outside librarian's remit to prioritize frontend's queue, and none
of these block anything currently in flight.

**Already-known, separately-tracked gaps, not counted as new here:** `global_tier` (thread 071),
`sim_generated_at`/`sim_settings_hash` (thread 072), the weekly-finishes/season-stats join to
`PlayerDetail.tsx`'s consistency heat-map (thread 052's open half).

---

## Disposition summary

| Disposition | Count | Items |
|---|---|---|
| **USE** | 0 | (item 1's `league_builder.py` finding is being separately actioned via FR-040/other agent, not counted here to avoid double-counting) |
| **FINISH** | 1 | Mock Lab UI (already an open, tracked item — not new) |
| **DELETE** | 0 | Nothing found warranting deletion this pass |
| **LEAVE** | 19 | `narrate.py`, ADR-C enforcement, 10 manual-CLI modules (generate_config_matrix, export_history, player_descriptions, mock_validation_report, regimes, run_draft_sim, export_strategies, spike_persistence, lambda_estimation, candidate_rankings), `ingest_play_callers.py`, 5 unrendered board.json fields (counted as one line item), the 7 ingest modules cleared of the false "no caller" finding |
| **CORRECTED IN PLACE** | 2 | `docs/operating-model.md`, `docs/design-handoff/HANDOFF-NOTES.md` (item 4) |
| **ESCALATED, NOT RESOLVED** | 1 | `CLAUDE.md` §5 coaching/route-data staleness (item 3) |

---

## Escalation (not resolved here — librarian does not resolve contradictions unilaterally)

Opened `docs/handoffs/<id>-audit-2026-07-29-claude-md-staleness-and-built-.md` (id from the
allocator, see thread for the exact number) to `pm`:

1. `CLAUDE.md` §5's coaching-data and route-data rows are stale against
   `docs/research/nflverse-unused-data-audit-2026-07-29.md` (same-day, same repo). A `CLAUDE.md`
   edit is a spec change and is out of librarian's authority per the project's own rules — PM/
   founder call.
2. Three built-but-structurally-disconnected backend capabilities now exist (Mock Lab store,
   `narrate.py`, ADR-C pre-registration enforcement). Naming the pattern in case it's worth a
   standing check, not asking for one to be built (per thread 062's "name a failure that has
   actually occurred" bar — this hasn't cost anything yet, unlike `league_builder.py`, which is
   why it's a note, not a build request).

## Commit

Two documents corrected in place this session, committed separately from this audit file per the
mid-task instruction to commit after each discrete step. See git log for hashes (`docs/operating-
model.md` + `docs/design-handoff/HANDOFF-NOTES.md` in one commit; this audit file in a second).
