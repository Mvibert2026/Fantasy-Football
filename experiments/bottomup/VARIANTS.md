# Variant log — the multiplicity denominator

Every configuration evaluated against fold results is logged here, including
abandoned ones. Bug fixes that change no modelling choice are logged as fixes,
not variants. Registration: docs/reviews/fable-ranking-design-2026-07-27.md.

| # | When | What | Status |
|---|---|---|---|
| V1 | 2026-07-27 | Registered configuration: S1 ridge (lambda=1.0, fixed a priori), games ~ prior_games+age, S2 k-grid {10..800} fold-local with caps 0.60/0.20, S3 bonus tables position x ypg-bin, arms long/usage | **the registered run — reported** |
| V2 | 2026-07-27 | QB pass-TD shrinkage cap raised 0.20 → 0.60 (hypothesis: the cap discards persistent QB TD signal and causes the QB deficit) | **run, rejected** — QB Δtau vs B1 moved only −0.108 → −0.097, still clearly negative; hypothesis falsified, QB weakness is structural, not the cap. Result file `results/usage_v2qbcap.json` |
| F1 | 2026-07-27 | Fix, not a variant: long arm's receptions-share feature divided by TEAM TARGETS (≈0 in 2003-08), poisoning fold 2004 (clean training features, exploded test features — RB season R² −12530). Changed denominator to team receptions. This was a violation of the long arm's own no-targets rule via a denominator — the exact ADR-E §4.3 availability-boundary hazard | applied; both arms rerun; pre-fix numbers survive only in the session transcript and in `usage_v2qbcap.json`'s QB rows |

| V3 | 2026-07-27 (session 3) | **Registered BEFORE fit, committed before any run.** Vacated/arrived-opportunity feature group (work order R1): 6 features (changed_team, vac_rec/carry/att_share, arr_rec/carry_share) from weeks-1–4 target-season roster membership (registered mild look-ahead, disclosed; rookies invisible to arrivals — registered blind spot). Full registration incl. per-position directional/magnitude predictions and falsification rule: docs/reviews/FABLE-EXT2-2026-07-27.md | registered; run pending |
| V4 | 2026-07-27 (session 3) | **Registered same commit, unconditioned on V3's result.** QB-only direct season-points ridge (features = V3 QB slice + prior_points, prior_ppg, prior2_ppg) replacing S1→S2→S3 at QB; other positions = V3 pipeline. Tests the PM's team-stable-passing-volume hypothesis. Registration: same file | registered; run pending |

**Final tally (session 2): 2 model configurations evaluated (V1, V2) + 1 defect fix (F1).**
The honest multiplicity read: with 2 configurations and the primary metric,
universe, baselines and fold sets all frozen in the registration before the
first fit, the reported WR/RB results are not meaningfully selection-inflated.
The per-position split (4 positions × 2 arms) is the real denominator to keep
in mind when reading any single position's delta: 8 position-arm cells were
examined under V1, so one cell clearing a 95% interval by luck alone is not
surprising; the WR result's strength (77% of folds, CI well clear of zero,
consistent across BOTH arms) is what makes it the credible one.
