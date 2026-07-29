#!/usr/bin/env python
"""Daily FFC ADP snapshot capture for CI, with loud failure on a bad capture.

Companion to tools/ci_adp_snapshot.py (MFL). Captures all three FFC formats
at 10 teams -- non-PPR, half-PPR, full PPR -- each to its own adp_source and
its own dated CSV under data/adp-snapshots-ffc/, per
src/ingest_ffc_adp.py's docstring and the never-blend rule (CLAUDE.md SS4).

WHY A SEPARATE FLOOR FOR NAME RESOLUTION. ci_adp_snapshot.py (MFL) requires
90% name resolution because MFL resolves by mfl_id directly -- a drop below
90% there signals the identity join itself broke. FFC resolves by NAME
against ff_playerids, and ~19 of ~200-240 rows on every pull are team
defenses ("Seattle Defense", "Denver Defense", ...) that ff_playerids does
not carry as distinct entities at all (verified 2026-07-29: zero DEF/defense
rows in players_canonical). That is a STRUCTURAL ceiling below 100%, not a
degraded join, so this script's floor is 80%, not 90% -- set below the
worst of the three formats measured this session (88.0%) with headroom, not
tuned to always pass.

FAILING LOUDLY IS THE POINT, same as ci_adp_snapshot.py: a silently empty or
degraded write is worse than a missed day, so every check below exits
non-zero rather than committing a bad file.
"""
from __future__ import annotations

import argparse
import csv
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO / "src"))

import ingest_ffc_adp as ffc  # noqa: E402
import sqlite3  # noqa: E402

MIN_ROWS = 100
MIN_NAME_RESOLUTION = 0.80


def fail(msg: str) -> None:
    print("::error::FFC ADP capture FAILED -- %s" % msg, file=sys.stderr)
    print("FAILED: %s" % msg, file=sys.stderr)
    sys.exit(1)


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--db", type=Path, required=True)
    ap.add_argument("--period", type=int, default=None)
    ap.add_argument("--teams", type=int, default=ffc.TEAMS)
    args = ap.parse_args()
    period = args.period or __import__("datetime").datetime.now(
        __import__("datetime").timezone.utc
    ).year

    if not args.db.exists():
        fail("no database at %s -- the ff_playerids pull step must run first" % args.db)

    conn = sqlite3.connect(args.db)
    try:
        n_ids = conn.execute("SELECT COUNT(*) FROM ff_playerids").fetchone()[0]
        if n_ids < 1000:
            fail("ff_playerids has only %d rows; identity join would produce a "
                 "degraded snapshot. Re-run the reference pull." % n_ids)
        print("ff_playerids rows: %d" % n_ids)

        csv_paths = []
        for format_key, format_slug in ffc.FORMATS.items():
            adp_source = ffc.format_key_to_source(format_key, args.teams)
            print("fetching %s (adp_source=%s) ..." % (
                ffc._build_url(period, args.teams, format_slug), adp_source))
            try:
                r = ffc.capture_one_format(
                    conn, args.db, format_key, format_slug, period, args.teams, force=True
                )
            except Exception as e:
                fail("capture raised %s for format=%s: %s" % (type(e).__name__, format_key, e))

            if r["csv_path"] is None:
                fail("no CSV written for format=%s -- refusing the silent-empty case" % format_key)

            with r["csv_path"].open(newline="", encoding="utf-8") as fh:
                rows = list(csv.DictReader(fh))
            if len(rows) < MIN_ROWS:
                fail("format=%s CSV has %d data rows, below the floor of %d" % (
                    format_key, len(rows), MIN_ROWS))

            # Every row that lands in the CSV is by definition resolved (unlike
            # MFL's module, unresolved rows never get a CSV row here -- they go
            # to ffc_adp_quarantine instead). So the resolution floor is checked
            # against match_rate = stored / (stored + quarantined), computed by
            # capture_one_format() from the full parsed table, not re-derived
            # from the CSV's contents (which would trivially always read 100%).
            match_rate = r.get("match_rate")
            if match_rate is None or match_rate < MIN_NAME_RESOLUTION:
                fail("format=%s match_rate=%s below %.0f%% floor (stored=%s, quarantined=%s)" % (
                    format_key, match_rate, MIN_NAME_RESOLUTION * 100,
                    r.get("stored"), r.get("quarantined")))

            total_drafts = r.get("total_drafts") or 0
            if total_drafts and total_drafts < 100:
                print("::warning::format=%s thin sample -- totalDrafts=%d" % (format_key, total_drafts))

            print("OK: %s -- %d rows, match_rate=%.1f%%, quarantined=%d, totalDrafts=%s" % (
                r["csv_path"].name, len(rows), match_rate * 100, r.get("quarantined", 0), total_drafts))
            csv_paths.append(str(r["csv_path"]))

        print("CSV_PATHS=%s" % ",".join(csv_paths))
    finally:
        conn.close()

    return 0


if __name__ == "__main__":
    sys.exit(main())
