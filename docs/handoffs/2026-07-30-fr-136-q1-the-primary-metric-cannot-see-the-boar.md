---
ID: 2026-07-30-fr-136-q1-the-primary-metric-cannot-see-the-boar
FROM: ranker
TO: strategist
STATUS: OPEN
BLOCKS: all bottom-up build work under FR-136 Q1
OPENED: 2026-07-30
---

## Ask

Four methodology rulings. **The first is blocking** — the founder has said build, and building a
bottom-up model graded by the current primary metric would waste the effort.

Full evidence: `docs/ranking/fr136-q1-bottom-up-assessment.md` (committed this session).

### 1. BLOCKING — replace the primary evaluation metric, or rule that it stays

**Measured.** `src/backtest.py:_rank_correlation_by_position` computes Kendall's τ_b *within* each
position, and ADR-B forbids any cross-position aggregate. The shipped board's within-position
ordering is **identical to consensus** at all four positions (`projected_points` refits to
`a + b·ln(positional rank)` with max residual 0.005 pts). Therefore:

```
rescored_consensus_board  vs  fantasypros_ecr_raw,  per-position tau_b delta
2022  QB 0.000000  RB 0.000000  WR 0.000000  TE 0.000000
2023  QB 0.000000  RB 0.000000  WR 0.000000  TE 0.000000
2024  QB 0.000000  RB 0.000000  WR 0.000000  TE 0.000000
```

Exactly zero, 12 of 12. The project's primary metric is **mathematically incapable** of
distinguishing the shipped board from raw consensus, and always was. This is not a null about
football; it is a structural property of the instrument.

**What I am NOT asking you to do:** pick the metric that scores my model. I built the object; I must
not choose its ruler.

**What I supply so you can rule.** The incumbent's error on the metric the product actually
displays, walk-forward, curve for season S fitted only on `fantasypros_ecr` seasons < S, universe =
that season's consensus board, busts retained at 0, **2025 untouched**:

| | QB | RB | WR | TE |
|---|---|---|---|---|
| mean MAE, projected vs realised season points, 2022–24 | **74.0** | **62.0** | **48.0** | **35.8** |
| MAE ÷ mean actual points | 0.30 | 0.40 | 0.32 | 0.31 |

Candidates already in the codebase, none of them mine to choose between:
`backtest.top_k_starter_vbd` (cross-position sensitive, says so in its own docstring),
`src/draft_sim.py`, or projected-points MAE as above.

**What I will do with the answer:** every subsequent step in the FR-136 Q1 build plan is graded
against whatever you name, and nothing gets built until you do.

### 2. Is refitting the rank curve on FFC ADP legitimate — as a power argument, not an accuracy one?

The board-vs-anything comparison is capped at **three seasons (2022–2024)**: the board needs a prior
consensus season and `fantasypros_ecr` starts 2021; FFC ADP ends 2024; 2025 is sealed. A sign test on
three seasons floors at p = 0.25.

Refitting the same object (`E[our_points | positional market rank]`) on FFC ADP (2018–2024) yields
**six** evaluation seasons instead of three.

**The reason this needs you and not me:** today's H1 measured **NULL** — ADP is *not* more accurate
than expert consensus at predicting realised pick order (mean gap −1.27 picks, in the incumbent's
favour). So the substitution can only be argued as *a longer rank series for power*, never as "ADP
is a better input." Rule on whether that argument holds.

### 3. May the component projections ship as displayed projections without clearing consensus on rank?

`component-model-*-pass-1.md` measured: the component models beat naive persistence on **every
component at all four positions**, and do **not** beat consensus ADP on rank anywhere (RB is the one
position with power and its point estimate is −0.052).

The founder's request today: *"Hopefully we have lots of components in our rankings, we want it to be
proprietary (youd think we'd have projections then too)."*

Shipping them **as the ranking** would ship a thing measured not to beat the market. Shipping them
**as projections displayed beside** a consensus-derived rank is a different claim and may be
defensible. **I must not be the one who decides my own model is good enough to show.** Rule, or route
to PM if it is a product call rather than a methodology one.

### 4. Register or reject the oracle ladder

`fr136-q1-bottom-up-assessment.md` §4. FFC half-PPR ADP boards 2018–2024, busts retained, 2025 not
touched, season bootstrap 4,000 reps:

| pos | gap: perfect per-game-rate foresight − consensus ADP | gap: perfect games-played foresight − consensus ADP |
|---|---|---|
| QB | +0.435 [+0.311, +0.555] | +0.364 [+0.204, +0.521] |
| RB | +0.399 [+0.300, +0.511] | +0.125 [−0.058, +0.261] |
| WR | +0.354 [+0.289, +0.419] | +0.132 [+0.066, +0.196] |
| TE | +0.426 [+0.274, +0.580] | +0.323 [+0.146, +0.499] |

**Stated against my own result before you read it:** these are oracles on target-season values, the
rate oracle shares its numerator with the outcome so it is an upper bound *by construction*, it is 12
uncorrected tests on 7 seasons, and the board is 12-team against a 10-team league. **It bounds the
room, not the reachable.** It is a hypothesis about where to look and I am not treating it as more.

Two claims in it are large enough that if you think they are too good, they probably are, and I would
rather you say so now: (a) the room in rate projection is +0.35–0.44 ρ against a component model
delivering +0.051 at WR; (b) perfect availability foresight *alone*, knowing nothing about talent,
beats the entire expert consensus at all four positions.

## Why

The founder has ordered the three model questions into a dependency chain —
**bottom-up → availability → recommender** — and both downstream models consume the ranking. The
shipped board is within-position identical to consensus, so availability is currently simulating a
draft over consensus ordering and the recommender is pricing opportunity cost out of four slopes. A
wrong ranking does not stay contained.

39 days to the 7 September draft. Item 1 blocks everything and cannot be resolved by me.

## Done looks like

1. A named primary metric for board/ranking evaluation, and an explicit ruling on whether ADR-B's
   no-aggregate rule stands as-is given the 12-of-12 zeros.
2. Yes/no on the FFC curve refit, with the H1 NULL taken into account.
3. Yes/no/route-to-PM on shipping component projections as displayed projections.
4. The oracle ladder either registered as a pre-registration under `docs/preregistration/`, or
   rejected with the reason — either outcome closes it.

### ranker · 2026-07-30

**Amending ask 1 before you rule on it, and adding a fifth.** Founder direction landed after I
opened this thread (`FR-2026-07-30-bottom-up-must-include-all-tier-0-table-stakes-n`: *"Our bottoms
up needs to include all the table stakes"*), and working it changed my own question.

**Ask 1 was wrong in shape. It is a pair, not a replacement.**

Per-position τ_b returns exactly 0.000000 **because** the board has one player-level input — the
consensus rank. The moment any table stake is wired, within-position ordering stops being identical
to consensus and **τ_b becomes informative for the first time.** The metric is not wrong in general;
it is blind *specifically to the current object*.

But τ_b still cannot see the cross-positional channel, which is the board's **entire** present
content and does not disappear when table stakes land. So what I need named is:

- a **within-position** metric — τ_b is a live candidate again, not a dead one; and
- a **cross-position** metric — `top_k_starter_vbd` or `src/draft_sim.py`; and
- **whether ADR-B's no-aggregate rule survives**, since the reason it exists (a pooled correlation
  mostly measures whether the ranking sorted positions by scale) is unchanged.

Projected-points MAE (§6.1's bar: QB 74.0 · RB 62.0 · WR 48.0 · TE 35.8) is orthogonal to both and
may sit alongside either.

**New ask 5 — a `CLAUDE.md` §11 tension I will not resolve myself.**

The PM's argument, which I think is **right on multiplicity**: table stakes are included on
construction grounds, never tested individually, so they contribute **zero** to the FDR denominator,
and the budget is spent on Tier 1/2. I would have got that wrong and I am adopting it.

Two things I am **not** willing to let it carry, and I need you to rule rather than me:

1. **It must not become "table stakes are free."** Multiplicity is avoided entirely; **estimation
   variance and leakage surface are not.** `CLAUDE.md` §6.3's "every added parameter must earn its
   place against a holdout" is about parameter count, not selection — twelve features against ~13
   usable seasons is real. My proposed operational form: include by construction, do **not** test each
   factor, but the Tier 0 block takes **one** holdout evaluation *as a block* (denominator +1), and
   every feature passes the existing `SeasonPanel` access-log audit. **Ratify or replace.**
2. **§11 says** *"'Everyone knows X' is a hypothesis to test."* Construction-grounds inclusion is in
   tension with that sentence as written. My reading — §11 governs *claims*, and "this is an input"
   is not a claim — is convenient for me, which is why it is yours to make. If it needs a `CLAUDE.md`
   change, that escalates past both of us.

**Evidence that bears on it, and it cuts against the intuition:** #5 depth-chart role and #6 injury
status are **already implemented** in `experiments/bottomup/components/pos_features.py` (arms B/D/E)
and both measured **NULL on ranking at all four positions**. Two of the twelve are built, are
unarguably table stakes, and produce nothing. I have recorded in `fr136-q1-bottom-up-assessment.md`
§6a.3 — **before anything is wired** — that I expect at most four of the twelve to carry non-zero
weight, so that "we added the table stakes and nothing moved" is a prediction rather than a
retrofit.
