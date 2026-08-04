# 2026-08-04 — backend — v3 candidate pool: standalone screen 2 + blocked-row re-audit

**Dispatch**: "Complete the v3 candidate pool" — re-audit the ledger's 17 `blocked` rows against
`data/nfl.db` as it exists today, and extend `standalone_screen1.py` (14 factors) to the full pool:
C1's 6, C2's 6, C3's 6, C4's 6, six predictive incumbents, everything newly unblocked, and the
within-cluster contrasts.

## What happened

**Environment note first**: this worktree's `git log` (`fd3bed1`) does not contain
`standalone_screen1.py` or `factors_c1–c4.py` — those exist only as uncommitted work in a sibling
checkout sharing this repo's `.git`. `experiments/bottomup/components/{pos_data,pos_features}.py`
**are** committed here. Wrote `experiments/bottomup/v2/standalone_screen2.py` fully self-contained
(does not import any of the uncommitted sibling files), reproducing the C1/C4 factor mechanisms
from their definition docs (`docs/ranking/batch-C3-candidates.md`, `batch-C4-candidates.md`) and
building the six predictive incumbents by calling `pos_features.build_features` directly — no
reimplementation risk for those six, since that module is genuinely shared.

**Task 1 — blocked-row audit.** Checked all 17 `blocked` ledger rows directly against the current
39-table schema (not against the old dispositions' prose). Findings:
- 7 NOW AVAILABLE and screened here: T0-10 (red-zone usage, already tested by C1, mislabelled),
  T0-11/N12 (odds, already tested by C2, mislabelled), T1-21 (team pace), **T1-22 PROE — never
  actually blocked once `pbp` landed, `pbp.xpass` was already in the ingested schema**, T1-29
  (coordinator continuity, partial — `play_callers_preseason` has 992 rows, a **Wikipedia proxy**,
  not the PFR-403 source the ledger names), N22 (same table).
- 5 NOW AVAILABLE but deliberately not built this pass (a real join or harder-than-stated
  construction behind each): T0-1 (not a factor, a harness switch), T1-28 (vacated opportunity —
  `rosters_weekly` now exists but the join is non-trivial), T1-30 (exact "first time anywhere"
  definition), N14 (red-zone snap rate), N21 (exact "tendency portability" definition).
- 5 confirmed STILL BLOCKED, schema checked directly rather than re-asserted: T0-2 (no
  component-level projection table anywhere), T1-32/N23 (no motion column in `pbp` or
  `participation`, at all, contradicting nothing — genuinely absent), N8 (no charting column), N24
  (**corrects the ledger**: no play-action column at team OR player level, despite the ledger
  claiming team-level was computable).

**Task 2 — extended screen.** `standalone_screen2.py` screens **119 base factor-position cells
(35 distinct factors, 4 positions where applicable) + 78 within-cluster-contrast cells (40 distinct
contrasts) = 197 total**, 2013–2019, same EXOGENOUS/CONSTITUENT/AMBIGUOUS discipline, same noise
benchmark, as screen 1. Full write-up: `docs/ranking/standalone-screen-2.md`.

**Headline findings, all descriptive, nothing decided:**
- `share_level` (T0-8's LEVEL — distinct from C4's `tshare_stability`) is among the strongest
  survivors at every position (WR raw ρ=0.68, TE 0.68, RB 0.57) and has never before faced this
  screen despite being in the base spec today.
- `age`/`draft_capital`/`depth_end_rank` all show raw-positive, partial-negative sign flips —
  consistent with regression-to-mean once prior points is controlled for.
- `depth_rostered_absent`/`depth_offroster`/`inj_unexp_missed_share` never reverse sign across any
  of the 7 screened seasons at any position — the most stable finding in the whole pool.
- `oc_disruption`, `hc_disruption`, `proe` are all essentially null everywhere.
- `tprr` reverses sign vs. every external source's reported direction, on thin (n_seasons=3)
  coverage — flagged as an open oddity for the fit, not resolved.

## Bottom line

**75 factors will be tested for inclusion in v3's joint fit (35 base + 40 contrasts). 5 remain
genuinely untestable with the data we hold** (T0-2, T1-32, N8, N23, N24).

## Handoff

Opened `docs/handoffs/2026-08-04-v3-candidate-pool-complete-standalone-screen-2-7.md` to
`ranker,strategist` — the season-budget split (2020–2024, ≤5 seasons for fit+test, disjoint) is
still unregistered and blocks fitting.

## Files

- `experiments/bottomup/v2/standalone_screen2.py`
- `experiments/bottomup/results/standalone_screen2_{results,collinearity,contrasts}.csv`
- `docs/ranking/standalone-screen-2.md`
- `docs/CURRENT-STATE.md` (updated in place)
- `docs/handoffs/2026-08-04-v3-candidate-pool-complete-standalone-screen-2-7.md` (new thread)
