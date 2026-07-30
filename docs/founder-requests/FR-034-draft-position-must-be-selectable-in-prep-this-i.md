---
ID: FR-034
STATUS: SHIPPED
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

## Update (2026-07-29, frontend)

**Item 1 (the concrete build) is done.** Item 2 (amending `CLAUDE.md` §1's "single user, local
only" framing) is **not touched** — that is a standing-spec change, and CLAUDE.md is explicit that
only a deliberate decision changes it, not a build session acting on its own read of a founder
quote relayed secondhand. Flagged back to whoever owns that decision.

Built: a SLOT control in the top bar (`ui/components/shell/TopBar.tsx`'s `DraftSlotControl`),
range strictly `1..league.teams` (never a hardcoded guess when `teams` isn't loaded yet), present
in **both Prep and Draft mode** since the top bar is mounted outside `App.tsx`'s mode switch —
confirmed by screenshot in both. One click to change slot, a "rand" button for a quick rehearsal
pick, and a clear ("×") control that appears only once overridden.

Storage: `ui/data/draftSlot.ts`, `prep.draftSlot.<leagueId>` — same shape/lifecycle as the existing
`prep.draft.<leagueId>` draft-state store, per-league, survives reload (screenshot-verified).

Recompute: `ui/data/league.ts`'s `applyUserSlotOverride` is the single seam every downstream
consumer (DraftRoom, PlayerDetail, Predictions, RoundGrid) reads through — none of those files
needed to change. The one non-obvious part: `league.json:pick_sequence` is real backend arithmetic
for the *sourced* slot only, so it had to be recomputed with the same snake-order formula
(`pickNumbersForSlot`) for the overridden slot, not left stale — otherwise DraftRoom's MY PICKS
panel and RoundGrid's "mine" highlighting would have silently pointed at someone else's picks.
Covered by `ui/__tests__/league-override.test.ts` (9 tests), including one that asserts the
recomputed sequence differs from the sourced one.

Two Cells stay separate on `LeagueConfig` (`userSlot` = effective value everything computes from,
`userSlotSourced` = the real `league.json` value, `userSlotOverridden` = a boolean) so a screen can
show both and mark which is which — an override never renders through the same path as a real
export value (Principle #1/#2). Predictions.tsx's new context line (FR-035) is the first consumer
of this distinction: it shows `your slot N (overridden, sourced M)` only when true.

Screenshots: `frontend/e2e/artifacts/fr034-slot-selector-prep-before.png`,
`-prep-overridden.png`, `-draft-mode.png`. Tests: `ui/__tests__/draftSlot.test.ts` (9),
`ui/__tests__/league-override.test.ts` (9). Commits `e54b83f`..`1775ac6` on branch
`worktree-agent-ad3fc0f6ee64497b5`.

## Update (2026-07-30, frontend) — colour fix per docs/design/SUPPLIED-VALUES.md

Design flagged that the overridden slot rendered in `--acc` green — the board's delta/"good" colour
— which a self-selected slot is not. Fixed: the TopBar SLOT control's border, label and value no
longer use `--acc` in the overridden state; the value carries a dotted underline instead (the app's
one and only "you put this here" marker), and the disclosure text changed from "· sourced N" to
"· set by you, league file says N" (same underlying `userSlotSourced` value, clearer wording). Same
fix applied to `Predictions.tsx`'s own "your slot N (overridden, sourced M)" readout — a third place
showing the identical value in the identical wrong colour, not named in the design spec but the same
defect class. Tests: `ui/__tests__/topbar-supplied-slot.test.tsx` (2, new),
`ui/__tests__/predictions.test.tsx` (+1). Screenshot:
`frontend/e2e/artifacts/supplied-1-topbar-slot-overridden.png`.
