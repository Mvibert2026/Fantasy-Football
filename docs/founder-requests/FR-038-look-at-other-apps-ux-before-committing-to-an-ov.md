---
ID: FR-038
STATUS: NEW
SOURCE: chat session 2026-07-29, relayed via researcher dispatch
RAISED: 2026-07-29
---

## Request
Look at what other apps do before committing to a frontend overhaul

> "features of other apps out there to see if we want to include them, or looking at good UI/UX
> features"

Founder's own words, 2026-07-29, ahead of a major frontend overhaul he is considering but has **not**
committed to.

**No ID typed by hand.** This file was staged by a researcher session with no shell tool; the ID is
allocated by `python tools/founder_requests.py sync`, which assigns `FR-NNN` to any `NEW-*.md` in
this directory. Hand-computed numbering has already collided four times in this project (threads
043/049/053, ADR-048).

## Why it matters

The overhaul is the largest single frontend decision open, and `docs/operating-model.md` records that
**a dispatch which misreads scope is the most expensive error available to the PM** — the ~374k-token
frontend run where about a third went on phone layouts the founder then pulled. Asking what good
looks like *before* committing is the correct sequence and should be recorded as a request in its own
right, not folded into FR-034.

## Answer, already delivered

`docs/research/competitive-ux-2026-07-29.md` (researcher, 2026-07-29). Headline: **the evidence
weakens the case for a visual overhaul rather than strengthening it**, and supports three scoped
structural changes instead — uncertainty surfaced on the board row, draft slot selectable (with a
randomise option) in the prep setup block, and league-scoped vs. account-scoped state labelled on
screen. ESPN's 2025 redesign is the category's cautionary case and the complaints are specifically
about lost density.

**This request is not closed by that document.** What remains is a founder decision: overhaul,
scoped changes, or neither. If he wants the overhaul anyway, that is a legitimate preference — but
`CLAUDE.md` §2 still says Phase 1 is the backtest harness and ranking algorithm and *"Not the draft
tool"*, so committing to one is a spec amendment (§8 escalation), not a sprint.

## Related
- **FR-034** — draft position must be selectable in prep; multi-league is the product. FR-034 itself
  notes it was *"raised alongside a possible frontend overhaul the founder has deferred, and worth
  sequencing with that rather than bolting a control onto a screen that may be rebuilt."*
- **FR-025** — phone support, deferred. Explicitly out of scope of any overhaul per the research.
- Unallocated handoff body:
  `docs/research/HANDOFF-BODY-unallocated-competitive-ux-2026-07-29.md`.
