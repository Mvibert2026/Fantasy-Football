# Factor-inclusion campaign — the founder's four numbers

**Generated 2026-08-04 01:25 UTC** by `experiments/bottomup/v2/report070.py` — regenerate any time with `.venv/bin/python -m experiments.bottomup.v2.report070`. The sweep driver regenerates it after every batch grades, so this file is as current as the compute.

Instrument: ADR-070 (permutation nulls, sequential MC, BH at campaign M = 442, calibrated consistency). Panel: tier 2, `m_panel_ppr12`, trained from 2002, graded 2013–2024 (per-position S_pos on every cell). VERIFY gate: PASSED — measured false-positive rate 5.0% against a pre-committed 5.0%, zero placebo inclusions.

## The four numbers

| | |
|---|---|
| **1. Factors tested for inclusion (ADR-070, tier 2)** | **0** (of 27 registered — 27 still computing) |
| **2. Factors that passed (INCLUDE at ≥ 1 position)** | **0** |
| **3. Per-position passes** | QB 0 · RB 0 · WR 0 · TE 0 — table below |
| **4. Untestable / not yet testable** | see the audit table below |

**27 registered factors are still in the compute queue** (sweep phases done: ['VERIFY']); the numbers above grow as it drains. Pending: D1A1:Q0 — games-model population refit (restrict); D1A1:Q1 — availability quality block (full); D1A1:Q2 — availability quality block (ppg-free); C1:F1 — offensive snap share, recency-weighted; C1:F2 — red-zone (inside-20) usage share of team; C1:F3 — expected fantasy points per game + realised-minus-expected residual; C1:F4 — NGS average separation (lag 1); C1:F5 — route participation and targets per route run (LABELLED PROXY); C1:F6 — steeper recency weighting of prior seasons (0.70/0.22/0.08); C2:A1 — WOPR, recency-weighted (WR/TE); C2:A2 — YAC per reception, EB-shrunk (RB) -- batch-7 block, reused; C2:A3 — receiving share of RB's own points (RB) -- batch-7 block, reused; ….

## 3 — Which factors passed, per position

- **QB:** none
- **RB:** none
- **WR:** none
- **TE:** none

## Every graded factor, per position

## Incumbents (batch AB1 — ablation audit, registered translation)

*Still in the compute queue.* Arms registered: ABAGE, ABEVID, ABEXP, ABGSH, ABPPG, ABSHARE, F0AB

**Four incumbents named in dispatches are NOT in the running model and have no ablation** — reporting them as ablated would be false:

| named incumbent | where it actually is | its real test |
|---|---|---|
| depth chart / role | AVAIL_E only, never shipped | additive arms C3E (and C3C/C3D for the injury side) |
| injury designations | AVAIL_B only, never shipped | additive arms C3C / C3D |
| air yards / aDOT | built by the feature builder, consumed by no spec | additive arms C1 F4 (separation), C2 A1 (WOPR) |
| draft capital (veteran side) | rookie path only; graded endpoint is board veterans | rookie-model registration (season-span-M4 §4), not yet run |

## 4 — Untestable, and why

- **Genuinely blocked on data** (factor ledger, dispositions standing): coordinator/OC continuity (T1-29/30 — `play_callers_preseason` 0 rows, PFR 403), college usage profile (T1-26 — no college table in the DB), player props (never ingested; game-level odds only), FTN charting factors (N1/N2/N6 — source starts 2022, S ≤ 2 inside the panel).
- **Not factors** (structural/config rows in the 132-row ledger): scoring settings, roster shapes, duplicates of base features — the reason the pool is ~45, not 95.
- **F6-class arms** (change a constant, not a column): steeper recency is NOT gradeable under §4.1 and awaits its own registered design (`PR-DRAFT-lag-weight-decay-profile.md`).
- **The blocked-list re-audit** (backend, running) re-checks all 20 BLOCKED rows against today's DB; anything it unblocks is added to the sweep via a batch flag and appears here automatically.
- **The ~90 batch-1–7 nulls are UNCALIBRATED** (old consensus-derived frame + retired estimator) and are cited nowhere in this report, per the standing rule.

## Provenance

Graded CSVs: `experiments/bottomup/results/sweep070/graded_<batch>.csv` (every cell carries Δ̄, the full per-season delta vector, p with its floor and stopping reason, both null tails, C and its null q95, the §4.8 key and S_pos). Registrations: `docs/ranking/factor-campaign-manifest/batch-{C1,C2,C3,C4,AB1,D1-amendment-1}.md`. Verification: `experiments/bottomup/results/sweep070/VERIFY_STATUS`. Watchdog Routine `sweep070-watchdog` (trig_01K9jC4ceHMbUkPQL7CgdVqJ) revives the sweep after container restarts — delete it when the sweep completes.
