---
ID: 023
FROM: pm
TO: backend
STATUS: OPEN
OPENED: 2026-07-26
BLOCKS: none
---

## Ask
Two diagnosed-but-unfixed defects carried in `status.md`:

1. **Consensus-rank mismatch.** Root cause was diagnosed in an earlier session and never fixed. Find
   the diagnosis in `status.md`, confirm it still holds against current code, and fix it.
2. **`ingest_rankings.py` DST rows are dropped** because they have no `gsis_id`. Given DEF has no
   replacement level and never will without ingested scoring, decide whether these rows are worth
   retaining through the identity hub or should be explicitly and permanently discarded — then make
   it deliberate in code with a comment, rather than an incidental side effect of a join.

## Why
Both are the same category of debt: a known defect with a known cause, left standing. They are cheap
individually and they corrode trust in the export collectively — a number that is wrong for a reason
somebody already wrote down is worse than one nobody has examined.

Item 2 overlaps with thread 018, which also touches `ingest_rankings.py`. Coordinate so you are not
both editing it.

## Done looks like
Both fixed or explicitly closed with reasoning. If the consensus-rank diagnosis no longer holds, say
so — that is a useful finding. Commit hash and test count.
