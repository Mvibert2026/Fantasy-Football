---
ID: 018
FROM: pm
TO: data-ops
STATUS: RESOLVED
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

---

### data-ops · 2026-07-26

**Backfill: done.** `src/ingest_rankings.py` already had a seasons loop (default
`range(2021, 2027)`) from an earlier session, so the multi-season path was mostly there; I ran it
fresh against the live source and confirmed real rows land per season:

| Season | Rows | as_of_date |
|---|---|---|
| 2021 | 519 | 2021-08-27 |
| 2022 | 504 | 2022-08-26 |
| 2023 | 485 | 2023-08-25 |
| 2024 | 558 | 2024-08-30 |
| 2025 | 474 | 2025-08-29 (already ingested pre-session) |

**`scoring=HALF`: investigated, NOT switched — premise correction, not a refusal.** Two live
checks this session:
1. The DynastyProcess mirror (`load_ff_rankings(type="all")`, what this file currently pulls
   from) has **no half-PPR variant of the overall board at all** — its `page_type` values are
   `redraft-overall` (no PPR distinction) and separate full-PPR-only position pages
   (`ppr-rb.php` etc). There is nothing to switch *to* within this source.
2. FantasyPros' live API (`api.fantasypros.com`, `.env` has `FANTASYPROS_API_KEY`) does support
   `type=ST&scoring=HALF`, and I re-confirmed live against it — but its free tier caps every
   response at **10 players regardless of position filter or pagination** (RB call: `count=209`
   in the body, 10 rows actually returned). Four position-filtered calls would yield ~40
   players/season, versus ~500 from the current mirror. That's not a usable substitute for
   backtest coverage — RB30/WR40 replacement-level cutoffs alone exceed one position's cap.

Switching sources as literally specified would trade a scoring-format fix for a 90%+ coverage
loss. I did not make that trade. The mismatch is real and documented in the module docstring
(`src/ingest_rankings.py`); it needs either the paid FantasyPros tier (already flagged in
`docs/CURRENT-STATE.md` open item 4) or a different half-PPR-native source, not this file.
Flagging for `pm`/`backend` to decide on the paid-tier question rather than resolving it
unilaterally.

**Rows ingested (this session, real network pull):** 2021: 519, 2022: 504, 2023: 485,
2024: 558, 2025: 474 (re-confirmed) — 2,540 total across 5 seasons.
**Rows quarantined:** 0 (no name-resolution quarantine needed here; rows with no `gsis_id` are
dropped upstream in `fetch_preseason_rankings`, same as before this session).
**Tests:** `tests/test_ingest_rankings.py`, 7 new, covering `resolve_snapshot_date`,
`ensure_table`/`upsert_dataframe`, and the multi-season `ingest()` loop (including a
skip-one-season-without-crashing case).
**Commit:** see session commit in `docs/status.md`.

STATUS: RESOLVED (backfill delivered; scoring=HALF is a flagged decision for pm/backend, not a
data-ops build blocker).
