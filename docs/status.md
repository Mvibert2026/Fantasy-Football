# Project Status

Running state of Phase 1. Updated at the end of each work session — read this first to see where
things stand before diving into `decisions.md` (why) or `deferred.md` (what's postponed).

---

## Standing requirements

Cross-cutting constraints that must be incorporated into future work, regardless of what phase
is active when they're addressed.

- **Bye-week clustering matters for actual roster construction.** A strategy that puts 4 starters
  on the same bye costs real points (6 bench + 1 IR gives some cushion, but not unlimited).
  Incorporate bye-week constraint modeling into draft strategy once rankings are validated. Related:
  test-registry.md Tier 2 #61 ("Bye-week clustering cost," currently `NEW`).

---

## Where Phase 1 stands (2026-07-25)

| Step (CLAUDE.md §3) | Status |
|---|---|
| 1. Data ingestion | Done — 2021-2025 nflverse weekly stats (`data/nfl.db`), FantasyPros 2025 preseason ECR. True multi-source ADP blocked (see `deferred.md`) |
| 2. Scoring engine | Done — `src/scoring.py`, ported and self-tested |
| 3. Backtest harness | Done — `src/backtest.py`, look-ahead cutoff structurally enforced and tested |
| 4. Ranking algorithm v1 | Not started |
| 5. Factor testing | Not started (test-registry.md Tier 0/1 items still `SPEC`/`NEW`) |

**39 automated tests passing** (`pytest`) across ingestion, scoring, the look-ahead-safe data
layer, and the backtest harness.

## This session: Phase 1 baseline backtest runs (test-registry.md #44/#45/#46)

Ran three ranking configurations against the 2025 season using a 10-team VBD-based BPA baseline
(`ReplacementLevels()` defaults: QB10/RB28/WR41/TE11 — corrected from an originally-requested
12-team figure that conflicted with this project's own settled league parameters).

**Headline finding: our VBD-based ranking lost to FantasyPros' preseason consensus by ~1,070
points of value-over-replacement.** Reported as a failure per `CLAUDE.md` §6.5, not softened — a
backward-looking "rank by last year's value" approach can't see current-year information (injuries,
depth-chart moves, rookies) that expert consensus incorporates.

**Hero RB (test #44): inconclusive — found a harness blind spot, not a real result.** The
comparison metric only tests which players land in the startable pool per position, not the
draft-order/cost paid to acquire them. Boosting already-top-24 RBs doesn't change pool membership,
so the metric can't see what Hero RB actually does. Needs a draft-cost-sensitive metric before this
can be answered for real (see `deferred.md`).

**Elite TE (test #45): real, measured cost of -226.4 points.** Bowers/McBride were already the
natural TE1/TE3 by 2024 VBD — the cost comes entirely from refusing every other TE, including that
season's real TE2. Whether that cost is worth playoff-bracket upside is **not answered** — this
harness has no playoff-probability or variance model yet (Tier 4 #55/#56, still `NEW`).

**QB1-vs-QB10 (test #46): justifies waiting, on real 2025 outcomes.** 74.7-point spread (25%) vs.
QB10, compared to a 225.8-point RB1-to-replacement spread. QBs cluster much tighter than RBs in
this scoring format.

Full mechanism detail and numbers: `docs/test-registry.md` (#44/#45/#46 findings note) and
`docs/decisions.md`.

## Next likely steps

1. Fix the Hero RB metric blind spot (draft-cost-sensitive comparison) before trusting any
   draft-order-based strategy test.
2. Resolve true multi-source ADP access (FFC needs explicit authorization request; others need
   ToS review) — currently the biggest gap in the baseline comparisons.
3. Backfill FantasyPros preseason snapshots for 2021-2024 so the harness can backtest seasons
   other than 2025.
