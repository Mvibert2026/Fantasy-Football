---
ID: 063
FROM: pm
TO: frontend
STATUS: OPEN
OPENED: 2026-07-27
REOPENS: 051 — treat as a regression, not a new request
---

## Founder report

> "You haven't fully fixed the predictive name generator. It should only open when I click into the
> text box, no other triggers. It seems to trigger every pick."

**This is the second attempt at this behaviour.** Thread 051 asked for the suggester to stop opening
unasked. It still opens on every pick. Do not add another guard on top of the last one — **find why it
reopens** and fix the cause. A third partial fix is worse than the current state, because it makes the
component harder to reason about while leaving the founder's problem in place.

## The rule

**The panel opens on explicit user intent to enter a pick. Nothing else opens it, ever.**

| Event | Opens? |
|---|---|
| Click into the pick-entry field | **Yes** |
| Typing into the field | **Yes** |
| A pick is committed (yours or an opponent's) | **No** |
| The board updates or recomputes | **No** |
| Component mount / page load / refresh | **No** |
| League switch | **No** |
| Returning to the Draft tab from another tab | **No** |
| Undo | **No** |
| Programmatic focus from any source | **No** |

**Closes on:** click outside, `Escape`, blur, and on commit.

## The likely cause, and the distinction that matters

The classic shape of this bug is an effect keyed on draft state — something along the lines of a
dependency on the current pick number — that calls focus or open on every change. Committing a pick
changes that state, the component re-renders, and the panel reopens. It looks like "opens every pick"
because that is exactly what it is.

**The distinction to build around: programmatic focus is not user focus.** A field that is focused by
code must not behave as though the founder clicked it. If the component cannot currently tell the two
apart, that is the actual defect — give it an explicit user-intent signal rather than inferring intent
from focus state.

Note that auto-focusing the field after a commit may well be *desirable* for fast entry — the `1-5 to
commit` affordance implies speed matters. **Focus and open must therefore be decoupled**: the field
may take focus, the panel must stay shut until the founder does something.

## Report the root cause

In the reply, state plainly what was actually causing it and why the 051 fix did not catch it. That
sentence is worth more than the diff — the same pattern is likely present elsewhere, and this is the
only way we find out.

## Done looks like

- One fix at the cause, not a guard stacked on a guard.
- **A test per row of the table above.** Nine rows, nine assertions. This is what stops a third round:
  enumerated triggers, each one pinned. A single "does not open unexpectedly" test is what allowed
  this to regress.
- The reply names the root cause and whether the pattern appears in other components.

**File boundary:** `frontend/` only, and the pick-entry component specifically. Coordinate with
threads 051 and 058 — both touch this screen, and 058 § C is on adjacent chrome.
