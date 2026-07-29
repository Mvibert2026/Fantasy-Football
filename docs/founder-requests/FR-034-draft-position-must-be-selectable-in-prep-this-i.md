---
ID: FR-034
STATUS: NEW
SOURCE: chat session 2026-07-29
RAISED: 2026-07-29
---

## Request
Draft position must be selectable in prep - this is a multi-league tool, not a Westwood tool

> "It's not for one league, it's dynamic - we will need the pages to allow for selecting a different
> draft position in prep. I have 3 leagues. At least."

Founder's own words, 2026-07-29, correcting the PM's framing in the org-structure proposal.

## Why it matters

**The PM described this as "a draft assistant for one league" in a proposal to the founder and he
corrected it.** That framing has been quietly wrong for a while and it shapes what gets built: a
one-league tool needs a config file, a multi-league tool needs the league and the draft slot to be
first-class, selectable state.

Concretely: **draft position changes everything downstream.** Availability, what survives to your next
pick, and the whole recommendation are computed from where you pick. Today the primary league's slot
is fixed and league 2's `user_draft_slot` is recorded as *"an unresolved placeholder — founder has not
supplied their actual slot."* So for one of his three leagues the tool is currently computing against
a made-up number.

## Initial read
**Two things, and only the first is small.**

1. **Draft slot must be selectable in Prep**, and everything derived from it must recompute. The
   value already exists in `LeagueConfig` (`user_draft_slot`); what is missing is a control and the
   recompute path.
2. **The multi-league framing is now confirmed as the product**, not a future scope note.
   `CLAUDE.md` §1 still says *"Current scope: single user, local only"* and describes multi-provider
   support as eventual. The founder has three leagues today and expects the tool to serve all of
   them, generically (FR-027). **That is a change to the standing spec and should be made
   deliberately rather than drifted into.**

Related and already unblocked: the model now reads its structural assumptions from `LeagueConfig`
rather than hardcoded constants (ADR-055), and every league exports the full artifact set (ADR-058).
Both were prerequisites for this and both landed 2026-07-29.

**Not yet dispatched** — raised alongside a possible frontend overhaul the founder has deferred, and
worth sequencing with that rather than bolting a control onto a screen that may be rebuilt.
