---
ID: FR-109
STATUS: NEW
PRIORITY: HIGH — potential invalidation of a headline result
SOURCE: chat 2026-07-30, PM session
RAISED: 2026-07-30
---

## Request
The VBD arm in the Zero RB simulation may be wrong — and strategy must be tested across draft slots

Founder's own words:

> "we can strategy probably needs to get tested against draft position. Hard for me really to believe
> vbd doesnt take a RB before 6th round."
>
> "Maybe a certain slot. But there's not 60 better players than the first rb. I have real questions
> about that test."

## Why this matters

He is challenging the mechanism behind a headline null, and **the challenge has independent support
from our own results.** This is not a preference disagreement; it is a possible invalidation.

## Three pieces of evidence, all pointing the same way

**1. The arithmetic he objects to is genuinely implausible.** `docs/ranking/fr085-zero-rb.md` §(6)
claims plain VBD takes its first RB in **round 6.3 on average**. The simulation runs on FFC's 12-team
archive, so round 6.3 is roughly overall pick 76. That asserts ~75 players carry more
value-over-replacement than the best available running back. His "there's not 60 better players than
the first RB" is the correct objection, and the real number is worse than the one he guessed.

**2. It contradicts our own measured slot values.** From the insights backfill, graded SURVIVES:

> VBD of the rank-1 slot over replacement, 2021–2025: **RB 168.5** [131.9, 217.9] > WR 153.2
> [135.6, 172.7] > QB 114.1 [57.0, 155.2] > TE 73.1 [53.3, 93.2]

**RB1 has the highest value-over-replacement of any position in this league.** A strategy defined as
"take the highest-VBD available player, no positional rules" (the pre-commitment's own wording,
`fr085-strategy-sim-precommit.md` §5) should therefore take an elite RB *early* — plausibly first
overall. Round 6.3 is not consistent with that, and both results cannot be right as stated.

**3. The agent flagged the likely cause itself.** From its own report:

> "I amended the pre-commitment's VBD definition after a smoke test but before any outcome
> comparison, which I've asked `strategist` to rule on rather than assume is fine."

A VBD definition amended after a smoke test is exactly where a discrepancy of this size would enter.

**4. A fourth signal that fits.** The same run found `bpa_consensus` — simply taking the
highest-consensus player — **beat the VBD arm** (+24.1 realistic points, +0.046 P(playoff)
[+0.006, +0.096], MARGINAL). If the VBD arm were behaving correctly on a board built from this
league's own measured replacement levels, consensus beating it would be surprising. If the VBD arm is
mis-specified, it is exactly what you would expect.

## The second half of the request, which is a separate real gap

**The simulation was run at one draft slot.** The run log shows `user slot 3, picks [3, 18, 23, 38,
43]`. Strategy value is obviously slot-dependent — at slot 1 the elite RB is available and at slot 10
he is not, so "should I take an RB early" has a different answer depending on where you sit. **Testing
one slot and generalising to a strategy verdict is not sound**, and the founder identified this
independently.

The machinery now exists: `src/live_availability.py` was extended yesterday (FR-057 part 1, ADR-061)
to sweep every draft slot.

## What must happen

1. **Audit the VBD arm before anything else.** Print, for a single seeded draft, the top-10
   available players by the simulator's own VBD at picks 1 through 76, with their VBD values and
   positions. If the best RB is not near the top early, the arm is mis-specified — and the reason
   will be visible in that dump.
2. **Reconcile against the 168.5/153.2/114.1/73.1 slot values**, or explain precisely why the
   simulator's VBD differs from the VBD that produced them.
3. **Re-run across every draft slot**, not slot 3 alone.
4. **Do not re-report the Zero RB verdict until 1–3 are settled.** If the VBD arm was wrong, the null
   is not a finding about Zero RB — it is a finding about a broken baseline, and everything compared
   against it inherits the defect.

**PM note:** I relayed "VBD already takes its first RB in round 6.3" to the founder as the
interesting mechanical explanation behind the null. I did not check it against the slot-value finding
sitting in the same ledger. That reconciliation was mine to do.
