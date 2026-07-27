"""T6 -- retired / IR / practice-squad assertion (interim, no new ingestion).

Full nflverse roster-status ingestion (active/IR/PS/not-rostered) is out of
scope for this pass -- it needs new DB writes, which this round is
deliberately not doing (see this session's report). What DOES already exist
in nfl.db without any new ingestion is `contracts.is_active`: a boolean per
contract row, already populated by an earlier ingest. It is NOT a roster
status field (it means "this specific contract record is the player's
current one," not "this player is on an active NFL roster this week") --
but a player with ZERO is_active=1 rows across their entire contract history
has no currently-active contract on file, which is a real (if imperfect)
signal that catches the clearest case: a long-retired player (Tom Brady,
gsis_id 00-0019596) shows is_active=0 on every one of his ~9 historical
contract rows, the same shape a released/inactive player would show.

This is pinned as a PROXY, explicitly labeled as such in roster_status.py's
docstring and in the board field name, not a definitive roster-status
signal. Written before src/roster_status.py exists.
"""

import sqlite3
from pathlib import Path

import pytest

import roster_status as rs

DB_PATH = Path(__file__).resolve().parents[1] / "data" / "nfl.db"


def _conn_with_contracts(rows):
    conn = sqlite3.connect(":memory:")
    conn.row_factory = sqlite3.Row
    conn.execute("CREATE TABLE contracts (gsis_id TEXT, is_active INTEGER)")
    conn.executemany("INSERT INTO contracts VALUES (?, ?)", rows)
    conn.commit()
    return conn


class TestContractStatus:
    def test_player_with_an_active_contract_row_is_active(self):
        conn = _conn_with_contracts([("00-1", 0), ("00-1", 0), ("00-1", 1)])
        assert rs.contract_status(conn, "00-1") == "active"

    def test_player_with_only_inactive_rows_has_no_active_contract(self):
        # The Brady shape: every historical contract row is_active=0.
        conn = _conn_with_contracts([("00-2", 0), ("00-2", 0), ("00-2", 0)])
        assert rs.contract_status(conn, "00-2") == "no_active_contract_on_file"

    def test_player_absent_from_contracts_entirely_is_unknown(self):
        # Rookies / undrafted players may have no contract row at all yet --
        # this is an honest "we don't know," never inferred as retired.
        conn = _conn_with_contracts([("00-1", 1)])
        assert rs.contract_status(conn, "00-99-not-present") == "unknown_no_contract_data"

    def test_none_gsis_id_is_unknown_not_a_crash(self):
        conn = _conn_with_contracts([("00-1", 1)])
        assert rs.contract_status(conn, None) == "unknown_no_contract_data"


class TestFlagBoardRows:
    def test_flags_are_attached_by_gsis_id(self):
        conn = _conn_with_contracts([("active-id", 1), ("retired-id", 0), ("retired-id", 0)])
        rows = [
            {"player": "Active Guy", "player_id_gsis": "active-id"},
            {"player": "Retired Guy", "player_id_gsis": "retired-id"},
            {"player": "Rookie Guy", "player_id_gsis": "unknown-id"},
        ]
        flagged = rs.attach_roster_status(rows, conn)
        by_name = {r["player"]: r["roster_status"] for r in flagged}
        assert by_name["Active Guy"] == "active"
        assert by_name["Retired Guy"] == "no_active_contract_on_file"
        assert by_name["Rookie Guy"] == "unknown_no_contract_data"


@pytest.mark.skipif(not DB_PATH.exists(), reason="nfl.db not available")
def test_known_retired_player_flagged_against_the_real_db():
    """The T6 fixture assertion: Tom Brady (retired 2023, gsis_id
    00-0019596) must resolve to 'no_active_contract_on_file' against the
    real ingested contracts table -- this is the acceptance evidence for
    'a known-retired player is excluded from the board or flagged.'"""
    conn = sqlite3.connect(f"file:{DB_PATH}?mode=ro", uri=True)
    try:
        status = rs.contract_status(conn, "00-0019596")
    finally:
        conn.close()
    assert status == "no_active_contract_on_file"
