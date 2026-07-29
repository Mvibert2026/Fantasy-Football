---
ID: FR-046
STATUS: NEW
PRIORITY: MEDIUM
SOURCE: chat 2026-07-29, PM session
RAISED: 2026-07-29
---

## Request
Make auto-fill actually draft players — wire up the opponent model that already exists

Founder's own words:

> "so autopick is not fully working, but something is going on, we'll need to repair it in the
> future"

Earlier in the same exchange:

> "I like having it, I can now mock draft myself"
> "but I guess nobody is actually picking, too many great players available too late"

## Why it matters

"Auto-fill to my pick" is doing exactly what it was built to do — advance the clock with honest
placeholders rather than inventing picks. **The limitation is the design, not a defect in it.** But
what it was built to do is not what a mock draft needs, and the founder has now found that edge
himself.

This is the difference between practising the interface and generating usable data. Mocks gate the
core availability claim (0 of ~30 logged), the founder now has a practical way to self-serve them,
and a mock where nobody drafts produces a board that never depletes.

## Initial read

Not the founder's own words — PM's read.

**The opponent model already exists and nobody has connected it.** `src/draft_sim.py:196`
`opponent_pick()` drafts to consensus ECR perturbed by Gaussian noise, in units of draft picks, with
strategies (`strategy_bpa`, `strategy_hero_rb`, `strategy_zero_rb`, positional bias) already written.
This is the third instance today of capability sitting unused — see FR-043.

So the repair is **wire up what exists**, not build a simulator. Two real questions in doing it:

1. **Where does it run?** `draft_sim.py` is Python and the hosted site has no backend. Either the
   opponent rule is small enough to reimplement client-side — it is essentially *rank + noise, with
   a roster-need penalty* — or auto-fill stays local-only. Reimplementing invites drift between two
   copies of the same model; that is a real cost and should be decided deliberately.
2. **Give the founder the sigma control he already likes.** He specifically praised the deviation
   adjustment in Predictions. The simulator's sigma is the same idea: how closely opponents follow
   consensus. A slider from "chalk" to "chaotic" is the natural surface, and it is the honest one —
   the answer genuinely depends on the assumption.

**A stale premise to correct while doing this.** `draft_sim.py:17-23` states sigma *"is NOT fitted to
anything: no observed draft-position data exists in this repo or is obtainable (ADR-018 — no ADP
source)."* **That is no longer true.** The project now captures FFC ADP daily in three formats
(`data/adp-snapshots-ffc/`) plus the MFL proxy, and holds 160 real picks from the founder's own 2025
draft (`tests/fixtures/real_draft_2025/`). Sigma may now be *fittable* rather than guessed.

That matters beyond this ticket: a fitted sigma makes simulated opponents realistic, which makes
self-served mocks realistic, which bears directly on whether they are admissible as calibration
evidence (see FR-045). **Route the sigma-fitting question to `strategist` before anyone fits it** —
it is a methodology decision, and this project's rule is that confirmatory work is registered before
it runs.

**Sequencing:** after the frontend work currently in flight and after FR-042 (preset scoring). Not
before the draft. The founder's own framing — *"repair it in the future"* — is the right pace.
