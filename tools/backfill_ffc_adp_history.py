#!/usr/bin/env python
"""One-time historical backfill of FFC ADP into ffc_adp_snapshots, thread 055.

WHY THIS EXISTS. `src/ingest_ffc_adp.py` captures TODAY's ADP daily, at
10-team (the primary league's own team count). Thread 055 asks for
*historical* seasons 2018-2024 (half-PPR priority) / 2010-2024 (non-PPR),
which FFC only archives at 12-team -- 10-team and 14-team URLs for a past
season silently 200 the 12-team page (verified,
`docs/research/historical-adp-availability-2026-07-29.md` SS4). This module
is a SEPARATE, one-time script rather than a change to the daily capture,
because it fetches a different (season, teams) axis that the daily job never
needs and must never run on a schedule (FFC's archived pages for a past
season do not change; re-fetching them daily would be pointless load against
a source we are already stretching a rate limit for).

LOOK-AHEAD GATE, PER SEASON -- computed, not assumed. FFC's archived ADP page
states its own sample window verbatim ("Data from N mock drafts between
DATE1 and DATE2"). A season is usable as a genuine PRE-DRAFT snapshot only if
DATE2 (the window's end) is strictly before that season's real Week 1
kickoff -- computed here from nflreadpy's `load_schedules()` (min REG-season
gameday), not the research doc's [SECONDARY] search-derived dates. Verified
2026-07-29 that the nflreadpy-derived kickoffs match the research doc's
figures exactly for every season checked. A season that fails the gate is
NOT fetched at all -- CLAUDE.md SS6.1 treats a look-ahead-contaminated row as
worse than a missing one, so there is no reason to spend a request on it.

CONTENT-VALIDITY CHECK, SEPARATE FROM THE DATE GATE. Manually verified
2026-07-29 that FFC's archived 2010 non-PPR/12-team page, despite PASSING the
date gate (window Sep 6-8 2010, kickoff Sep 9 2010), returns a garbled board
-- 25 rows, dominated by DEF/QB/PK, missing every real RB1 of that season
(no Adrian Peterson, no Chris Johnson, no Arian Foster). This is not a parser
bug (`parse_adp_table` extracts the rows correctly; the underlying HTML table
itself is degenerate) and not the WebFetch markdown-conversion artifact the
research doc guessed at (`[GAP]` in that doc, now closed: reproduced with a
direct HTTP GET, no WebFetch involved). It plausibly shares a root cause with
the 2007-2009 "window ends June 20 2010" anomaly already flagged as a
migration artifact. 2010 is therefore EXCLUDED here despite passing the date
gate -- recorded as "content invalid", a third disposition alongside
"usable" and "gate fail", per the instruction to report rather than
substitute.

Every other candidate season-format was checked for a sane top-12 (real
skill players in roughly ascending ADP order) before being trusted; none
showed 2010's failure mode. Shallower boards in the early-to-mid 2010s
(2013: 43 rows; 2014: 39; 2015-2016: ~70) are real but THIN -- FFC's own
archive keeps fewer mocked players from before ~2018, not a parsing loss.
Reported as thin-but-valid, not dropped: an honest partial board beats no
board, and every row it has still carries a verified pre-draft date.

SCHEMA / STORAGE. Reuses `ffc_adp_snapshots` unchanged -- no new table.
teams=12 rows get their own `adp_source` (`ffc_{format}_12team`), distinct
from the daily 10-team capture's `ffc_{format}_10team` -- CLAUDE.md SS4's
never-blend rule applies across team-count as much as across format.
`as_of_date` is set to the parsed window END date (the real historical
draft-activity cutoff), NOT the day this script happened to run -- this is
the field a season-N backtest checks against that season's Week 1, so it
must carry the historical date or it is useless for exactly the reason this
thread exists. `sample_window` (verbatim FFC sentence) is kept unchanged,
per the ranker's explicit ask in thread 055.

RATE LIMIT / CACHE. Sequential, >=1s between requests (`time.sleep(1)`
after every fetch, cache-checked first). Every response is cached to
`data/raw/ffc/<format>-12team-<year>.html` and re-read from there on any
rerun unless `--refresh` is passed -- each season-format is fetched at most
once, ever, matching thread 055's "pull each season-format exactly once"
instruction for the original 10-team daily job, extended here to the
one-time historical set.
"""
from __future__ import annotations

import argparse
import datetime as dt
import re
import sqlite3
import sys
import time
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO / "src"))

import ingest_ffc_adp as ffc  # noqa: E402

RAW_DIR = REPO / "data" / "raw" / "ffc"
QA_DIR = REPO / "data" / "qa"
DEFAULT_DB = REPO / "data" / "nfl.db"
TEAMS = 12

# Season -> disposition, decided 2026-07-29 from the researcher's date-gate
# table (docs/research/historical-adp-availability-2026-07-29.md SS3/SS4),
# re-verified against nflreadpy schedules (see module docstring), plus this
# script's own content-validity check for 2010.
NON_PPR_GATE_FAIL = {
    2007: "window ends 2010-06-20, accumulated aggregate not a preseason sample",
    2008: "window ends 2010-06-20, accumulated aggregate not a preseason sample",
    2009: "window ends 2010-06-20, accumulated aggregate not a preseason sample",
    2011: "window Sep 7-9 2011 ends AFTER Week 1 kickoff Sep 8 2011",
    2012: "window ends same day as kickoff (Sep 5 2012) -- marginal, excluded conservatively",
}
NON_PPR_CONTENT_INVALID = {
    2010: "date gate passes but board is garbled (DEF/QB/PK-heavy, missing every real "
          "RB1 of 2010) -- excluded, see module docstring",
}
NON_PPR_SEASONS = [y for y in range(2013, 2025) if y not in NON_PPR_GATE_FAIL and y not in NON_PPR_CONTENT_INVALID]
HALF_PPR_SEASONS = list(range(2018, 2025))  # no half-PPR archive before 2018 (empty shell)

# PPR, added 2026-07-30 (FR-087) closing the gap this module's docstring left open
# ("FFC PPR, 12-team: 2010 verified; 2011-2024 not probed [GAP]",
# docs/research/historical-adp-availability-2026-07-29.md SS1). Kickoff-date gate
# is season-level, not format-level, so the same GATE_FAIL/MARGINAL seasons
# (2011 window ends after kickoff, 2012 window ends same day) apply unchanged.
# Content-validity was NOT assumed to transfer -- independently re-verified
# 2026-07-30 by fetching the PPR archive directly: 2010 PPR reproduces the exact
# same migration-artifact failure as non-PPR 2010 (26 rows, DEF/QB-heavy, no real
# RB1 of that season -- e.g. no Adrian Peterson/Chris Johnson/Arian Foster), so it
# is excluded on the same basis. 2013 PPR spot-checked sane (42 rows, real top
# players: Jimmy Graham, A.J. Green, Julio Jones, Aaron Rodgers in plausible
# order) -- same "thin but valid" pattern as non-PPR's early years.
PPR_GATE_FAIL = NON_PPR_GATE_FAIL
PPR_CONTENT_INVALID = {
    2010: "date gate passes but board is garbled (DEF/QB/PK-heavy, missing every real "
          "RB1 of 2010), same failure mode as non-PPR 2010 -- excluded, see module docstring",
}
PPR_SEASONS = [y for y in range(2013, 2025) if y not in PPR_GATE_FAIL and y not in PPR_CONTENT_INVALID]

FORMAT_SLUGS = {"non_ppr": "standard", "half_ppr": "half-ppr", "ppr": "ppr"}


def _cache_path(format_key: str, season: int) -> Path:
    return RAW_DIR / f"{FORMAT_SLUGS[format_key]}-{TEAMS}team-{season}.html"


def _fetch_cached(format_key: str, season: int, refresh: bool) -> str:
    path = _cache_path(format_key, season)
    if path.exists() and not refresh:
        return path.read_text(encoding="utf-8")
    html = ffc.fetch_html(season, teams=TEAMS, fmt=FORMAT_SLUGS[format_key])
    RAW_DIR.mkdir(parents=True, exist_ok=True)
    path.write_text(html, encoding="utf-8")
    time.sleep(1.0)  # >=1 request/second ceiling, honoured even on a cache write
    return html


_WINDOW_DATE_RE = re.compile(r"([A-Za-z]+ \d{1,2},\s*\d{4})")


def _parse_window_end_date(window: str) -> str | None:
    """'September 2, 2013 to September 4, 2013' -> '2013-09-04'. None if the
    trailing date cannot be parsed -- caller must drop the row rather than
    guess (CLAUDE.md's never-fabricate rule)."""
    if not window:
        return None
    dates = _WINDOW_DATE_RE.findall(window)
    if not dates:
        return None
    try:
        d = dt.datetime.strptime(dates[-1].strip(), "%B %d, %Y").date()
    except ValueError:
        return None
    return d.isoformat()


def backfill_one(conn: sqlite3.Connection, db_path: Path, format_key: str, season: int, refresh: bool) -> dict:
    html = _fetch_cached(format_key, season, refresh)
    parsed = ffc.parse_adp_table(html)
    total_drafts, window = ffc.parse_sample_window(html)
    adp_source = f"ffc_{format_key}_{TEAMS}team"

    if not parsed:
        return {
            "format_key": format_key, "season": season, "adp_source": adp_source,
            "dropped_no_data": True, "reason": "zero rows parsed (empty archive shell)",
        }

    as_of_date = _parse_window_end_date(window)
    if as_of_date is None:
        return {
            "format_key": format_key, "season": season, "adp_source": adp_source,
            "dropped_no_data": True,
            "reason": f"could not parse a window end date from {window!r} -- dropped, not dated",
            "rows_would_have_stored": len(parsed),
        }

    result = ffc.store_adp(
        conn, parsed, period=season, teams=TEAMS, fmt=FORMAT_SLUGS[format_key],
        is_retrospective_aggregate=False,  # gate already excluded any season that fails this
        as_of_date=as_of_date,
        total_drafts_in_sample=total_drafts, sample_window=window,
        adp_source=adp_source,
    )
    # export_snapshot_csv() filters by substr(retrieved_at, 1, 10), i.e. the day
    # THIS SCRIPT RAN -- not as_of_date (the historical draft-window-end date
    # stored in the as_of_date column). Passing as_of_date here silently
    # exported zero rows for every historical season on the first run of this
    # module; fixed by using today's date, matching what store_adp() actually
    # stamped into retrieved_at.
    retrieved_today = dt.datetime.now(dt.timezone.utc).date().isoformat()
    csv_path = ffc.export_snapshot_csv(conn, db_path, retrieved_today, period=season, adp_source=adp_source)
    return {
        "format_key": format_key, "season": season, "adp_source": adp_source,
        "dropped_no_data": False, "as_of_date": as_of_date, "sample_window": window,
        "total_drafts": total_drafts, "csv_path": csv_path, **result,
    }


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--db", type=Path, default=DEFAULT_DB)
    ap.add_argument("--refresh", action="store_true", help="Re-fetch even if a cached HTML file exists.")
    ap.add_argument(
        "--format-key",
        choices=sorted(FORMAT_SLUGS),
        default=None,
        help="Default: run all three (non_ppr, half_ppr, ppr).",
    )
    args = ap.parse_args()

    plan = []
    if args.format_key in (None, "half_ppr"):
        plan += [("half_ppr", y) for y in HALF_PPR_SEASONS]
    if args.format_key in (None, "non_ppr"):
        plan += [("non_ppr", y) for y in NON_PPR_SEASONS]
    if args.format_key in (None, "ppr"):
        plan += [("ppr", y) for y in PPR_SEASONS]

    conn = sqlite3.connect(args.db)
    conn.execute(ffc._CREATE_SQL)
    conn.execute(ffc._QUARANTINE_CREATE_SQL)
    results = []
    try:
        for format_key, season in plan:
            r = backfill_one(conn, args.db, format_key, season, args.refresh)
            results.append(r)
            if r["dropped_no_data"]:
                print(f"[{format_key} {season}] DROPPED -- {r['reason']}")
            else:
                print(
                    f"[{r['adp_source']} {season}] stored={r['stored']} "
                    f"quarantined={r['quarantined']} match_rate={r['match_rate']} "
                    f"as_of_date={r['as_of_date']} window={r['sample_window']!r} "
                    f"total_drafts={r['total_drafts']}"
                )
    finally:
        conn.close()

    print()
    print("excluded seasons (never fetched):")
    for y, reason in sorted(NON_PPR_GATE_FAIL.items()):
        print(f"  non_ppr {y}: GATE FAIL -- {reason}")
    for y, reason in sorted(NON_PPR_CONTENT_INVALID.items()):
        print(f"  non_ppr {y}: CONTENT INVALID -- {reason}")
    for y, reason in sorted(PPR_GATE_FAIL.items()):
        print(f"  ppr {y}: GATE FAIL -- {reason}")
    for y, reason in sorted(PPR_CONTENT_INVALID.items()):
        print(f"  ppr {y}: CONTENT INVALID -- {reason}")

    stored_total = sum(r.get("stored", 0) for r in results)
    quarantined_total = sum(r.get("quarantined", 0) for r in results)
    dropped = [r for r in results if r["dropped_no_data"]]
    print()
    print(f"TOTAL stored={stored_total} quarantined={quarantined_total} "
          f"season-formats dropped={len(dropped)} of {len(plan)} attempted")


if __name__ == "__main__":
    main()
