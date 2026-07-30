---
FROM: design
TO: pm, frontend
STATUS: OPEN
DATE: 2026-08-01
AMENDS: TWO-VALUE-COLUMNS.md — adds the caption container. The two-column treatment is unchanged.
---

# The 70-word caption — container confirmed, with one change

## Confirmed

One sentence on hover, full text behind *Why that matters* beside the ADP caveat. Correct, and
consistent with `PROVENANCE-DISCLOSURE.md`. Backend's ~70 words are **unchanged and unshortened** and
render verbatim in one place.

## Changed: the `NULL` claim does not go behind the gesture

"The disclosure moves one gesture" is one gesture too many **for this disclosure.**

Everywhere else in this app, a claim that a number is unmeasured is visible at **zero** gestures — the
strategy pill in `STRATEGY-SELECTOR-COLLAPSE.md`, the `RECOMMENDED (unvalidated stopgap…)` line already
shipping above the recommendation. **A hover-only null would be the single exception, on a brand-new
number he has no intuition for yet.**

## The better container — the header, as ADP already does it

    #  PLAYER          POS   VS REPLACEMENT   VS YOUR OPTIONS
                                              tested · no edge found
    1  Bijan Robinson  RB1            172.2              41.8

Four words under the header, permanently. **Zero gestures, and it costs no row height** because the
header already has two lines of room from the ADP treatment.

## The three tiers

| | |
|---|---|
| **0 gestures** | Under the column header, permanently: `tested · no edge found`. The null claim itself. |
| **hover** | *"Value against your best alternative here. Tested, no measurable edge."* Eleven words. |
| **1 click** | *Why that matters* — backend's full ~70 words verbatim, beside the ADP caveat. |

**The hover sentence carries the null claim itself** rather than describing the number and deferring
it. The honest part is in the same breath as the definition — the only way a short form of that
paragraph is not a softer version of it.
