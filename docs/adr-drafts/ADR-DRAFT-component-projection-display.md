# ADR-DRAFT — May the component-model projections be displayed?

**Status:** Proposed (ruling issued; number to be allocated by `tools/handoffs.py adr next` at landing)
**Date:** 2026-07-30
**Owner:** Strategist (ruling) / Ranker + Backend (execution) / PM (the one residual founder question)
**Answers:** `docs/handoffs/2026-07-30-fr-136-q1-the-primary-metric-cannot-see-the-boar.md` item 3
**Related:** FR-054, FR-056, PR-004 §11.3 (escalation still open), `CLAUDE.md` §4 never-blend rule

---

## 0. The ruling

The question does not have one answer, because "ship as displayed projections" describes two
materially different acts and the ranker's framing merges them.

| Act | Ruling |
|---|---|
| Component projections **replace `board.json:projected_points`** | **NO.** Blocked until the model clears the primary-metric gate. Not negotiable by relabelling |
| Component projections ship as a **new, separately-named, non-load-bearing field** displayed beside a consensus-derived rank | **YES, conditionally** — four conditions in §3, all pre-committed. **Condition (a) has since been measured and FAILS at all four positions (§2.1), so today's answer is NO everywhere.** The conditional path stays open for a future model |

**This is a methodology question with a product consequence, and it has a methodology answer. Not
routed to PM.** One genuinely-founder-level question is left open in §5 and it is not this one.

> **Landed while this ruling was being written, and it decides it.** `backend` ran the head-to-head
> the ranker's §6.2 asked for — `docs/ranking/component-model-vs-incumbent-headtohead.md`, 2026-07-30.
> **The component model loses to the incumbent on projection error at all four positions.** The
> conditions below were written before that result was read; they are left exactly as written, and
> §2.1 applies them. Nothing here was reverse-engineered to fit the answer.

---

## 1. Why replacing `projected_points` is a NO regardless of how it is labelled

`projected_points` is not a display field. It is the **load-bearing input** to everything downstream:
`compute_vbd` reads it, VBD sets rank order across positions, rank order sets tiers, and the
availability simulation and the recommender both consume the resulting board — the ranker's own §6
dependency chain says so, and says a wrong ranking does not stay contained.

So writing a component projection into `projected_points` **is changing the ranking**, whatever the
caption says. The component models are measured *not* to beat consensus ADP on rank at any position,
and at RB — the one position where the experiment demonstrably has power — the point estimate is
**−0.052**. Putting that into the field the board is built from ships a ranking measured to be no
better than the market and possibly worse, and it does it through a channel labelled "display."

**Named failure mode: "displayed-only" as a laundering channel.** A number that cannot clear the
ranking bar gets shipped as a display, and then a downstream consumer reads the field and it becomes
load-bearing without anyone deciding that it should. This project has the antidote already —
ADR-035/ADR-060 established "ADP is display-only" *with evidence*, by demonstrating no code path
reads it. The same standard applies here and is condition (c).

---

## 2. Why the conditional YES is nevertheless the right answer

Three facts make the display case genuinely defensible rather than a consolation prize:

1. **The incumbent displayed number is very bad, and now measured.** R² 0.158–0.266; the 95% band on
   a single player's projection is **1.43×–2.41× wider than the entire spread from the best to the
   worst draftable player at that position**; walk-forward MAE is 0.30–0.40 of what the average board
   player actually scores. Whatever else is true, the bar is low and it is on the record.
2. **The component model is the one unambiguous win in the bottom-up work.** It beats naive
   persistence on **every component at all four positions**. "Does not beat expert consensus on rank
   order" and "is a worse projection than a log curve of consensus rank" are different claims, and
   only the first has been measured.
3. **It is what the founder asked for**, in his words: *"Hopefully we have lots of components in our
   rankings, we want it to be proprietary (youd think we'd have projections then too)."*

But note the asymmetry that makes conditions necessary: fact (2) is a comparison against *naive
persistence*, which is not one of `CLAUDE.md` §6.5's baselines in the form that matters here. Beating
persistence on component MAE says nothing about beating a consensus-rank curve on **season points**.

**That asymmetry is no longer hypothetical. It has been measured, and it is the whole answer.**

## 2.1 Condition (a), applied to the measurement that landed the same day

`docs/ranking/component-model-vs-incumbent-headtohead.md` (backend, 2026-07-30) — same universe (FFC
half-PPR 12-team ADP, 2018–2024), same units (season points via `pos_model.score_components()` under
this league's ruleset), walk-forward, busts retained, 2025 never read, six evaluation seasons,
season-block bootstrap 4,000 reps:

| position | incumbent MAE | component MAE | Δ (component − incumbent) | 95% CI |
|---|---|---|---|---|
| QB | **75.7** | 85.7 | +10.04 | [−3.84, +20.70] |
| RB | **58.6** | 64.8 | +6.18 | **[+0.92, +11.07]** |
| WR | **50.5** | 52.2 | +1.65 | [−0.87, +4.04] |
| TE | **39.8** | 44.7 | +4.86 | **[+3.77, +6.47]** |

**Condition (a) fails at all four positions.** Every point estimate favours the incumbent; two losses
(RB, TE) have intervals clear of zero; the other two are directionally worse and underpowered at n=6.
There is no position at which `SS_component > SS_incumbent` can hold, because the skill score is a
monotone decreasing function of MAE against a **shared** floor — the floor cancels in the comparison,
so the MAE ordering *is* the skill-score ordering. No further computation is required to apply the
condition.

> **Ruling, applied: the component projections do not ship as a displayed field at any position
> today.**

**Multiplicity cannot rescue this, and it is worth saying why so nobody tries.** Backend correctly
flags the comparison as four uncorrected tests. Correction only ever makes it *harder* to declare a
difference — so BH would, if anything, weaken the two "significant loss" verdicts at RB and TE. It
cannot move any point estimate, and **there is no position where the point estimate favours the
component model.** The decision-relevant fact is 4-of-4 directional, not the two p-values.

**What this does not settle**, restated from backend's own §"What this does and does not settle" so it
is not lost: it is one non-pre-registered comparison, six seasons, walk-forward but not the
embargoed-LOSO design of PR-004/PR-005, and it says nothing about the deeper rank-correlation
question those registrations answer separately. It answers exactly the question condition (a) asks,
and that is enough to apply condition (a).

**Backend's explanation of the loss is the most useful sentence in the document and should survive
into any summary:** the incumbent's curve is fitted on *this season's own market-anticipated rank
order*, which already prices in the injuries, role changes and depth-chart shifts the component model
must infer bottom-up from stale lagged features. The oracle-ladder room is real; the project has not
captured enough of it to clear a curve fitted to the market's own forward-looking read.

---

## 3. The four conditions. All pre-committed. None met today.

### (a) It must beat the incumbent on the incumbent's own bar

Per-position **MAE skill score** as defined in the companion primary-metric ruling §3: walk-forward,
same universe, busts retained at 0, 2025 sealed, season-level bootstrap.

> **`SS_component(p) > SS_incumbent(p)` at position `p`, or the component projection is not displayed
> at position `p`.**

Per position, not globally. A model that wins at WR and loses at QB displays at WR and not at QB.
Partial adoption is the correct outcome, not a fudge.

### (b) Both must beat the constant-predictor floor, or nothing is displayed

> **If `SS ≤ 0` for both the incumbent and the component model at position `p`, the product displays
> no projected-points number at that position and states why.**

This is the outcome I am most concerned nobody will accept later, so it is written now. A number that
is worse than "predict this position's average" is not a weak projection, it is an anti-informative
one, and displaying it beside a rank makes the rank look sourced when it is not. **An honest blank
with a reason is a shippable product state.** The project already ships blanks with reasons (DEF,
`def_supported = false`; archetype's four honest states; `evaluative_adjustment_available`).

### (c) A new field name, and nothing computes from it

- The field is **not** `projected_points`. A new key, e.g. `component_projection`, additive contract
  bump, handoff to `frontend` per the standing rule.
- **A test asserts no computation reads it** — not a comment, not a docstring, a test. Same standard
  ADR-060 met for ADP.
- `projected_points`, VBD, tiers, availability and the recommender continue to read the
  consensus-derived curve until the component model clears the primary-metric gate. That is a
  separate decision with a separate ADR.

### (d) The label is a specific enumerated behaviour list, not "it says it's a projection"

Founder-observable behaviours, each individually checkable (this is the evidence standard the
operating model requires for a founder-observable claim — an enumerated trigger list, not "tests
pass"):

| # | Behaviour |
|---|---|
| 1 | The field's measured MAE **for that position** is reachable from the number (tooltip/hover), stated in points |
| 2 | The screen states that the **rank is not derived from this number** — in plain words, wherever the two appear together |
| 3 | Where the projection and the rank **disagree in ordering**, that disagreement is visible rather than silently presented as agreement |
| 4 | Rookies with no stat history fall back to consensus and are **labelled as such on screen**, per the ranker's §6.4 (six of the top 150; highest is Jeremiyah Love at consensus #33) |
| 5 | Positions failing condition (a) or (b) show **no number and a stated reason**, not a blank cell |
| 6 | The 12-team-vs-10-team provenance caveat, if the underlying fit came from FFC, is reachable |

Behaviour 3 is the one most likely to be dropped and it is the most important. Two orderings on one
screen with no rule for which wins is a product that contradicts itself; making the contradiction
visible is the only honest resolution available, and it is also genuinely useful — a disagreement
between a bottom-up projection and consensus is exactly the signal the founder wants a proprietary
model for.

---

## 4. The sequencing constraint nobody may skip

A **2026** component projection requires 2025 features, and 2025 is the sealed holdout.
`holdout.release_for_final_fit()` exists for this transition and releases **after** model decisions
are frozen, never before.

> **This ruling does not authorise an unseal.** Unsealing is irreversible, closes the family, and
> requires a named human approver in `UNSEAL_LOG.md` (PR-004 §7). No agent may perform one under this
> ADR.

Order, and it is not reorderable:

1. Primary metric implemented, including its two preconditions.
2. Component models scored **through `pos_model.score_components()` under this league's rules, on
   season points**, on 2018–2024, against the incumbent — conditions (a) and (b) evaluated.
3. Decision frozen: which positions display, which do not.
4. **Only then**, with founder approval, `release_for_final_fit` and a 2026 run.

Step 2 is arithmetic on two objects that already exist and both of which are committed. It requires
no new model. It is the cheapest real answer available in this whole programme and it has never been
run.

---

## 5. The one question that is genuinely the founder's, re-flagged not resolved

`CLAUDE.md` §4: *"Ranking sources stay separate, never blended."*

Displaying a proprietary projection beside a consensus-derived rank is **not** a violation — the two
numbers stay separate and separately attributed, which is what §4 exists to protect. Condition (c)
is what keeps it that way.

**Averaging them into one score would be a violation** and would require a founder amendment to
`CLAUDE.md`. PR-004 §11.3 already escalated exactly this — the founder's own preferred product shape
is *"consensus adjusted for what we do have"*, which is a blend — and **that escalation has never been
answered.** It is re-flagged here, unresolved, and this ruling explicitly does not resolve it.

The middle path PR-004 §11.3 offered still stands and this ADR endorses it as the shape to build
toward: **consensus adjusts display and confidence — labelled overlay, disagreement flags — rather
than being averaged into a score.** Condition (d) behaviour 3 is precisely that shape.

---

## 6. What would falsify this ruling

- **Falsifies the conditional YES:** condition (b) failing at every position — if nothing beats the
  constant predictor, there is no defensible projection to display and the correct product is a
  blank with a reason.
- **Falsifies the NO on `projected_points`:** the component model clearing the primary metric's full
  ADOPT gate (§5 (a),(b),(c) of that ruling) at a position. Then it is not a display question at all,
  it is a ranking adoption, under its own ADR.
- **Falsifies condition (c)'s strictness:** a demonstration that a second projection field is
  unreadable to users without at least one derived quantity computed from it. Then the derived
  quantity gets its own registration; the field still is not `projected_points`.
