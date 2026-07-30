# 2026-07-30 — backend — sleeper screen (FR-094)

**Dispatch:** build the evidence base for FR-094 ("can we predict late-round sleepers"). Sonnet/
default tier (not dispatched to Opus/high, flagged per operating rules rather than stopping).

## What shipped

- `analysis/sleeper_screen.py` — self-contained, reproducible, no network calls (~10s runtime).
- `docs/analysis/sleeper-screen-2026-07-30.md` — full writeup.
- `data/qa/sleeper-screen-2026-07-30.json` — raw output.
- `docs/handoffs/NEW-fr-094-sleeper-screen-methodology-review.md` — TO: strategist, unallocated
  per this dispatch's explicit instruction not to assign a thread ID this session.
- `docs/handoffs/NEW-fr-096-bust-candidate-screen-scope.md` — TO: backend, scoping the founder's
  mid-session extension (bust-candidate mirror of the sleeper screen), not built this session
  per the coordinator's explicit sequencing instruction.
- `docs/CURRENT-STATE.md` updated in place.
- `docs/ideas-inbox.md` — logged a worktree-branch-drift finding (see below).

## Headline result

**Step 1 (base rate, round-10+ FFC 12-team ADP universe, `actual_vbd>0` hit definition):**
24.1% [19.1%,30.0%] Wilson train (2018-2023), 24.5% [14.6%,38.1%] holdout (2024). Roughly 1 in 4
late-round players return startable value — a real, publishable finding independent of step 2.

**Step 2 (three pre-registered features):** none reach significance (raw p 0.209/0.643/0.266,
BH-adjusted higher). RISING_SHARE inverted in holdout (0/6 vs 24.5% base) — read as
disconfirmation. AGE_YOUNG is the one candidate worth carrying forward as a hypothesis
(direction held in holdout, independently evidenced on the full board in the sibling
ADP-vs-production analysis) but is underpowered at this cutoff (n=47 train / n=8 holdout
flagged).

**Verdict: no flag from this pass should ship.** Reported plainly per the founder's own
instruction that a negative result here is the most valuable output available.

## A structural environment finding, not this session's analysis

This worktree's branch (forked from `main` at `f07cf88`) predates the ADP-vs-production
analysis's merge — `analysis/`, `docs/analysis/`, and founder-request files past FR-071 do not
exist on this branch at all, even though `docs/CURRENT-STATE.md` in the shared/main checkout
describes that work as landed. Not the same issue as the documented `nfl.db`-does-not-survive-
worktrees gotcha, but the same *class* of problem, generalized to arbitrary committed work.
Rebuilt `data/nfl.db` from scratch this session (it was the standard 0-byte stub) and wrote
`analysis/sleeper_screen.py` self-contained rather than importing the sibling script, to avoid
depending on code this branch cannot see. Logged to `docs/ideas-inbox.md` for whoever owns
branch/worktree lifecycle.

## Not done this session (explicitly, not silently)

- FR-096 bust-candidate screen — scoped in a NEW- handoff, not built, per the coordinator's own
  sequencing instruction.
- Depth-chart position change / vacated targets feature — named by FR-094, not built (logged to
  `docs/ideas-inbox.md` in the earlier ADP-vs-production session's spirit; time-boxed here too).
- Route participation — confirmed BLOCKED, no data exists anywhere in this project's ingested
  tables.

## Tests / verification

No `src/` or `tests/` code touched this session (analysis-only, per the dispatch's own scope —
`src/`, `tests/`, export contract, ADR log were not in play here beyond the DB rebuild, which
used existing ingestion scripts unmodified). Ran the full pytest suite for a sanity check after
the DB rebuild; see commit message / final report for count.
