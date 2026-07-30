---
id: PR-006
title: Does a global flex-eligible replacement baseline beat the current per-position one? (test-registry #35)
hypothesis: Current replacement levels (RB30/WR40/TE10/QB10, `scoring.ReplacementLevels`,
  ADR-029) are derived by splitting the league's 20 flex slots across RB/WR/TE using a
  MEASURED historical flex-win share, then applying a separate replacement rank per
  position. Test-registry #35 proposes instead using ONE global replacement points figure —
  set by the Nth-best flex-eligible player overall, where N=80 (RB20+WR30+TE10 mandated +
  20 flex slots, arithmetic derived in docs/ranking/valuation-tests-35-36-precommit.md, not
  assumed) — applied identically to RB, WR and TE. QB is unaffected by either scheme (not
  flex-eligible in this league) and is held fixed at QB10 in both arms.
metric: Season-paired margin in realised roster points (weekly-optimal lineup,
  `draft_sim.weekly_optimal_points`, scored under this league's real rules against ACTUAL
  historical outcomes) between a plain best-available-by-VBD strategy run on the GLOBAL
  board vs the CURRENT-scheme board, both built from season S-1's real points (no
  player-level pre-season projection exists yet, ADR-017) via
  `db.CutoffEnforcedStore(cutoff_season=S)`. `draft_sim.strategy_bpa` drives both boards
  unmodified — this isolates the replacement-level definition, not a different pick
  policy. Also reported against the required baselines: `bpa_consensus` (market ADP/ECR)
  and P(top-4 of 10) as a secondary metric. VBD MAGNITUDES themselves are never compared —
  a shifted replacement level moves every player's VBD by construction; only realised
  decisions/outcomes count.
confirmation_threshold: SURVIVES requires the season-paired points margin (global minus
  current) to clear zero (95% CI excludes zero) at BOTH sigma in {10, 20}, AND the
  corrected sign-test p (Benjamini-Hochberg, across every comparison run in this joint
  pass with PR-008/test #36) to clear 0.05. MARGINAL is a CI endpoint near zero or a result
  holding at only one sigma. NULL is a CI including zero at either sigma, or a negative
  point estimate. A NULL here is a reportable, useful result — it closes #35 as measured
  rather than SPEC, which the registry currently marks it.
status: REGISTERED
run_date: 2026-07-30
primary_comparison: vbd_global_flex vs vbd_current (paired by season), both also vs bpa_consensus
sensitivity_requirement: sigma in {10, 20} (two of draft_sim.SIGMA_SWEEP's three points, to
  bound runtime in this session — reported explicitly as a narrower sweep than the module's
  full default, not silently substituted for it).
window: Development seasons 2021-2024 only. 2025 is the LOCKED HOLDOUT and is not accessed
  by this test (holdout.py's guard is not invoked because this pass never requests 2025).
  With n=4 seasons, sign_test's own stated power ceiling applies: p=0.125 is the smallest
  attainable two-sided p, stated up front per PR-003's precedent.
full_design: docs/ranking/valuation-tests-35-36-precommit.md
---
