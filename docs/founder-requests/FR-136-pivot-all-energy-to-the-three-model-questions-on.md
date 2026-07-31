---
ID: FR-136
STATUS: NEW
SOURCE: PM session 2026-07-30, founder chat
RAISED: 2026-07-30
PRIORITY: HIGHEST — this is the founder's bar, and it outranks the six
NEEDS: pm to sequence; fable, strategist, ranker, researcher, data-ops
---

## Request

Founder's own words:

> "after these last front end items, all of our energy should be pointed at the three key questions -
> the true value (now I think we are close enough on the presentation of it to the front end) - we
> really need to sharpen the data/research/strategy portions significantly"

## What "the three key questions" are

His bar, from `docs/pm/HANDOFF.md` §6, in his own words:

> "If I don't have those three things in place, I don't want to use the tool for my real draft."

1. The best **bottom-up rankings** — true value
2. The best **availability prediction**
3. The best **suggested-pick model** — accounting for his roster, opponents' rosters and availability,
   dynamically during the draft

**A previous PM framed these as off-season design work and was overruled**, in terms worth keeping in
front of anyone who picks this up:

> "NO, they are this season questions, we will finish all these items quickly, I am working much
> faster than Fable, just stop worrying about time honestly."

## What this message changes

Two things, and the second is the significant one.

**"Close enough on the presentation."** Frontend and design work drops from the top of the queue once
the in-flight items land. It does not stop — FR-135's draft board is a real gap and the light-theme
and rankings-pane items are in flight — but it stops being where energy is *pointed*.

**"Sharpen the data/research/strategy portions significantly."** This is the pivot. The three questions
are all model questions, and the honest position is that none of the three has been adversarially
reviewed.

## The thing to do first, and it is already written

`docs/fable-mandate-M-2026-07-29.md` is **written and has never been run.** It is aimed at exactly
these three questions, it carries the founder's correction of the PM's framing verbatim, and no
M1/M2/M3 output exists anywhere in the repo.

Fable has not been used this week.

**Correction, founder 2026-07-30 — this PM had it wrong twice and was told to stop:** Fable is
*accounted* separately, but it **draws on the main pool and counts against the weekly total.** It is
not free capacity and running it is not costless. It is dispatched at the end of the week because that
is when the founder chooses to spend that budget, not because the budget is separate from everything
else. Any sentence implying "Fable costs nothing from the main budget" is wrong.

## Honest state of the three, 2026-07-30

| Question | State |
|---|---|
| **1 · Bottom-up rankings** | Component models exist for WR and RB/QB/TE. Never adversarially reviewed. The variance-preference idea was tested four ways and is dead (CLAUDE.md §7) — that is the standard the rest should be held to |
| **2 · Availability** | Under active methodology review — thread 119, strategist, answered 2026-07-30 with a pre-registration document. Computed for **2 of 26 leagues** (FR-133). Browser-side recompute unblocking now |
| **3 · Suggested pick** | Weakest of the three. The measured `need` parameter is an open decision that PM must not frame, because PM authored the claim |

## Sequencing

Explicitly gated by him on the in-flight frontend work: *"after these last front end items."* Not
before.

Before dispatching a campaign, the test ideas need collecting into one list with a falsifier and a
baseline per item — see FR-134. Parallel agents pointed at an uncollected list produce parallel
opinions rather than evidence, and §6.3's multiple-comparisons exposure applies to the campaign as a
whole, not to each test in isolation.
