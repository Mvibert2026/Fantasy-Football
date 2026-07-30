---
ID: FR-111
STATUS: NEW
SOURCE: chat 2026-07-30, PM session (screenshot feedback)
RAISED: 2026-07-30
---

## Request
Draft headers still do not line up with the stats below them

Founder's own words:

> "He headers in draft still don't line up well to the stats below them"

## Why it matters / PM's read

**This shipped as fixed yesterday (FR-067) and is still wrong.** The fix introduced a shared
`DRAFT_LIST_COLS` definition and was verified at two viewport widths with screenshots.

Treat this as a **verification failure, not a new bug**. Whatever was checked did not match what the
founder is looking at. Before proposing a fix, establish the gap: which columns, which width, which
mode. His screenshot is the reference — `RANK PLAYER / POS / TM / ADP / delta / VBD / AVAIL` against
the rows beneath.

Do not ship a third attempt without reproducing his exact view first.
