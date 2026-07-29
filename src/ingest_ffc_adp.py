"""
Ingest Fantasy Football Calculator (FFC) Half-PPR, 10-team ADP into
data/nfl.db (thread: 2026-07-29 data-ops session; FR-023; ADR pending).

WHY THIS EXISTS. The daily capture (`src/ingest_mfl_adp.py`) has been running
against MyFantasyLeague with `IS_PPR=1` (full PPR) because MFL's `IS_PPR` flag
is BINARY (0/1/-1) -- it has no half-PPR option. Westwood, the primary league,
is half-PPR. Full-PPR ADP is receiver-forward relative to half-PPR (an extra
0.5 pt/reception pulls WRs up disproportionately), so `mfl_proxy` has been a
systematically biased proxy for the league this project actually serves.

FFC publishes Half-PPR ADP broken out by team size, including 10-team --
an exact match: https://fantasyfootballcalculator.com/adp/half-ppr/10-team/all/{year}

AUTHORISATION. FFC was recorded BLOCKED in
`docs/research/source-audit-2026-07.md` (ToS unretrievable -> conservative
default). The founder contacted FFC directly on 2026-07-29 and reported no
restrictions on use ("we hve no blocks from FFC, we can use as needed"),
recorded in `docs/pm/MEMORY.md` SS4 and `docs/founder-requests/FR-023-*`.
This supersedes the conservative default for recurring use, not just a
one-time historical pull (that distinction is what D-021 did NOT cover).
Verified independently this session:
  - `robots.txt` disallows `/api/`, `/ajax/`, `/ajax-v2/`, `/import/`,
    `/adp/csv/`, `/draft/`, `/rate-my-team/results/`, `/rankings/custom/`.
    The HTML page this module fetches, `/adp/<format>/<teams>-team/all/<year>`,
    is NOT in that list.
  - The `/adp/csv/` path is explicitly avoided; this module parses the
    server-rendered HTML table instead, never that disallowed endpoint.
Standing conditions that still bind (not lifted): private single-user use
only; rate-limit and cache (one request per calendar day per format/team
combination, descriptive User-Agent, backoff on 429); never blend with
`mfl_proxy` or any other `adp_source`.

WHAT THIS IS. A same-day, dated ADP snapshot scraped from FFC's rendered
HTML ADP table for half-PPR, 10-team leagues. Stored under
`adp_source='ffc_half_ppr_10team'` -- distinct from `mfl_proxy`, never
overwritten into it and never averaged with it. CLAUDE.md SS4's
`ranking_source` enum and this project's stated never-blend rule
(`src/ingest_mfl_adp.py` docstring) apply identically here: a second
ADP-bearing source gets its own `adp_source` value and its own rows, full
stop.

IDENTITY RESOLUTION. FFC's page carries only a player's display name (plus
an internal FFC numeric id used purely for their own graph-embed JS, not a
crosswalk id this project has anywhere). Resolution goes through
`identity.resolve_name()` (name + position, same normalization already used
by `ingest_mock_drafts.py`, measured elsewhere at ~98.5% on the live board).
A name that does not resolve -- or resolves ambiguously -- goes to
`ffc_adp_quarantine` with a reason. NEVER a fuzzy-matched guess.

HISTORICAL DATA. FFC's ADP page also serves prior seasons
(.../adp/half-ppr/10-team/all/{year}). This module can pull a single past
season on request (`--period`), but treats that pull as a RETROSPECTIVE
AGGREGATE, not a preseason snapshot -- FFC does not expose an as-of date for
historical years, and there is no way to confirm the sample was drafted
before that season's Week 1 rather than accumulated across the whole year
(including in-season and post-season mock activity). Rows from a --period
other than the current season are stamped `is_retrospective_aggregate=1` in
the CSV/DB so nothing downstream mistakes them for a real preseason board --
using one as a preseason board would be exactly the look-ahead bias
CLAUDE.md SS6.1 describes. Only the CURRENT season's daily pull
(`is_retrospective_aggregate=0`) is a genuine point-in-time capture.

CACHING / RATE LIMITING. At most one fetch per calendar day per (format,
teams, period): `already_fetched_today()` checks before hitting the network.
`--force` bypasses it. Descriptive User-Agent, single GET, no retries beyond
a small backoff on HTTP 429 honouring Retry-After -- same posture as
`src/ingest_mfl_adp.py`.

CSV IS THE CANONICAL ARCHIVE, SAME AS MFL's MODULE. `data/nfl.db` is
gitignored; the dated CSV under `data/adp-snapshots-ffc/` is what survives
and is committed. A distinct directory from `data/adp-snapshots/` (MFL) was
chosen deliberately -- mixing two sources' dated CSVs in one directory would
make `YYYY-MM-DD.csv` ambiguous between MFL full-PPR and FFC half-PPR rows
for the same date; a source-specific directory keeps the filename
unambiguous without inventing a new naming scheme. `--import-csv-dir`
restores CSVs back into a rebuilt DB, mirroring `ingest_mfl_adp.py` exactly
-- the earlier gap (export-only for days) is not being reintroduced here.
"""

from __future__ import annotations

import argparse
import csv
import datetime as dt
import html as html_lib
import re
import sqlite3
import time
import urllib.error
import urllib.request
from pathlib import Path
from typing import List, Optional

import identity

DEFAULT_DB_PATH = Path(__file__).resolve().parent.parent / "data" / "nfl.db"

ADP_SOURCE = "ffc_half_ppr_10team"
FORMAT_SLUG = "half-ppr"
TEAMS = 10

USER_AGENT = (
    "FantasyFootballBacktestProject/1.0 "
    "(personal non-commercial research project; contact via repo owner)"
)

_CSV_COLUMNS = [
    "adp_source", "ffc_player_id", "mfl_id", "player_name", "position", "team",
    "bye", "rank", "average_pick", "std_dev", "high_pick", "low_pick",
    "times_drafted", "total_drafts_in_sample", "sample_window", "period",
    "teams", "format", "is_retrospective_aggregate", "as_of_date",
    "retrieved_at", "ingested_at",
]

_CREATE_SQL = """
CREATE TABLE IF NOT EXISTS ffc_adp_snapshots (
    adp_source TEXT NOT NULL,
    ffc_player_id TEXT,
    mfl_id TEXT,
    player_name TEXT,
    position TEXT,
    team TEXT,
    bye INTEGER,
    rank INTEGER,
    average_pick REAL,
    std_dev REAL,
    high_pick TEXT,
    low_pick TEXT,
    times_drafted INTEGER,
    total_drafts_in_sample INTEGER,
    sample_window TEXT,
    period INTEGER NOT NULL,
    teams INTEGER NOT NULL,
    format TEXT NOT NULL,
    is_retrospective_aggregate INTEGER NOT NULL,
    as_of_date TEXT NOT NULL,
    retrieved_at TEXT NOT NULL,
    ingested_at TEXT NOT NULL,
    PRIMARY KEY (adp_source, player_name, position, retrieved_at)
)
"""

_QUARANTINE_CREATE_SQL = """
CREATE TABLE IF NOT EXISTS ffc_adp_quarantine (
    adp_source TEXT NOT NULL,
    player_name_raw TEXT NOT NULL,
    position TEXT,
    team TEXT,
    reason TEXT NOT NULL,
    retrieved_at TEXT NOT NULL,
    quarantined_at TEXT NOT NULL,
    PRIMARY KEY (adp_source, player_name_raw, position, retrieved_at)
)
"""

_ROW_RE = re.compile(r"<tr class='(\w+)'>(.*?)</tr>", re.S)
_NAME_RE = re.compile(r'href="/players/[^"]*">([^<]+)</a>', re.S)
_TD_RE = re.compile(r"<td[^>]*>(.*?)</td>", re.S)
_FFC_ID_RE = re.compile(r"updatePlayer\((\d+),")


def _build_url(period: int, teams: int = TEAMS, fmt: str = FORMAT_SLUG) -> str:
    return f"https://fantasyfootballcalculator.com/adp/{fmt}/{teams}-team/all/{period}"


def fetch_html(period: int, teams: int = TEAMS, fmt: str = FORMAT_SLUG, max_retries: int = 4) -> str:
    """GET the FFC ADP HTML page. Retries on 429 with exponential backoff,
    honouring Retry-After when sent. Never touches /adp/csv/ or any other
    robots-disallowed path."""
    url = _build_url(period, teams, fmt)
    req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    delay = 2.0
    for attempt in range(max_retries):
        try:
            with urllib.request.urlopen(req, timeout=20) as resp:
                return resp.read().decode("utf-8", errors="replace")
        except urllib.error.HTTPError as e:
            if e.code == 429 and attempt < max_retries - 1:
                wait = float(e.headers.get("Retry-After", delay)) if e.headers else delay
                time.sleep(wait)
                delay *= 2
                continue
            raise
    raise RuntimeError("unreachable")  # pragma: no cover


def _clean(cell: str) -> str:
    return html_lib.unescape(re.sub(r"<[^>]+>", "", cell)).strip()


def parse_sample_window(page_html: str) -> tuple:
    """Returns (total_drafts, window_text) from the 'Data from N mock drafts
    between DATE1 and DATE2' sentence. (None, None) if not found -- never
    fabricated."""
    m = re.search(
        r"Data from ([\d,]+) .*?mock drafts.*?between (.*?) and\s*([^.<]*?)\.",
        page_html, re.S,
    )
    if not m:
        return None, None
    total = int(m.group(1).replace(",", ""))
    window = f"{m.group(2).strip()} to {m.group(3).strip()}"
    return total, window


def parse_adp_table(page_html: str) -> List[dict]:
    """Parses the server-rendered ADP table. Returns one dict per row with raw
    (unresolved) fields -- identity resolution happens separately in
    store_adp() so parsing stays independent of the DB/identity layer and is
    directly unit-testable against a saved HTML fixture."""
    table_start = page_html.find('<table class="table adp')
    if table_start == -1:
        return []
    table_end = page_html.find("</table>", table_start)
    table_html = page_html[table_start:table_end]

    out = []
    for pos_class, body in _ROW_RE.findall(table_html):
        cells = [_clean(c) for c in _TD_RE.findall(body)]
        name_m = _NAME_RE.search(body)
        ffc_id_m = _FFC_ID_RE.search(body)
        if not cells or not name_m:
            continue
        # cells: [rank, name(dup, has <a> so cleaned text == name), pos, team,
        #         bye, overall, std_dev, high, low, times_drafted, <graph td>]
        # `bye` is only present for skill positions -- DST rows have one fewer
        # cell. Detect by length rather than assuming a fixed layout.
        try:
            rank = int(cells[0])
        except (ValueError, IndexError):
            continue
        name = html_lib.unescape(name_m.group(1)).strip()
        # locate position/team by scanning cells after the name for known
        # tokens rather than a fixed index, since bye is sometimes absent
        remaining = cells[2:]
        position = remaining[0] if remaining else pos_class
        team = remaining[1] if len(remaining) > 1 else None
        numeric_tail = remaining[2:] if len(remaining) > 2 else []
        # numeric_tail is either [bye, overall, std_dev, high, low, times] (6)
        # or [overall, std_dev, high, low, times] (5, no bye e.g. DST/K rows)
        bye = overall = std_dev = high = low = times = None
        if len(numeric_tail) >= 6:
            bye, overall, std_dev, high, low, times = numeric_tail[:6]
        elif len(numeric_tail) == 5:
            overall, std_dev, high, low, times = numeric_tail[:5]

        def _f(v):
            try:
                return float(v)
            except (TypeError, ValueError):
                return None

        def _i(v):
            try:
                return int(v)
            except (TypeError, ValueError):
                return None

        out.append({
            "rank": rank,
            "player_name": name,
            "position": position or pos_class,
            "team": team or None,
            "bye": _i(bye),
            "average_pick": _f(overall),
            "std_dev": _f(std_dev),
            "high_pick": high or None,
            "low_pick": low or None,
            "times_drafted": _i(times),
            "ffc_player_id": ffc_id_m.group(1) if ffc_id_m else None,
        })
    return out


def already_fetched_today(
    conn: sqlite3.Connection, adp_source: str = ADP_SOURCE, period: Optional[int] = None
) -> bool:
    today = dt.datetime.now(dt.timezone.utc).date().isoformat()
    q = "SELECT 1 FROM ffc_adp_snapshots WHERE adp_source=? AND substr(retrieved_at, 1, 10)=?"
    params: list = [adp_source, today]
    if period is not None:
        q += " AND period=?"
        params.append(period)
    row = conn.execute(q, params).fetchone()
    return row is not None


def store_adp(
    conn: sqlite3.Connection,
    parsed_rows: List[dict],
    period: int,
    teams: int,
    fmt: str,
    is_retrospective_aggregate: bool,
    as_of_date: str,
    total_drafts_in_sample: Optional[int],
    sample_window: Optional[str],
) -> dict:
    """Writes resolved rows to ffc_adp_snapshots and unresolved rows to
    ffc_adp_quarantine. Returns counts. Never guesses a mfl_id -- an
    ambiguous or zero-match name is quarantined with a reason, never picked."""
    conn.execute(_CREATE_SQL)
    conn.execute(_QUARANTINE_CREATE_SQL)

    # identity.resolve_name() needs players_canonical; build it if absent.
    has_canonical = conn.execute(
        "SELECT 1 FROM sqlite_master WHERE type='table' AND name='players_canonical'"
    ).fetchone()
    if not has_canonical:
        identity.build_identity_tables(conn)

    now = dt.datetime.now(dt.timezone.utc).isoformat()
    stored_rows = []
    quarantine_rows = []

    for r in parsed_rows:
        mfl_id = identity.resolve_name(conn, r["player_name"], r["position"])
        if mfl_id is None:
            # resolve_name() matches on identity.normalize_name() (suffix/punct
            # stripped), not exact lowercase -- name_dob_match_candidates() uses
            # exact lowercase and can undercount, so replicate resolve_name's own
            # matching to report an accurate candidate count for the reason.
            key = identity.normalize_name(r["player_name"])
            canon_rows = conn.execute(
                "SELECT mfl_id, display_name, position FROM players_canonical"
            ).fetchall()
            matches = [
                row for row in canon_rows
                if row[1] and identity.normalize_name(row[1]) == key
                and (r["position"] is None or row[2] == r["position"])
            ]
            reason = (
                "no_name_match" if not matches else
                f"ambiguous_name_match:{len(matches)}_candidates"
            )
            quarantine_rows.append((
                ADP_SOURCE, r["player_name"], r["position"], r["team"], reason, now, now,
            ))
            continue
        stored_rows.append((
            ADP_SOURCE, r["ffc_player_id"], mfl_id, r["player_name"], r["position"], r["team"],
            r["bye"], r["rank"], r["average_pick"], r["std_dev"], r["high_pick"], r["low_pick"],
            r["times_drafted"], total_drafts_in_sample, sample_window, period, teams, fmt,
            int(is_retrospective_aggregate), as_of_date, now, now,
        ))

    conn.executemany(
        "INSERT OR REPLACE INTO ffc_adp_snapshots VALUES (" + ",".join("?" * 22) + ")",
        stored_rows,
    )
    conn.executemany(
        "INSERT OR REPLACE INTO ffc_adp_quarantine VALUES (?,?,?,?,?,?,?)",
        quarantine_rows,
    )
    conn.commit()
    return {
        "stored": len(stored_rows),
        "quarantined": len(quarantine_rows),
        "match_rate": round(len(stored_rows) / len(parsed_rows), 4) if parsed_rows else None,
    }


def snapshot_dir_for_db(db_path: Path) -> Path:
    """Sibling of data/adp-snapshots/ (MFL), deliberately separate so a
    filename never has to disambiguate which source it came from."""
    return db_path.resolve().parent / "adp-snapshots-ffc"


def export_snapshot_csv(
    conn: sqlite3.Connection,
    db_path: Path,
    date_str: str,
    period: int,
    adp_source: str = ADP_SOURCE,
) -> Optional[Path]:
    rows = conn.execute(
        "SELECT " + ", ".join(_CSV_COLUMNS) + " FROM ffc_adp_snapshots "
        "WHERE adp_source=? AND period=? AND substr(retrieved_at, 1, 10)=?",
        (adp_source, period, date_str),
    ).fetchall()
    if not rows:
        return None
    out_dir = snapshot_dir_for_db(db_path)
    out_dir.mkdir(parents=True, exist_ok=True)
    suffix = f"{date_str}_period{period}" if period != dt.datetime.now(dt.timezone.utc).year else date_str
    out_path = out_dir / f"{suffix}.csv"
    with out_path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(_CSV_COLUMNS)
        writer.writerows(rows)
    return out_path


_CSV_INT_COLS = {
    "bye", "rank", "times_drafted", "total_drafts_in_sample", "period", "teams",
    "is_retrospective_aggregate",
}
_CSV_FLOAT_COLS = {"average_pick", "std_dev"}


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
    """Counterpart to export_snapshot_csv -- restores a committed CSV back
    into ffc_adp_snapshots. Same round-trip guarantee as ingest_mfl_adp.py."""
    conn.execute(_CREATE_SQL)
    with csv_path.open(newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        rows = [_coerce_csv_row(r) for r in reader]
    if not rows:
        return 0
    conn.executemany(
        "INSERT OR REPLACE INTO ffc_adp_snapshots VALUES (" + ",".join("?" * 22) + ")", rows
    )
    conn.commit()
    return len(rows)


def import_all_snapshot_csvs(conn: sqlite3.Connection, snapshot_dir: Path) -> dict:
    results: dict[str, int] = {}
    for csv_path in sorted(snapshot_dir.glob("*.csv")):
        results[csv_path.name] = import_snapshot_csv(conn, csv_path)
    return results


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--db", type=Path, default=DEFAULT_DB_PATH)
    ap.add_argument("--period", type=int, default=dt.datetime.now(dt.timezone.utc).year)
    ap.add_argument("--teams", type=int, default=TEAMS)
    ap.add_argument("--format", type=str, default=FORMAT_SLUG)
    ap.add_argument("--force", action="store_true")
    ap.add_argument(
        "--import-csv-dir", type=Path, default=None,
        help="Restore ffc_adp_snapshots from every *.csv in this directory -- no network.",
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
    conn.execute(_QUARANTINE_CREATE_SQL)
    try:
        today = dt.datetime.now(dt.timezone.utc).date().isoformat()
        current_year = dt.datetime.now(dt.timezone.utc).year
        is_retro = args.period != current_year
        if not args.force and already_fetched_today(conn, period=args.period):
            print("already fetched today (UTC) for this period; use --force to re-fetch")
            csv_path = export_snapshot_csv(conn, args.db, today, args.period)
            if csv_path is not None:
                print(f"CSV archive already present: {csv_path}")
            return

        page_html = fetch_html(args.period, args.teams, args.format)
        parsed = parse_adp_table(page_html)
        total_drafts, window = parse_sample_window(page_html)

        if not parsed:
            raise RuntimeError("parsed zero rows from FFC ADP page -- refusing to write an empty snapshot")

        result = store_adp(
            conn, parsed, args.period, args.teams, args.format, is_retro, today,
            total_drafts, window,
        )
        print(
            f"wrote {result['stored']} rows, adp_source={ADP_SOURCE}, "
            f"quarantined={result['quarantined']}, match_rate={result['match_rate']}, "
            f"sample=totalDrafts={total_drafts}, window={window}, "
            f"is_retrospective_aggregate={is_retro}"
        )
        if is_retro:
            print(
                "NOTE: this pull is for a PAST season and FFC exposes no as-of date for it -- "
                "treated as a RETROSPECTIVE AGGREGATE, not a preseason snapshot. Do not use as a "
                "preseason board (CLAUDE.md SS6.1 look-ahead bias)."
            )
        if total_drafts and total_drafts < 100:
            print(f"CAUTION: only {total_drafts} drafts behind this snapshot -- thin sample")

        csv_path = export_snapshot_csv(conn, args.db, today, args.period)
        if csv_path is None:
            print("WARNING: no ffc_adp_snapshots rows found for today's date -- CSV archive NOT written")
        else:
            print(f"wrote CSV archive: {csv_path} ({result['stored']} rows)")
    finally:
        conn.close()


if __name__ == "__main__":
    main()
