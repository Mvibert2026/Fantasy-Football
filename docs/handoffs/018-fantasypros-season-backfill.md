---
ID: 018
FROM: pm
TO: data-ops
STATUS: OPEN
OPENED: 2026-07-26
BLOCKS: 019 (bootstrap CIs)
---

## Ask
Backfill FantasyPros preseason rankings for **2021, 2022, 2023, 2024**. Only 2025 is currently
ingested.

`deferred.md` records that `load_ff_rankings(type="all")` already returns history back to 2020, so
this is a loop over seasons in `src/ingest_rankings.py` — no new source, no new auth.

While you are in that file: it currently pulls from a DynastyProcess mirror that has no PPR variant.
Switch to the live API with `scoring=HALF` to match this league's format. That fix is also already
logged as outstanding.

## Why
The doc calls this "cheap" and it gates two things: any backtest of a season other than 2025, and the
bootstrap confidence intervals in thread 019. It is the highest ratio of unblocking to effort in the
whole backlog.

## Constraints
Judge-only discipline does not apply here — this is consensus ranking data, not mock draft data. But
2025 remains a locked holdout for methodology work; ingesting it is fine, testing against it is not.

## Done looks like
Four seasons ingested with row counts reported per season, `scoring=HALF` confirmed, tests covering
the multi-season path. Commit hash and test count.
