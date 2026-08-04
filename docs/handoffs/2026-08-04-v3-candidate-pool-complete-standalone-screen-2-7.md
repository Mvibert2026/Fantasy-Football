---
ID: 2026-08-04-v3-candidate-pool-complete-standalone-screen-2-7
FROM: backend
TO: ranker,strategist
STATUS: OPEN
BLOCKS: none
OPENED: 2026-08-04
---

## Ask
Per `FR-2026-08-04-v3-build-strategy-screen-all-factors-for-predict.md`, the full v3 candidate pool
has been screened and is ready to feed the joint fit: `docs/ranking/standalone-screen-2.md`
(supersedes screen 1), built by `experiments/bottomup/v2/standalone_screen2.py`, results in
`experiments/bottomup/results/standalone_screen2_{results,collinearity,contrasts}.csv`.

**75 distinct candidate constructs** (35 base factors + 40 within-cluster contrasts), screened
2013–2019, per position, EXOGENOUS/CONSTITUENT/AMBIGUOUS-classified, against a noise floor — this
covers C1's 6, C2's 6, C3's 6, C4's 6, the six predictive incumbents (no grandfather clause per
your own FR), and two factors this session's blocked-row re-audit newly unblocked (PROE, T1-22 —
never actually blocked once `pbp` landed; OC-level coordinator continuity, T1-29/T1-30/N21/N22 —
`play_callers_preseason` has 992 rows, a Wikipedia proxy, not the PFR-403 source the ledger names).

**What you need to know before fitting**: this document's Part A is a full re-audit of the ledger's
17 `blocked` rows against `data/nfl.db` as it exists today — 7 are now available and screened here,
5 more are now available but deliberately not built this pass (flagged for a follow-up batch: T1-28
vacated opportunity, N14 red-zone snap rate, T1-30's exact "first time anywhere" definition, N21's
exact "tendency portability" definition, T0-1's baseline-arm switch), and 5 remain genuinely
blocked (T0-2, T1-32, N8, N23, N24 — schema checked directly, not merely re-asserted).

**Notable finding for the fit itself**: `share_level` (T0-8's LEVEL, distinct from C4-I's
stability) is among the strongest survivors at every position — WR raw ρ=0.68, TE 0.68, RB 0.57 —
and has never before faced this screen despite being in the base spec today. `age`/`draft_capital`/
`depth_end_rank` all show raw-positive, partial-negative sign flips (regression-to-mean pattern) —
worth understanding before interpreting their v3 coefficients. `oc_disruption`/`hc_disruption`/
`proe` are all essentially null. `tprr` reverses sign vs. every external source's reported
direction on thin (n_seasons=3) coverage — flagged as an open oddity, not resolved.

Season-budget risk (screen spent 2013–2019, ≤5 seasons of 2020–2024 remain for fit+test, disjoint,
before the sealed 2025 holdout) is unchanged from screen 1 and still unregistered.

## Why
This is the direct input `FR-2026-08-04-v3-build-strategy-screen-all-factors-for-predict.md`
calls for before any v3 coefficient is fit. Without the incumbents in the pool on equal footing,
the fit repeats the "already included is a reason to skip" error the founder specifically
overruled. Without the season-budget split registered, the fit risks re-fitting noise on a
2-season test set.

## Done looks like
`strategist` registers the exact fit/test split over 2020–2024 (and which evaluation universe —
exact-format ADP vs. wider no-constraint) before `ranker` fits v3; `ranker` treats
`standalone_screen2_results.csv`/`..._contrasts.csv` as the candidate pool, per position, per the
FR's binding rules (ridge/elastic net, standardised, no correlation pruning, LOSO+bootstrap
stability reported per coefficient). Reply here with the registered split or with a disagreement
about the pool before fitting begins.
