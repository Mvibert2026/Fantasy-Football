---
ID: FR-2026-07-30-bottom-up-first
STATUS: NEW
SOURCE: PM session 2026-07-30, founder chat
RAISED: 2026-07-30
PRIORITY: HIGHEST — sets the order of the three model questions
NEEDS: ranker (build), then strategist/backend (availability), then the recommender
---

## Request

Founder's own words:

> "Let's prioritize bottoms up. I think availability is probably most based on ADP, then the way the
> draft has fallen so far, other teams needs etc. The recommender would depend on both."

## What this settles

**A dependency order for the three model questions**, which had none. They were a list; he has made
them a chain.

    bottom-up rankings  ->  availability  ->  recommender

Both later stages consume the first. That is why he put it first, and it is correct: availability
simulates a draft over *some* ranking, and the recommender's opportunity-cost term `q·g` needs `g`
— value over the realistic fallback — which is a ranking output. **A wrong ranking makes both
downstream models confidently wrong**, and today's Q1 finding is that the shipped board is
within-position identical to consensus.

## His decomposition of availability, which matches the measurement

He names three inputs in order: **ADP**, then **how the draft has actually fallen so far**, then
**other teams' needs**.

That is not a guess and it lines up with what strategist established independently on thread 119:

- **ADP as central tendency** — adopted on estimand grounds, not accuracy grounds (H1 measured NULL
  2026-07-30; ADP is not more accurate, it is the right *quantity*, measured in picks with an
  uncertainty).
- **Draft state** — strategist's finding that with ADP plus per-player dispersion, the
  *unconditional* marginal is nearly closed-form, so **the simulator only earns its keep conditioned
  on live draft state.** The founder's second input is precisely the thing that justifies simulating
  at all.
- **Opponent needs** — the roster-need term. `need_penalty_per_surplus` and
  `mechanical_need_targets` already exist in the export; whether they are fitted or guessed is open.

**He has independently described the model the measurements point to.** Worth recording because it
is the second time today his instinct pointed at the right structure while his stated reason was not
the durable one.

## Consequence for the current queue

Ranker's Q1 pass was scoped as an assessment. It should end with a **build plan**, not only a
verdict — the founder has now said build. Everything else stays sequenced behind it, with the
exception of the three no-measurement card fixes already in flight, which correct false statements
rather than model behaviour.
