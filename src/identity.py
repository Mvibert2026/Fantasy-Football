"""
Player identity resolution hub (ADR-036, Task B).

HUB IS mfl_id, NOT gsis_id -- measured, not assumed. Checked empirically this
session over the full 12,468-row `ff_playerids` crosswalk (already ingested,
src/ingest_reference.py, table `ff_playerids`, no re-fetch needed here):

    column          non-null    collision groups (one value -> >1 mfl_id)
    mfl_id          100.0%      0
    gsis_id          62.1%      10
    pfr_id            76.8%     16
    espn_id           65.3%     13
    sleeper_id         50.9%     6
    yahoo_id           44.0%     5
    fantasypros_id     38.3%     2
    sportradar_id      59.6%     5

mfl_id is the only column that is both complete and collision-free. Anything
built on gsis_id inherits a hole in a third of rows AND ten silent wrong joins.

'depth_chart' IS NOT A SEPARATE ID SPACE. depth_charts_weekly and
depth_charts_snapshots (src/ingest_reference.py) key players by gsis_id (and
carry espn_id), so a depth-chart row resolves through the gsis or espn spoke,
not through a column of its own. Listed as a source in the schema request for
completeness; there is no depth_chart_id to crosswalk.

COLLISIONS ARE EXCLUDED, NEVER GUESSED AT. A (source, source_id) pair that
maps to more than one mfl_id gets NO row in `player_ids` -- it goes to
`player_id_collisions` instead, and `resolve()` returns None for it. Picking a
winner (most recent, alphabetical, first-seen) would produce a confident wrong
join indistinguishable downstream from a correct one, which is exactly the
failure `mfl_id is NOT unique` guards already avoid one level up. Same
principle, applied at every spoke.

NAME MATCHING IS FALLBACK ONLY, NEVER AUTOMATIC. `name_dob_match_candidates()`
returns candidates for a HUMAN to confirm; nothing it returns is written to
`player_ids` automatically. `manually_confirm()` is the only way a
name-matched pair becomes resolvable, and it is stamped `method='manual'` so
the provenance is visible forever, not silently indistinguishable from a
direct crosswalk hit. As of this session it has zero consumers -- MFL ADP
(ADR-035) resolves against `ff_playerids.mfl_id` directly, needing no name
matching at all -- so it exists because the requested schema names the method,
not because anything calls it yet.
"""

from __future__ import annotations

import json
import re
import sqlite3
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Dict, List, Optional

_SUFFIX_RE = re.compile(r"\s+(jr|sr|ii|iii|iv|v)\.?$", re.IGNORECASE)
_PUNCT_RE = re.compile(r"[.'\-]")


def normalize_name(name: str) -> str:
    """Coverage-report matching only -- see coverage_report_for_board's
    docstring. Never used to populate player_ids; a wrong match here only
    mislabels a stat, not a join a downstream feature would trust."""
    n = _PUNCT_RE.sub("", name.strip().lower())
    n = _SUFFIX_RE.sub("", n)
    return " ".join(n.split())

DIRECT_CROSSWALK_SOURCES: Dict[str, str] = {
    "gsis": "gsis_id",
    "pfr": "pfr_id",
    "espn": "espn_id",
    "yahoo": "yahoo_id",
    "sleeper": "sleeper_id",
    "fantasypros": "fantasypros_id",
    "sportradar": "sportradar_id",
}

VALID_SOURCES = set(DIRECT_CROSSWALK_SOURCES) | {"depth_chart"}
VALID_METHODS = {"direct_crosswalk", "name_dob_match", "manual"}

_CREATE_SQL = [
    """
    CREATE TABLE IF NOT EXISTS players_canonical (
        mfl_id TEXT PRIMARY KEY,
        display_name TEXT,
        position TEXT,
        team TEXT,
        birthdate TEXT
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS player_ids (
        mfl_id TEXT NOT NULL REFERENCES players_canonical(mfl_id),
        source TEXT NOT NULL,
        source_id TEXT NOT NULL,
        confidence TEXT NOT NULL,
        method TEXT NOT NULL,
        resolved_at TEXT NOT NULL,
        PRIMARY KEY (source, source_id)
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS player_id_collisions (
        source TEXT NOT NULL,
        source_id TEXT NOT NULL,
        candidate_mfl_ids TEXT NOT NULL,
        note TEXT NOT NULL,
        PRIMARY KEY (source, source_id)
    )
    """,
]


def _table_exists(conn: sqlite3.Connection, name: str) -> bool:
    row = conn.execute(
        "SELECT 1 FROM sqlite_master WHERE type='table' AND name=?", (name,)
    ).fetchone()
    return row is not None


def build_identity_tables(conn: sqlite3.Connection) -> Dict[str, int]:
    """(Re)build players_canonical / player_ids / player_id_collisions from the
    already-ingested ff_playerids table. Idempotent: drops and rebuilds, same
    pattern as ingest_reference.py, so a stale row can never survive a re-run.
    """
    if not _table_exists(conn, "ff_playerids"):
        raise RuntimeError(
            "ff_playerids is not ingested. Run: python src/ingest_reference.py --only ff_playerids"
        )

    for stmt in ["DROP TABLE IF EXISTS players_canonical",
                 "DROP TABLE IF EXISTS player_ids",
                 "DROP TABLE IF EXISTS player_id_collisions"]:
        conn.execute(stmt)
    for stmt in _CREATE_SQL:
        conn.execute(stmt)

    rows = conn.execute(
        "SELECT mfl_id, name, position, team, birthdate, "
        + ", ".join(DIRECT_CROSSWALK_SOURCES.values())
        + " FROM ff_playerids"
    ).fetchall()

    now = datetime.now(timezone.utc).isoformat()
    canonical_rows = []
    by_source_value: Dict[str, Dict[str, List[str]]] = {s: {} for s in DIRECT_CROSSWALK_SOURCES}

    col_names = ["mfl_id", "name", "position", "team", "birthdate"] + list(
        DIRECT_CROSSWALK_SOURCES.values()
    )
    for row in rows:
        r = dict(zip(col_names, row))
        canonical_rows.append((r["mfl_id"], r["name"], r["position"], r["team"], r["birthdate"]))
        for source, col in DIRECT_CROSSWALK_SOURCES.items():
            val = r[col]
            if val is None:
                continue
            val = str(val)
            by_source_value[source].setdefault(val, []).append(r["mfl_id"])

    conn.executemany(
        "INSERT INTO players_canonical (mfl_id, display_name, position, team, birthdate) "
        "VALUES (?, ?, ?, ?, ?)",
        canonical_rows,
    )

    id_rows = []
    collision_rows = []
    for source, mapping in by_source_value.items():
        for source_id, mfl_ids in mapping.items():
            uniq = sorted(set(mfl_ids))
            if len(uniq) == 1:
                id_rows.append((uniq[0], source, source_id, "high", "direct_crosswalk", now))
            else:
                collision_rows.append((
                    source, source_id, json.dumps(uniq),
                    f"{source_id} maps to {len(uniq)} distinct mfl_id values in ff_playerids; "
                    f"excluded from player_ids, resolve() returns None",
                ))

    conn.executemany(
        "INSERT INTO player_ids (mfl_id, source, source_id, confidence, method, resolved_at) "
        "VALUES (?, ?, ?, ?, ?, ?)",
        id_rows,
    )
    conn.executemany(
        "INSERT INTO player_id_collisions (source, source_id, candidate_mfl_ids, note) "
        "VALUES (?, ?, ?, ?)",
        collision_rows,
    )
    conn.commit()

    return {
        "canonical_players": len(canonical_rows),
        "resolvable_ids": len(id_rows),
        "collisions_excluded": len(collision_rows),
    }


def resolve(conn: sqlite3.Connection, source: str, source_id: str) -> Optional[str]:
    """mfl_id for (source, source_id), or None if unresolvable OR colliding.

    Never guesses. A caller getting None must treat the row as unjoinable, not
    retry with a heuristic -- that is the whole point of excluding collisions
    up front rather than picking a winner here.
    """
    if source not in VALID_SOURCES:
        raise ValueError(f"unknown source {source!r}, expected one of {sorted(VALID_SOURCES)}")
    row = conn.execute(
        "SELECT mfl_id FROM player_ids WHERE source=? AND source_id=?",
        (source, str(source_id)),
    ).fetchone()
    return row[0] if row else None


def coverage_report(conn: sqlite3.Connection) -> Dict[str, dict]:
    """Per-source coverage over the FULL crosswalk (all 12,468 mfl_id rows).

    Reports the count AFTER collision exclusion, which is the number that
    actually resolves through resolve() -- not the raw non-null count quoted
    in this module's docstring, which is slightly higher because it includes
    the handful of mfl_id rows whose source_id collided and was dropped.
    """
    total = conn.execute("SELECT COUNT(*) FROM players_canonical").fetchone()[0]
    out = {}
    for source in DIRECT_CROSSWALK_SOURCES:
        n = conn.execute(
            "SELECT COUNT(DISTINCT mfl_id) FROM player_ids WHERE source=?", (source,)
        ).fetchone()[0]
        collisions = conn.execute(
            "SELECT COUNT(*) FROM player_id_collisions WHERE source=?", (source,)
        ).fetchone()[0]
        out[source] = {
            "resolvable_mfl_ids": n,
            "coverage": round(n / total, 4) if total else None,
            "collisions_excluded": collisions,
        }
    out["depth_chart"] = {
        "resolvable_mfl_ids": None,
        "coverage": None,
        "collisions_excluded": None,
        "note": "not a distinct ID space -- resolves via the gsis or espn spoke",
    }
    return out


def coverage_report_for_board(
    conn: sqlite3.Connection, season: int = 2026
) -> Dict[str, object]:
    """Coverage restricted to the players actually on the board -- the number
    that matters for feature-pipeline planning, not the global crosswalk rate.

    Board players are identified by NAME ONLY (rankings has no external ID), so
    this first does a lowercase exact match against ff_playerids.merge_name.
    That match itself is imperfect and its rate is reported alongside the
    per-source figures -- an unmatched board player shows as 0% coverage
    because the NAME JOIN failed, not because the source lacks them, and
    conflating those two would overstate how broken the crosswalk is.
    """
    board_names = [
        r[0] for r in conn.execute(
            "SELECT DISTINCT player_name FROM rankings "
            "WHERE source='fantasypros_ecr' AND season=?", (season,)
        ).fetchall()
    ]
    if not board_names:
        raise ValueError(f"no fantasypros_ecr rankings for season {season}")

    merge_to_mfl: Dict[str, str] = {}
    for mfl_id, name in conn.execute("SELECT mfl_id, display_name FROM players_canonical"):
        if name:
            merge_to_mfl.setdefault(normalize_name(name), mfl_id)

    matched_mfl_ids = []
    unmatched = []
    for name in board_names:
        mfl_id = merge_to_mfl.get(normalize_name(name))
        if mfl_id:
            matched_mfl_ids.append(mfl_id)
        else:
            unmatched.append(name)

    out: Dict[str, object] = {
        "board_players": len(board_names),
        "name_matched_to_mfl_id": len(matched_mfl_ids),
        "name_match_rate": round(len(matched_mfl_ids) / len(board_names), 4),
        "unmatched_names_sample": unmatched[:15],
        "per_source": {},
    }
    if not matched_mfl_ids:
        return out

    placeholders = ",".join("?" for _ in matched_mfl_ids)
    for source in DIRECT_CROSSWALK_SOURCES:
        n = conn.execute(
            f"SELECT COUNT(DISTINCT mfl_id) FROM player_ids "
            f"WHERE source=? AND mfl_id IN ({placeholders})",
            (source, *matched_mfl_ids),
        ).fetchone()[0]
        out["per_source"][source] = {
            "resolvable_of_matched": n,
            "coverage_of_matched_board_players": round(n / len(matched_mfl_ids), 4),
        }
    return out


def resolve_name(
    conn: sqlite3.Connection, player_name_raw: str, position: Optional[str] = None
) -> Optional[str]:
    """mfl_id for a raw player name, via the SAME suffix/punctuation
    normalization as coverage_report_for_board() (measured there at 98.5% on
    the live board). Returns None on zero matches OR on more than one
    (ambiguous) -- never guesses, same invariant as resolve(). Used by
    ingest_mock_drafts.py to resolve player_name_raw -- unmatched or
    ambiguous names must go to quarantine, not a best-effort pick.
    """
    key = normalize_name(player_name_raw)
    rows = conn.execute("SELECT mfl_id, display_name, position FROM players_canonical").fetchall()
    matches = [r for r in rows if r[1] and normalize_name(r[1]) == key]
    if position:
        matches = [r for r in matches if r[2] == position]
    if len(matches) != 1:
        return None
    return matches[0][0]


@dataclass
class NameMatchCandidate:
    mfl_id: str
    display_name: str
    position: Optional[str]
    team: Optional[str]
    match_basis: str


def name_dob_match_candidates(
    conn: sqlite3.Connection,
    name: str,
    position: Optional[str] = None,
) -> List[NameMatchCandidate]:
    """Fallback candidates for a human to confirm. NEVER inserted into
    player_ids automatically -- pass a chosen candidate's mfl_id to
    manually_confirm() after a human has actually looked.

    Birthdate narrowing is not implemented (no caller currently supplies a
    birthdate to match against; the schema names the method so this exists,
    but adding DOB logic with no test case to verify it against would be
    exactly the over-engineering CLAUDE.md's gates flag). Position is used as
    a coarse filter when supplied.
    """
    key = name.strip().lower()
    q = "SELECT mfl_id, display_name, position, team FROM players_canonical WHERE lower(display_name)=?"
    params: list = [key]
    if position:
        q += " AND position=?"
        params.append(position)
    rows = conn.execute(q, params).fetchall()
    return [
        NameMatchCandidate(mfl_id=r[0], display_name=r[1], position=r[2], team=r[3],
                            match_basis="exact_lowercase_name" + ("+position" if position else ""))
        for r in rows
    ]


def manually_confirm(
    conn: sqlite3.Connection, mfl_id: str, source: str, source_id: str, note: str
) -> None:
    """Record a human-confirmed (source, source_id) -> mfl_id pair.
    method='manual' so it is never mistaken for an automated crosswalk hit."""
    if source not in VALID_SOURCES:
        raise ValueError(f"unknown source {source!r}, expected one of {sorted(VALID_SOURCES)}")
    conn.execute(
        "INSERT OR REPLACE INTO player_ids "
        "(mfl_id, source, source_id, confidence, method, resolved_at) VALUES (?, ?, ?, ?, ?, ?)",
        (mfl_id, source, str(source_id), "manual", "manual", datetime.now(timezone.utc).isoformat()),
    )
    conn.commit()


def main() -> None:
    import db as dbmod

    conn = dbmod.connect()
    try:
        report = build_identity_tables(conn)
        print("build:", report)
        print()
        print("coverage (full crosswalk, 12,468 players):")
        for source, stats in coverage_report(conn).items():
            print(f"  {source:<12} {stats}")
        print()
        print("coverage restricted to board_2026:")
        board = coverage_report_for_board(conn, season=2026)
        print(f"  matched {board['name_matched_to_mfl_id']}/{board['board_players']} "
              f"by name ({board['name_match_rate']:.1%})")
        for source, stats in board["per_source"].items():
            print(f"  {source:<12} {stats}")
        if board["unmatched_names_sample"]:
            print(f"  unmatched sample: {board['unmatched_names_sample']}")
    finally:
        conn.close()


if __name__ == "__main__":
    main()
