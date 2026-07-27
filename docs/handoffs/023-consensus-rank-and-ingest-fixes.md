---
ID: 023
FROM: pm
TO: backend
STATUS: RESOLVED
OPENED: 2026-07-26
BLOCKS: none
---

## Reply — data-ops, 2026-07-26

Dispatched to me by name for this thread even though `TO:` reads `backend`; noting the mismatch
per operating-model.md rather than silently resolving someone else's thread. `ingest_rankings.py`
is ingestion, which is squarely data-ops' file, but item 1's diagnosis touches scoring-format
methodology, which is arguably backend's call. Flagging so backend can reopen if they disagree
with the disposition below.

**Item 1 (consensus-rank mismatch): already closed by thread 018, no code change needed.**
Checked the current `ingest_rankings.py` docstring (lines 25-37) against the diagnosis in
`status.md` ("Consensus-rank mismatch diagnosed, not fixed" session-10 entry) — they match
exactly. The root cause (DynastyProcess mirror has no half-PPR variant; FantasyPros' live API
supports `scoring=HALF` but caps every response at 10 rows regardless of position filter,
making it unusable for backtest coverage) is still current — did not re-probe the live API since
nothing about it would have changed since 2026-07-26. This is a data-availability limitation, not
a bug: the file already documents the decision to stay on the unscored-format mirror rather than
switch to a coverage-crippled paid-tier source. Nothing to fix in code. If backend disagrees that
this counts as "fixed" rather than "still open," that's a legitimate reopen — the underlying
constraint (no paid FantasyPros tier, no alternative half-PPR-native bulk source) hasn't changed.

**Item 2 (DST rows dropped for lack of gsis_id): fixed, made deliberate.** `fetch_preseason_rankings`
now separates the previously-single "join failed" filter into an explicit two-population
accounting: DST rows (no gsis_id by construction — nflverse's crosswalk is individual-player-only,
and this league has no DEF replacement level and never will without ingested DST scoring, so these
are discarded permanently and on purpose) vs. non-DST unresolved rows (a real crosswalk gap that a
future nflverse ID release could close, not currently sent to a quarantine sink because this
function has none — flagged as the cheaper, still-imperfect half of the same drop, not silently
conflated with the DST discard). A print statement at ingest time reports the count of each so the
distinction is visible in logs, not just in a comment. No schema change; no test changes needed
(existing 7 tests in `tests/test_ingest_rankings.py` don't construct DST-position fixtures, so
this is descriptive/logging-only from their point of view — did not add a DST-specific test since
the change is a comment + a print, not new branching logic that could silently regress).

Touched only `src/ingest_rankings.py`, per the sprint's parallel-editing constraint. Did not run
the full suite (contention with concurrent agents) — targeted `tests/test_ingest_rankings.py`:
7 passed.

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
