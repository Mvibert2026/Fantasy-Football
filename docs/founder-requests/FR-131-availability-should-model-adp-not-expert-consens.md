---
ID: FR-131
STATUS: NEW
SOURCE: PM session 2026-07-30, founder chat
RAISED: 2026-07-30
PRIORITY: HIGH
NEEDS: strategist, then backend
---

## Request

Founder's own words, on being told the availability model and the board run on different ranking
sources:

> "Availability is probably more related to ADP than consensus"

## Why it matters

**He is right, and the measurement is stronger than the argument.**

The availability model asks *who will still be on the board when my turn comes*. That is a question
about **what drafters do**, not about **what analysts think**. Expert consensus is a normative
ranking; ADP is the empirical distribution of the exact behaviour being simulated. Modelling opponent
behaviour off consensus means modelling drafters as if they drafted correctly — which is the one
assumption a draft simulator cannot afford.

### The data is already in the database, in this league's exact format

    as_of 2026-07-29 · half-ppr · 10 teams · 180 players

Half-PPR, ten teams, is Westwood. And it is **fresher than either ranking source** the product
currently uses — one day old, against the board's three and availability's six.

### It also carries the number the simulator is currently guessing

`ffc_adp_snapshots` has a per-player `std_dev`, measured across real drafts, alongside
`high_pick`, `low_pick`, `times_drafted` and `total_drafts_in_sample`.

Today's simulator uses **one global sigma for every player**, offered at 5 / 10 / 20, and its own
exported metadata admits what it is:

> "Sigma is how far the other opposing teams stray from consensus... **It is a guess, not fitted to
> observed drafts**, which is why every number is given at all three settings."

Measured against this league's format:

| Per-player `std_dev` | |
|---|---|
| Minimum | **0.4** |
| Median | **9.7** |
| Maximum | **39.2** |

The median lands almost exactly on the default guess of 10, which is a point in the guess's favour.
**But the spread is the finding, and it is structured, not noise:**

| The room agrees | | The room does not | |
|---|---|---|---|
| Jahmyr Gibbs | sd 0.6 | Evan McPherson | sd 39.2 |
| Bijan Robinson | sd 0.7 | Hunter Henry | sd 28.0 |
| Puka Nacua | sd 0.4 | George Kittle | sd 26.9 |
| Christian McCaffrey | sd 1.3 | Alvin Kamara | sd 26.2 |

**A single global sigma treats Bijan Robinson and Alvin Kamara as equally unpredictable.** They are
not, by a factor of forty. Bijan goes at pick 2 in essentially every draft; Kamara's landing spot is
close to a coin flip across three rounds. Every availability probability for a high-variance player
is currently computed with the wrong dispersion, and the direction of the error differs by player —
so it does not wash out.

This matters most exactly where the founder uses the number: *"will he last until my next pick?"* is
a question whose answer is dominated by dispersion, not central tendency.

## Initial read

**Two separable changes, and the second may be the bigger win.**

1. **Central tendency: ADP instead of expert consensus** as what opponents draft from. Directly what
   the founder proposed.
2. **Dispersion: per-player `std_dev` instead of one global sigma.** He did not ask for this — it
   fell out of checking whether (1) was feasible — and it replaces an admitted guess with a
   measurement, which is a stronger kind of improvement than swapping one ranking for another.

**Both need strategist before either is built.** Real questions that are not PM's to answer:

- Is FFC's ADP room representative of a Yahoo room? It is a different population, and the founder's
  own mock drafts are Yahoo-lobby drafts, so there is a check available.
- Does `std_dev` from FFC transfer, or only its *shape*? Per-player relative dispersion may transfer
  where absolute values do not.
- The current model draws one shared noise vector per simulated draft — *"the room collectively
  valued him a round higher this year"*. Per-player sigma has to compose with that, not replace it
  silently.
- ADP coverage is 180 players against the board's 510. What happens past the ADP tail is a real
  design question, not an implementation detail.

**One thing that must not get lost.** ADR-035 established a binding constraint: MFL ADP is a proxy
and must **never be presented as this league's ADP**. FFC half-PPR 10-team is materially closer to
Westwood than MFL is, but it is still not this league's own draft room. If it becomes the opponent
model's basis, the same honesty rule applies to how it is described.

**And a licensing note.** ADR-018 concluded no market ADP was legally obtainable, FFC included. That
conclusion was reached under a redistribution framing the founder corrected today: nothing here is
redistributed, the site is password-gated, and personal use is the posture. FFC data is already being
captured on a schedule. Worth stating explicitly so nobody re-litigates it from the old ADR.
