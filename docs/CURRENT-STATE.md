# CURRENT STATE

**This file is the canonical answer to "where is the project right now."**
It is edited **in place**. When something changes, replace the affected line — never append a new
section, never leave the old value "for contrast." If you find yourself adding a second version of
a number that already appears here, you are doing it wrong.

Do **not** read `docs/status.md` to answer a current-state question. That file is an append-only
session log and contains superseded figures presented in the same voice as current ones. Same
hazard `docs/assistant-context.md` warns about for `decisions.md`. It is fine to read `status.md`
to learn *what happened*; it is not fine to read it to learn *what is true*.

**Last verified:** 2026-07-26, read directly from the working tree (sprint 1 closeout session).

---

## Build state

| | Value | Notes |
|---|---|---|
| Backend branch / commit | `master` @ `3ea391b` | Local only — **no git remote configured** |
| Backend tests | **400 passing** | Suite runtime ~5.5 min; DB-backed archetype/description tests dominate. +1 from sprint 1 (mailbox health test) |
| Agent infrastructure | **Live** | Six subagents in `.claude/agents/` (backend, frontend, data-ops, strategist, researcher, librarian), `/inbox` command, mailbox tooling at `tools/handoffs.py` + `tools/sprint_status.py`, mailbox health enforced in the test suite (`tests/test_handoffs.py`) |
| Data contract | **1.7.0** | `assistant-context.md` still says 1.6.0 — fix on next touch |
| Frontend branch / commit | `frontend-prep` @ `7276a2d` | Separate working session, **not in this repo** |
| Frontend tests | **unrecorded** | No count exists anywhere. Record one next frontend session. |
| Python modules | 33 in `src/` | |
| Export artifacts | 7 + `player_descriptions.json` | `player_descriptions.json` versions independently, by design |
| Config matrix | 24 dirs under `data/export/` | board + league + availability stub only; **hazard model not rerun per config** |

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

Alpha detection is **closed until ~2028** (ADR-026) — the season-level bootstrap floor sits above
the Benjamini-Hochberg threshold regardless of effect size. Do not reopen; it is a sample-size
result, not a modelling failure.

## Built and working

Board + VBD with format-corrected replacement levels · identity hub (`mfl_id`) with quarantine ·
live-availability hazard model · need-weighted `strategy_balanced` · mock-draft ingestion and
validation report · archetype assignment and display-only descriptions · multi-league config and
export routing · 24-config board matrix · deterministic narration Facts layer.

## Not built / null-stated

Opponents and Predictions tabs (**absent from the shipped app**, previously misreported as
"folded into one pane") · Season mode entirely · Settings editor · Mock Lab UI and backend ·
Compare tray · live "Ask the assistant" wiring · LLM prose renderer (deliberately deferred —
hallucination risk, reasoning stated in code) · `RB_HANDCUFF` archetype (depth charts end 2024) ·
full league rosters endpoint · weekly finishes / season stats tables · recompute progress streaming.

## Top open items

1. **Per-pick draft-state logging** — must land *before* mock collection begins, or the mocks
   collected cannot validate `delta` no matter how many there are.
2. **ADP snapshot capture** — unrecoverable if delayed; a past date's snapshot cannot be backfilled.
3. **Mock drafts toward n=30** — gates the pre-registered availability decision rule.
4. **FantasyPros paid tier decision** (~$72/yr) — free tier caps at 10 rows, reaches 40 players,
   none of the 233 that need projections. Cannot be engineered around.
5. **Full league rosters endpoint** — the Opponents tab cannot render anything real without it.

## Hard dates

- **Late August** — board re-pull. Current board is `is_preseason_final = 0`; rankings will move.
- **Late Aug / early Sept** — the draft. Everything above is measured against this.
