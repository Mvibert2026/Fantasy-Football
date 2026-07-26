# Settings editor — session handoff
**Date:** 26 July 2026 · **Screen:** League settings editor · **Status:** specified, referenced, unbuilt

---

## What's in this export

| Path | What it is |
|---|---|
| `SETTINGS-EDITOR-SPEC.md` | The spec. 11k, structured, meant to be read end to end. |
| `spec/settings-tokens.json` | **Additive** design tokens — two new (`--fail`, `--hatch`) plus the fresh/stale/null treatment matrix. Everything not listed is unchanged from the Draft handoff. |
| `spec/settings-screen.json` | Machine-readable: geometry, state machine, stage list, the four new endpoints, contract requirements, 14 assertable checks, and the founder decisions. |
| `reference/01-at-rest.dc.html` … `06-recompute-failure.dc.html` | **One working reference per state.** Each opens directly in that state — no clicking to get there. `support.js` must stay beside them. |
| `reference/*.png` | 2× render of each state, matching its HTML file. |
| `HANDOFF-NOTES.md` | This file. |

Open any reference HTML directly in a browser. No build step, no server. Each file keeps the state
switcher in its header so an engineer can step between states in one place, but the filename and the
header label tell you which state that file *is*.

---

## The one decision that shaped the screen

**Shadow recompute with an atomic, user-triggered swap.**

The 60-second scoring recompute runs in the background. The app stays fully usable. Nothing on screen
changes. The new values land only when the user presses **Apply**.

The reframe that makes it work: **the pre-edit numbers are not stale, they are correct.** The change
has not been applied, so the old scoring is still in force, and every number computed under it is
exactly right. What is running in the background is a *proposal*.

Three consequences worth stating to whoever builds it:

1. "Never show a part-applied recompute" is satisfied **by construction**, not by vigilance. There is
   no moment when some numbers are new and others old, because the swap is a single state transition.
2. **Failure is trivially safe.** Nothing was applied, so there is nothing to unwind and no recovery
   flow to design. The failure copy can honestly say "you are in a known-good state".
3. **Nobody gets ambushed.** Auto-applying at second 60 would rearrange the board under someone
   mid-scan. Requiring Apply means the change lands when the user is ready for it.

I rejected the two obvious alternatives, with reasons, in §1 of the spec: a modal freeze reads as a
hang at that duration and removes the exact thing the user came for; marking everything stale hatches
out the whole app, because a scoring change invalidates nearly every number — a slower freeze that
also teaches users to ignore the stale treatment we need them to respect.

---

## Decisions I flagged for the founder rather than making myself

Four. All four are recorded in `spec/settings-screen.json#founderDecisions` and §8 of the spec.

**1. Are scoring edits blocked during a live draft?**
The reference blocks tier-2 edits while a draft is live. Changing scoring mid-draft rebases every
recommendation the user has already acted on, which is a trust problem rather than a layout problem.
*My recommendation: block, and state the reason on screen.* But this trades flexibility for trust and
that is your call, not mine.

**2. If the user closes the tab mid-job, does the result auto-apply on next open?**
*My recommendation: wait.* Ambush is worse than staleness — a user who returns to a rearranged board
has lost their bearings and does not know why. Needs your call because it has a real cost: someone
who starts a recompute and leaves finds it still unapplied.

**3. If the user edits again mid-job, do we cancel and restart automatically, or ask?**
*My recommendation: restart automatically and say so.* A held result nobody wants is clutter, and the
server already needs a `superseded` response for this case. Asking adds a dialog to a flow that is
already 60 seconds long.

**4. Who is allowed to edit — commissioner only, or anyone with the league open?**
**No recommendation.** This is a permissions question I do not have the context to answer, and it
changes the design: if more than one person can edit, the pending-change banner needs an actor name
("Dave queued a scoring change"), and the whole flow needs a concurrency story I have not designed.

---

## What is unresolved and needs engineering input

- **`recompute.stage` granularity.** The reference shows five named stages. If the real job cannot
  report stage boundaries, the design degrades to a bare percentage, which at 60 seconds is
  noticeably worse. Confirm the backend can emit them before committing to this progress design.
- **Job ownership.** The spec requires the job to belong to the *league*, not the session, so other
  tabs and devices see the same state. That is a real infrastructure requirement, not a UI detail.
- **Held-result lifetime.** How long does the server hold a computed-but-unapplied result before
  discarding it? Not specified — the UI can handle any answer, but it needs one.

---

## Prototype data caveat

The board preview at the bottom of the screen shows five players with sample values, and the
timestamps are illustrative. The layouts, the state machine, the copy and the fresh/stale/null
treatments are final; the wiring is the work.
