"""
Ingest per-player COMPONENT projections (yards, catches, TDs -- not just a
season points total) from Sleeper's public projections endpoint into
data/nfl.db (thread 091; FR-053 follow-up;
docs/research/component-projections-and-fr-053-features-2026-07-29.md).

WHY THIS EXISTS. `board.json`'s `projected_points` is a per-position rank-
curve lookup (`a + b*ln(rank)`), never a per-player forecast of yards,
catches and touchdowns. That absence blocks custom scoring, correct scoring
for the founder's other leagues, and pricing this league's stacking yardage
bonuses (CLAUDE.md SS7) -- a threshold bonus is a nonlinear function of a
per-game distribution and cannot be recovered from a season points total.
This module is INGESTION ONLY. No modelling, no re-scoring, no change to how
board.json is built. Whether these projections improve anything is a
separate, pre-registered question for ranker/strategist.

AUTHORISATION. The founder ruled 2026-07-29: "personal use, proceed" (this
session's dispatch). Verified independently this session, not just trusted
from the researcher's record (which had no shell to run anything):
  - GET https://api.sleeper.com/projections/nfl/2026?season_type=regular&position[]=QB
    returns HTTP 200, a JSON list, 355 QB rows for season 2026, every row
    carrying `company: "rotowire"` and a `stats` block with `pass_att/cmp/yd/
    td/int`, `rush_att/yd/td`, `rec/rec_yd/rec_td`, `fum_lost`, `gp`, 2pt
    fields, and reception-bucket detail (`rec_0_4` .. `rec_40p`) -- matches
    the researcher's record. RB=741, WR=1362, TE=647 rows the same day.
  - https://api.sleeper.com/robots.txt is entirely commented out (every
    Disallow line is a `#` comment) -- nothing is disallowed, matching the
    researcher's finding.
Standing conditions, same shape as ingest_ffc_adp.py: PRIVATE, SINGLE-USER
USE ONLY (never wired into board.json or any public export -- see
CLAUDE.md SS10 and this session's dispatch); descriptive User-Agent; backoff
on HTTP 429; at most one fetch per position per calendar day; never blended
with any other projection source if a second one is ever added
(CLAUDE.md SS4's ranking_source separation applies to projection provenance
the same way it applies to adp_source).

WHAT THIS IS NOT. Not wired into board.json, not a public export, not a
ranking input. Landing surfaces are exactly two: `data/nfl.db` and
`data/projection-snapshots/`. FastAPI, export_static.py and the frontend are
untouched by this module.

IDENTITY RESOLUTION. Sleeper's `player_id` is a direct crosswalk spoke
already present in `ff_playerids.sleeper_id` (identity.py's
DIRECT_CROSSWALK_SOURCES). Resolution goes through `identity.resolve(conn,
"sleeper", player_id)` -- a real ID match, not name matching (identity.py
documents sleeper_id at 50.9% non-null with 6 collision groups already
excluded during build_identity_tables()). A player_id with no crosswalk hit
or a collision returns None from resolve() and goes to
`sleeper_projection_quarantine` with a reason -- never a fuzzy-matched
guess, per CLAUDE.md's quarantine discipline.

AS_OF_DATE. Sleeper's payload carries no as-of date field of its own -- only
`last_modified`/`updated_at` epoch-millisecond timestamps recording when
Rotowire's own estimate last changed, which is per-row and does not describe
"the state of the board on this date" the way an ADP snapshot's as_of_date
does. Per CLAUDE.md SS4 ("every time-sensitive record carries an
as_of_date"), `as_of_date` here is OUR capture date (UTC), stamped
identically to every row fetched in one run -- the same convention
ingest_ffc_adp.py uses for as_of_date vs. its own `retrieved_at`. The
source's `last_modified`/`updated_at` are preserved verbatim as
`source_last_modified`/`source_updated_at` so a later user can tell a
projection last touched by Rotowire in June from one touched yesterday,
without confusing that with when THIS project captured it.

CSV IS THE CANONICAL ARCHIVE, same pattern as data/adp-snapshots(-ffc)/.
`data/nfl.db` is gitignored; `data/projection-snapshots/{date}_{position}.csv`
is what survives and is committed. `--import-csv-dir` restores CSVs back
into a rebuilt DB.
"""

from __future__ import annotations

import argparse
import csv
import datetime as dt
import json
import sqlite3
import time
import urllib.error
import urllib.request
from pathlib import Path
from typing import List, Optional

import identity

DEFAULT_DB_PATH = Path(__file__).resolve().parent.parent / "data" / "nfl.db"

PROJECTION_SOURCE = "sleeper_rotowire"
POSITIONS = ["QB", "RB", "WR", "TE"]

USER_AGENT = (
    "FantasyFootballBacktestProject/1.0 "
    "(personal non-commercial research project; contact via repo owner)"
)

# Component stat fields kept from Sleeper's `stats` block. Deliberately
# excludes the adp_* fields (that is ADP, a separate concept already covered
# by ingest_mfl_adp.py / ingest_ffc_adp.py under its own adp_source values)
# and the idp_*/def_*/pr_td fields (not offense skill-position stats this
# league scores). pts_std/pts_half_ppr/pts_ppr are Sleeper's OWN season-point
# totals under ITS scoring assumptions, not Westwood's -- kept for reference
# only, never treated as this league's projected_points.
_STAT_FIELDS = [
    "gp",
    "pass_att", "pass_cmp", "pass_yd", "pass_td", "pass_int", "pass_2pt", "cmp_pct",
    "rush_att", "rush_yd", "rush_td", "rush_2pt",
    "rec", "rec_yd", "rec_td", "rec_2pt",
    "fum_lost",
    "pts_std", "pts_half_ppr", "pts_ppr",
]

_CSV_COLUMNS = (
    ["projection_source", "sleeper_player_id", "mfl_id", "player_name", "position",
     "query_position", "team", "season", "season_type", "company"]
    + _STAT_FIELDS
    + ["source_last_modified", "source_updated_at", "as_of_date", "retrieved_at", "ingested_at"]
)

_CREATE_SQL = """
CREATE TABLE IF NOT EXISTS sleeper_projections (
    projection_source TEXT NOT NULL,
    sleeper_player_id TEXT NOT NULL,
    mfl_id TEXT,
    player_name TEXT,
    position TEXT NOT NULL,
    query_position TEXT NOT NULL,
    team TEXT,
    season TEXT NOT NULL,
    season_type TEXT NOT NULL,
    company TEXT,
    gp REAL, pass_att REAL, pass_cmp REAL, pass_yd REAL, pass_td REAL,
    pass_int REAL, pass_2pt REAL, cmp_pct REAL,
    rush_att REAL, rush_yd REAL, rush_td REAL, rush_2pt REAL,
    rec REAL, rec_yd REAL, rec_td REAL, rec_2pt REAL,
    fum_lost REAL,
    pts_std REAL, pts_half_ppr REAL, pts_ppr REAL,
    source_last_modified INTEGER,
    source_updated_at INTEGER,
    as_of_date TEXT NOT NULL,
    retrieved_at TEXT NOT NULL,
    ingested_at TEXT NOT NULL,
    PRIMARY KEY (projection_source, sleeper_player_id, season, season_type, as_of_date)
)
"""

_QUARANTINE_CREATE_SQL = """
CREATE TABLE IF NOT EXISTS sleeper_projection_quarantine (
    projection_source TEXT NOT NULL,
    sleeper_player_id TEXT NOT NULL,
    player_name_raw TEXT,
    position TEXT,
    query_position TEXT,
    team TEXT,
    reason TEXT NOT NULL,
    as_of_date TEXT NOT NULL,
    quarantined_at TEXT NOT NULL,
    PRIMARY KEY (projection_source, sleeper_player_id, query_position, as_of_date)
)
"""


def _build_url(season: int, position: str, season_type: str = "regular") -> str:
    return (
        f"https://api.sleeper.com/projections/nfl/{season}"
        f"?season_type={season_type}&position[]={position}"
    )


def fetch_json(season: int, position: str, season_type: str = "regular", max_retries: int = 4):
    """GET one position's projections. Retries on 429 with backoff, honouring
    Retry-After when sent -- same posture as ingest_ffc_adp.fetch_html."""
    url = _build_url(season, position, season_type)
    req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    delay = 2.0
    for attempt in range(max_retries):
        try:
            with urllib.request.urlopen(req, timeout=30) as resp:
                return json.loads(resp.read().decode("utf-8"))
        except urllib.error.HTTPError as e:
            if e.code == 429 and attempt < max_retries - 1:
                wait = float(e.headers.get("Retry-After", delay)) if e.headers else delay
                time.sleep(wait)
                delay *= 2
                continue
            raise
    raise RuntimeError("unreachable")  # pragma: no cover


def parse_rows(payload: list, position: str) -> List[dict]:
    """Extract the fields this module keeps from Sleeper's raw JSON list.
    Never fabricates a missing stat -- an absent stat field stays None/NULL,
    per CLAUDE.md's honest-nulls rule.

    `position` (arg) is the position we REQUESTED via `position[]=` -- kept
    verbatim as `query_position` on every parsed row. Sleeper's own
    `player.position` field is NOT guaranteed to match the requested filter
    (measured 2026-07-29: an `RB` fetch returned some rows with
    `player.position` of `WR`, `TE`, `FB`) -- multi-eligible or misclassified
    players. `query_position` is what gates the daily skip-check, the DELETE
    scope on re-run, and the CSV filename/content, because those need to
    stay partitioned by WHICH FETCH wrote the row, not by a field the source
    itself is inconsistent about. `position` is kept too, verbatim from
    Sleeper, for informational value only."""
    out = []
    for row in payload:
        player = row.get("player") or {}
        stats = row.get("stats") or {}
        player_id = row.get("player_id")
        if player_id is None:
            continue
        first = player.get("first_name") or ""
        last = player.get("last_name") or ""
        name = f"{first} {last}".strip() or None
        parsed = {
            "sleeper_player_id": str(player_id),
            "player_name": name,
            "position": player.get("position") or position,
            "query_position": position,
            "team": player.get("team") or row.get("team"),
            "season": row.get("season"),
            "season_type": row.get("season_type"),
            "company": row.get("company"),
            "source_last_modified": row.get("last_modified"),
            "source_updated_at": row.get("updated_at"),
        }
        for field in _STAT_FIELDS:
            parsed[field] = stats.get(field)
        out.append(parsed)
    return out


def already_fetched_today(conn: sqlite3.Connection, position: str) -> bool:
    today = dt.datetime.now(dt.timezone.utc).date().isoformat()
    row = conn.execute(
        "SELECT 1 FROM sleeper_projections WHERE projection_source=? AND query_position=? "
        "AND as_of_date=? LIMIT 1",
        (PROJECTION_SOURCE, position, today),
    ).fetchone()
    return row is not None


def store_projections(
    conn: sqlite3.Connection,
    parsed_rows: List[dict],
    season: int,
    as_of_date: str,
) -> dict:
    """Writes resolved rows to sleeper_projections and unresolved rows to
    sleeper_projection_quarantine. Never guesses an mfl_id -- an unresolved
    or colliding sleeper_player_id is quarantined with a reason."""
    conn.execute(_CREATE_SQL)
    conn.execute(_QUARANTINE_CREATE_SQL)

    has_canonical = conn.execute(
        "SELECT 1 FROM sqlite_master WHERE type='table' AND name='players_canonical'"
    ).fetchone()
    if not has_canonical:
        identity.build_identity_tables(conn)

    now = dt.datetime.now(dt.timezone.utc).isoformat()
    stored_rows = []
    quarantine_rows = []

    for r in parsed_rows:
        mfl_id = identity.resolve(conn, "sleeper", r["sleeper_player_id"])
        if mfl_id is None:
            reason = "no_sleeper_crosswalk_match"
            quarantine_rows.append((
                PROJECTION_SOURCE, r["sleeper_player_id"], r["player_name"], r["position"],
                r["query_position"], r["team"], reason, as_of_date, now,
            ))
            continue
        stored_rows.append((
            PROJECTION_SOURCE, r["sleeper_player_id"], mfl_id, r["player_name"], r["position"],
            r["query_position"], r["team"], str(r["season"] or season),
            r["season_type"] or "regular", r["company"],
            *[r.get(f) for f in _STAT_FIELDS],
            r["source_last_modified"], r["source_updated_at"], as_of_date, now, now,
        ))

    # OVERWRITE, NEVER APPEND, for the same (source, query_position, season,
    # as_of_date) -- a re-run for the same day replaces that day's rows for
    # THIS FETCH, never duplicates them. Scoped by query_position (what we
    # asked Sleeper for), not the source's own `position` field, because that
    # field is not reliably consistent with the request (see parse_rows).
    if parsed_rows:
        query_position = parsed_rows[0]["query_position"]
        conn.execute(
            "DELETE FROM sleeper_projections WHERE projection_source=? AND query_position=? "
            "AND season=? AND as_of_date=?",
            (PROJECTION_SOURCE, query_position, str(season), as_of_date),
        )
        conn.execute(
            "DELETE FROM sleeper_projection_quarantine WHERE projection_source=? "
            "AND query_position=? AND as_of_date=?",
            (PROJECTION_SOURCE, query_position, as_of_date),
        )

    conn.executemany(
        "INSERT OR REPLACE INTO sleeper_projections VALUES ("
        + ",".join("?" * (10 + len(_STAT_FIELDS) + 5)) + ")",
        stored_rows,
    )
    conn.executemany(
        "INSERT OR REPLACE INTO sleeper_projection_quarantine VALUES (?,?,?,?,?,?,?,?,?)",
        quarantine_rows,
    )
    conn.commit()
    return {
        "stored": len(stored_rows),
        "quarantined": len(quarantine_rows),
        "match_rate": round(len(stored_rows) / len(parsed_rows), 4) if parsed_rows else None,
    }


def snapshot_dir_for_db(db_path: Path) -> Path:
    return db_path.resolve().parent / "projection-snapshots"


def export_snapshot_csv(
    conn: sqlite3.Connection, db_path: Path, date_str: str, position: str, season: int,
) -> Optional[Path]:
    rows = conn.execute(
        "SELECT " + ", ".join(_CSV_COLUMNS) + " FROM sleeper_projections "
        "WHERE projection_source=? AND query_position=? AND season=? AND as_of_date=?",
        (PROJECTION_SOURCE, position, str(season), date_str),
    ).fetchall()
    if not rows:
        return None
    out_dir = snapshot_dir_for_db(db_path)
    out_dir.mkdir(parents=True, exist_ok=True)
    out_path = out_dir / f"{date_str}_{position}.csv"
    with out_path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(_CSV_COLUMNS)
        writer.writerows(rows)
    return out_path


_CSV_INT_COLS = {"source_last_modified", "source_updated_at"}
_CSV_FLOAT_COLS = set(_STAT_FIELDS)


def _coerce_csv_row(row: dict) -> tuple:
    out = []
    for col in _CSV_COLUMNS:
        v = row.get(col, "")
        if v == "":
            out.append(None)
        elif col in _CSV_INT_COLS:
            out.append(int(float(v)))
        elif col in _CSV_FLOAT_COLS:
            out.append(float(v))
        else:
            out.append(v)
    return tuple(out)


def import_snapshot_csv(conn: sqlite3.Connection, csv_path: Path) -> int:
    conn.execute(_CREATE_SQL)
    with csv_path.open(newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        rows = [_coerce_csv_row(r) for r in reader]
    if not rows:
        return 0
    conn.executemany(
        "INSERT OR REPLACE INTO sleeper_projections VALUES ("
        + ",".join("?" * len(_CSV_COLUMNS)) + ")",
        rows,
    )
    conn.commit()
    return len(rows)


def import_all_snapshot_csvs(conn: sqlite3.Connection, snapshot_dir: Path) -> dict:
    results: dict[str, int] = {}
    for csv_path in sorted(snapshot_dir.glob("*.csv")):
        results[csv_path.name] = import_snapshot_csv(conn, csv_path)
    return results


def capture_one_position(
    conn: sqlite3.Connection,
    db_path: Path,
    position: str,
    season: int,
    season_type: str,
    force: bool,
) -> dict:
    today = dt.datetime.now(dt.timezone.utc).date().isoformat()

    if not force and already_fetched_today(conn, position):
        csv_path = export_snapshot_csv(conn, db_path, today, position, season)
        return {"position": position, "skipped": True, "csv_path": csv_path}

    payload = fetch_json(season, position, season_type)
    parsed = parse_rows(payload, position)
    if not parsed:
        raise RuntimeError(
            f"parsed zero rows from Sleeper projections for position={position} -- "
            "refusing to write an empty snapshot"
        )

    result = store_projections(conn, parsed, season, today)
    csv_path = export_snapshot_csv(conn, db_path, today, position, season)
    return {"position": position, "skipped": False, "csv_path": csv_path, **result}


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--db", type=Path, default=DEFAULT_DB_PATH)
    ap.add_argument("--season", type=int, default=dt.datetime.now(dt.timezone.utc).year)
    ap.add_argument("--season-type", type=str, default="regular")
    ap.add_argument(
        "--position", type=str, default=None, choices=POSITIONS,
        help="Capture only this one position. Default: all four (QB, RB, WR, TE).",
    )
    ap.add_argument("--force", action="store_true")
    ap.add_argument(
        "--import-csv-dir", type=Path, default=None,
        help="Restore sleeper_projections from every *.csv in this directory -- no network.",
    )
    args = ap.parse_args()

    if args.import_csv_dir is not None:
        conn = sqlite3.connect(args.db)
        try:
            results = import_all_snapshot_csvs(conn, args.import_csv_dir)
            total = sum(results.values())
            for name, n in results.items():
                print(f"  {name}: {n} rows")
            print(f"imported {total} rows from {len(results)} CSV(s) in {args.import_csv_dir}")
        finally:
            conn.close()
        return

    positions_to_run = [args.position] if args.position else POSITIONS

    conn = sqlite3.connect(args.db)
    conn.execute(_CREATE_SQL)
    conn.execute(_QUARANTINE_CREATE_SQL)
    try:
        summary = []
        for position in positions_to_run:
            r = capture_one_position(conn, args.db, position, args.season, args.season_type, args.force)
            summary.append(r)
            if r["skipped"]:
                print(f"[{position}] already fetched today (UTC); use --force to re-fetch")
                if r["csv_path"] is not None:
                    print(f"  CSV archive already present: {r['csv_path']}")
                continue
            print(
                f"[{position}] wrote {r['stored']} rows, quarantined={r['quarantined']}, "
                f"match_rate={r['match_rate']}"
            )
            if r["csv_path"] is None:
                print(f"  WARNING: no rows for today's date -- CSV archive NOT written")
            else:
                print(f"  wrote CSV archive: {r['csv_path']} ({r['stored']} rows)")

        print()
        print("summary:")
        for r in summary:
            print(f"  {r['position']:<4} stored={r.get('stored', '(skipped)')} "
                  f"quarantined={r.get('quarantined', '-')}")
    finally:
        conn.close()


if __name__ == "__main__":
    main()
