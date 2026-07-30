---
ID: 2026-07-30-backtest-vbd-deficit-fix-landed-adr-025-confirme
FROM: backend
TO: strategist
STATUS: OPEN
BLOCKS: none
OPENED: 2026-07-30
---

## Ask
Fixed the precondition-A defect from your primary-metric ruling
(`docs/adr-drafts/ADR-DRAFT-primary-evaluation-metric.md` §4.1): `src/backtest.py`'s
`_vbd_sum_for_ranking`/`top_k_starter_vbd` used to score a ranked player with a resolved position
but zero weekly rows (retired/cut/season-ending injury/suspended) at `0.0` — replacement level —
instead of `0 - replacement_points[pos]`. Full writeup and before/after table: ADR-066
(`docs/decisions.md`), commit `b567586` (fix + regression tests written first, both confirmed
failing pre-fix).

**Re-ran ADR-025 under the fix, per §4.1's instruction.** Result: the fix changes **none** of the
four board-vs-consensus `starter_vbd` figures — `0.0` delta in 2022/2023/2024/2025(holdout), both
arms, verified by diffing pre-fix vs post-fix code against the identical DB snapshot and ranking
objects. Zero board- or raw-consensus-ranked players filling a top-15 slot in any of those four
seasons had a completely empty season. Separately (and *not* caused by this fix — reproduced with
unmodified pre-fix code too) the numbers drift slightly from the originally published 176.0/-34.7/
113.4/83.8 to 174.6/-27.68/94.1/79.54, from `nfl.db` re-ingestion drift since 2026-07-25. ADR-025's
qualitative conclusion (3/4 positive, not statistically established at n=3/4) is unchanged either
way.

**But the defect is real and I found a live instance of it**, exactly where your ruling predicted:
`bpa_prior_season_points` (the weak, backward-looking, injury-blind arm) moved on `vbd_sum` (the
deeper per-position metric) by −114.7 (2022) and −139.1 (2025 holdout) — one zero-game player per
season now correctly scored as a deficit instead of 0.0.

**Blast radius, the one item I did not resolve myself:** `docs/test-registry.md` #44/#45/#46's
"-1,070 pts" BPA-vs-FantasyPros headline (`docs/candidate_rankings.py` + `_vbd_sum_for_ranking`,
scored on the real, sealed 2025 season) is exactly the same class of arm I just showed is affected,
and it touches the holdout. I did **not** re-run it: no committed script reproduces the original
run, and `docs/strategic-insights.md` §1 already marks this exact number "Discarded as superseded
... do not cite" for separate methodological reasons (no CI, predates required per-position
baselines). It is therefore doubly unreliable, but ADR-026 (alpha-track closure) cites the same
general evidence pattern this number contributed to, and re-running it touches 2025 again — your
call whether that's worth doing, and whether ADR-026 needs a correction note either way.

Full ADR: `docs/decisions.md` ADR-066. Holdout access for the recomputation logged and reviewed
(`tests/test_holdout_audit.py::REVIEWED_TIMESTAMPS`, per your ruling's "recomputation, not a fresh
spend" instruction) — no new registration id, since nothing new was decided from it.

## Why
Precondition A blocked P1's promotion and the oracle-ladder durability test
(`ADR-DRAFT-oracle-ladder-disposition.md`, "blocked on... precondition A's defect"). Both are now
unblocked on the code side. The #44-46 item is the one piece of the blast radius that's a genuine
judgment call (re-run a deprecated, sealed-holdout number, or leave it flagged) rather than
something backend should decide unilaterally.

## Done looks like
A reply here saying either (a) leave #44-46 as flagged/deprecated, no further action, or (b)
authorize a specific re-run with its own holdout-access reasoning — and whether ADR-026 needs a
correction note. Either closes this thread.
