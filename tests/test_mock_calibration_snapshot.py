"""Sanity checks for ADR-054's extension of the batch mock-ingestion path:
frozen league-config snapshot, per-pick prediction computation at ingest
time, and the calibration_usable gate. Written before the corresponding
ingest_mock_drafts.py changes land (see that file's diff in the same
commit)."""

import json
import sqlite3

import pytest

import ingest_mock_drafts as imd
import league_config as lc


def _conn_with_players_and_rankings():
    conn = sqlite3.connect(":memory:")
    conn.execute(
        "CREATE TABLE players_canonical (mfl_id TEXT, display_name TEXT, position TEXT, "
        "team TEXT, birthdate TEXT)"
    )
    conn.executemany(
        "INSERT INTO players_canonical VALUES (?,?,?,?,?)",
        [
            ("1001", "Ja'Marr Chase", "WR", "CIN", None),
            ("1002", "Bijan Robinson", "RB", "ATL", None),
            ("1003", "Justin Jefferson", "WR", "MIN", None),
        ],
    )
    conn.execute(
        "CREATE TABLE rankings (source TEXT, season INTEGER, player_id TEXT, "
        "adp_rank INTEGER, as_of_date TEXT)"
    )
    conn.execute(
        "CREATE TABLE player_ids (mfl_id TEXT, source TEXT, source_id TEXT, "
        "confidence TEXT, method TEXT, resolved_at TEXT)"
    )
    rows = [("g1001", "1001", 1), ("g1002", "1002", 2), ("g1003", "1003", 3)]
    for gsis_id, mfl_id, rank in rows:
        conn.execute(
            "INSERT INTO rankings VALUES ('fantasypros_ecr', 2026, ?, ?, '2026-07-01')",
            (gsis_id, rank),
        )
        conn.execute(
            "INSERT INTO player_ids (mfl_id, source, source_id, confidence, method, resolved_at) "
            "VALUES (?, 'gsis', ?, 'high', 'test', '2026-01-01')",
            (mfl_id, gsis_id),
        )
    return conn


def _write(tmp_path, payload, name="mock.json"):
    p = tmp_path / name
    p.write_text(json.dumps(payload), encoding="utf-8")
    return p


def _draft(picks, mock_id="m1", drafted_at="2026-08-01", league_config_id="primary"):
    return {
        "mock_id": mock_id,
        "league_config_id": league_config_id,
        "platform": "TestMockSite",
        "drafted_at": drafted_at,
        "source": "https://example.com/mock/1",
        "is_mock": True,
        "picks": picks,
    }


class TestFrozenConfigSnapshot:
    def test_ingest_freezes_league_shape_fields(self, tmp_path):
        conn = _conn_with_players_and_rankings()
        path = _write(tmp_path, _draft([{"overall_pick": 1, "mfl_id": "1001"}]))
        imd.ingest_mock_draft_file(conn, path)
        row = conn.execute(
            "SELECT teams, draft_type, user_draft_slot, flex_slots, bench, ir, "
            "starters_json, league_config_hash FROM mock_drafts WHERE mock_id='m1'"
        ).fetchone()
        teams, draft_type, slot, flex_slots, bench, ir, starters_json, cfg_hash = row
        assert teams == lc.CURRENT_LEAGUE.teams
        assert draft_type == lc.CURRENT_LEAGUE.draft_type
        assert slot == lc.CURRENT_LEAGUE.user_draft_slot
        assert flex_slots == lc.CURRENT_LEAGUE.flex_slots
        assert bench == lc.CURRENT_LEAGUE.bench
        assert ir == lc.CURRENT_LEAGUE.ir
        assert json.loads(starters_json) == lc.CURRENT_LEAGUE.starters
        assert cfg_hash  # non-empty hash string

    def test_hash_differs_for_different_configs(self, tmp_path):
        conn = _conn_with_players_and_rankings()
        primary_hash = imd._league_config_hash(lc.CURRENT_LEAGUE)
        other = lc.LeagueConfig(
            league_id="x", name="x", platform="other", teams=8,
            scoring={"offense": {"receptions": 0.5}},
            starters={"QB": 1, "RB": 2, "WR": 3, "TE": 1}, flex_slots=2,
            flex_eligible=("RB", "WR", "TE"), bench=6, ir=1, user_draft_slot=1,
        )
        other_hash = imd._league_config_hash(other)
        assert primary_hash != other_hash


class TestPredictionSnapshotComputation:
    def test_complete_predictions_marks_calibration_usable(self, tmp_path):
        conn = _conn_with_players_and_rankings()
        path = _write(tmp_path, _draft([
            {"overall_pick": 1, "mfl_id": "1002"},
            {"overall_pick": 2, "mfl_id": "1001"},
            {"overall_pick": 3, "mfl_id": "1003"},
        ], drafted_at="2026-08-01"))
        imd.ingest_mock_draft_file(conn, path)
        row = conn.execute(
            "SELECT predictions_complete, calibration_usable, predictions_model_version "
            "FROM mock_drafts WHERE mock_id='m1'"
        ).fetchone()
        assert row[0] == 1
        assert row[1] == 1
        assert row[2] == "adp_rank_exp_v1"
        pick1 = conn.execute(
            "SELECT predicted_top, predicted_p, board_as_of_date FROM mock_picks "
            "WHERE mock_id='m1' AND overall_pick=1"
        ).fetchone()
        assert pick1[0] is not None
        assert pick1[1] is not None
        assert pick1[2] == "2026-07-01"

    def test_missing_snapshot_marks_predictions_incomplete_and_blocks_calibration(self, tmp_path):
        """No rankings snapshot at all before drafted_at -- an honest gap,
        not papered over. calibration_usable must be 0 even though
        format_conforms is 1."""
        conn = _conn_with_players_and_rankings()
        path = _write(tmp_path, _draft(
            [{"overall_pick": 1, "mfl_id": "1001"}],
            drafted_at="2020-01-01",  # before any rankings snapshot on file
        ))
        report = imd.ingest_mock_draft_file(conn, path)
        assert report.format_conforms is True
        row = conn.execute(
            "SELECT predictions_complete, calibration_usable, calibration_usable_note "
            "FROM mock_drafts WHERE mock_id='m1'"
        ).fetchone()
        assert row[0] == 0
        assert row[1] == 0
        assert "prediction" in row[2].lower()

    def test_quarantined_pick_blocks_calibration_usability(self, tmp_path):
        conn = _conn_with_players_and_rankings()
        path = _write(tmp_path, _draft([
            {"overall_pick": 1, "mfl_id": "1001"},
            {"overall_pick": 2, "player_name_raw": "Totally Unknown Guy"},
        ]))
        report = imd.ingest_mock_draft_file(conn, path)
        assert report.picks_quarantined == 1
        row = conn.execute(
            "SELECT calibration_usable FROM mock_drafts WHERE mock_id='m1'"
        ).fetchone()
        assert row[0] == 0

    def test_never_uses_a_post_dated_snapshot(self, tmp_path):
        """The look-ahead-bias guard end-to-end through ingest: a snapshot
        dated AFTER drafted_at must not be used even though it exists."""
        conn = _conn_with_players_and_rankings()
        conn.execute(
            "INSERT INTO rankings VALUES ('fantasypros_ecr', 2026, 'g_future', 1, '2026-12-31')"
        )
        conn.execute(
            "INSERT INTO player_ids (mfl_id, source, source_id, confidence, method, resolved_at) "
            "VALUES ('1001', 'gsis', 'g_future', 'high', 'test', '2026-01-01')"
        )
        path = _write(tmp_path, _draft(
            [{"overall_pick": 1, "mfl_id": "1001"}],
            drafted_at="2026-08-01",
        ))
        imd.ingest_mock_draft_file(conn, path)
        used_date = conn.execute(
            "SELECT board_as_of_date FROM mock_picks WHERE mock_id='m1' AND overall_pick=1"
        ).fetchone()[0]
        assert used_date != "2026-12-31"
        assert used_date == "2026-07-01"


class TestCalibrationUsableGate:
    def test_format_nonconforming_blocks_even_with_complete_predictions(self, tmp_path):
        conn = _conn_with_players_and_rankings()
        bad_cfg = lc.LeagueConfig(
            league_id="notconforming", name="x", platform="other", teams=12,
            scoring={"offense": {"receptions": 0.5}},
            starters={"QB": 1, "RB": 2, "WR": 3, "TE": 1}, flex_slots=2,
            flex_eligible=("RB", "WR", "TE"), bench=6, ir=1, user_draft_slot=1,
        )
        import unittest.mock as um
        with um.patch.object(imd, "_load_league_config", return_value=bad_cfg):
            path = _write(tmp_path, _draft(
                [{"overall_pick": 1, "mfl_id": "1001"}],
                league_config_id="notconforming",
            ))
            imd.ingest_mock_draft_file(conn, path)
        row = conn.execute(
            "SELECT format_conforms, calibration_usable FROM mock_drafts WHERE mock_id='m1'"
        ).fetchone()
        assert row[0] == 0
        assert row[1] == 0


class TestMigrationSurvival:
    def test_existing_mock_drafts_row_survives_schema_migration(self, tmp_path):
        """Simulates a pre-ADR-054 DB: mock_drafts/mock_picks already exist
        without the new columns. ensure_tables must ALTER TABLE, not drop
        and rebuild -- an already-logged real mock draft must not be lost."""
        conn = sqlite3.connect(":memory:")
        conn.execute(
            "CREATE TABLE mock_drafts (mock_id TEXT PRIMARY KEY, league_config_id TEXT, "
            "platform TEXT, drafted_at TEXT, source TEXT, is_mock INTEGER, "
            "format_conforms INTEGER, format_conforms_note TEXT, "
            "bot_seat_status TEXT, bot_seat_count INTEGER, ingested_at TEXT)"
        )
        conn.execute(
            "INSERT INTO mock_drafts VALUES ('2025_league_draft_real','primary','manual',"
            "'2025-08-30','user_provided_screenshots',0,1,'conforms','unknown',NULL,"
            "'2026-01-01T00:00:00')"
        )
        conn.execute(
            "CREATE TABLE mock_picks (mock_id TEXT, overall_pick INTEGER, round INTEGER, "
            "team_slot INTEGER, mfl_id TEXT, player_name_raw TEXT, predicted_top TEXT, "
            "predicted_p REAL, timestamp TEXT, drafter_type TEXT, resolution_method TEXT, "
            "PRIMARY KEY (mock_id, overall_pick))"
        )
        conn.execute(
            "INSERT INTO mock_picks VALUES ('2025_league_draft_real',1,1,1,'1001',"
            "'Ja Marr Chase',NULL,NULL,NULL,NULL,'resolved_name')"
        )
        imd.ensure_tables(conn)
        row = conn.execute(
            "SELECT mock_id FROM mock_drafts WHERE mock_id='2025_league_draft_real'"
        ).fetchone()
        assert row is not None
        pick = conn.execute(
            "SELECT mfl_id FROM mock_picks WHERE mock_id='2025_league_draft_real'"
        ).fetchone()
        assert pick == ("1001",)
        # new columns exist and are nullable (no backfill forced)
        cols = {r[1] for r in conn.execute('PRAGMA table_info("mock_drafts")').fetchall()}
        assert "calibration_usable" in cols
        assert "league_config_hash" in cols
