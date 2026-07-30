---
FROM: design
TO: pm, frontend
STATUS: OPEN — needs agreement before item 2 leaves the queue
DATE: 2026-08-01
AMENDS: PLAYER-PROFILE.md §4
---

# The archetype chip leaves the identity strip

## What the measurement changed

57.8% `UNCLASSIFIED` across 460 covered rows does more than support the old rule — **it changes what
the rule should be.**

§4 said the chip renders only on a real label, which left the strip one item shorter on **three cards
in five.** That is right for an occasional gap and wrong for the majority case: it makes the *common*
card look like the degraded one.

And the strip now has a claimant present on every player that can invalidate a pick. Both facts point
the same way.

## Why status wins the strip — and it is not 100% vs 42%

Frequency is the weaker argument and would be the wrong one to decide on: a rare fact can matter more
than a common one, which is the whole reason this app marks nulls at all.

**The real reason is what each one does to the decision.** A status can make the pick wrong outright —
you do not draft a suspended player at his ADP. An archetype changes how you *think* about a pick you
are still free to make. **One is a gate, the other is commentary, and only the gate belongs on the
line he cannot avoid reading.**

Frequency decides one thing only: **how loud status is allowed to be.** See `AVAILABILITY-STATUS.md`.

## The amended rule

**Archetype moves out of the identity strip into the disclosed section, where it renders on all four
states — including the three absences, each with its own sentence.**

Better than the rule it replaces on both counts:

- **The strip stops reflowing**, because its slots are now always filled. Stable geometry rather than
  one that varies across three cards in five.
- **The three nulls stop competing for a chip they were never suited to.** Per handoff 115 they are a
  modelling gap, a plumbing gap and a taxonomy gap. Three different claims cannot be told apart by
  three greyed chips; they can be told apart by three sentences.

| State | Kind of gap | What the card says |
|---|---|---|
| a real label | — | The label, plus what it means for a roster in one sentence. 194 of 460. |
| `UNCLASSIFIED` | taxonomy | "Covered position, but he met no archetype's threshold." The majority case — 266 of 460 — so it reads as a normal outcome, not a failure. |
| `ARCHETYPE N/A` | modelling | "The taxonomy covers RB, WR and TE only." A stable fact about scope; never resolves for a QB. |
| `ARCHETYPE —` | plumbing | "No `player_descriptions.json` was exported for this league." Names the missing input — **the only one that could resolve on its own**, so the only `not yet` of the three. |

## Forward compatibility with FR-123, which is not mine

If the rebuilt taxonomy lands as two axes — how a team uses him, what owning him does to a roster —
**this amendment is what makes that survivable.** Two labels would not have fitted the identity strip
at all; the disclosed section takes two lines without argument.

Moving it now is cheap and moving it after the taxonomy doubles is not, and the modelling work stays
free to change shape without a design dependency.
