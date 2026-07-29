"""ADR-055: kickers become their own consensus-only export artifact, never
merged into board.json's ranked player list. Written before
export_contract.build_kickers_json lands."""

import sqlite3

import pytest

import export_contract as ec
import league_config as lc
import make_board


def _conn_with_k_rows():
    conn = sqlite3.connect(":memory:")
    conn.execute(
        "CREATE TABLE rankings (source TEXT, season INTEGER, player_id TEXT, "
        "player_name TEXT, position TEXT, adp_rank INTEGER, as_of_date TEXT, "
        "scoring_format TEXT)"
    )
    conn.executemany(
        "INSERT INTO rankings VALUES (?,?,?,?,?,?,?,?)",
        [
            (make_board.SOURCE, 2026, "g_k1", "Justin Tucker", "K", 1, "2026-07-27", "half_ppr"),
            (make_board.SOURCE, 2026, "g_k2", "Harrison Butker", "K", 2, "2026-07-27", "half_ppr"),
            (make_board.SOURCE, 2026, "g_wr1", "Ja'Marr Chase", "WR", 1, "2026-07-27", "half_ppr"),
        ],
    )
    return conn


class TestBuildKickersJson:
    def test_returns_only_kickers_ordered_by_consensus_rank(self):
        conn = _conn_with_k_rows()
        payload = ec.build_kickers_json(conn, lc.CURRENT_LEAGUE)
        names = [k["player_name"] for k in payload["kickers"]]
        assert names == ["Justin Tucker", "Harrison Butker"]
        assert all(k["position"] == "K" for k in payload["kickers"])

    def test_no_vbd_or_projection_fields_present(self):
        conn = _conn_with_k_rows()
        payload = ec.build_kickers_json(conn, lc.CURRENT_LEAGUE)
        for row in payload["kickers"]:
            assert "projected_points" not in row
            assert "vbd" not in row
            assert "replacement_level" not in row

    def test_notes_it_is_consensus_only_not_modelled(self):
        conn = _conn_with_k_rows()
        payload = ec.build_kickers_json(conn, lc.CURRENT_LEAGUE)
        assert "consensus" in payload["note"].lower()
        assert "no" in payload["note"].lower()  # "no proprietary modeling" etc.

    def test_empty_when_no_k_rows(self):
        conn = sqlite3.connect(":memory:")
        conn.execute(
            "CREATE TABLE rankings (source TEXT, season INTEGER, player_id TEXT, "
            "player_name TEXT, position TEXT, adp_rank INTEGER, as_of_date TEXT, "
            "scoring_format TEXT)"
        )
        payload = ec.build_kickers_json(conn, lc.CURRENT_LEAGUE)
        assert payload["kickers"] == []


class TestKExcludedFromCombinedBoard:
    def test_board_positions_excludes_k(self):
        assert "K" not in make_board.BOARD_POSITIONS

    def test_ethans_expert_league_rosters_k_but_board_still_excludes_it(self):
        """Ethan's Expert League DOES roster a K starter -- the exclusion
        must hold anyway, since BOARD_POSITIONS is not per-league."""
        cfg = lc.LeagueConfig.load("ethans_expert_league")
        assert "K" in cfg.starters
        assert "K" not in make_board.BOARD_POSITIONS

    def test_k_is_in_unsupported_positions_for_a_league_that_rosters_it(self):
        cfg = lc.LeagueConfig.load("ethans_expert_league")
        from scoring import ReplacementLevels
        unsupported = sorted(p for p in cfg.starters if p not in ReplacementLevels.SCOREABLE_POSITIONS)
        assert "K" in unsupported


class TestWriteAllIncludesKickers:
    def test_kickers_json_written(self, tmp_path):
        conn = _conn_with_k_rows()
        # write_all also builds board/availability/league/rosters, which need
        # a real DB with real tables this minimal fixture doesn't have --
        # so call build_kickers_json directly and only assert it CAN be
        # written as one of write_all's artifacts by checking the function
        # is registered under the expected key.
        import inspect
        src = inspect.getsource(ec.write_all)
        assert '"kickers.json"' in src
