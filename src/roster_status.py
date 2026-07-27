"""T6 -- interim retired/inactive assertion, built on an EXISTING column,
no new ingestion.

Full nflverse roster-status ingestion (active / IR / practice-squad /
not-rostered, per-week) is explicitly out of scope for this round -- it
needs new DB writes, which this session is not doing (parallel session is
doing DB-writing work on the half-PPR ECR swap; this round's changes are
src/+tests/ only). See the session's report for the schema addition
data-ops would need to build the real thing.

What this module does instead: reads `contracts.is_active`, a column that
ALREADY EXISTS in nfl.db from an earlier ingest. It is a proxy, not a roster
status field -- state that plainly every time it's surfaced. `is_active`
means "this specific contract row is the player's current contract," not
"this player is on an active NFL roster this week." But a player with NO
is_active=1 row anywhere in their contract history has no currently-active
contract on file, which is a real signal that catches the clean case: a
long-retired player's entire contract history reads is_active=0 (verified
against Tom Brady, gsis_id 00-0019596, in tests/test_roster_status.py).

What this does NOT catch: a player between contracts but still actively
rostered (rare), in-season trades, or IR/practice-squad status at all --
those need the real roster-status ingest (T6's non-interim half).
"""

from __future__ import annotations

import sqlite3
from typing import Iterable, List, Optional

ACTIVE = "active"
NO_ACTIVE_CONTRACT = "no_active_contract_on_file"
UNKNOWN = "unknown_no_contract_data"


def contract_status(conn: sqlite3.Connection, gsis_id: Optional[str]) -> str:
    """ACTIVE if any contract row for this gsis_id has is_active=1;
    NO_ACTIVE_CONTRACT if the player has contract rows but none active (the
    Brady/retired shape); UNKNOWN if the player has no contract rows at all
    on file (rookies, undrafted players -- an honest 'we don't know', never
    inferred as retired)."""
    if not gsis_id:
        return UNKNOWN
    rows = conn.execute(
        "SELECT is_active FROM contracts WHERE gsis_id = ?", (gsis_id,)
    ).fetchall()
    if not rows:
        return UNKNOWN
    if any(r[0] for r in rows):
        return ACTIVE
    return NO_ACTIVE_CONTRACT


def attach_roster_status(
    rows: Iterable[dict], conn: sqlite3.Connection, gsis_key: str = "player_id_gsis"
) -> List[dict]:
    """Adds a 'roster_status' key to each dict in rows (mutates and returns
    the same list), looked up by the gsis id under `gsis_key`."""
    out = []
    for r in rows:
        r = dict(r)
        r["roster_status"] = contract_status(conn, r.get(gsis_key))
        out.append(r)
    return out
