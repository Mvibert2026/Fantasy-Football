---
ID: FR-047
STATUS: NEW
PRIORITY: MEDIUM
SOURCE: chat 2026-07-29, PM session
RAISED: 2026-07-29
ROUTED-TO: strategist, researcher
---

## Request
Per-opponent deviation, and deviation should widen as the draft goes on

Founder's own words, two messages:

> "A nice enhancement would be to allow me to set my opponents level of deviation individually based
> on what I know about them - Usually one or two wild cards in there.."

> "and deviation usually starts later in the draft than the first 20 picks or so, third round is
> where it starts, and only gets wider from there, probably something for our strategist and
> researcher etc. it should widen over the draft, picking is a nice option, so keep the three we
> have, but default should be some widening function.."

## Why it matters

**This is the founder supplying domain knowledge the model does not have, and it is testable.** The
simulator currently draws opponent noise from a single sigma applied uniformly across the whole
draft (`src/draft_sim.py:17-27`) — the same deviation at pick 3 as at pick 130, identical for every
opponent. Both of those are simplifications nobody has ever challenged with data.

The founder's two claims are separable and both are empirical:

1. **Deviation is not uniform across managers.** Some drafters track consensus closely; one or two
   are wild cards. This is the thing he actually knows about his league and cannot currently tell the
   app.
2. **Deviation is not uniform across the draft.** He puts the turn at roughly round 3 — the first
   ~20 picks are close to chalk, and it widens monotonically from there.

Claim 2 is the more valuable of the two because it applies to **every** league, including the
generic ones where nothing is known about the managers. Claim 1 only pays off in Westwood.

## Initial read

Not the founder's own words — PM's read.

**His explicit instruction on scope: keep the existing three sigma settings as a manual option, and
make the default a widening function.** Not a replacement — an addition, with the better default.

**This is a methodology question before it is a build.** Route to `strategist` (design and
registration) and `researcher` (whether published draft data supports a shape), per the founder's
own suggestion. Specifically:

- **Is the widening real, and what shape?** Linear in pick number, step at a round boundary, or
  proportional to consensus-rank dispersion at that point in the board? A shape fitted from data
  beats a shape assumed, and this is now fittable — see below.
- **Where does it start?** The founder says round 3. That is a hypothesis with a number attached,
  which makes it directly checkable rather than a vibe.
- **Does per-manager variance survive measurement**, or is what looks like a wild card just the tail
  of one common distribution? Worth answering before building a control that encodes an illusion.

**The data position has changed and this is the part that unblocks it.** `draft_sim.py` states sigma
*"is NOT fitted to anything: no observed draft-position data exists in this repo or is obtainable."*
That is now stale — FFC ADP is captured daily in three formats (`data/adp-snapshots-ffc/`) and
`tests/fixtures/real_draft_2025/` holds 160 real picks from the founder's own draft. **But the
binding constraint is historical ADP**: the ranker's pass 2 found `nfl.db` carries no ADP history at
all, both tables 2026-only, and opened thread 055 for FFC half-PPR 2018–2024. That backfill gates a
fitted answer here too.

**Calibration prior applies to the founder as well as to us.** "Deviation starts in round 3" is a
recalled impression of past drafts. It is a good hypothesis and it is exactly the kind of compelling
situational story this project's own record says is most reliably wrong. Test it; do not encode it.

**Sequencing:** behind FR-046 (wiring the opponent model into auto-fill at all) — a per-opponent
control is meaningless until opponents actually pick. Registration can start before the build.
