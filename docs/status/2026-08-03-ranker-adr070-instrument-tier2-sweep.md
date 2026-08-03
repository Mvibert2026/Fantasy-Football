# 2026-08-03 · ranker · ADR-070 instrument built, tier-2 panel live, detached sweep launched

**Commits `fdca7f7` → `fee403a`** (plus `a9f0d0e` from the previous attempt: `adr070.py` + 27
tests). Branch `claude/pm-agent-setup-gobxa0`.

## What exists now

- **The §4.1 draw engine** (`ensemble070.py`): joint within-season permutation of the arm's own
  column block, sha256 season-keyed; tier-2 window map (`m_panel_ppr12`; QB/RB ff=2002 S=12,
  WR/TE ff=2012 S=11); both endpoint families (rho_points, mae_games); §4.8 keys asserted on every
  delta join; audit-preserving cross-draw frame cache; `adp_fmt` added to WalkForward (additive,
  default reproduces every prior batch).
- **D1-A1 models** (`d1a1_models.py`): Q0 restrict/weight population refit with a
  membership-permutation null (arm adds no column — F6 class); Q1/Q2 quality-block availability
  specs; PG0 games-endpoint placebo.
- **The grader** (`grade070.py`): CellReports from disk — Besag–Clifford (h=20, L=5,999),
  calibrated consistency, BH at campaign **M=259** (C2's registered 29 restored), lazy VOID via
  paired k-arm p, `delta_bar_pre2018` on every cell for the F3-RB confirmatory slice.
- **The driver** (`sweep070.py`): detached, resumable, **phase-gated** — VERIFY (LOO + end-to-end
  placebo) must PASS or the process exits before any real factor grades.
- **C3 reconciled and registered** (`factors_c3_adapter.py`, `batch-C3.md`, m_b=25): backend's
  builders mapped to the real block interface; per-factor matched windows; own placebo.
- **§4.8 backfill**: 865 published B1/C1/C2 rows keyed, no numbers re-derived.

## Running when this session ended

`sweep070` PID 10688 (launched 23:22 UTC), VERIFY phase drawing (~2.6 s/draw wall, 3 workers).
Queue: VERIFY → D1A1 (Q0 first) → C1 → C2 → C3 → VD2/VD3. Est. 1–3 days. State:
`experiments/bottomup/results/sweep070/` — see `docs/ranking/adr070-tier2-execution.md` NEXT STEP
for the relaunch line and the successor checklist.

## Findings flagged (thread `2026-08-01-m-1-m-6-…`, still OPEN)

1. ppr12 archive shallow pre-2017 → realised S_pos QB 10 / RB 9 / WR 11 / **TE 7** — TE gains
   nothing from tier 2.
2. Campaign M under-counted (230 omitted C2's 29) → grading at 259/284.
3. Q0 needs its own family (T2Q, 2015–2024) — board history starts 2013.
4. Q0's membership-permutation null construction — strategist can veto before D1A1 grades.
5. Q0 smoke at TE: board bias −2.29 → +0.60, MAE 3.63 → 2.46 (naive 3.12) — direction matches the
   registered finding; not a grade, the ensemble decides.

## Not done

M-5, M-7, and the M-6 re-grade of C1 **at S=7 on CTRL-A/B/C** (the tier-2 re-run deliberately does
not discharge it — span and estimator must not confound). Rookie build unstarted.
