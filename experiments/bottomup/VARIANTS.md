# Variant log — the multiplicity denominator

Every configuration evaluated against fold results is logged here, including
abandoned ones. Bug fixes that change no modelling choice are logged as fixes,
not variants. Registration: docs/reviews/fable-ranking-design-2026-07-27.md.

| # | When | What | Status |
|---|---|---|---|
| V1 | 2026-07-27 | Registered configuration: S1 ridge (lambda=1.0, fixed a priori), games ~ prior_games+age, S2 k-grid {10..800} fold-local with caps 0.60/0.20, S3 bonus tables position x ypg-bin, arms long/usage | **the registered run — reported** |
| V2 | 2026-07-27 | QB pass-TD shrinkage cap raised 0.20 → 0.60 (hypothesis: the cap discards persistent QB TD signal and causes the QB deficit) | **run, rejected** — QB Δtau vs B1 moved only −0.108 → −0.097, still clearly negative; hypothesis falsified, QB weakness is structural, not the cap. Result file `results/usage_v2qbcap.json` |
| F1 | 2026-07-27 | Fix, not a variant: long arm's receptions-share feature divided by TEAM TARGETS (≈0 in 2003-08), poisoning fold 2004 (clean training features, exploded test features — RB season R² −12530). Changed denominator to team receptions. This was a violation of the long arm's own no-targets rule via a denominator — the exact ADR-E §4.3 availability-boundary hazard | applied; both arms rerun; pre-fix numbers survive only in the session transcript and in `usage_v2qbcap.json`'s QB rows |

| V3 | 2026-07-27 (session 3) | **Registered BEFORE fit (commit 678615c).** Vacated/arrived-opportunity feature group (work order R1): 6 features (changed_team, vac_rec/carry/att_share, arr_rec/carry_share) from weeks-1–4 target-season roster membership (registered mild look-ahead, disclosed; rookies invisible to arrivals — registered blind spot). Registration incl. predictions and falsification rule: docs/reviews/FABLE-EXT2-2026-07-27.md | **run — NOT a carry candidate**: RB prediction failed (flat); QB gain (−0.108→−0.018) traced to the no-early-appearance self-vacated availability leak. Kept only as the leak's upper-bound measurement. `results/{usage,long}_v3vac.json` |
| V4 | 2026-07-27 (session 3) | **Registered same commit, unconditioned on V3's result.** QB-only direct season-points ridge (features = V3 QB slice + prior_points, prior_ppg, prior2_ppg) replacing S1→S2→S3 at QB; other positions = V3 pipeline. Tests the PM's team-stable-passing-volume hypothesis | **run** — QB Δτ vs B1 −0.055 usage / −0.000 long, still ≤ B1; superseded by V6 (clean features). `results/{usage,long}_v4qb.json` |
| V5 | 2026-07-27 (session 3) | **Registered in the FABLE-EXT2 amendment BEFORE run (commit 1c16ab4).** = V3 with each player's own production removed from his OWN vacated numerators (kills the availability self-leak; arrivals already excluded self) | **run — THE CARRY CANDIDATE**: RB +0.057 [+0.018,+0.095] & VBD +0.032 (both CI-clear, 10/13), TE VBD +0.073; QB falls back to −0.125 (the V3 QB gain was ~all leak); consensus gap unmoved anywhere. `results/{usage,long}_v5clean.json` |
| V6 | 2026-07-27 (session 3) | **Registered same amendment.** V4's QB-direct on V5's clean features (the hybrid-board candidate) | **run, rejected** — QB −0.141 [−0.201,−0.079], 1/13 folds; worse than the composition. QB is closed: nothing tried beats last-season points. `results/{usage,long}_v6qbclean.json` |

| V7 | 2026-07-27 (session 4) | **Registered BEFORE any code existed (commit 5af349e; implementation bf1c2d1).** V5 + same-position rookie-arrival draft capital: rook_cap_same (Σ 1/√overall pick), rook_top64_same, rook_cap_x_vac (× self-excluded position-relevant vacated share). draft_picks 1980–2026, PFR→canon crosswalk with totality test. Registration incl. predictions and falsification rule: docs/reviews/FABLE-EXT3-2026-07-27.md | **run — FALSIFIED, not a carry candidate**: RB improved on neither co-primary (τ +0.057→+0.054, VBD +0.032→+0.018) and the consensus gap did not move (−0.110→−0.112). Rookie arrivals via draft capital eliminated as the RB-gap explanation. `results/{usage,long}_v7.json` |

**Final tally (session 2): 2 model configurations evaluated (V1, V2) + 1 defect fix (F1).**
**Final tally (session 4): V7 added, registered before its code existed; 7 model
configurations total (V1–V7, + F1 fix). V5 remains the sole carry candidate.**
**Final tally (session 3): 4 more configurations (V3, V4, V5, V6), each registered before its
run; 6 configurations total. Multiplicity read: 6 configs × 4 positions × 2 arms — the V5 RB
result is the one to trust most (registered direction AND magnitude band from V3's
registration, hit by the clean variant, both co-primaries CI-clear, consistent sign in both
arms); single-cell CI escapes elsewhere (e.g. TE) carry the usual 48-cell caveat.**
The honest multiplicity read: with 2 configurations and the primary metric,
universe, baselines and fold sets all frozen in the registration before the
first fit, the reported WR/RB results are not meaningfully selection-inflated.
The per-position split (4 positions × 2 arms) is the real denominator to keep
in mind when reading any single position's delta: 8 position-arm cells were
examined under V1, so one cell clearing a 95% interval by luck alone is not
surprising; the WR result's strength (77% of folds, CI well clear of zero,
consistent across BOTH arms) is what makes it the credible one.
