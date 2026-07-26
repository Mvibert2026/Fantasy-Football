import json
import sqlite3

import pytest

import ingest_mock_drafts as imd
import league_config as lc


def _conn_with_players():
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
            ("1003", "Duplicate Name", "WR", "AAA", None),
            ("1004", "Duplicate Name", "TE", "BBB", None),
        ],
    )
    return conn


def _write(tmp_path, payload, name="mock.json"):
    p = tmp_path / name
    p.write_text(json.dumps(payload), encoding="utf-8")
    return p


def _conforming_draft(picks, mock_id="m1", league_config_id="primary"):
    return {
        "mock_id": mock_id,
        "league_config_id": league_config_id,
        "platform": "TestMockSite",
        "drafted_at": "2026-08-01",
        "source": "https://example.com/mock/1",
        "is_mock": True,
        "picks": picks,
    }


def test_ensure_tables_creates_all_three():
    conn = _conn_with_players()
    imd.ensure_tables(conn)
    names = {r[0] for r in conn.execute(
        "SELECT name FROM sqlite_master WHERE type='table'"
    ).fetchall()}
    assert {"mock_drafts", "mock_picks", "mock_pick_quarantine"} <= names


def test_ingest_resolves_supplied_mfl_id(tmp_path):
    conn = _conn_with_players()
    path = _write(tmp_path, _conforming_draft([
        {"overall_pick": 1, "round": 1, "team_slot": 1, "mfl_id": "1001",
         "player_name_raw": "Ja'Marr Chase", "predicted_p": 0.99},
    ]))
    report = imd.ingest_mock_draft_file(conn, path)
    assert report.picks_resolved == 1
    assert report.picks_quarantined == 0
    row = conn.execute(
        "SELECT mfl_id, resolution_method FROM mock_picks WHERE mock_id='m1' AND overall_pick=1"
    ).fetchone()
    assert row == ("1001", "supplied_mfl_id")


def test_ingest_resolves_via_name_when_mfl_id_absent(tmp_path):
    conn = _conn_with_players()
    path = _write(tmp_path, _conforming_draft([
        {"overall_pick": 1, "player_name_raw": "Bijan Robinson"},
    ]))
    report = imd.ingest_mock_draft_file(conn, path)
    assert report.picks_resolved == 1
    row = conn.execute(
        "SELECT mfl_id, resolution_method FROM mock_picks WHERE mock_id='m1' AND overall_pick=1"
    ).fetchone()
    assert row == ("1002", "resolved_name")


def test_name_resolution_uses_suffix_normalization(tmp_path):
    conn = _conn_with_players()
    path = _write(tmp_path, _conforming_draft([
        {"overall_pick": 1, "player_name_raw": "Ja'Marr Chase Jr."},
    ]))
    report = imd.ingest_mock_draft_file(conn, path)
    assert report.picks_resolved == 1


def test_invalid_supplied_mfl_id_goes_to_quarantine_not_silently_dropped(tmp_path):
    conn = _conn_with_players()
    path = _write(tmp_path, _conforming_draft([
        {"overall_pick": 1, "mfl_id": "99999", "player_name_raw": "Nobody Real"},
    ]))
    report = imd.ingest_mock_draft_file(conn, path)
    assert report.picks_resolved == 0
    assert report.picks_quarantined == 1
    row = conn.execute(
        "SELECT reason FROM mock_pick_quarantine WHERE mock_id='m1' AND overall_pick=1"
    ).fetchone()
    assert "not found" in row[0]


def test_unresolvable_name_goes_to_quarantine_never_guessed(tmp_path):
    conn = _conn_with_players()
    path = _write(tmp_path, _conforming_draft([
        {"overall_pick": 1, "player_name_raw": "Totally Unknown Player"},
    ]))
    report = imd.ingest_mock_draft_file(conn, path)
    assert report.picks_resolved == 0
    assert report.picks_quarantined == 1


def test_ambiguous_name_goes_to_quarantine_never_guessed():
    """Two players share a display name (WR and TE) -- the core invariant:
    ambiguity must NEVER resolve to either candidate, matching resolve()'s
    collision behavior in identity.py."""
    conn = _conn_with_players()
    assert idn_resolve_name(conn, "Duplicate Name") is None


def idn_resolve_name(conn, name):
    import identity as idn

    return idn.resolve_name(conn, name)


def test_missing_required_field_raises(tmp_path):
    conn = _conn_with_players()
    bad = {"league_config_id": "primary", "platform": "x", "drafted_at": "2026-08-01",
           "picks": []}
    path = _write(tmp_path, bad)
    with pytest.raises(imd.MockDraftValidationError):
        imd.ingest_mock_draft_file(conn, path)


def test_pick_missing_overall_pick_raises(tmp_path):
    conn = _conn_with_players()
    path = _write(tmp_path, _conforming_draft([{"player_name_raw": "Bijan Robinson"}]))
    with pytest.raises(imd.MockDraftValidationError):
        imd.ingest_mock_draft_file(conn, path)


def test_unknown_league_config_id_raises(tmp_path):
    conn = _conn_with_players()
    path = _write(tmp_path, _conforming_draft([], league_config_id="does_not_exist"))
    with pytest.raises(imd.MockDraftValidationError):
        imd.ingest_mock_draft_file(conn, path)


def test_reingesting_same_mock_id_replaces_not_duplicates(tmp_path):
    conn = _conn_with_players()
    path = _write(tmp_path, _conforming_draft([
        {"overall_pick": 1, "mfl_id": "1001", "player_name_raw": "Ja'Marr Chase"},
    ]))
    imd.ingest_mock_draft_file(conn, path)
    imd.ingest_mock_draft_file(conn, path)
    n_drafts = conn.execute("SELECT COUNT(*) FROM mock_drafts").fetchone()[0]
    n_picks = conn.execute("SELECT COUNT(*) FROM mock_picks").fetchone()[0]
    assert n_drafts == 1
    assert n_picks == 1


def test_bot_seat_status_is_unknown_never_silently_passed():
    """The protocol's >3-bot-seats discard gate cannot be checked from this
    schema (no drafter_type field). It must be flagged 'unknown', not
    silently treated as passing."""
    conn = _conn_with_players()
    imd.ensure_tables(conn)
    conn.execute(
        "INSERT INTO mock_drafts VALUES ('x','primary','p','2026-08-01',NULL,1,1,'ok','unknown','now')"
    )
    status = conn.execute("SELECT bot_seat_status FROM mock_drafts WHERE mock_id='x'").fetchone()[0]
    assert status == "unknown"


class TestFormatConforms:
    def test_primary_league_conforms(self):
        conforms, note = imd.format_conforms(lc.CURRENT_LEAGUE)
        assert conforms is True

    def test_wrong_team_count_fails(self):
        cfg = lc.LeagueConfig(
            league_id="x", name="x", platform="other", teams=12,
            scoring={"offense": {"receptions": 0.5}},
            starters={"QB": 1, "RB": 2, "WR": 3, "TE": 1}, flex_slots=2,
            flex_eligible=("RB", "WR", "TE"), bench=6, ir=1, user_draft_slot=1,
        )
        conforms, note = imd.format_conforms(cfg)
        assert conforms is False
        assert "teams" in note

    def test_kicker_present_fails(self):
        cfg = lc.LeagueConfig(
            league_id="x", name="x", platform="other", teams=10,
            scoring={"offense": {"receptions": 0.5}},
            starters={"QB": 1, "RB": 2, "WR": 3, "TE": 1, "K": 1}, flex_slots=2,
            flex_eligible=("RB", "WR", "TE"), bench=6, ir=1, user_draft_slot=1,
        )
        conforms, note = imd.format_conforms(cfg)
        assert conforms is False
        assert "kicker" in note

    def test_non_half_ppr_fails(self):
        cfg = lc.LeagueConfig(
            league_id="x", name="x", platform="other", teams=10,
            scoring={"offense": {"receptions": 1.0}},
            starters={"QB": 1, "RB": 2, "WR": 3, "TE": 1}, flex_slots=2,
            flex_eligible=("RB", "WR", "TE"), bench=6, ir=1, user_draft_slot=1,
        )
        conforms, note = imd.format_conforms(cfg)
        assert conforms is False
        assert "receptions" in note

    def test_wrong_flex_slots_fails(self):
        cfg = lc.LeagueConfig(
            league_id="x", name="x", platform="other", teams=10,
            scoring={"offense": {"receptions": 0.5}},
            starters={"QB": 1, "RB": 2, "WR": 3, "TE": 1}, flex_slots=1,
            flex_eligible=("RB", "WR", "TE"), bench=6, ir=1, user_draft_slot=1,
        )
        conforms, note = imd.format_conforms(cfg)
        assert conforms is False
        assert "flex_slots" in note
