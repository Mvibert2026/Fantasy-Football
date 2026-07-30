---
ID: FR-064
STATUS: NEW
PRIORITY: MEDIUM
ROUTED-TO: design
SOURCE: chat 2026-07-30, PM session
RAISED: 2026-07-30
---

## Request
Look and feel reads dated; draft rankings pane too narrow, middle pane should scroll

Founder's own words, on the live Draft screen:

> "there are parts that feel old, or not well aligned, that screenshot I sent, the lines and text look
> basically like an old powerpoint slide - I think there's some modernization to be done look and feel
> and spacing wise, the rankings in the left on draft may need to be a wider pane to show the data
> better, the middle pane can scroll if it gets thinner"

## Why this is worth acting on rather than filing

**It is the first aesthetic judgement he has made about our own product.** Everything before this was
about competitors — Yahoo *"looks like a childs toy"*, FantasyPros *"still looks pretty good"*. This
is the same eye turned on us, and it lands on the screen he will actually use on 7 September.

*"Like an old PowerPoint slide"* is specific, not vague: it points at **rules, borders and spacing**
rather than colour or typography. Hairline boxes around everything, uniform padding regardless of
hierarchy, and content that fills its container rather than being composed within it.

## Three separate things, and they should not be collapsed

1. **Spacing, alignment and line weight.** The "modernization" ask. Density is a stated principle
   here and must survive — the answer is not more whitespace everywhere, it is *deliberate* spacing
   that encodes hierarchy instead of applying one value uniformly.
2. **The draft rankings pane is too narrow for its data.** A concrete layout fix, not a taste
   question.
3. **The middle pane should scroll when it narrows**, rather than the layout breaking or the content
   compressing. He has given the trade-off himself: **width goes to the rankings, and the middle pane
   absorbs it by scrolling.** That is a decision, not a question.

## The tension to design against, and it is real

Design's own round-one finding was that **the periodic-table grid needs full width to be a pattern**
— six cells across is a list with extra steps. Widening the left rankings pane takes width from
exactly the space that argument depends on. **Both cannot have it.** Resolving that is design's call
and it should be made explicitly rather than by whichever spec is built first.

## Context that has just changed

The Draft screen was rebuilt this session (four tabs, next-decision footer, supplied-value markers).
**This feedback is on the new version, not the old one** — it was given after that shipped. Fresh
captures are in `frontend/e2e/artifacts/middle-pane-*.png` and `supplied-*.png`.

Also open and in the same area: **FR-063** (the scarcity warning measures the wrong horizon) and the
**dark-mode dropdown defect** — the SLOT selector's open list renders near-white on near-white, only
the highlighted row legible.

**Design is currently paused** until the frontend queue clears. This is queued for its next round,
not a reason to restart it.
