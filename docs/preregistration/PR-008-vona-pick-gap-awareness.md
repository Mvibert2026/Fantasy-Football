---
id: PR-008
title: Does gap-aware VONA beat gap-blind VONA under simulation? (test-registry #36)
hypothesis: In a snake draft the gap to the user's next pick alternates — short right after
  the turn, long right before it. For USER_SLOT=3/N_TEAMS=10 (`draft_sim`'s own module
  constants) the real intervening-opponent-pick gaps are 14, 4, 14, 4, ... (a deterministic,
  ~3.5x alternation, not a measurement). Test-registry #36 claims urgency in a
  value-over-next-available (VONA) framework should scale with this real gap rather than a
  single constant assumption ("gap-blind": fixed at N_TEAMS-1=9, the textbook "assume one
  round" approximation used throughout the rest of the pass). Both arms use IDENTICAL VBD
  inputs (the current per-position scheme, PR-006's arm A) so this test isolates
  gap-awareness alone, not a different valuation.
metric: (1) Decision divergence — fraction of simulated drafts where gap-aware and
  gap-blind VONA pick a different full roster, run against IDENTICAL opponent-noise
  realisations (same RNG seed feeds both arms' single `effective_rank` draw, so any
  difference traces to the user's own pick, not re-randomised opponents). (2) Season-paired
  margin in realised roster points (`weekly_optimal_points`) between the two arms, plus
  against `bpa_consensus` (market ADP) and against plain `vbd_current`
  best-available-by-VBD (no VONA reasoning at all) as the two required baselines. P(top-4)
  reported as a secondary metric.
confirmation_threshold: SURVIVES requires the gap-aware minus gap-blind season-paired
  points margin to clear zero (95% CI excludes zero) at BOTH sigma in {10, 20}, AND the
  corrected sign-test p (Benjamini-Hochberg, joint pass with PR-006/test #35) to clear
  0.05. Divergence rate is reported regardless of the win condition — "changes the pick"
  and "the change is better" are different, both pre-registered questions; a high
  divergence rate with a null points margin is a legitimate, reportable shape of result
  (gap-awareness moves WHICH player, not necessarily the final roster's quality), not a
  discarded intermediate step. MARGINAL/NULL follow PR-006's same definitions.
status: REGISTERED
run_date: 2026-07-30
primary_comparison: vona_gap_aware vs vona_gap_blind (paired by season AND by sim-level
  seed), both also vs bpa_consensus and vs plain vbd_current BPA
sensitivity_requirement: sigma in {10, 20}, same narrowed sweep as PR-006 and for the same
  stated reason (runtime bound in this session).
window: Development seasons 2021-2024 only. 2025 is the LOCKED HOLDOUT and is not accessed.
  Same n=4/p=0.125 power ceiling as PR-006.
full_design: docs/ranking/valuation-tests-35-36-precommit.md
---
