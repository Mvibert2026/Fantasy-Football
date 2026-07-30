---
ID: FR-070
STATUS: NEW
PRIORITY: HIGH
ROUTED-TO: strategist
SOURCE: chat 2026-07-30, PM session
RAISED: 2026-07-30
---

## Request
Calibration mocks cannot use my real league settings — triangulate, or use them for behaviour only

Founder's own words:

> "I won't be able to mock draft my real league settings against others, I can draft a few different
> leagues in yahoo against real people and we can do our best to triangulate, or use it for behavioral
> analysis"

## Why this matters more than it sounds

**The availability model is this product's signature claim and it is calibrated on nothing.** The
plan was ~30 mock drafts to fix that. He is now saying the mocks cannot be run under Westwood's
settings — public rooms are standard scoring with a kicker and one flex, his league is half-PPR with
stacking bonuses, three receivers, two flex and no kicker.

**So the sample and the target differ, and pretending otherwise would be the exact failure this
project's guardrails exist to prevent.** He has proposed the two honest options himself, and they are
genuinely different things:

**1 · Triangulate.** Run mocks across several Yahoo formats, model how draft behaviour varies with
format, and extrapolate to Westwood. Real, and it needs a method — extrapolating from three or four
formats to a fifth is a modelling claim, not an averaging exercise, and it needs its own error bars.

**2 · Behaviour only.** Use the mocks to measure *how far real drafters stray from consensus* —
which is sigma, the simulator's single unfitted assumption (`src/draft_sim.py:17-27`) — and
deliberately **not** to measure positional demand, which does not transfer across roster shapes.

## The PM's read: option 2 is the stronger one and it is nearly free

**Sigma is format-agnostic in a way positional demand is not.** How much a human deviates from the
consensus list is a fact about drafters; how many running backs go in round three is a fact about
roster requirements. The first transfers, the second does not.

And sigma is the assumption everything else rests on — availability, the strategy simulations, the
opponent model in FR-046/047. Fitting it would be the highest-leverage measurement available, and
**mocks in any format serve it.**

Option 1 should not be discarded, but it is a second-order refinement and it costs a real modelling
effort. Do 2 first; 1 becomes cheaper once sigma is fitted anyway.

## What this changes about the ~30 target

**The "0 of 30" framing needs revisiting.** Thirty drafts was never derived — it is a round number
attached to a claim nobody has priced. Given the sample cannot match the target league, `strategist`
should say what the mocks *can* answer and how many are needed for that, rather than counting toward
a target that may not mean what it appears to.

Related: `data/mock-drafts/founder-mock-2026-07-29.json` already holds one complete 150-pick draft
under FantasyPros mock settings. **It is the first data point for option 2** and its admissibility
question is exactly this one.
