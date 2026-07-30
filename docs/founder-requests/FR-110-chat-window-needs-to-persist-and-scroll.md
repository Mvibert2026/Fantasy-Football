---
ID: FR-110
STATUS: NEW
SOURCE: chat 2026-07-30, PM session (screenshot feedback)
RAISED: 2026-07-30
---

## Request
Chat window needs to persist and scroll

Founder's own words:

> "Chat behavior is improving, but the window is crap - needs to have a constant window to be able to continue the conversation, it also doesn't allow for scrolling."

## Why it matters / PM's read

Behaviour improved with FR-076/077 (page context, standing input, history). The **container** did
not. Two concrete defects: the window does not persist as a constant surface for continuing a
conversation, and its content does not scroll.

Known and previously logged as out of scope: `AssistantDock.tsx`'s panel chrome is fixed at
430px/72vh and the shipping screenshots already showed text overflow at that size. That was deferred
as "the founder's ask was about the conversation inside it, not the dock's own sizing." **He has now
asked about the dock's own sizing.** No longer deferred.
