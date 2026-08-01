---
ID: FR-2026-08-01-find-the-early-qb-penalty-scientifically-rather
STATUS: NEW
SOURCE: chat 2026-08-01
RAISED: 2026-08-01
---

## Request
Find the early-QB penalty scientifically rather than hand-setting -25

Founder's own words, chat 2026-08-01, immediately after Fable's M2 review reported that the
recommender's -25 constant is a hand patch over a category error:

> "Ok so instead of -25 should it be more given the cost of an early qb? Can we find it
> scientifically."

## Why it matters

The recommender's ordering function is `vbd + unfilled_need(+8) + tier1_te(+18) +
early_qb_penalty(-25)`. All three constants are hardcoded and none was ever fitted to anything --
the module's own docstring calls itself a stopgap. The founder has now caught this component
failing by eye twice, and it is the third of his three "must be true" questions.

The -25 is also the specific patch over the Allen-at-6 problem: VBD inflates elite QBs by ~20
places, and -25 was chosen to push them back down. So the question "should it be bigger" is the
natural one to ask, and answering it wrong -- by tuning the number -- would harden the error
rather than fix it.

## Initial read

**The honest answer is that it probably should not be a constant at all, and PM told the founder
so rather than tuning it.** Fable's M2-3 finding (`docs/fable/M2-findings.md`) dissolves the
apparent contradiction between the board (Allen at overall 6) and PR-003 (early QB costs -115
points from slot 3, negative in 12 of 12 cells) as **stock vs flow**: season VBD is a value stock,
a pick recommendation is a policy. Both findings are right about different quantities.

What the -25 approximates is **opportunity cost**, which is contextual -- it depends on draft
slot, live board state, and who survives to the next pick. The measured reason early QB is costly
is that QB value is cheaply available later (the QB premium collapsed -67 -> -4). Fitting a single
value to that would be fitting a constant to something that is not constant, and would fit it to
`draft_sim`'s opponent model, which is ECR plus an unfitted global sigma the code's own metadata
calls "a guess."

**Action taken 2026-08-01:** PR-007 (`docs/preregistration/PR-007-recommendation-constants-ablation.md`)
was dispatched to `backend`. It was registered 2026-07-29 by strategist and had sat unrun for
three days while ~90 factor tests ran -- Fable flagged exactly that. It is a leave-one-out
ablation of all three live constants measured in **paired roster points against actual historical
outcomes** under this league's scoring, not rank correlation, and a constant must clear seven
criteria including a positive margin in all nine season-by-sigma cells to survive. It is powered
to delete. The DEF term is deleted unconditionally with no arm run.

**Explicitly out of scope for PR-007, and deliberately:** a sweep over the penalty's *value*. The
dispatch instructs backend not to add one, for the reason above, and to state instead whether its
measurements support or undercut the contextual-quantity argument.

**The real replacement is VONA** -- `score = VBD - E[best same-position VBD at your next pick]`,
i.e. the -25 computed rather than guessed. Gated, not free: PR-008 already measured a naive VONA
with a crude scarcity input **losing** to plain VBD by ~-106 to -126 points. Opportunity-cost
logic is only as good as the survival model beneath it, so the correct order is availability
sigma calibration (M3) before the recommender rewrite -- which is the founder's own stated build
order.

If PR-007 returns DELETE for a constant, removal from `frontend/ui/data/recommendation.ts` goes
through a handoff thread to `frontend`, not a self-merge by the agent that measured it.
