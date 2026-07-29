#!/usr/bin/env python
"""Daily ADP snapshot capture for CI, with loud failure on a bad capture.

WHY THIS EXISTS. `data/adp-snapshots/YYYY-MM-DD.csv` is the canonical archive
of MFL ADP (`src/ingest_mfl_adp.py` docstring: the CSV is canonical, the DB is
a cache of it). MFL serves a *rolling* aggregate -- its `totalDrafts` has
already been observed moving down, 50 on 2026-07-26 to 43 on 2026-07-29 -- so a
day not captured is a day gone permanently, with no backfill path at any price
(`docs/can-we-rebuild-the-database.md`). Until now capture depended on a
Windows Scheduled Task that `schtasks` reports as `Logon Mode: Interactive
only`, i.e. it does not fire from a locked or logged-out machine, and nobody
had verified an unattended fire. This script exists to run that capture
somewhere that does not depend on one computer being awake.

WHAT IT DOES NOT DO. It does not write `data/nfl.db` -- CI has no copy and the
file is gitignored (813 MB). Only the CSV is produced. Backfilling the DB from
the committed CSVs is a local operation and is deliberately left to the local
machine, per the founder's instruction that the CSV is the irreplaceable part.

FAILING LOUDLY IS THE POINT. `ingest_mfl_adp.main()` prints a warning and exits
0 when no CSV is written. In an unattended workflow that is indistinguishable
from success, and a committed empty file is worse than a missed day because it
looks like data. Every check below exits non-zero instead.

IDENTITY RESOLUTION. `ingest_mfl_adp` fills `player_name`/`position`/`team` by
joining MFL ids against the `ff_playerids` table. A fresh CI database has no
such table, and the join would silently yield a CSV of nulls in those columns --
structurally valid, quietly degraded, and different from every locally captured
file. So this script REQUIRES `ff_playerids` to be present and verifies the
join actually resolved, rather than trusting that it did.
"""
from __future__ import annotations

import argparse
import csv
import datetime as dt
import sqlite3
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO / "src"))

import ingest_mfl_adp as adp  # noqa: E402

# Floors, not targets. Real captures have run 225-232 players; anything far
# below that means a truncated or degenerate response, not a quiet news day.
MIN_ROWS = 100
MIN_NAME_RESOLUTION = 0.90


def fail(msg: str) -> None:
    print("::error::ADP capture FAILED -- %s" % msg, file=sys.stderr)
    print("FAILED: %s" % msg, file=sys.stderr)
    sys.exit(1)


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--db", type=Path, required=True,
                    help="Throwaway SQLite path. Put it under data/ so the CSV "
                         "lands in data/adp-snapshots/ and the .db stays gitignored.")
    ap.add_argument("--period", type=int, default=2026)
    ap.add_argument("--fcount", type=int, default=10)
    ap.add_argument("--is-ppr", type=int, default=1)
    ap.add_argument("--is-keeper", type=int, default=0)
    ap.add_argument("--is-mock", type=int, default=0)
    ap.add_argument("--cutoff", type=int, default=10)
    args = ap.parse_args()

    today = dt.datetime.now(dt.timezone.utc).date().isoformat()
    print("UTC capture date: %s" % today)

    if not args.db.exists():
        fail("no database at %s -- the ff_playerids pull step must run first" % args.db)

    conn = sqlite3.connect(args.db)
    try:
        conn.execute(adp._CREATE_SQL)

        n_ids = conn.execute("SELECT COUNT(*) FROM ff_playerids").fetchone()[0]
        if n_ids < 1000:
            fail("ff_playerids has only %d rows; identity join would produce a "
                 "CSV of nulls. Re-run the reference pull." % n_ids)
        print("ff_playerids rows: %d" % n_ids)

        # One request. The endpoint is hit exactly once per run, which satisfies
        # the one-request-per-second constraint by construction; fetch_adp also
        # backs off on 429 and sends the project's descriptive User-Agent.
        print("fetching %s ..." % adp._build_url(
            args.period, args.fcount, args.is_ppr, args.is_keeper, args.is_mock, args.cutoff))
        try:
            payload = adp.fetch_adp(
                args.period, args.fcount, args.is_ppr, args.is_keeper,
                args.is_mock, args.cutoff,
            )
        except Exception as e:  # network, HTTP, JSON -- all fatal here
            fail("fetch raised %s: %s" % (type(e).__name__, e))

        block = (payload or {}).get("adp") or {}
        players = block.get("player") or []
        if isinstance(players, dict):
            players = [players]
        total_drafts = int(block.get("totalDrafts") or 0)
        print("response: %d players, totalDrafts=%d" % (len(players), total_drafts))

        if not players:
            fail("response contained zero players -- refusing to write an empty snapshot")
        if total_drafts <= 0:
            fail("totalDrafts=%d -- degenerate response, refusing to record it" % total_drafts)

        n = adp.store_adp(
            conn, payload, args.fcount, args.is_ppr, args.is_keeper,
            args.is_mock, args.cutoff, args.period,
        )
        print("stored %d rows" % n)

        csv_path = adp.export_snapshot_csv(conn, args.db, today)
        if csv_path is None:
            fail("export_snapshot_csv wrote nothing for %s -- no rows matched today's "
                 "UTC date. This is the silent-empty case; failing instead." % today)
    finally:
        conn.close()

    # ---- validate the artifact itself, not our belief about it ----
    with csv_path.open(newline="", encoding="utf-8") as fh:
        rows = list(csv.DictReader(fh))

    if len(rows) < MIN_ROWS:
        fail("CSV has %d data rows, below the floor of %d -- treating as a "
             "truncated capture rather than a real one" % (len(rows), MIN_ROWS))

    named = sum(1 for r in rows if (r.get("player_name") or "").strip())
    ratio = named / len(rows)
    if ratio < MIN_NAME_RESOLUTION:
        fail("only %d/%d rows (%.1f%%) resolved to a player name, below %.0f%% -- "
             "the identity join degraded; a nameless snapshot is not usable data"
             % (named, len(rows), ratio * 100, MIN_NAME_RESOLUTION * 100))

    if total_drafts < 100:
        # Not fatal: a thin sample is a real, recordable observation, and the
        # existing ingester already treats it as a caution rather than an error.
        print("::warning::thin sample -- totalDrafts=%d; do not weight heavily "
              "without measuring first" % total_drafts)

    print("OK: %s -- %d rows, %d/%d named (%.1f%%), totalDrafts=%d"
          % (csv_path.name, len(rows), named, len(rows), ratio * 100, total_drafts))

    # Surface the path for the workflow's commit step.
    print("CSV_PATH=%s" % csv_path.as_posix())
    return 0


if __name__ == "__main__":
    sys.exit(main())
