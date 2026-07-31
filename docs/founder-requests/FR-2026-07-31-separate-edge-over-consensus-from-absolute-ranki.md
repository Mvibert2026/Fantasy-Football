---
ID: FR-2026-07-31-separate-edge-from-absolute-quality
STATUS: NEW
SOURCE: PM session 2026-07-31, founder chat
RAISED: 2026-07-31
PRIORITY: HIGHEST — a methodology correction affecting how every result so far is read
NEEDS: strategist, then a measurement
---

## Request

> "Are we making sure to separate edge over consensus and having the best rankings we can have?
> These analysts all aren't better than consensus. Certainly not every year."

## He is right, and the harness half-agrees with him already

**Two different questions have been reported as one.**

1. **Absolute quality** — are our rankings the best we can make them? Measured by `E1a`, component
   projection MAE against the incumbent.
2. **Edge over consensus** — do they beat the market? Measured by `E1b` (board error) and `E2`
   (board rank correlation).

The grading vocabulary **does** separate them — `PROJECTION-ONLY` exists precisely for "improves the
projection, does not improve the board", and several arms across batches 3, 6 and 7 earned it. But
every founder-facing summary has led with *"nothing survives"*, which is the **edge** verdict, and
that has buried the absolute-quality result underneath it.

**Concrete cases already on file where the distinction changes the reading:**

| Arm | E1a (absolute) | Board | Reported as |
|---|---|---|---|
| ANY/A at QB | −1.43, −1.26% | −3.06 board error, but E2 negative | "PROJECTION-ONLY" — buried |
| Passer rating at QB | −0.96 | −3.45 board error, E2 excludes zero on the wrong side | same |
| Lagged YPC → RB volume | **−1.88%** | E1b −0.72 | post-hoc, unshipped |
| Explosive rush rate | −1.51% | E1b −0.03 | PROJECTION-ONLY |

**These are real improvements to the rankings.** Graded against §6.5's baseline rule they are
failures, because that rule makes the comparison the headline. Both readings are correct; only one
has been reported.

## The second half of his point, which is the deeper one

> "These analysts all aren't better than consensus. Certainly not every year."

**This is the wisdom-of-crowds result, and it is the strongest argument against treating
"beat consensus" as the only bar.** Consensus *is* the aggregate of the analysts. Individual
analysts do not reliably beat their own average — that is what makes an average worth taking.

Today's own measurement is consistent with it: prior points-per-game replicated at **ρ = +0.668** and
was the **ceiling** — all ten alternative predictors, including every published analyst metric tested,
came in below it (batch 5).

So **"no edge over consensus" is the expected outcome, not a failure signal.** Reporting it as a
failure, session after session, misrepresents what was learned.

## The measurement nobody has run

**How good is consensus, year by year — and how much does that vary?**

Every result so far compares to consensus as though it were a fixed bar. The founder's
"certainly not every year" says it is not. If consensus is strong on average but poor in identifiable
seasons, then:

- "Beat consensus every year" is the wrong bar, and no factor will ever clear it
- "Be robust in the years consensus is wrong" is a different, achievable, and more valuable goal
- A proprietary source's job may not be to beat consensus but to be **independently wrong in
  different places** — which is what makes a second opinion worth having, and what
  `CLAUDE.md` §4's never-blend rule preserves

## What to do

Route to `strategist` before any further factor testing is graded, because it changes what the grades
mean. Then measure consensus's own year-to-year variance against realised outcomes.

---

## Strategist ruling, 2026-07-31

Full rulings: `docs/adr-drafts/ADR-DRAFT-edge-vs-absolute-quality.md`. Ruling-4 design:
`docs/preregistration/PR-DRAFT-consensus-quality-by-season.md`. Handoff to `backend` staged
(unallocated, no shell in this role): `docs/handoffs/STAGED-strategist-consensus-quality-by-season.md`.

**The founder's underlying point is accepted. This document's diagnosis of the mechanism is not, and
the correction runs the opposite way.**

1. **The two goals are not separated — but `E1a` is not the absolute-quality metric this document
   takes it for, and `E1b`/`E2` are not edge metrics at all.** `E1b` is the same component MAE
   *restricted to the ADP-board universe* (a population filter); `E2` is ADP-board Spearman
   **arm − primary model**. Consensus appears in neither. The only §6.5-shaped endpoint in the whole
   campaign is `E4`, present in one batch of seven.
2. **Three of the four rows in this document's own table invert.** ANY/A (`E2` −0.0118) and passer
   rating (`E2` −0.0180 [−0.0350, −0.0005]) did not lose to consensus — they made the ranking **worse
   than the incumbent model's own ranking**, the second with the interval excluding zero on the
   harmful side. They are measured degradations, not suppressed wins.
3. **`CLAUDE.md` §6.5 is not amended.** It governs *ranking versions*; a component arm is not one, so
   it never bound batches 1–7. **One escalation for the founder:** §6.5 and
   `docs/statistical-guardrails.md` §5 list *different* required baselines, and it matters here —
   his sentence is about **analysts** (expert consensus, what the shipped board runs off), while every
   measured "consensus" number in the campaign is **market** ADP. Different crowds; which is the bar
   is his call.
4. **"No edge over consensus" is the expected outcome in the weak form and the campaign has been
   misreporting it — accepted.** "Consensus is unbeatable" is refused: ADP's effective independence
   across 11 shops is ~6, a systematic era-robust early-round RB mispricing is already measured, and
   **no ranking version has ever been tested.**
5. **`ρ = +0.668` does not support this document's argument.** That is prior points per game —
   baseline #2 — measured against ten *rate statistics*. **Consensus ADP is not in that table.**

**Status: ruling issued; the measurement is specified and unrun.** PM: re-run
`python tools/founder_requests.py sync` if the status field is advanced.
