"""
Ingest MyFantasyLeague ADP into data/nfl.db (ADR-035).

WHAT THIS IS. MFL publishes aggregate average-draft-position data, free, no
login, documented endpoint:
    https://api.myfantasyleague.com/{year}/export?TYPE=adp&...&JSON=1
It returns MFL's OWN player ids, which join natively to `mfl_id` -- verified
this session against 10 sampled players (Ja'Marr Chase, Jahmyr Gibbs, Josh
Allen, ...), 232/232 (100%) resolved directly against `ff_playerids`. No name
matching is needed or used.

WHAT THIS IS NOT. This supersedes ADR-018's finding that FFC/Yahoo/ESPN ADP
were blocked or unattemptable -- MFL is a source that search missed -- but it
is a PROXY, never this league's ADP. Different population (whoever drafts on
MFL, largely dynasty/redraft hobbyists), different scoring defaults, and per
this pull, TINY sample: `totalDrafts` behind this snapshot was 50, and
individual players' `draftsSelectedIn` ranged 5-58. Stored under
`adp_source='mfl_proxy'`, never blended into or presented as 'league_adp'.

PER-PLATFORM SOURCE STAMPING IS A STATED RULE, NOT AN IMPLICIT COLUMN.
`adp_source` is not bookkeeping metadata -- drafters pick off their own
platform's displayed ranks, so ADP is a per-platform behavioural variable,
and different platforms MUST NEVER be averaged, merged, or blended into one
"consensus ADP" number. Every row this module writes carries exactly one
`adp_source` value. If a second ADP-bearing source is ever added (MFL
draft-results, a different mock aggregator, this league's own real ADP once
enough drafts exist), it gets its own distinct `adp_source` value and its
own rows in this same table -- never rewritten into `mfl_proxy`'s rows and
never combined with them into a single figure anywhere downstream. Any code
that computes a single ADP-like number by aggregating across more than one
`adp_source` value in this table is a bug, not a convenience feature.

CACHING. At most one fetch per calendar day: `main()` checks whether a row for
today's UTC date already exists before hitting the network, so re-running this
script (e.g. from a scheduled task) does not hammer the endpoint. `--force`
bypasses the check.

RATE LIMITING. A descriptive User-Agent identifies this project. On HTTP 429,
retries with exponential backoff (honouring `Retry-After` if present), capped
at a few attempts -- this is a small hobby endpoint, not a production API, and
repeated aggressive retries would be an inconsiderate way to use it.

WHY A SEPARATE TABLE, NOT THE EXISTING `rankings` TABLE. `rankings` already
carries `spread_sd`/`rank_best`/`rank_worst` for exactly this kind of
dispersion data (ADR-024), and CLAUDE.md's `ranking_source` enum names
`market_adp` for precisely this case. It was deliberately NOT reused here:
wiring a new source into the same table used by make_board.py/backtest.py
risks changing board/backtest behaviour as a side effect of an ingestion
task, which nobody asked for this session. `adp_snapshots` is the table name
CLAUDE.md's own core-tables sketch (SS4) already reserved for this. Per-row
format metadata (fcount, is_ppr, is_keeper, is_mock, cutoff) is preserved so a
future session can tell exactly what population and rules produced each
number -- required by ADR-024's "never a pre-blended point estimate" rule.

THE CSV IS THE CANONICAL ARCHIVE. THE DB IS A QUERYABLE CACHE OF IT. Every
run also writes a dated CSV to data/adp-snapshots/YYYY-MM-DD.csv (UTC date,
same date logic as the once-per-day cache check), one row per player,
mirroring the adp_snapshots columns exactly. This is not a convenience
export -- it exists because `data/nfl.db` is gitignored (too large for
GitHub) and adp_snapshots rows are the one thing in that DB that cannot be
re-fetched once a day has passed: a lost local file means a permanently
missing historical snapshot with no recovery path. The CSV under
data/adp-snapshots/ is deliberately NOT gitignored (see .gitignore) so it
gets committed and pushed as an off-machine backup. If the DB and a day's
CSV ever disagree, the CSV is authoritative and the DB should be considered
stale/corrupt for that date, not the other way around.
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
from typing import Dict, Optional

DEFAULT_DB_PATH = Path(__file__).resolve().parent.parent / "data" / "nfl.db"

_CSV_COLUMNS = [
    "adp_source", "mfl_id", "player_name", "position", "team", "rank",
    "average_pick", "min_pick", "max_pick", "drafts_selected_in",
    "draft_sel_pct", "fcount", "is_ppr", "is_keeper", "is_mock", "cutoff",
    "period", "total_drafts_in_sample", "mfl_timestamp", "retrieved_at",
    "ingested_at",
]

USER_AGENT = (
    "FantasyFootballBacktestProject/1.0 "
    "(personal non-commercial research project; contact via repo owner)"
)

ADP_SOURCE = "mfl_proxy"

_CREATE_SQL = """
CREATE TABLE IF NOT EXISTS adp_snapshots (
    adp_source TEXT NOT NULL,
    mfl_id TEXT NOT NULL,
    player_name TEXT,
    position TEXT,
    team TEXT,
    rank INTEGER,
    average_pick REAL,
    min_pick INTEGER,
    max_pick INTEGER,
    drafts_selected_in INTEGER,
    draft_sel_pct REAL,
    fcount INTEGER,
    is_ppr INTEGER,
    is_keeper INTEGER,
    is_mock INTEGER,
    cutoff INTEGER,
    period INTEGER,
    total_drafts_in_sample INTEGER,
    mfl_timestamp INTEGER,
    retrieved_at TEXT NOT NULL,
    ingested_at TEXT NOT NULL,
    PRIMARY KEY (adp_source, mfl_id, retrieved_at)
)
"""


def _build_url(period: int, fcount: int, is_ppr: int, is_keeper: int, is_mock: int, cutoff: int) -> str:
    return (
        f"https://api.myfantasyleague.com/{period}/export?TYPE=adp"
        f"&FCOUNT={fcount}&IS_PPR={is_ppr}&IS_KEEPER={is_keeper}&IS_MOCK={is_mock}"
        f"&CUTOFF={cutoff}&JSON=1"
    )


def fetch_adp(
    period: int = 2026,
    fcount: int = 10,
    is_ppr: int = 1,
    is_keeper: int = 0,
    is_mock: int = 0,
    cutoff: int = 10,
    max_retries: int = 4,
) -> dict:
    """GET the MFL ADP endpoint. Retries on 429 with exponential backoff,
    honouring Retry-After when the server sends one."""
    url = _build_url(period, fcount, is_ppr, is_keeper, is_mock, cutoff)
    req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    delay = 2.0
    for attempt in range(max_retries):
        try:
            with urllib.request.urlopen(req, timeout=20) as resp:
                return json.loads(resp.read())
        except urllib.error.HTTPError as e:
            if e.code == 429 and attempt < max_retries - 1:
                wait = float(e.headers.get("Retry-After", delay)) if e.headers else delay
                time.sleep(wait)
                delay *= 2
                continue
            raise
    raise RuntimeError("unreachable")  # pragma: no cover


def already_fetched_today(conn: sqlite3.Connection, adp_source: str = ADP_SOURCE) -> bool:
    today = dt.datetime.now(dt.timezone.utc).date().isoformat()
    row = conn.execute(
        "SELECT 1 FROM adp_snapshots WHERE adp_source=? AND substr(retrieved_at, 1, 10)=? LIMIT 1",
        (adp_source, today),
    ).fetchone()
    return row is not None


def _name_team_pos(conn: sqlite3.Connection, mfl_id: str) -> Dict[str, Optional[str]]:
    row = conn.execute(
        "SELECT name, position, team FROM ff_playerids WHERE mfl_id=?", (mfl_id,)
    ).fetchone()
    if row is None:
        return {"player_name": None, "position": None, "team": None}
    return {"player_name": row[0], "position": row[1], "team": row[2]}


def store_adp(
    conn: sqlite3.Connection,
    payload: dict,
    fcount: int, is_ppr: int, is_keeper: int, is_mock: int, cutoff: int, period: int,
) -> int:
    conn.execute(_CREATE_SQL)
    adp = payload["adp"]
    total_drafts = int(adp.get("totalDrafts", 0) or 0)
    mfl_ts = int(adp.get("timestamp", 0) or 0)
    now = dt.datetime.now(dt.timezone.utc).isoformat()

    rows = []
    for p in adp.get("player", []):
        mfl_id = str(p["id"])
        meta = _name_team_pos(conn, mfl_id)
        rows.append((
            ADP_SOURCE, mfl_id, meta["player_name"], meta["position"], meta["team"],
            int(p["rank"]), float(p["averagePick"]),
            int(p["minPick"]) if p.get("minPick") not in (None, "") else None,
            int(p["maxPick"]) if p.get("maxPick") not in (None, "") else None,
            int(p["draftsSelectedIn"]) if p.get("draftsSelectedIn") not in (None, "") else None,
            float(p["draftSelPct"]) if p.get("draftSelPct") not in (None, "") else None,
            fcount, is_ppr, is_keeper, is_mock, cutoff, period,
            total_drafts, mfl_ts, now, now,
        ))
    conn.executemany(
        "INSERT OR REPLACE INTO adp_snapshots VALUES (" + ",".join("?" * 21) + ")", rows
    )
    conn.commit()
    return len(rows)


def snapshot_dir_for_db(db_path: Path) -> Path:
    """CSV archive lives as a sibling of the DB's data/ dir, so it tracks
    whichever checkout/worktree the DB belongs to."""
    return db_path.resolve().parent / "adp-snapshots"


def export_snapshot_csv(
    conn: sqlite3.Connection,
    db_path: Path,
    date_str: str,
    adp_source: str = ADP_SOURCE,
) -> Optional[Path]:
    """Write data/adp-snapshots/{date_str}.csv from the adp_snapshots rows
    already in the DB for (adp_source, date_str). Returns the path written,
    or None if there are no matching rows (never writes an empty file --
    an absent snapshot must stay absent, not look like a zero-row 'capture').
    """
    rows = conn.execute(
        "SELECT " + ", ".join(_CSV_COLUMNS) + " FROM adp_snapshots "
        "WHERE adp_source=? AND substr(retrieved_at, 1, 10)=?",
        (adp_source, date_str),
    ).fetchall()
    if not rows:
        return None

    out_dir = snapshot_dir_for_db(db_path)
    out_dir.mkdir(parents=True, exist_ok=True)
    out_path = out_dir / f"{date_str}.csv"
    with out_path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(_CSV_COLUMNS)
        writer.writerows(rows)
    return out_path


_CSV_INT_COLS = {
    "rank", "min_pick", "max_pick", "drafts_selected_in", "fcount", "is_ppr",
    "is_keeper", "is_mock", "cutoff", "period", "total_drafts_in_sample", "mfl_timestamp",
}
_CSV_FLOAT_COLS = {"average_pick", "draft_sel_pct"}


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
    """The counterpart to `export_snapshot_csv` -- loads a committed
    data/adp-snapshots/YYYY-MM-DD.csv back into `adp_snapshots`, row for row,
    no re-derivation. This is the only way the point-in-time CSVs (each one a
    daily capture MFL's rolling aggregate makes impossible to reconstruct
    later, per this module's own docstring: "THE CSV IS THE CANONICAL
    ARCHIVE") can be restored into a rebuilt database; without it, a rebuild
    only ever has today's MFL pull, and every prior day's snapshot -- once
    the CSV can't be read back -- is effectively gone even though the file
    sits right there in the repo.

    Idempotent (INSERT OR REPLACE, same primary key
    `(adp_source, mfl_id, retrieved_at)` the live fetch path uses) and safe
    to call once per file on every rebuild.
    """
    conn.execute(_CREATE_SQL)
    with csv_path.open(newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        rows = [_coerce_csv_row(r) for r in reader]
    if not rows:
        return 0
    conn.executemany(
        "INSERT OR REPLACE INTO adp_snapshots VALUES (" + ",".join("?" * 21) + ")", rows
    )
    conn.commit()
    return len(rows)


def import_all_snapshot_csvs(conn: sqlite3.Connection, snapshot_dir: Path) -> dict:
    """Import every data/adp-snapshots/*.csv found in `snapshot_dir`, in
    filename (date) order. Returns {filename: rows_imported}."""
    results: dict[str, int] = {}
    for csv_path in sorted(snapshot_dir.glob("*.csv")):
        results[csv_path.name] = import_snapshot_csv(conn, csv_path)
    return results


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--db", type=Path, default=DEFAULT_DB_PATH)
    ap.add_argument("--period", type=int, default=2026)
    ap.add_argument("--fcount", type=int, default=10)
    ap.add_argument("--is-ppr", type=int, default=1)
    ap.add_argument("--is-keeper", type=int, default=0)
    ap.add_argument("--is-mock", type=int, default=0)
    ap.add_argument("--cutoff", type=int, default=10)
    ap.add_argument("--force", action="store_true", help="bypass the once-per-day cache check")
    ap.add_argument(
        "--import-csv-dir", type=Path, default=None,
        help="Instead of fetching from MFL, restore adp_snapshots from every "
             "*.csv in this directory (e.g. data/adp-snapshots/) -- no network.",
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

    conn = sqlite3.connect(args.db)
    conn.execute(_CREATE_SQL)
    try:
        today = dt.datetime.now(dt.timezone.utc).date().isoformat()
        if not args.force and already_fetched_today(conn):
            print("already fetched today (UTC); use --force to re-fetch")
            csv_path = export_snapshot_csv(conn, args.db, today)
            if csv_path is not None:
                print(f"CSV archive already present: {csv_path}")
            return
        payload = fetch_adp(
            args.period, args.fcount, args.is_ppr, args.is_keeper, args.is_mock, args.cutoff
        )
        n = store_adp(
            conn, payload, args.fcount, args.is_ppr, args.is_keeper, args.is_mock,
            args.cutoff, args.period,
        )
        total_drafts = payload["adp"].get("totalDrafts")
        print(f"wrote {n} rows, adp_source={ADP_SOURCE}, sample=totalDrafts={total_drafts}")
        if total_drafts and int(total_drafts) < 100:
            print(f"CAUTION: only {total_drafts} drafts behind this snapshot -- thin sample, "
                  f"do not weight heavily against fantasypros_ecr without measuring first")
        csv_path = export_snapshot_csv(conn, args.db, today)
        if csv_path is None:
            print("WARNING: no adp_snapshots rows found for today's date -- CSV archive NOT written")
        else:
            print(f"wrote CSV archive: {csv_path} ({n} rows) -- CSV is the canonical archive")
    finally:
        conn.close()


if __name__ == "__main__":
    main()
