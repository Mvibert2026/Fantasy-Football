"""Session-local restore of the `rankings` table from the COMMITTED artifact
`data/rankings-history/rankings_2021_2025.csv`.

WHY THIS EXISTS: in a Claude Code cloud session, `ingest_rankings.py`'s real
working path (the DynastyProcess mirror on github.com) 403s through the agent
proxy. scripts/rebuild_database.py documents this as an expected, reportable
block and deliberately does NOT patch around it -- correctly, because patching
the ingester would ship a base-URL substitution the founder's machine and CI
never needed.

This is NOT a source swap and NOT a substitute ingester. It restores a
byte-exact committed dump of the same table the ingester writes (the artifact
tests/test_unreproducible_artifacts.py already guards). It lives in
experiments/, not src/ or scripts/, and nothing in the pipeline calls it.

Usage: python experiments/restore_rankings_from_committed_csv.py
"""

from __future__ import annotations

import csv
import sqlite3
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
CSV_PATH = ROOT / "data" / "rankings-history" / "rankings_2021_2025.csv"
DB_PATH = ROOT / "data" / "nfl.db"

COLUMNS = [
    "ranking_source", "source", "season", "player_id", "player_name", "team",
    "adp_rank", "adp_value", "spread_sd", "rank_best", "rank_worst",
    "as_of_date", "position", "is_preseason_final", "ingested_at",
]


def main() -> None:
    conn = sqlite3.connect(DB_PATH)
    live_cols = {r[1] for r in conn.execute("PRAGMA table_info(rankings)")}
    cols = [c for c in COLUMNS if c in live_cols]
    with CSV_PATH.open(newline="", encoding="utf-8") as f:
        rows = [tuple(r[c] or None for c in cols) for r in csv.DictReader(f)]
    placeholders = ",".join("?" * len(cols))
    conn.executemany(
        f"INSERT OR REPLACE INTO rankings ({','.join(cols)}) VALUES ({placeholders})",
        rows,
    )
    conn.commit()
    got = conn.execute(
        "SELECT season, COUNT(*) FROM rankings WHERE source='fantasypros_ecr' "
        "GROUP BY season ORDER BY season"
    ).fetchall()
    print(f"restored {len(rows)} rows from {CSV_PATH.name}")
    for season, n in got:
        print(f"  {season}: {n}")
    conn.close()


if __name__ == "__main__":
    main()
