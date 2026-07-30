---
ID: FR-127
STATUS: IN-BUILD
SOURCE: PM session 2026-07-30, founder chat
RAISED: 2026-07-30
---

## Request

Founder's own words, after asking what `CI` meant and having to get the answer from a human:

> "the chat bot should have been able to answer the question like you did about CI - even hovering
> over CI to tell me that would have been ok."

Preceded by, on the same number:

> "What is 'CI' stand for - It wasn't that the info was bad, I just wanted to understand it"

## Why it matters

**The glossary already contains the answer, well written, and nothing in the product can reach it.**

`data/export/glossary.json` carries 14 terms. One of them is:

> **confidence interval** — "A range the true value probably sits in — wide means we are guessing."

The assistant *does* retrieve glossary documents — `retrieval.ts:342`, one doc per term. It failed for
a precise and unglamorous reason: **the app displays an abbreviation the glossary does not index.**
The column header reads `CI`. The glossary key is `confidence interval`. Nothing joins them, so a
lexical match on "CI" returns nothing, and the lane correctly refuses to answer rather than inventing
one. The refusal was right. The gap was upstream.

Measured against the glossary's key set, of the abbreviations the UI actually renders:

| Shown | Indexed in the glossary |
|---|---|
| `ADP`, `VBD`, `TIER` | yes |
| `CI`, `PROJ`, `CONS`, `MFL`, `AVAIL`, `POS`, `TM`, `BYE` | **no** |

So eight of eleven displayed labels are unexplainable, by the assistant or by hover, and the founder
hit the first one he asked about.

**This is the second time in one day that a correct value was rendered unreadable by its label** — the
other being the `PROJ (CI)` header over a VBD interval. Different bug, same class: the product knows
the answer and does not surface it where the question is asked.

## Initial read

**Two fixes, both cheap, both dispatched into the agent already working in those files** (the CI
labelling fix owns `Board.tsx`, `PlayerDetail.tsx`, `DraftRoom`'s cells and `assistant/retrieval.ts` —
exactly the right surface).

**1 · An alias map, displayed label → glossary key**, fed into `glossaryDocs()` so a retrieval hit on
`CI` returns the `confidence interval` document. In one place next to the glossary loader, not
scattered per call site: the next abbreviation added to a header should cost one line, not a hunt.

**2 · The short definition on the column header, on hover.** The founder said a hover would have been
enough. `docs/design/PROVENANCE-DISCLOSURE.md` already caps hover at one human sentence, ~12 words —
and the glossary's short definitions are already written to that length, so they go in verbatim rather
than being recomposed. Driven off the same alias map, so a new column inherits the behaviour instead
of needing to remember it.

**A definition is not provenance and is not gated by trace mode.** Trace mode hides field paths. What
a column *means* is visible in both states — gating it would reintroduce this bug behind a keystroke.

**The instruction that matters most: do not weaken the assistant's refusal to fix this.** Its rules —
every claim traceable to exactly one retrieved item, never a number that is not in the context
verbatim — are why it is trustworthy. The failure was that a real, retrievable fact was unreachable,
not that the lane was too strict. A "helpful" relaxation here would trade one visible gap for an
invisible fabrication.

**Reported back as a finding:** which displayed labels have no glossary entry at all. Where none
exists, an alias must not be invented to fill the table — that list is the input to writing the
missing entries, which is part of the standing glossary work the founder has now asked for three
times.
