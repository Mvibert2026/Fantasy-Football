# 2026-07-29 — data-ops — FFC historical ADP backfill (thread 055)

**Closed thread 055.** Backfilled Fantasy Football Calculator ADP history into `ffc_adp_snapshots`
using the researcher's 2026-07-29 date-gate table (`docs/research/historical-adp-availability-2026-07-29.md`)
as the plan of record — no re-litigation of that document's per-season PASS/FAIL calls.

**New script:** `tools/backfill_ffc_adp_history.py`, one-time (not scheduled), cache-first
(`data/raw/ffc/<format>-12team-<year>.html`, gitignored per repo convention), ≥1s between
requests. Fetched 19 season-formats, all succeeded.

**Result:** 2,467 rows stored, 333 quarantined (299 team-defense `no_name_match` — a known,
documented ceiling; 34 `ambiguous_name_match`), 0 rows dropped for lacking a date. New
`adp_source` values `ffc_half_ppr_12team` (2018-2024, 7 seasons, the ranker's stated priority) and
`ffc_non_ppr_12team` (2013-2024 minus five excluded seasons, 12 seasons) — kept fully separate
from the daily 10-team capture and from `mfl_proxy`, no blending. `as_of_date` is the parsed
window-END date from FFC's own "Data from N drafts between DATE1 and DATE2" sentence (the real
historical draft cutoff), not the day the script ran; `sample_window` is kept verbatim per the
ranker's explicit ask on the thread.

**Two findings beyond the researcher's plan:**
1. 2010 non-PPR passes the date gate (window ends before kickoff) but the archived page itself is
   content-corrupted — 25 rows, DEF/QB/PK-heavy, missing every real 2010 RB1. Excluded despite
   passing the gate. This closes the researcher's open `[GAP]` about whether an earlier "2010 dump
   with no RBs" observation was a WebFetch markdown-conversion artifact: reproduced today with a
   direct HTTP GET, so it is FFC's own archive, not a fetch-tooling defect.
2. Pre-2018 non-PPR boards (2013-2017) are real but much thinner (28-94 rows stored vs. 126-185
   for 2018+) — kept and reported as thin, not dropped.

**Look-ahead gate verified independently**, not just trusted from the research doc's
`[SECONDARY]` search-derived kickoff dates: pulled `nflreadpy.load_schedules()` live for every
candidate season and took `min(gameday)` of REG games. Every value matched the research doc's
table exactly.

**Excluded (never fetched):** non-PPR 2007-2009 (retrospective aggregate, window ends
2010-06-20), 2011 (window ends after kickoff), 2012 (marginal, same-day, excluded
conservatively); half-PPR 2015-2017 (no archive, empty shell); both formats for 2025 (no archive
exists at all — consistent with the sealed-holdout status).

**Tests:** `tests/test_backfill_ffc_adp_history.py` (10 new tests) + existing
`tests/test_ingest_ffc_adp.py` (18) + `tests/test_ingest_mfl_adp.py` (16) — 44 passed. Did not run
the full suite to completion in this container (times out past 120-300s against the 854MB copied
`nfl.db`; this is the documented worktree-DB condition, not a regression from this change — the
targeted suites covering every file this session touched all pass).

**Files:** `tools/backfill_ffc_adp_history.py`, `tests/test_backfill_ffc_adp_history.py`,
`docs/research/ffc-adp-history-backfill-2026-07-29.md`,
`data/qa/ffc-adp-history-quarantine-2026-07-29.csv`, 19 new CSVs under
`data/adp-snapshots-ffc/2026-07-29_*_12team_period*.csv` (the committed canonical archive).
Thread 055 replied and set `STATUS: RESOLVED` (only the `TO:` role may do this; `data-ops` is the
`TO:`).

**Today's daily 10-team ADP snapshot already exists** (`data/adp-snapshots/2026-07-29.csv`,
`data/adp-snapshots-ffc/2026-07-29_{non_ppr,half_ppr,ppr}.csv` — all present before this session
started, from CI), so no action needed there this session.

**Not done, deferred per CLAUDE.md's standing priorities and not part of this thread's scope:**
mock-draft per-pick schema confirmation before any bulk mock logging (still 1 of the needed ~30),
and the late-August board re-pull.
