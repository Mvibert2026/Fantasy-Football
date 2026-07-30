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
status: RUN
result: NULL on the win condition, but the decision-divergence question is a clean YES.
  vona_gap_aware minus vona_gap_blind season-paired points margin is -37.2 [-118.8,+36.0] at
  sigma=10 and -2.8 [-48.0,+37.1] at sigma=20 -- both include zero, signs 1/4 and 2/4 (a coin
  flip), per-season margins bounce both directions (-154.0 to +86.7 across the 8 season-sigma
  cells) with no consistent sign. Simulation SE (~9.3 pts at 300 sims/cell, measured directly)
  is small relative to these CIs -- the imprecision is the n=4-season bootstrap, not too few
  simulated drafts; per the coordinator's instruction, stating this rather than reporting a
  noisy point estimate as a verdict. SEPARATELY, decision divergence is measured directly and
  is decisive: gap-aware and gap-blind VONA choose a DIFFERENT full roster in 100% of paired
  simulated drafts, every one of the 8 season x sigma cells (n=300 or 299 per cell, paired on
  identical opponent-noise draws) -- the real ~3.5x gap alternation does change the
  recommendation essentially every time, exactly as the registry's premise claims. It just
  does not reliably change the OUTCOME at this sample size, which is a different, both
  pre-registered question. A THIRD finding, not the primary comparison but consistent both
  sigmas: this VONA formulation (either gap variant) underperforms plain vbd_current
  best-available-by-VBD by -106.4 [-182.4,-54.3] (sigma=10) and -126.0 [-214.5,-69.2]
  (sigma=20) -- CIs exclude zero at both sigmas, though sign_p floors at 0.125 (n=4) and
  neither survives BH (n_total=63, adj_p=0.984). Read as a caution against shipping VONA
  reaching under this share-based scarcity estimate, not as a confirmed loss -- the direction
  is consistent but the significance floor cannot resolve it further at this season count.
  Full log: data/qa/valuation-tests-35-36-run-2026-07-30.log.
run_date: 2026-07-30
primary_comparison: vona_gap_aware vs vona_gap_blind (paired by season AND by sim-level
  seed), both also vs bpa_consensus and vs plain vbd_current BPA
sensitivity_requirement: sigma in {10, 20}, same narrowed sweep as PR-006 and for the same
  stated reason (runtime bound in this session).
window: Development seasons 2021-2024 only. 2025 is the LOCKED HOLDOUT and is not accessed.
  Same n=4/p=0.125 power ceiling as PR-006.
full_design: docs/ranking/valuation-tests-35-36-precommit.md
---
