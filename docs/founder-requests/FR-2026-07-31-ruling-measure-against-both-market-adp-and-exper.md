---
ID: FR-2026-07-31-both-baselines
STATUS: RESOLVED — founder ruled
SOURCE: PM session 2026-07-31, founder chat
RAISED: 2026-07-31
PRIORITY: HIGHEST — settles a contradiction that ran through a full campaign
---

## The escalation

Strategist found `CLAUDE.md` §6.5 and `docs/statistical-guardrails.md` §5 naming **different**
required baselines, and flagged it as load-bearing rather than cosmetic:

- §6.5: market ADP / prior points / tier heuristic
- guardrails §5: BPA / market ADP / **FantasyPros expert consensus**

The founder's own sentence — *"these analysts all aren't better than consensus"* — is about
**analysts** (expert consensus, which is what the shipped board and the availability model actually
run on). **Every measured "consensus" figure in the entire campaign is market ADP.** Different crowds,
used interchangeably for a day.

## The ruling

> "I'd measure against both."

**Correct, and it resolves the contradiction by requiring rather than choosing.** The two are not
substitutes:

| Baseline | What it is |
|---|---|
| **Market ADP** | The empirical distribution of what drafters actually did |
| **Expert consensus** | Analyst opinion — and what `src/draft_sim.py:120` and the shipped board run on |

A version can beat one and lose to the other, **and which one it beat is the finding.** Beating
analysts while losing to the market means something different from the reverse: the first says we
read the room better than the pundits, the second says we know something the market has not priced.

## Applied

`CLAUDE.md` §6.5 amended — four required baselines, both crowds named explicitly, with the rule that
a version beating one and not the other must **report exactly that, not the flattering half**.

Also folded in strategist's Ruling 2 scope finding, since it lives in the same paragraph: **§6.5 binds
a *ranking version*, not a single feature inside one component of an unshipped model.** That
misapplication ran through seven factor batches, labelling an arm-versus-primary-model comparison as
the consensus bar.
