"""
PARKED. Play-caller ingestion — schema only, no data.

WHY PARKED. The supplied table has 22 of 64 cells populated; the rest are
UNKNOWN because play-calling duty is usually not settled until training camp and
is rarely announced. A plausible-looking but wrong table is worse than no table,
so nothing is ingested until a verified source exists.

COMPLETION TRIGGER: the ESPN 32-team play-caller roundup, published in late
August. Precedent verified — the feature ran in 2024 ("What to know on all 32
NFL playcallers", id 41018846) and 2025 (id 46137832). Two consecutive years, so
a 2026 edition is a reasonable expectation rather than a hope.

=======================================================================
THE SCHEMA FIX, APPLIED NOW SO THE DATA CANNOT BE INGESTED WRONG LATER
=======================================================================

The supplied CSV keys on (team, season) with a single `play_caller`. That is
structurally unable to represent a mid-season handoff, and those happen — the
cited case is Cleveland 2025, where Stefanski handed play-calling to Rees partway
through the year. Under the flat schema that row is simply wrong, and nothing in
the data would reveal it.

So the table below keys on (team, season, start_week) with an explicit
`end_week`. A team-season with no change is one row spanning weeks 1-18. A
handoff is two rows. This costs nothing when there is no change and is the only
shape that can express one.

This matters more than it looks for test-registry #29/#30: those tests are about
coordinator *continuity*, and a schema that cannot see a mid-season change would
score a team that switched play-callers in week 8 as perfectly continuous.
"""

from __future__ import annotations

import csv
import sqlite3
from pathlib import Path
from typing import List, Optional

TABLE_NAME = "play_callers"
DEFAULT_DB_PATH = Path(__file__).resolve().parent.parent / "data" / "nfl.db"

_CREATE_SQL = f"""
CREATE TABLE IF NOT EXISTS "{TABLE_NAME}" (
    team TEXT NOT NULL,
    season INTEGER NOT NULL,
    -- Week range this play-caller was responsible for. A season with no change
    -- is a single row, weeks 1-18. A mid-season handoff is two rows. The flat
    -- (team, season) key in the source CSV cannot express the second case.
    start_week INTEGER NOT NULL,
    end_week INTEGER NOT NULL,
    play_caller TEXT,
    title TEXT,                    -- HC | OC | other
    is_hc_calling INTEGER,
    changed_from_prior_year INTEGER,
    -- 'high' only where a named source confirms it. UNKNOWN rows are stored as
    -- NULL play_caller with confidence='unknown' rather than omitted, so the
    -- absence is visible to anything that joins against this table.
    confidence TEXT NOT NULL,
    source TEXT,
    retrieved_at TEXT,
    PRIMARY KEY (team, season, start_week)
)
"""

VALID_CONFIDENCE = {"high", "medium", "low", "unknown"}
REQUIRED_CSV_COLUMNS = {
    "team", "season", "play_caller", "title", "is_hc_calling",
    "changed_from_prior_year", "confidence", "source",
}


class PlayCallerDataUnavailable(RuntimeError):
    """Raised on any attempt to ingest before a verified source exists."""


def ensure_table(conn: sqlite3.Connection) -> None:
    conn.execute(_CREATE_SQL)


def validate_rows(rows: List[dict]) -> List[str]:
    """Return a list of problems. Empty list means the file is ingestible."""
    problems: List[str] = []
    seen = set()
    for i, r in enumerate(rows, 1):
        conf = (r.get("confidence") or "").strip().lower()
        if conf not in VALID_CONFIDENCE:
            problems.append(f"row {i}: confidence {conf!r} not in {sorted(VALID_CONFIDENCE)}")
        if conf != "unknown" and not (r.get("source") or "").strip():
            problems.append(f"row {i}: confidence={conf} but no source cited")
        try:
            sw = int(r.get("start_week", 1))
            ew = int(r.get("end_week", 18))
        except (TypeError, ValueError):
            problems.append(f"row {i}: start_week/end_week not integers")
            continue
        if not (1 <= sw <= ew <= 22):
            problems.append(f"row {i}: invalid week range {sw}-{ew}")
        key = (r.get("team"), r.get("season"), sw)
        if key in seen:
            problems.append(f"row {i}: duplicate key {key}")
        seen.add(key)
    return problems


def load_csv(path: Path) -> List[dict]:
    """Read the source CSV and widen it to the week-ranged schema.

    A source row without start_week/end_week is assumed to span the full season,
    which is the correct reading of a flat (team, season) row -- but it is an
    ASSUMPTION, and any team-season known to have had a handoff must be split
    into two rows in the source file rather than relying on this default.
    """
    with path.open(encoding="utf-8") as f:
        rows = list(csv.DictReader(f))
    missing = REQUIRED_CSV_COLUMNS - set(rows[0].keys() if rows else [])
    if missing:
        raise PlayCallerDataUnavailable(f"CSV missing required columns: {sorted(missing)}")
    for r in rows:
        r.setdefault("start_week", 1)
        r.setdefault("end_week", 18)
    return rows


def ingest(csv_path: Optional[Path] = None, db_path: Path = DEFAULT_DB_PATH) -> int:
    if csv_path is None or not Path(csv_path).exists():
        raise PlayCallerDataUnavailable(
            "Play-caller data is PARKED. No verified source file exists. The completion "
            "trigger is the ESPN 32-team play-caller roundup published in late August "
            "(precedent: 2024 id 41018846, 2025 id 46137832). Supply a CSV with "
            "start_week/end_week columns and re-run. Nothing is ingested from an "
            "incomplete table -- 22 of 64 cells populated is not a table, it is a guess "
            "with citations attached to some of it."
        )
    rows = load_csv(Path(csv_path))
    problems = validate_rows(rows)
    if problems:
        raise PlayCallerDataUnavailable(
            f"{len(problems)} validation problem(s); nothing ingested:\n  "
            + "\n  ".join(problems[:10])
        )
    conn = sqlite3.connect(db_path)
    try:
        ensure_table(conn)
        conn.executemany(
            f'INSERT OR REPLACE INTO "{TABLE_NAME}" (team, season, start_week, end_week, '
            "play_caller, title, is_hc_calling, changed_from_prior_year, confidence, source, "
            "retrieved_at) VALUES (?,?,?,?,?,?,?,?,?,?,datetime('now'))",
            [
                (r["team"], int(r["season"]), int(r["start_week"]), int(r["end_week"]),
                 r.get("play_caller") or None, r.get("title"),
                 1 if str(r.get("is_hc_calling")).upper() == "TRUE" else 0,
                 1 if str(r.get("changed_from_prior_year")).upper() == "TRUE" else 0,
                 r["confidence"], r.get("source"))
                for r in rows
            ],
        )
        conn.commit()
        return len(rows)
    finally:
        conn.close()


if __name__ == "__main__":
    print(__doc__)
    print("\nStatus: PARKED. Run ingest(csv_path=...) once a verified source exists.")
