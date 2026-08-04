# 2026-08-04 — backend — standalone predictiveness screen 1

**Dispatch**: run a standalone, model-independent predictiveness screen over candidate factors —
the founder's own idea, distinct from the incremental (model-dependent) factor-inclusion campaign.
Mid-session, the founder redirected the deliverable's purpose (it now feeds a future v3 joint
multivariate fit, v2 kept as a revert checkpoint) and issued two corrections: (1) partial
correlation controlling for prior-season points is only valid for factors exogenous to last
year's box score — for constituent factors it is an arithmetic artifact; (2) the collinearity map
is diagnostic for the eventual fitter, not a pruning instrument, and tight clusters should also
be screened as within-cluster contrasts (percentile-rank gaps).

## What happened

1. Discovered this worktree's committed tree does not contain `experiments/bottomup/v2/` at all —
   `factors_c1/c2/c3.py`, `run_c1.py`, `sweep070/` exist only as uncommitted work in a sibling
   checkout (confirmed: this worktree's `git log` matches `origin/main` byte-for-byte, and
   `ls experiments/bottomup/v2` fails here). Per this task's own dispatch not to touch those files
   or the concurrent `factors_c4.py` work, wrote a fully self-contained script instead, importing
   only `experiments/bottomup/components/{pos_data,pos_features}.py` (which do exist, committed,
   in this worktree) — no code shared with the in-flight batch files, no collision risk on merge.
2. Built `experiments/bottomup/v2/standalone_screen1.py`: 14 factors (injury burden, practice
   severity, end-of-season depth-chart rank, combine athletic composite, team neutral-situation
   pass rate, yards-over-expected rate, WOPR, snap share, red-zone usage share, YAC/reception,
   RB's own receiving-points share, late-season role trend, QB rush attempts/game, team explosive-
   rush rate) + a seeded-noise placebo, screened across applicable positions, 2013–2019 only.
3. Classified every factor EXOGENOUS/CONSTITUENT/AMBIGUOUS **before** interpreting any number
   (per the founder's correction), and report raw + partial rho for every factor always, headline
   picked by class.
4. Caught and fixed a real bug in my own first draft before reporting anything from it: the
   prior-points lookup relabelled each player-season's own points as "prior_points" for the *same*
   season with no lag shift, producing a same-season duplicate (matched-sample prior-points rho
   was reading ~1.0 for everything). Fixed, reran, documented in the deliverable.
5. Produced the inclusive survivor set (32 of 45 base factor-position cells clear their position's
   noise floor), the full pairwise collinearity matrix, 13 within-cluster contrast factors
   (constructed for every |rho| >= 0.6 pair and screened identically), and a stated season-budget
   flag: only 5 unspent seasons (2020–2024) remain for a disjoint v3 fit+test split, which is thin
   against a ~15–25-predictor survivor set and this project's own overfitting hazard (CLAUDE.md
   §6.3, and C1's own measured 14.6% false-positive rate on an unguarded rule).

## Discipline honored

- Screened 2013–2019 only; 2020–2024 untouched by this script.
- Sealed 2025 holdout never read (every SQL loader gates `season < 2025`).
- Every factor value built from data strictly before the target season (lag-1 or 3-lag weighted).
- No decisions made — no INCLUDE/EXCLUDE anywhere in the output; nothing added to any campaign
  multiplicity denominator.
- No new direct `sqlite3.connect()` outside the ingestion allowlist issue applies to `src/` only;
  this is `experiments/`, and every prior factor batch in this project (C1/C2/C3/factor_features*)
  connects to `nfl.db` directly the same way for the same reason (read-only historical loaders).

## Files

- `docs/ranking/standalone-screen-1.md` — the deliverable
- `experiments/bottomup/v2/standalone_screen1.py` — self-contained script
- `experiments/bottomup/results/standalone_screen1_results.csv` (45 rows)
- `experiments/bottomup/results/standalone_screen1_collinearity.csv` (238 rows)
- `experiments/bottomup/results/standalone_screen1_contrasts.csv` (13 rows)
- `docs/CURRENT-STATE.md` — updated in place with a new "Last verified" block

## Commit

`18207c3` on branch `worktree-agent-aa416e7b8fcf416ee`, pushed to origin.

## Next step (for whoever picks this up)

`strategist`/`ranker` should register the v3 fit/test season split (and which population — exact
ADP-format vs. no-ADP-constraint universe) before any joint-fit coefficient is estimated; the
season budget is thin enough that this is a real design risk, not a formality.
