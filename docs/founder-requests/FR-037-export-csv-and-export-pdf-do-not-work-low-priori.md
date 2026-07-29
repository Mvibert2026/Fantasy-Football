---
ID: FR-037
STATUS: NEW
PRIORITY: LOW
SOURCE: chat 2026-07-29, PM session
RAISED: 2026-07-29
---

## Request
Export CSV and Export PDF do not work

Founder's own words:

> "Export csv and export off don't work. Low on the list of priorities. Just needs to be logged."

("export off" read as "Export PDF" — the two controls sit side by side on the board.)

## Why it matters

Not because the feature is needed — the founder explicitly deprioritised it. It matters because it
is the **sixth present-but-inert control** found in the app, and the founder has now personally
tripped over two of them (this and Refresh data, FR-030). A control that renders like a control and
does nothing is the app misrepresenting itself, and the founder discovering them one at a time by
clicking is a bad way to find out.

Full inventory of inert controls, measured 2026-07-29:

| Control | Location |
|---|---|
| Export CSV | `frontend/ui/views/Board.tsx:225` |
| Export PDF | `frontend/ui/views/Board.tsx:237` |
| League settings | `frontend/ui/components/shell/TopBar.tsx:195` |
| Compare | `frontend/ui/components/PlayerDetail.tsx:509` |
| Ask | `frontend/ui/components/PlayerDetail.tsx:512` |
| Ask the assistant (per glossary term) | `frontend/ui/views/Glossary.tsx:81` |

All six carry `aria-disabled="true"` and all six were deliberate — `Board.tsx:22-24` documents the
choice at the time: *"Export CSV / Export PDF are visually present but inert. Nothing in this app
generates either file yet."* They were ported from the prototype's shell to preserve its layout.
That was a defensible call when the app had no users; it is not one now that the founder is using
it.

## Initial read

Not the founder's own words — PM's read.

**Two separate pieces of work, and only the first is worth doing soon.**

1. **The pattern.** `design` owns the question of what a control that cannot work should look like —
   it was already asked in `docs/design-briefing-2026-07-29.md` §1 for the hosted-vs-local case, and
   this is the same question with a different cause (not-built rather than not-possible). One answer
   should cover all six. Cheap, and it stops the founder finding number seven.
2. **Actually building CSV/PDF export.** Deferred at the founder's explicit instruction. CSV is
   genuinely small — the board is already a table in memory. PDF is not, and needs a real reason
   before anyone starts.

Sequencing: do not build either export before the 7 September draft. Do settle the inert-control
treatment, because it is a one-time decision that six places are waiting on.
