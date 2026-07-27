---
ID: 061
FROM: pm
TO: researcher
STATUS: OPEN
OPENED: 2026-07-27
BLOCKS: honest assessment of our own differentiator
---

## Founder request

> "FantasyPros does a decent job of recommending different players and showing a percentage of who it
> would pick (it doesn't explain why, but I'm sure it's thinking some of these things). Have the
> researcher look into it."

## What this is actually asking, and why it matters more than competitive curiosity

The project's central claim is that **availability-aware recommendation is our differentiator** — that
competitors rank players and we tell you what taking one costs you. FantasyPros Draft Wizard shows a
percentage next to recommended players. **Nobody here has established what that percentage is.**

Two possibilities, with opposite consequences:

- **It is availability-aware** — it changes based on how long until your next pick. Then our core
  differentiator is materially weaker than every document in this repo claims, and we should find that
  out now rather than after building around it.
- **It is a confidence or value score** with no survival modelling behind it. Then the claim holds, and
  we can state it with evidence instead of assumption.

**This test can damage our own thesis, which is exactly why it should be run.** Report whichever
answer the evidence gives.

## Method — probe the product, do not read the marketing

Their blog and help pages describe what they want you to believe. **Behaviour is the evidence.** Feed
controlled inputs and observe what changes. The founder holds a free-tier login; use the product as a
user, manually, at human pace.

**The diagnostic experiments, in priority order:**

1. **Vary picks-until-your-next-turn, hold everything else constant.** The decisive test. Set up two
   mocks with an identical board, identical roster, identical available players — but one where you
   pick again in 2 and one where you pick again in 20. **If the recommendation or percentage changes,
   they are modelling availability.** If it does not, they are ranking value. Nothing else in this
   thread matters as much as this one result.
2. **Vary your roster, hold the board constant.** Does a roster already stacked at running back change
   the recommendation? Tests roster-awareness and marginal-value reasoning.
3. **Vary league scoring** — standard vs half-PPR vs PPR — with the same board. Tests whether scoring
   genuinely propagates or only reorders a static list.
4. **Do the percentages sum to 100** across the displayed set? If yes it is a distribution over a
   choice set; if not, independent per-player scores. Different objects entirely.
5. **Is it deterministic?** Same inputs twice — identical output, or does it vary? Variation implies
   sampling or simulation underneath.
6. **Bye weeks and stacking.** Construct a roster with a bye collision and see whether the
   recommendation penalises a player who worsens it. Directly relevant to thread 059's addendum, where
   I registered a prediction that this effect should be small.
7. **Edge behaviour.** What does it do with a suspended player, an injured player, a rookie? Cheap to
   check, and it doubles as a table-stakes benchmark under FR-007.

Record inputs and outputs for each. **Screenshots or transcribed values, not impressions.**

## Constraints

- **Manual, human-paced use of a product the founder has an account for.** No automated harvesting, no
  bulk collection, no volume. This is using the product, not scraping it, and the distinction is the
  whole basis for it being fine.
- **Do not reproduce their numbers in our product.** This is research to inform our design; their
  output is not an input to ours. That would also reintroduce exactly the circularity the ranking work
  is trying to eliminate.
- Note anything relevant in their terms as you go, but do not restart the D-000 / D-020 licence
  analysis — those are settled for private use.

## Also worth establishing

- **What do they publish about the method?** Any stated basis — ADP-driven, expert-consensus-driven,
  simulation-driven. Tag it as a claim by them, not a fact.
- **Do other tools do this better?** Sleeper, ESPN, Yahoo and Underdog all ship draft assistants. A
  one-line characterisation of each is enough. We should know whether availability modelling is a
  genuinely empty niche or a crowded one nobody advertises well.
- **What does their UI do that ours does not**, specifically around explaining a recommendation? The
  founder notes it does not explain why. Confirm — and if it does explain, in what form.

## Done looks like

`docs/research/competitor-recommendation-audit-2026-07.md`:

- Per experiment: setup, observed output, and what it implies. Confidence tagged.
- **A direct verdict on experiment 1** — availability-aware or not — stated in one sentence at the
  top, because it is the finding that matters.
- An honest assessment of what our differentiator actually is, given the evidence. **If the evidence
  weakens it, say so plainly.** A weakened claim discovered now is worth more than a strong claim that
  turns out to be wrong.
- Anything they do well that we should adopt. Learning from a competitor's interface is not a
  concession.

**File boundary:** `docs/research/`. No code.
