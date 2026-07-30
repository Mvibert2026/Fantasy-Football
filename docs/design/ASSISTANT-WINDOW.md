---
FROM: design
TO: pm, frontend
STATUS: OPEN
PRIORITY: 4 of 8
DATE: 2026-07-31
COVERS: founder ask "the window is crap… needs a constant window… doesn't allow for scrolling"
DEPENDS ON: PROVENANCE-DISCLOSURE.md
---

# The assistant window

The behaviour improved. The container did not.

## What the captures show beyond the size

Both reported faults are visible: the answer in `fr077-followup-conversation.png` begins
mid-sentence at *"likely to survive to your pick at 18"*, its opening clipped above the top edge with
no way to reach it.

**But two more things are in the same frame, and they are why the window feels smaller than it is.**
The model's context keys are printed **inline, mid-paragraph, as section dividers**:

> …That difference, not the point gap, is the reason for the order. `[page.next_pick_reference]`
> Reference point for the user's next pick, overall 3 of 87 left…

Six of them, plus a `model prose over context: page.draft_state, page.roster_needs, …` footer. That is
class 1 provenance from `PROVENANCE-DISCLOSURE.md`, in the worst possible position — *inside a
sentence*. **Removing it reclaims real height before the container is touched at all.**

## The container

| | |
|---|---|
| **Now** | 430px × 72vh, fixed. Content clips, no scroll, no scrollbar. |
| **Width** | **520px minimum**, may grow to 720. An answer citing three players needs a line long enough to hold a name and a number together. |
| **Height** | Fills to a bottom margin rather than a viewport fraction. 72vh of a short laptop window is not a readable panel. |
| **Scroll** | The transcript scrolls; header and input do not. New answers pin to the bottom. **The scrollbar is always visible**, so the panel never looks finished when it is cut. |
| **Persistence** | Collapses to its header, never unmounts. **The conversation survives a pick** — that is what "continuing" means. |

## Two things to keep

- **The three suggestion chips** in `fr077-dock-open-3-suggestions.png` are good and stay. They are
  the fastest input device in the panel.
- **"Answers come only from the exports… Nothing is ever answered from general football knowledge."**
  This is the standing scope note and it stays, in the empty state. It is the opposite of a
  "Coach can make mistakes" footer: it says what the thing *can* do, not that it might be wrong.

Per-answer, the scope note becomes one line — *Answered from what is on screen* — with a
`3 sources` disclosure that opens the list. In trace mode that expands to the `page.*` keys, which is
where they belonged all along.
