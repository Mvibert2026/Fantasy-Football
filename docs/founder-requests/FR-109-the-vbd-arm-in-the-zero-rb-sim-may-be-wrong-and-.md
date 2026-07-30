---
ID: FR-109
STATUS: ANSWERED — ranker 2026-07-30; two follow-ups routed to strategist (see response)
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

---

## Ranker response, 2026-07-30 — audit complete

Code: `experiments/strategy/audit_vbd.py`, `why_first_rb.py`, `slot_sweep.py`.
Results written into `docs/ranking/fr085-zero-rb.md` §5.5 (new) and §5.4 (replaced), with §1(6) and
the closing paragraphs of §5.1 withdrawn. Raw output: `data/qa/fr109-slot-sweep-ffc-r16.json`.

**Step 1 — the arm is NOT mis-specified.** At overall pick 1 the highest-VBD player on the
simulator's board is RB1 (2022: Jonathan Taylor, VBD 229.5), the second-highest is RB2, five of the
top ten are running backs, the need penalty is zero for everyone, and the arm takes RB1. There are
not 60 better players than the first RB; there are none. Dump published in §5.5.1.

**Step 2 — the two results do not contradict each other.** Simulator rank-1 VBD (2021–24 mean) is
RB 223.1 > WR 178.6 > TE 109.5 ≈ QB 107.1; ADR-016's is RB 168.5 > WR 153.2 > QB 114.1 > TE 73.1.
**Both rank RB1 first**, which is the claim this FR said could not hold alongside round 6.3. It can,
and does. The estimators do differ — the simulator reads *finish*-rank curves where ADR-016 fits
*consensus*-rank curves, inflating magnitudes 1.1–1.5× at the top — and that is an undeclared
departure from a settled ADR which I have recorded as mine. It does not change the arm's behaviour:
the round-2 RB-vs-WR call comes out the same way under both curves.

**Step 3 — 6.33 is a mean of a bimodal distribution and should never have been reported alone.**
44.6% of drafts take an RB in round 1; 44.0% wait until round 11–12; **rounds 3–5 together are 0.5%,
with zero drafts in round 3.** Slot 1 is 100% round 1. It is also the most extreme cell in the run's
own σ grid — every other (board, σ) cell is between 1.17 and 4.64, and the primary ECR cell is 1.39.
And 97% of the round-11/12 picks are caused by the **need-penalty amendment**, not by value.
The founder's "maybe a certain slot" was the correct diagnosis.

**Step 4 — swept all ten slots.** The pooled §5.2 margins already drew slots uniformly, so they did
not need redoing; what was missing was the per-slot split, plus one real code bug — §5.4's slot table
came from the σ=20 cell because `playoff_rate_by_slot` was assigned outside the σ loop. Fixed.
The sweep's finding: **Zero RB and VBD draft 94–96% of the same players at slots 5–10.** Every
per-slot Zero RB margin is NULL; 5 MARGINALs out of 160 tests, against ~8 expected by chance.

**Verdict on the rule "do not re-report the Zero RB verdict until 1–3 are settled":** they are
settled, and **the null does not inherit a defect from the arm** — the arm executes its own
definition faithfully. The null does carry a **power** qualification now stated in §1(5): seven of
ten seats carry almost no treatment, so "not distinguishable" is right but "tested" is generous.

**Two things this audit surfaced that need an owner and are not mine to decide:**

1. **Replacement level is the parameter that decides this and it has never been tested.** Under the
   current teams×starters baselines (QB10/RB30/WR40/TE10) the round-2 call is WR by 25.3 VBD points.
   Under a "last rostered" baseline measured from the board's own top 150 (QB24/RB54/WR57/TE15) it is
   **RB by 2.8 — the sign flips.** Neither is obviously right. This is not test-registry #35 (a
   single global flex baseline, closed NULL); it is a per-position question and needs a
   pre-registered test owned by `strategist`.
2. **The need-penalty amendment carries about half the load** in the number I reported to the
   founder. The `strategist` ruling I asked for on that amendment should happen before any further
   strategy number is quoted, not after.

**On the QB crowd-out hypothesis** (raised separately, that our board over-ranks QBs and they crowd
out the RBs): the shipped-board figures reproduce exactly — `data/export/board.json` puts QB1 at
overall 6 against consensus 26 — but **the simulator does not draft from that board**, and on the one
it does the effect is not the mechanism. Pooled, the arm takes **0.98 QB against 3.26 WR** before its
first RB, **zero QBs in round 1**, and the pre-first-RB QBs go in round 4.9 on average. The crowd-out
is receivers, not quarterbacks. The shipped board's QB placement is a real and separate concern that
belongs to whoever owns `src/make_board.py`. Detail in §5.5.6.

**One correction back to this FR:** `src/live_availability.py` / ADR-061 is the *availability* model
covering every draft slot's pick numbers. It is not a strategy-simulation slot sweep and could not be
reused here — `experiments/strategy/sim.py` already took a `user_slot` argument; what was missing was
per-slot reporting, which is what `slot_sweep.py` adds.
