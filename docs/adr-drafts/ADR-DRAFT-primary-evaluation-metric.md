# ADR-DRAFT — The primary evaluation metric for board and ranking work

**Status:** Proposed (ruling issued; number to be allocated by `tools/handoffs.py adr next` at landing)
**Date:** 2026-07-30
**Owner:** Strategist (ruling) / Backend (execution)
**Answers:** `docs/handoffs/2026-07-30-fr-136-q1-the-primary-metric-cannot-see-the-boar.md` item 1
**Supersedes nothing. Amends nothing. In particular it does NOT amend ADR-B.**
**Blocks:** all bottom-up build work under FR-136 Q1

---

## 0. The ruling in one table

| Output being graded | Primary metric | Status |
|---|---|---|
| **The ordering the board publishes** — rank, VBD, tiers, and everything `availability` and the recommender consume | **`backtest.top_k_starter_vbd`**, paired per season against the incumbent shipped board and against `fantasypros_ecr_raw`, season-level bootstrap CI, seed recorded | **PROMOTED to primary, conditional on §4's two preconditions** |
| **The number displayed as a projection** | **Per-position MAE skill score against a frozen constant-predictor floor** (§3) | **NEW. Primary for projection work only** |
| Player-level ordering content | Per-position Kendall τ_b (the incumbent primary) | **RETAINED, DEMOTED to mandatory reported diagnostic. Never a gate. Never deleted.** |

**ADR-B stands, unamended.** See §2.

---

## 1. First, the framing gets attacked, because the finding is convenient for whoever supplied it

The ranker reported that per-position τ_b returns **exactly 0.000000** between the shipped board and
raw consensus, twelve of twelve position-seasons, and concluded the instrument is defective. That
conclusion is a comfortable one for an agent who has just measured that its own board is not
proprietary. It gets checked before it gets acted on.

### 1.1 The twelve zeros are not twelve measurements. They are one identity, printed twelve times.

Kendall's τ_b is invariant under any strictly monotone transform applied *within* the units being
correlated. The board's `projected_points` is `a + b·ln(positional consensus rank)` with `b < 0` at
every position (assessment §1.1) — a strictly monotone decreasing function of the consensus rank,
applied within position. Therefore `Δτ_b = 0` **exactly, in every season, at every position, for
every possible outcome vector, forever.** No data was required to know it. Running it on 2022–24
produced no information that §1.1 did not already contain.

This matters for two reasons and neither is cosmetic:

1. **It is stronger than a measurement** — there is no sampling uncertainty, no n, no CI. Good.
2. **It is zero evidence that τ_b is a bad instrument.** A tautology about one degenerate object
   cannot indict a metric in general. Any statement of the form "the primary metric is
   mathematically incapable" needs the qualifier "*for objects that are monotone re-scorings of
   their own input*," which is a property of the board, not of τ_b.

**Correction required in `docs/ranking/fr136-q1-bottom-up-assessment.md` §1.2:** the twelve zeros are
described as "Measured." They are derived. The word should change, and the invariance argument
should replace the table, which invites a reader to think twelve independent things were checked.

### 1.2 Is the metric wrong, or is the board wrong? **The board.**

τ_b was asked "does this board order players within a position better than consensus does," and it
answered "it does not order them differently at all." That answer is **correct, useful, and the
single most important fact in the assessment.** An instrument that returns the right answer is not
broken.

The real defect is narrower and it is a *harness* defect, not a *metric* defect:

> The board makes exactly one claim — a cross-positional tilt, +5.3 places at QB and +10.6 at TE —
> and **no instrument in the harness is pointed at that claim**, because ADR-B forbade the
> cross-position aggregate that the obvious instrument would have been.

So the fix is an **addition**, never a substitution. And the addition must not be permitted to retire
§1.1's finding. Whatever gets promoted, **τ_b keeps being computed and printed**, because it is the
only thing in the harness that can say "your gain came from tilting positions harder, not from
knowing anything about players." That sentence is the exact failure mode the next six weeks will
produce if nobody is watching for it.

### 1.3 The failure mode this ruling is most at risk of

**Choosing the ruler that flatters the thing about to be built.** Three structural defences,
pre-committed:

| Defence | Mechanism |
|---|---|
| The promoted metric already has an unfavourable track record on the incumbent | `top_k_starter_vbd` is the metric behind ADR-025's `+84.9, 2/3 positive, sign-test p = 1.000` — the project's own reading of which is *"the board's advantage is not statistically established."* This is not a fresh ruler with no history |
| The promotion is conditional on a fix that makes the metric **harsher**, not softer | §4 precondition A |
| The unflattering incumbent metric is retained, not deleted | §0, §5 gate (c) |

---

## 2. Ruling on ADR-B: it stands, unamended, and it pre-authorised this move itself

ADR-B forbids **an aggregate across per-position correlations**. `top_k_starter_vbd` is not one. It
is not an aggregate of position-level statistics at all: it is a single roster-level quantity — the
realised value-over-replacement of the best legal starting lineup fillable from a ranking's top-15 —
computed on one object, once.

ADR-B's own *"What would falsify this"* section names this class of exception in advance:

> *"a weighting scheme derived from something external and non-negotiable — e.g. weights fixed by
> actual draft capital spent per position in the 10-team/0.5-PPR/no-K format, published and frozen
> before any correlation is computed. That removes the free-parameter objection. It does not remove
> objections 1 and 3, so it would need to be an addition alongside per-position reporting, never a
> replacement."*

Both conditions are met and both are hereby adopted as binding:

1. **The weights are external and frozen.** They are this league's own starting-lineup shape —
   1 QB / 2 RB / 3 WR / 1 TE / 2 FLEX (`backtest.STARTER_SLOTS`, `FLEX_SLOTS`), verified against the
   live Yahoo platform (ADR-052, `CLAUDE.md` §7). Not fitted, not chosen after seeing a result, not
   tunable. If the roster shape changes, the metric changes with it — that is correct behaviour, not
   a free parameter.
2. **It is an addition alongside per-position reporting, never a replacement.** §0 makes τ_b
   mandatory-reported and §5 makes it a gate condition.

ADR-B's objections 1 (sign disagreement) and 3 (uninformative small-n positions) are *not* removed by
this, exactly as ADR-B said. They are handled by keeping per-position τ_b visible, which is where
they were always handled.

**Nothing in ADR-B is edited. No cross-position correlation aggregate is created, stored, or logged.
`_rank_correlation_by_position` keeps returning a per-position mapping and a scalar return type
stays a lint failure.**

---

## 3. P2 — the projection metric, and why it is not raw MAE

The ranker supplied the incumbent's error on the number the product displays: mean MAE 74.0 / 62.0 /
48.0 / 35.8 points at QB/RB/WR/TE, 0.30–0.40 of what the average board player scores. That is a real
and previously-unmeasured bar. **It is not usable as a primary metric in that form**, for three
reasons:

1. **It has no baseline, which violates `CLAUDE.md` §6.5 at the level of the metric itself.** §6.5's
   rule is that the comparison *is* the result. A bare MAE is a raw accuracy number in isolation —
   the exact object §6.5 forbids reporting.
2. **MAE is minimised by the conditional median, so it can be improved by shrinking toward the
   positional mean — which strictly degrades ordering, and ordering is what a draft consumes.** A
   model that predicts one constant per position has a bounded, possibly respectable MAE and exactly
   zero decision content. Adopting raw MAE would make "beat the bar by shrinking" a winning move.
3. **It is not comparable across positions.** QB 74.0 vs TE 35.8 says nothing about which position is
   better predicted; it mostly says QBs score more points.

### 3.1 The metric, stated exactly

For position `p`, evaluation season `S`:

```
SS(p, S) = 1 − MAE_model(p, S) / MAE_floor(p, S)
```

- **Universe:** that season's pre-season consensus board at position `p`, frozen before Week 1,
  **busts retained at realised 0 points.** No games-played filter of any kind (ADR-B:54).
- **Outcome:** realised season total under this league's scoring engine (`scoring.score_offensive_game`,
  summed per game so the stacking yardage bonuses are computed at the game level, per `CLAUDE.md` §7).
- **`MAE_floor` — the frozen constant predictor:** predict, for every player at position `p` in season
  `S`, the **mean realised season points of that position's same-universe players over seasons < S**.
  Walk-forward; no target-season information; computable pre-season; frozen here and not tunable.
- **Reported alongside, always:** raw `MAE_model`, raw `MAE_floor`, and `n`.
- **Uncertainty:** season-level bootstrap on the per-season `SS`, 10,000 draws, integer seed recorded
  (guardrails §11 — never builtin `hash()`).

### 3.2 Why this form specifically

| Property | Consequence |
|---|---|
| Dimensionless | Comparable across positions, so one table reads correctly |
| Baseline built into the definition | §6.5 satisfied by construction; a bare number cannot be quoted |
| Negative exactly when the model is worse than knowing nothing about the player | Shrinking to the mean drives SS to 0, not up. The pathology in §3(2) is closed |
| Can fail the incumbent | See §3.3 |

### 3.3 Registered prediction, before the number exists

Written now so it can embarrass me later. `board.json:curve_fits` reports R² 0.158–0.266, so the
curve explains roughly a sixth to a quarter of outcome variance in-sample.

> **Prediction: `SS` lands between +0.05 and +0.20 at every position, and may be negative at QB.**
> The QB curve's walk-forward bias runs +33.4, +36.8, −15.3 (assessment §6.1) — a biased predictor
> can lose to a constant.

**Pre-committed audit trigger, adopting ADR-E §8's pattern and guardrails §8.7:** any `SS > 0.35` at
any position **halts reporting and escalates as suspected leakage**, for either the incumbent or a
candidate. An unusually good result here is evidence of a bug more often than of a good model.

---

## 4. Two preconditions on promoting `top_k_starter_vbd`. Both blocking.

### 4.1 Precondition A — a defect found by reading the code, and it flatters the wrong thing

**Blocking. Must be fixed and re-measured before P1 gates anything.**

`src/backtest.py:414-444` and `455-489` both accumulate value with:

```python
total += vbd.get(pid, 0.0)
```

`vbd` is built by `_vbd_lookup` (line 403) **only over players present in `_season_actuals`** — i.e.
only players with at least one weekly stat row in season `S`. `compute_vbd` (`src/scoring.py:212`)
returns `pts − replacement`, so a genuine zero-point season *that happened* correctly scores a large
negative.

But a ranked player with **no weekly row at all** — retired, cut, season-ending preseason injury,
suspended for the year — is absent from `actuals`, so:

- his position still resolves, via `build_position_lookup`'s second query, where *"rankings win"*
  (line 234-239), so
- **he consumes a starting slot**, and
- `vbd.get(pid, 0.0)` returns **`0.0`** — which on the VBD scale means *exactly replacement level*.

**A first-round pick who never takes a snap is scored as a replacement-level player, not as a
disaster.** His correct contribution is `0 − replacement_points`, roughly −100 at RB and −90 at WR on
this league's baselines.

This is not the same error as a survivorship filter and it is easy to mistake for compliance:
guardrails §2 and ADR-B:57 both require the never-played player **retained at zero points**. He is
retained — but scored at zero *VBD*, which is a completely different and far gentler quantity. The
harness passes the letter of the rule and violates its purpose.

**Direction of the bias:** it systematically under-penalises any ranking that promotes
injury-, suspension- or roster-risk players. That is precisely the channel the assessment's §4 claims
is the largest one on the table. Promoting a metric with this defect and then testing an availability
hypothesis on it would be a closed loop.

**Required fix:** a ranked player with a resolved position and no realised production contributes
`0 − replacement_points[pos]`, not `0.0`, in both `top_k_starter_vbd` and `_vbd_sum_for_ranking`.
Regression test asserting it, written before the fix.

**Required re-measurement, because a published number depends on it:** ADR-025's board-vs-consensus
figures (+176.0 / −34.7 / +113.4 / **+83.8 on the sealed holdout**) were computed under the defective
version. They must be re-reported under the fix, with the count of affected player-seasons per arm
per season stated. **Re-computing an already-spent holdout number under a corrected metric does not
constitute a second holdout access** — the season was already unsealed for exactly this decomposition
(three entries in `holdout_access_log.jsonl`, ADR-025) and no new decision is being made from it. Log
it as a recomputation with that reason, do not treat it as a fresh spend, and do not let the corrected
number become a new claim.

### 4.2 Precondition B — the no-opponent bias is a permanent reporting obligation

`top_k_starter_vbd` assumes the top-15 arrives uncontested. Its own docstring says so. In a 10-team
snake from slot 3 the user receives roughly the 3rd, 18th, 23rd… best *available* player, never his
own top 15. The metric therefore answers *"is your list a better starting lineup than their list"* and
**not** *"does this ranking draft a better roster."* Those diverge exactly when scarcity binds.

Not a code fix. A binding reporting rule:

1. Every report of P1 carries the adjacent line: *"no opponents: assumes the top-15 arrives
   uncontested; measures ordering quality, not draft-day scarcity."*
2. **P1 may never gate a question whose whole effect is draft timing** (Hero RB, Zero RB, VONA,
   pick-gap awareness, positional runs). Those go to `src/draft_sim.py`, reported with its measured
   noise floor (≈8.5 pts / 300 sims, and the n=4-season bootstrap binding, per the 2026-07-30 #35/#36
   session) stated beside the estimate.

---

## 5. The pre-committed decision rule

Per position, evaluated once per candidate. Written before any candidate exists.

**ADOPT a candidate ranking or projection at position `p` iff all three hold:**

| | Criterion | Instrument |
|---|---|---|
| (a) | paired mean `Δ top_k_starter_vbd` vs the incumbent shipped board **> 0**, season-level bootstrap 95% CI reported | P1 |
| (b) | `SS(p)` **strictly greater** than the incumbent's `SS(p)`, **and both > 0** | P2 |
| (c) | per-position τ_b **not degraded by more than 0.02** vs the incumbent | diagnostic |

**(c) is the anti-tilt guard and its threshold is not fitted.** PR-004 §4 established +0.04 Δτ_b as
the materiality floor from decision-relevance arithmetic — over a ~48-player draft-relevant universe
(1,128 pairs), Δτ = 0.04 corrects ~23 pairwise inversions, about one improved pick per draft. Half of
that, 0.02, is roughly half a pick: the largest player-level degradation that can be called "did no
harm." Same arithmetic, same universe, no new free parameter.

(a), (b) and (c) are a **conjunction**, so they do not enter the FDR denominator — a conjunction can
only reduce rejections. The denominator is the count of *positions × candidates* declared before the
campaign, fixed in a family manifest under `docs/preregistration/families/`.

### 5.1 Power, pre-committed and not relaxable

Usable board-vs-market evaluation seasons are the intersection of board-buildable (2022+) and market
coverage, minus the sealed 2025: **three seasons today.** A two-sided sign test floors at **p = 0.25**
at n=3 and **p = 0.125** at n=4. *This design cannot produce a significant result at any effect size.*

> **Pre-committed: while the usable evaluation-season count is below 6, no result on P1 or P2 may be
> published as "beats the market," "has edge," or any directional claim. Results are reported as the
> raw paired season differences with a season-level bootstrap CI and no p-value.**

This extends ADR-B:65's existing floor to P1 and P2 verbatim. It is written before any number exists
precisely so that a favourable number cannot buy an exception.

**These are build-decision gates, not publication instruments.** They exist to stop the next six
weeks being spent optimising against a ruler that returns 0.000000 by construction. They do not
answer "does the board have edge." Nothing available before 2027 answers that.

---

## 6. What would falsify this ruling

- **Falsifies the P1 promotion:** precondition A's defect turns out not to exist (backend measures
  zero affected player-seasons across all arms and seasons), *and* someone demonstrates a class of
  ranking on which `top_k_starter_vbd` and a real draft simulation give opposite signs at n≥6. Then
  the simulation is primary and P1 is the cheap proxy.
- **Falsifies P2's floor:** the constant predictor turns out to be beaten by nothing — if every model
  including the incumbent posts SS ≤ 0, the honest product action is to display no projection at all,
  and this ADR pre-commits to that outcome rather than lowering the floor.
- **Falsifies the whole two-metric split:** a single instrument that is simultaneously
  cross-position-sensitive, opponent-aware, and powered at n≤6. `src/draft_sim.py` is the candidate
  and its measured noise floor currently says no.
- **Falsifies §5.1's publication freeze:** the evaluation-season count reaching 6 by a route that does
  not change the estimand. See the companion ruling on the market-rank curve source, which finds the
  proposed route does change it.

---

## 7. Guardrails accounting

Look-ahead §1: P2's floor is walk-forward and uses only seasons < S; universes frozen pre-Week-1;
2025 sealed and untouched by anything registered here. Survivorship §2: busts retained at realised 0
points, no games filter, and precondition A exists precisely because "retained at 0 VBD" was quietly
not the same thing as "retained at 0 points." Multiple comparisons §3: gates are conjunctive and
excluded from the denominator by construction; the denominator is positions × candidates, declared in
a family manifest before the campaign. Non-stationarity §4: not addressed here; any candidate cleared
under §5 carries an era-split obligation from its own registration. Baselines §5: built into P2's
definition and named explicitly in P1's pairing. Metrics §6: P1 is the roster-shaped metric §6.6 asks
for, with its no-opponent gap stated rather than papered over. Uncertainty §7: season-level bootstrap
on every figure, `n` printed. Reproducibility §11: integer seeds, recorded.
