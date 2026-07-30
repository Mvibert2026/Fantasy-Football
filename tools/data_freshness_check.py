#!/usr/bin/env python3
"""Data freshness tripwire for every dated source the site depends on (FR-130).

WHY THIS EXISTS. `board.json` has carried a freshness gate
(`snapshot_as_of_date` / `snapshot_age_days` / `snapshot_max_age_days` /
`snapshot_stale`, `src/freshness.py`, T5) since 2026-07-27, but it only covers
one source (`rankings.fantasypros_csv_2026draft`) and only fires as a hard
`enforce_freshness` refusal at build time -- no warning before the limit, and
nothing at all for ADP, the availability ranking source, or
`player_descriptions.json`. On 2026-07-30 that gap let a full day of captured
ADP (`data/adp-snapshots/2026-07-30.csv`, `data/adp-snapshots-ffc/2026-07-30_*.csv`)
sit on disk, never ingested into `data/nfl.db`, discovered only because the
founder happened to ask (FR-130). This script is the standing check that
would have caught it the same morning.

THIS EXTENDS `src/freshness.py`'S PATTERN RATHER THAN INVENTING A SECOND ONE.
DB-backed sources reuse `freshness.check_freshness()` verbatim; this script
adds (a) file-backed sources `check_freshness` cannot see (exported JSON
artifacts) and (b) the capture-without-ingest check, which is new because
nothing existing looks at the filesystem at all.

WHAT IT CHECKS, per source:
  - age = today (UTC) minus the source's most recent as-of date
  - status:
      OK       age <= warn_at_days
      WARN     warn_at_days < age <= max_age_days   (visible before the wall)
      STALE    age > max_age_days                    (the hard-stop line)
      MISSING  no as-of date on file at all
      BLOCKED  the source is currently unreachable from this environment
               (recorded, not silently skipped -- see CAPTURE_WITHOUT_INGEST
               and the fantasypros_ecr row)

CAPTURE-WITHOUT-INGEST. For every (capture directory, DB table) pair, compares
the newest dated filename on disk against the newest as-of value actually
ingested into the table it feeds. A file newer than the row is exactly
2026-07-30's ADP gap, one query, no assumptions.

EXIT CODE. Non-zero if any source is STALE, MISSING, or a capture-without-
ingest gap is found. WARN and BLOCKED do not fail the run by themselves --
they are visible in the table but are not (yet) a hard stop, matching this
script's job of surfacing problems in one place rather than making every
warning a build failure. Wiring this into the export pipeline as a hard gate
is a separate decision for whoever owns that pipeline step.

OWNERSHIP. Every row states who can actually fix a stale reading:
  - "data-ops, automated"    -- rerun the ingest script, no human input needed
  - "data-ops, needs founder" -- the source is a founder-supplied file/action
  - "founder"                -- only the founder can produce a fresher input

USAGE.
    python tools/data_freshness_check.py [--db data/nfl.db] [--export-dir data/export]
Prints one table, one line per source, then a summary. Exits 1 if any source
is STALE/MISSING or a capture-without-ingest gap exists, 0 otherwise.
"""
from __future__ import annotations

import argparse
import datetime as dt
import json
import re
import sqlite3
import sys
from pathlib import Path
from typing import Optional

REPO = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO / "src"))

import freshness as fr  # noqa: E402
import league_config as lc  # noqa: E402

DEFAULT_DB = REPO / "data" / "nfl.db"
DEFAULT_EXPORT_DIR = REPO / "data" / "export"

SEASON = lc.CURRENT_LEAGUE.season if hasattr(lc.CURRENT_LEAGUE, "season") else 2026
DATE_RE = re.compile(r"(\d{4}-\d{2}-\d{2})")


def _today(today: Optional[dt.date]) -> dt.date:
    return today or dt.datetime.now(dt.timezone.utc).date()


def _status(age: Optional[int], warn_at: int, max_age: int) -> str:
    if age is None:
        return "MISSING"
    if age > max_age:
        return "STALE"
    if age > warn_at:
        return "WARN"
    return "OK"


def _rankings_source_row(conn, source: str, warn_at: int, max_age: int, owner: str,
                          today: Optional[dt.date]) -> dict:
    r = fr.check_freshness(conn, SEASON, source, max_age, today=today)
    status = _status(r["age_days"], warn_at, max_age)
    return {
        "source": f"rankings:{source}", "as_of": r["as_of_date"], "age_days": r["age_days"],
        "warn_at_days": warn_at, "max_age_days": max_age, "status": status, "owner": owner,
    }


def _table_max_date_row(conn, label: str, sql: str, params: tuple, warn_at: int, max_age: int,
                         owner: str, today: Optional[dt.date]) -> dict:
    row = conn.execute(sql, params).fetchone()
    as_of = row[0] if row else None
    as_of_date = as_of[:10] if as_of else None  # tolerate a datetime or a plain date string
    age = None
    if as_of_date:
        age = (_today(today) - dt.date.fromisoformat(as_of_date)).days
    status = _status(age, warn_at, max_age)
    return {
        "source": label, "as_of": as_of_date, "age_days": age,
        "warn_at_days": warn_at, "max_age_days": max_age, "status": status, "owner": owner,
    }


def _file_json_field_row(label: str, path: Path, field: str, warn_at: int, max_age: int,
                          owner: str, today: Optional[dt.date]) -> dict:
    if not path.exists():
        return {
            "source": label, "as_of": None, "age_days": None,
            "warn_at_days": warn_at, "max_age_days": max_age, "status": "MISSING", "owner": owner,
        }
    data = json.loads(path.read_text(encoding="utf-8"))
    raw = data.get(field)
    as_of_date = None
    if raw:
        as_of_date = raw[:10]
    age = None
    if as_of_date:
        age = (_today(today) - dt.date.fromisoformat(as_of_date)).days
    status = _status(age, warn_at, max_age)
    return {
        "source": label, "as_of": as_of_date, "age_days": age,
        "warn_at_days": warn_at, "max_age_days": max_age, "status": status, "owner": owner,
    }


def _newest_dated_filename(directory: Path, pattern: re.Pattern = DATE_RE) -> Optional[str]:
    """Newest YYYY-MM-DD found in any filename directly under `directory`.
    Filenames, not mtimes: git checkout resets mtimes to checkout time, so
    mtime cannot distinguish a fresh capture from an old one once committed
    (docs/environment.md's worktree note applies here too)."""
    best = None
    if not directory.exists():
        return None
    for p in directory.glob("*.csv"):
        m = pattern.search(p.name)
        if m and (best is None or m.group(1) > best):
            best = m.group(1)
    return best


def capture_without_ingest_checks(conn) -> list:
    """One row per (capture directory, table) pair: file-newer-than-row gaps.
    This is the check that would have caught 2026-07-30's ADP gap the same
    morning -- see module docstring."""
    results = []

    # 1. MFL daily ADP: data/adp-snapshots/*.csv -> adp_snapshots(mfl_proxy)
    newest_file = _newest_dated_filename(REPO / "data" / "adp-snapshots")
    row = conn.execute(
        "SELECT MAX(retrieved_at) FROM adp_snapshots WHERE adp_source='mfl_proxy'"
    ).fetchone()
    newest_db = row[0][:10] if row and row[0] else None
    results.append({
        "pair": "data/adp-snapshots/*.csv -> adp_snapshots(mfl_proxy)",
        "newest_file": newest_file, "newest_in_db": newest_db,
        "gap": bool(newest_file and (newest_db is None or newest_file > newest_db)),
    })

    # 2. FFC daily 10-team ADP: data/adp-snapshots-ffc/YYYY-MM-DD_{half_ppr,non_ppr,ppr}.csv
    #    -> ffc_adp_snapshots(ffc_{half_ppr,non_ppr,ppr}_10team). Excludes the
    #    *_12team_periodYYYY.csv historical-backfill files deliberately --
    #    those are one-off retrospective pulls, not a daily schedule, so
    #    "newest on disk" for them is not a freshness signal.
    ffc_dir = REPO / "data" / "adp-snapshots-ffc"
    daily_pattern = re.compile(r"^(\d{4}-\d{2}-\d{2})_(half_ppr|non_ppr|ppr)\.csv$")
    newest_by_format: dict[str, str] = {}
    if ffc_dir.exists():
        for p in ffc_dir.glob("*.csv"):
            m = daily_pattern.match(p.name)
            if not m:
                continue
            date_str, fmt = m.group(1), m.group(2)
            if fmt not in newest_by_format or date_str > newest_by_format[fmt]:
                newest_by_format[fmt] = date_str
    for fmt, newest_file in newest_by_format.items():
        adp_source = f"ffc_{fmt}_10team"
        row = conn.execute(
            "SELECT MAX(as_of_date) FROM ffc_adp_snapshots WHERE adp_source=?", (adp_source,)
        ).fetchone()
        newest_db = row[0] if row and row[0] else None
        results.append({
            "pair": f"data/adp-snapshots-ffc/*_{fmt}.csv -> ffc_adp_snapshots({adp_source})",
            "newest_file": newest_file, "newest_in_db": newest_db,
            "gap": bool(newest_file and (newest_db is None or newest_file > newest_db)),
        })

    return results


def build_report(db_path: Path, export_dir: Path, today: Optional[dt.date] = None) -> dict:
    conn = sqlite3.connect(db_path)
    try:
        cfg = lc.CURRENT_LEAGUE
        rows = []

        # Rankings sources.
        rows.append(_rankings_source_row(
            conn, "fantasypros_csv_2026draft", warn_at=cfg.freshness_max_age_days - 1,
            max_age=cfg.freshness_max_age_days, owner="data-ops, needs founder (browser export)",
            today=today,
        ))
        rows.append(_rankings_source_row(
            conn, "fantasypros_ecr", warn_at=5, max_age=7,
            owner="data-ops, automated (nflreadpy/DynastyProcess mirror) "
                  "-- BLOCKED 2026-07-30: mirror returned HTTP 403 from this environment",
            today=today,
        ))

        # ADP sources.
        rows.append(_table_max_date_row(
            conn, "adp_snapshots:mfl_proxy",
            "SELECT MAX(retrieved_at) FROM adp_snapshots WHERE adp_source='mfl_proxy'", (),
            warn_at=1, max_age=2, owner="data-ops, automated (CI daily, MFL)", today=today,
        ))
        for fmt in ("half_ppr", "non_ppr", "ppr"):
            adp_source = f"ffc_{fmt}_10team"
            rows.append(_table_max_date_row(
                conn, f"ffc_adp_snapshots:{adp_source}",
                "SELECT MAX(as_of_date) FROM ffc_adp_snapshots WHERE adp_source=?",
                (adp_source,), warn_at=1, max_age=2,
                owner="data-ops, automated (CI daily, FFC)", today=today,
            ))

        # Exported JSON artifacts (file-backed, not DB-backed).
        rows.append(_file_json_field_row(
            "export:board.json", export_dir / "board.json", "generated_utc",
            warn_at=cfg.freshness_max_age_days - 1, max_age=cfg.freshness_max_age_days,
            owner="data-ops, run export_contract.py after any ingest", today=today,
        ))
        rows.append(_file_json_field_row(
            "export:availability.json", export_dir / "availability.json", "generated_utc",
            warn_at=5, max_age=7,
            owner="data-ops, run export_contract.py after any ingest", today=today,
        ))
        rows.append(_file_json_field_row(
            "export:player_descriptions.json", export_dir / "player_descriptions.json",
            "generated_utc", warn_at=2, max_age=3,
            owner="data-ops, run player_descriptions.py after board changes", today=today,
        ))

        gaps = capture_without_ingest_checks(conn)
    finally:
        conn.close()

    return {"sources": rows, "capture_without_ingest": gaps}


def print_report(report: dict) -> int:
    exit_code = 0
    print("=" * 100)
    print("DATA FRESHNESS -- tools/data_freshness_check.py")
    print("=" * 100)
    print(f"{'source':45} {'as_of':12} {'age':>5} {'warn':>5} {'max':>5} {'status':8} owner")
    print("-" * 100)
    for r in report["sources"]:
        print(
            f"{r['source']:45} {str(r['as_of']):12} "
            f"{str(r['age_days']):>5} {r['warn_at_days']:>5} {r['max_age_days']:>5} "
            f"{r['status']:8} {r['owner']}"
        )
        if r["status"] in ("STALE", "MISSING"):
            exit_code = 1

    print()
    print("CAPTURE-WITHOUT-INGEST -- file on disk newer than the table it feeds")
    print("-" * 100)
    any_gap = False
    for g in report["capture_without_ingest"]:
        marker = "GAP" if g["gap"] else "ok"
        if g["gap"]:
            any_gap = True
            exit_code = 1
        print(f"  [{marker:3}] {g['pair']:65} file={g['newest_file']}  db={g['newest_in_db']}")
    if not report["capture_without_ingest"]:
        print("  (no capture/ingest pairs configured)")
    if not any_gap:
        print("  no gaps found")

    print()
    print(f"exit code: {exit_code}  ({'violations found' if exit_code else 'all clear'})")
    return exit_code


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--db", type=Path, default=DEFAULT_DB)
    ap.add_argument("--export-dir", type=Path, default=DEFAULT_EXPORT_DIR)
    args = ap.parse_args()

    if not args.db.exists():
        print(f"::error:: no database at {args.db}", file=sys.stderr)
        return 1

    report = build_report(args.db, args.export_dir)
    return print_report(report)


if __name__ == "__main__":
    sys.exit(main())
