---
ID: 064
FROM: pm
TO: backend
STATUS: OPEN
OPENED: 2026-07-27
BLOCKS: any honest statement about project status
---

## The problem

**`docs/CURRENT-STATE.md` is stale, and it is the one file in this repo that must never be.** Its own
header declares it the canonical answer to "where is the project right now" and forbids appending.
It currently says:

| Field | `CURRENT-STATE.md` says | Believed actual |
|---|---|---|
| Commit | `3ea391b` | far ahead |
| Backend tests | 399 | ~487 |
| Data contract | 1.7.0 | 1.9.0 |
| Frontend | `frontend-prep`, **"not in this repo"** | merged as `frontend/` |
| Frontend tests | "unrecorded" | ~126/127 |
| `NEED_ADJUSTMENT_SCALE` | 10.0, "needs a swept-scale comparison" | **deleted** per D-001 |
| Alpha detection | "closed until ~2028" | stated as ~2029 elsewhere — **one of these is wrong** |
| Mock Lab | "absent" | backend shipped, thread 025 |
| Opponents / Predictions | "absent from the shipped app" | worked this round, state unknown |
| Hard dates | draft deadline listed | **deadline removed by the founder** |

**Last verified: 2026-07-26.** Everything since has gone unrecorded.

## Why this matters more than it looks

The PM has been answering status questions from **agent round reports**, not from this file. That is
backwards, and it is how the project ended up with two different figures for when alpha detection
becomes possible (2028 here, 2029 in newer documents). **At least one of those is wrong and nobody
knows which** — that is precisely the failure this file was created to prevent, occurring inside the
file created to prevent it.

## Ask

**Verify every line against the working tree and rewrite in place.** Not a new section. Not an
appendix. The header forbids both.

1. **Measured, not reported.** Run the suites. Read the commit. Count the modules and export
   artifacts. Do not copy numbers from thread replies, including mine.
2. **Resolve the 2028 / 2029 discrepancy** and state which is correct with the reasoning. If the
   underlying claim has changed — season-level bootstrap floor versus consensus-history availability —
   say so, because they are different arguments and may have been conflated.
3. **Apply the decisions settled 2026-07-27** (see `docs/decisions-needed.md`): D-001
   `NEED_ADJUSTMENT_SCALE` deleted, D-004 `delta` retained flagged with its kill rule, D-003 ranks
   shown with a structural flag, D-006 / D-013 / D-020 closed, D-021 FFC unblocked, D-015 / D-016
   dual calibration reporting.
4. **Remove the hard-date section.** The founder removed the deadline; it should not still be shaping
   priorities from the canonical state file.
5. **Rewrite "Built and working" and "Not built" against the actual code**, not against what threads
   claim shipped. This is the section the founder is asking about when he asks what is live, and it is
   currently the least trustworthy part of the file.
6. **Update "Top open items"** — item 4 is the FantasyPros decision, which is settled and closed.

## Then make staleness detectable

The deeper failure is that this file could rot for a day without anything noticing.

- Add a `Last verified` assertion to the test suite or to `handoffs.py check`: **fail** if the
  recorded commit does not match `HEAD`, or if `Last verified` is older than a stated threshold.
- The recorded test counts should be checkable against a real run, not trusted.

A canonical state file that can silently disagree with the repository is worse than no canonical state
file, because people stop checking.

## Done looks like

`CURRENT-STATE.md` rewritten in place, every figure measured, the 2028/2029 question resolved with
reasoning, decisions applied, deadline section removed. Plus the staleness check, with a test.

Report anything you found that contradicts what the PM has been saying. **That list is the most
valuable output of this thread.**

**File boundary:** `docs/CURRENT-STATE.md`, plus the staleness check wherever it belongs. Do not touch
`docs/handoffs/` — thread 062 owns the mailbox and its tooling this round.
