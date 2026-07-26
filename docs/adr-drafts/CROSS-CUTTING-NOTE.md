## Cross-cutting note for the Backend engineer

Three things in the current state should be treated as blocking regardless of which ADR is executed first:

1. `_rank_correlation()` pooling across positions is not a rounding error — it can report healthy correlation for a model with zero within-position skill. Any figure it has produced should be retracted, not adjusted.
2. `lambda = 0.352` with `z = 5.04` rests on cluster-robust SEs from 10 clusters, which is below the range where CRVE is reliable and biased toward overstating significance. A wild cluster bootstrap-t re-derivation is cheap and should happen before the figure appears in any user-facing methodology text.
3. No configuration of the `NEED_ADJUSTMENT_SCALE` superiority test can clear BH on 4 seasons — minimum attainable p is 0.0625 with a single test at infinite effect size. Run the inertness test (A-1), which needs no inference at all; leave A-2 registered and unrun.
