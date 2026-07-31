# 2026-07-30 — backend — availability opponent-model M0/M1 measurements

Ran the M0 gate and M1 central-tendency measurement pre-registered in
`docs/ranking/availability-opponent-model-precommit.md`, dispatched via
`docs/handoffs/2026-07-30-availability-adp-measurements-m0-m5.md`. Full results, citations, and
per-mock tables are in that thread's `### backend · 2026-07-30` reply — this is a pointer, not a
duplicate.

**M0 (gate): FAILS to reconcile.** FFC's own help documentation
(`help.fantasyfootballcalculator.com/article/34-...`) says nothing about how `times_drafted` relates
to `total_drafts_in_sample`; live-API-verified (not just the committed CSV) that
`sum(times_drafted)` is 6.4% of the picks-per-draft × n_drafts figure FFC's own API meta implies,
and Ja'Marr Chase's count fell 189→175 while the total rose 1187→1254. No defensible per-player n.
**M2/M3 (dispersion) stay blocked**, per the pre-registration's own rule.

**M1: H1 NULL.** FFC half-PPR ADP beats `fantasypros_ecr` on pick-MAE in only 1 of 3 logged mocks
(founder mock, by 0.16 picks); loses by 1.26 picks (10-team Yahoo) and 2.71 picks (12-team Yahoo).
Mean gap across mocks: **−1.27 picks, ECR ahead**. Neither pre-registered threshold (all-three /
mean gap ≥ 2.0) is met. Reproduced the pre-registered arithmetic check exactly (10-team mock R1/R2/R3
MAE vs FFC half-PPR = 1.12/3.66/8.22 picks). Per the pre-registration, this NULL blocks any
founder-facing "ADP is more accurate" claim; it does not block adopting ADP on estimand grounds
(thread 119).

**Process gap surfaced and escalated, not worked around:** no allocator exists for `PR-0NN`
pre-registration ids — third session to hit this. Opened
`docs/handoffs/2026-07-30-no-allocator-exists-for-pr-0nn-pre-registration.md` to `pm` rather than
hand-typing an id. M1 therefore ran outside `src/preregistration.require_confirmatory` and is not
yet in `docs/preregistration/test_run_log.jsonl` — the pre-registration's thresholds and rules were
followed to the letter regardless; only the formal logging step is deferred.

**Scope not attempted this session:** M2 (blocked by M0 anyway), M3, M4, M5 — the dispatch scoped
this session to M0/M1 only. The pipeline (`analysis/availability_adp_m0_m1.py`) is reusable for a
follow-up.

**Files touched:**
- `analysis/availability_adp_m0_m1.py` (new) — the M0/M1 pipeline, reproducible from the committed
  CSVs and `data/nfl.db`.
- `docs/handoffs/2026-07-30-availability-adp-measurements-m0-m5.md` — full reply with citations,
  per-mock MAE/ρ tables, and the guardrails checklist.
- `docs/handoffs/2026-07-30-no-allocator-exists-for-pr-0nn-pre-registration.md` (new) — the
  allocator-gap escalation to `pm`.
- `docs/CURRENT-STATE.md` — in-place update to the CONTRACT_VERSION 1.17.0 paragraph noting the
  M0/M1 outcome.

**Commit:** `e551dcc`.
