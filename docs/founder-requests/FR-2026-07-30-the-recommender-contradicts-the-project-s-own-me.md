---
ID: FR-2026-07-30-recommender-contradicts-own-findings
STATUS: NEW
SOURCE: PM session 2026-07-30, founder chat
RAISED: 2026-07-30
PRIORITY: HIGHEST — names the mandate for Fable
NEEDS: fable, then ranker
---

## Request

Founder's own words, after being shown the inverted pick logic:

> "just odd recommendation model is suggestiong things that don't agree with other findings, we need
> consistency, again, this is what fable will need to tear into"

## This is a bigger claim than the bug that prompted it, and it is correct

The inverted availability logic
(`FR-2026-07-30-recommendation-logic-is-inverted-it-prefers-the.md`) is one defect. The founder is
naming the **class**: the recommender makes suggestions that contradict findings this project has
already measured, and nothing detects that.

The screenshot proves it in the product's own voice. The assistant told him, unprompted, that
early-QB was the most costly strategy tested — negative in all 12 scenarios, worst case −115.4
points — and that the live recommendation cut against it. **Two surfaces of the same product,
disagreeing on screen, and only one of them was right.**

## The structural cause, stated as a hypothesis for Fable to attack

**This project's findings live in markdown. The model lives in code. Nothing connects them.**

Measured results are written into `docs/`, ADRs, and thread replies — and then the recommender is
free to contradict every one of them, because no test asserts a finding is respected. Examples
already on file:

| Finding, measured | Encoded anywhere in the model? |
|---|---|
| Early-QB most costly strategy tested, negative in all 12 scenarios | Unknown — the recommender just did it |
| Variance preference from yardage bonuses is dead, four independent tests (CLAUDE.md §7) | Unknown |
| Archetype fall-through is common, not an edge case | Unknown |
| H1 NULL: ADP is not more accurate than consensus on the only evidence we have | Just measured; nothing consumes it |

This is exactly the failure mode CLAUDE.md §8 gives Fable standing authority over — *"unearned
confidence"* — but at the level of the system rather than a single claim.

## What the founder is asking for

**Consistency as a property, not a bug fix.** A recommender that cannot contradict a measured
finding without something failing. That is a testable design goal and it is likely a bigger piece of
work than any single defect on the list.

## Sequencing

Written into the Fable M mandate as a fourth section. **Fable is dispatched at end of week, when
the founder chooses to spend that budget** — it is accounted separately but draws on the main pool
and counts against the weekly total (his correction, 2026-07-30; PM had this wrong twice).
