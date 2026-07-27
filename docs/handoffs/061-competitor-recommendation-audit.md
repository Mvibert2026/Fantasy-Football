---
ID: 061
FROM: pm
TO: researcher
STATUS: BLOCKED-EXTERNAL
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

---
### researcher · 2026-07-27

**Artifact:** `docs/research/competitor-recommendation-audit-2026-07.md`.
**Status set to `BLOCKED-EXTERNAL`, not `RESOLVED`** — deliberately. Experiment 1, the one this
thread says matters more than everything else in it, was **not run**. Marking this resolved would
make an unrun experiment indistinguishable from a completed one, which is the exact failure this
thread was written to avoid.

**Verdict on experiment 1, to the extent it can be answered without running it:** the percentage the
founder saw is **Expert Voting** — an expert-consensus vote share that FantasyPros' own documentation
says holds *"all other things being equal"* and explicitly excludes your roster and team needs — but
FantasyPros separately ships **Pick Predictor**, a premium tab that simulates over multi-source ADP to
give the odds a player survives to your next pick, taking opponents' roster needs and picks-until-your-turn
as inputs. So the founder's specific number is not availability-aware; the feature one tab over is.
All of that is `[SNIPPET]` — their help centre returns **HTTP 403** to my fetcher and I did not route
around it.

**Why experiment 1 was not run:** this session had no browser tool, no interactive session, and no
credentials, and the only web capability is a stateless GET. Constructing two mocks with identical
boards and different pick distances requires session state. Not a time problem — structurally
impossible here. Their `/api/`, `/ajax/`, `/json/` paths are additionally `Disallow`ed in
`robots.txt`, so the backend route was closed regardless; recorded as blocked, not worked around.

**The finding that should change PM/strategist behaviour**, and it is worse for us than the thread
anticipated: **the thesis is materially weakened, but not by the expert-voting percentage.** It is
weakened because availability modelling is not an empty niche. FantasyPros ships it (Pick Predictor).
**DraftMilk** ships *"percentage chance each player is still on the board at your next pick,"*
*"roster-aware verdicts: value, urgency, need, and bye conflicts,"* and *"every recommendation shows
its reasoning — no black boxes"* — for **$14.99 one-off, with a free tier** (`[VERIFIED]`, fetched
from their site; verified as a published claim, not as working behaviour). A rival vendor's own
comparison credits Razzball War Room with the same idea. **"Competitors just rank players" is false
as a general statement and should be struck from every doc asserting it.**

What survives is narrower: *integration* (they split value / fit / survival across three separately
named indicators, survival paywalled; we compute one decision-relevant quantity) and *calibration* —
but calibration is currently a plan, not an asset, at **1 of ~30 mocks logged**. No competitor
publishes calibration evidence either, so today we and DraftMilk make the same unevidenced claim and
they make it to paying customers. §7 of the artifact proposes replacement wording.

**Worth adopting** (§8): they pre-publish *why their components disagree* — "Top Lift can have a lower
Expert Voting % because Top Lift considers your roster and Expert Voting does not." We blend marginal
value, need (λ=0.352) and run (δ=0.10) into one number and can show the user no such decomposition.
That is the cheapest high-value port here. Also: a 1/2/3-round horizon toggle on availability.

**Back to `pm`/`founder` for:**
1. A browser-capable session **plus** confirmation the founder's tier exposes Pick Predictor at all —
   it is premium-gated, which is the likely reason this capability went unnoticed until now.
2. Note for whoever runs it: record queue *ordering* and *percentage* as two separate observations.
   We already expect the two percentages to diverge; whether the **ordering** moves with pick distance
   is the real open question. Pre-register before looking.
3. `[GAP]` unclosed: Sleeper / ESPN / Yahoo native draft-recommendation behaviour. My searches
   returned draft-strategy journalism, not product docs. Do not read that as "the platforms don't do
   this."

**Repo state:** this session had **no shell** — could not pull, branch, commit, or push. The artifact
and this reply are **uncommitted in the worktree**. `D-000`/`D-020` untouched; no FantasyPros numbers
reproduced anywhere.
