---
ID: 066
FROM: frontend
TO: backend
STATUS: OPEN
BLOCKS: 058 section B1 (design fidelity)
OPENED: 2026-07-27
---

## Ask

Thread 058 (draft board design gap) section B1 asked for tier-grouped headers on the Draft Room's
board list, matching the design reference. That's already correctly built when a single position tab
is selected (`board.json:tier_label`, real, per-position). Under the `ALL` tab, the design reference
appears (from its screenshot) to group *across* positions under one shared "TIER N" header — e.g. a
WR12, a QB2 and an RB10 all under "TIER 3."

I read the actual interactive prototype source, not just the screenshot, to check this before
building it (`docs/design-reference/prototype.dc.html`, `renderVals()` around line 3416-3430). It is
**not** reusing the per-position tier for this — it computes a separate `gtier` ("global tier") field:
walk the whole board sorted by a VBD-like `score`, cut a new tier whenever the score gap between
adjacent players exceeds 4.5 points (with a minimum bucket size of 2 and a maximum of 9), see
`board()` around line 2438-2452.

I confirmed directly against the real `data/export/board.json` that `tier`/`tier_label` are
per-position only — e.g. QB tier 1 stops at positional rank 2 (overall rank 13) while RB tier 1 runs
to positional rank 4 (overall rank 8). A QB1 and an RB4 sharing the label "T1" are not describing the
same value tier. Mixing them under one shared header the way the design's ALL tab does would be
actively misleading, and it's exactly the reason `DraftRoom.tsx` already restricts tier bands to a
single position tab (thread 029, pre-dating this thread) — that restriction is correct and I left it
in place rather than building a fake cross-position grouping.

**Ask:** would a `global_tier` (or similarly named) field on each `board.json` player row — computed
the same way the design's `gtier` is (or via whatever clustering approach the real ranking model
actually supports; the 4.5pt/2/9 constants are the *design mockup's* placeholder values, not
necessarily the right ones for the real VBD scale) — be worth adding? If so, I'll wire the ALL-tab
board list to group by it, matching the design exactly. If this isn't worth the modeling effort right
now, say so and I'll close this out as declined rather than leave it open indefinitely.

## Why

Without it, the Draft Room's `ALL` position tab shows a flat list (correct, but less than the design
intends) while a single-position tab already shows real tier bands. This is a legitimate, bounded gap
in design fidelity, not a build oversight — it needs a backend/statistical decision (what constitutes
a "tier" across positions of very different value scales) before frontend can build it honestly.

## Done looks like

A decision, either way:
- **Add it:** `board.json` gains a `global_tier` field (or equivalent), contract version bumped, this
  thread updated with the field name and semantics so frontend can wire it up in a follow-up.
- **Decline it:** a one-line reason (e.g. "not worth the modeling effort for a display-only grouping"),
  and this thread closed as `RESOLVED` with that reason on record.
