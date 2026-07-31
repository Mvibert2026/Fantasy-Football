---
ID: FR-2026-07-31-fable-next-week-sequencing
STATUS: RESOLVED — founder decision
SOURCE: PM session 2026-07-31, founder chat
RAISED: 2026-07-31
PRIORITY: HIGH — sets the week's shape and the holdout timeline
---

## Decision

> "Eh I can go through 9m tokens in a single day easily. So we have lots of 'time' in the 38 days
> left. Not enough tokens this week for fable. We'll run that to start next week after the reset."

**Fable runs first thing next week. Everything holdout-dependent waits behind it, by his own
2026-07-31 ruling that the sealed 2025 season does not open until fable has run.**

## What this settles, and one PM error it corrects

**Token budget is not the constraint over the 38 days; this week's remainder is.** PM recommended
cutting the testing programme and cited an estimate of ~2.5M tokens as though that were expensive.
**That framing was wrong.** The correct reason to stop testing external factors is that the source is
exhausted — 90 registered tests, zero edges, and every published factor is by construction already
inside consensus, because consensus is made of the people who published it. That argument holds at any
budget. The cost argument did not, and should not have been made.

**With capacity available, the programme should be wider rather than narrower** — but wider in
*shapes*, not in *factors*. Everything tested so far was a single global linear weight. Gates,
thresholds, interactions and position-specific weights are entirely untested, and the founder's own
high-carry-threshold question is a gate.

## Consequence for the holdout

The 2025 holdout is gated on fable. Fable starts next week. **So the earliest any result can be
confirmed against 2025 is mid-next-week.**

That is not blocking, and it is worth recording why: **the v1 agent declined to ask for the holdout
even when it could have.** Its reasoning — v1 is not frozen, four named feature blocks sit untouched
in the database, and spending a single-use asset to confirm a loss buys nothing — is the right
standard and should hold for anything queued behind it.

## Shape of the work

| Window | Work |
|---|---|
| **Rest of this week** | Everything fable-independent and holdout-independent: the player-availability defect, the internal wires, untested functional forms, M0's data defect, the recommender constants, the QB-tilt reconciliation, merge and deploy |
| **Start of next week** | Fable, on mandate M — five sections, including the consistency mandate and the audit-trail index |
| **After fable** | Whatever it does not kill, and only then the holdout |
