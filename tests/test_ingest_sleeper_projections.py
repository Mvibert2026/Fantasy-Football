import csv
import sqlite3

import ingest_sleeper_projections as sp

_SAMPLE_PAYLOAD = [
    {
        "stats": {
            "pass_att": 550.0, "pass_cmp": 380.0, "pass_yd": 4200.0, "pass_td": 30.0,
            "pass_int": 9.0, "gp": 17.0, "rush_att": 40.0, "rush_yd": 150.0, "rush_td": 2.0,
            "fum_lost": 3.0, "pts_std": 300.5, "pts_half_ppr": 300.5, "pts_ppr": 300.5,
        },
        "category": "proj",
        "last_modified": 1785311409344,
        "season": "2026",
        "season_type": "regular",
        "player": {
            "first_name": "Joe", "last_name": "Star", "position": "QB", "team": "KC",
        },
        "player_id": "1001",
        "updated_at": 1785311409999,
        "company": "rotowire",
    },
    {
        "stats": {"gp": 12.0, "rush_att": 10.0, "rush_yd": 30.0},
        "category": "proj",
        "last_modified": 1785311400000,
        "season": "2026",
        "season_type": "regular",
        "player": {
            "first_name": "No", "last_name": "Crosswalk", "position": "QB", "team": "SEA",
        },
        "player_id": "9999",
        "updated_at": 1785311400000,
        "company": "rotowire",
    },
]


def _conn_with_ff_playerids():
    conn = sqlite3.connect(":memory:")
    conn.execute(
        "CREATE TABLE ff_playerids (mfl_id TEXT, name TEXT, position TEXT, team TEXT, "
        "birthdate TEXT, gsis_id TEXT, pfr_id TEXT, espn_id TEXT, yahoo_id TEXT, "
        "sleeper_id TEXT, fantasypros_id TEXT, sportradar_id TEXT)"
    )
    conn.executemany(
        "INSERT INTO ff_playerids (mfl_id, name, position, team, sleeper_id) VALUES (?,?,?,?,?)",
        [("20001", "Joe Star", "QB", "KC", "1001")],
    )
    conn.commit()
    return conn


def test_parse_rows_extracts_fields_and_company():
    rows = sp.parse_rows(_SAMPLE_PAYLOAD, "QB")
    assert len(rows) == 2
    star = rows[0]
    assert star["player_name"] == "Joe Star"
    assert star["position"] == "QB"
    assert star["team"] == "KC"
    assert star["company"] == "rotowire"
    assert star["pass_yd"] == 4200.0
    assert star["pass_td"] == 30.0
    assert star["source_last_modified"] == 1785311409344


def test_parse_rows_never_fabricates_missing_stat():
    rows = sp.parse_rows(_SAMPLE_PAYLOAD, "QB")
    unresolved = rows[1]
    # rec/rec_yd were never in the source stats block for this player
    assert unresolved["rec"] is None
    assert unresolved["rec_yd"] is None


def test_store_projections_resolves_matched_player_and_quarantines_unmatched():
    conn = _conn_with_ff_playerids()
    rows = sp.parse_rows(_SAMPLE_PAYLOAD, "QB")
    result = sp.store_projections(conn, rows, season=2026, as_of_date="2026-07-29")
    assert result["stored"] == 1
    assert result["quarantined"] == 1

    stored = conn.execute(
        "SELECT projection_source, mfl_id, player_name, pass_yd, company FROM sleeper_projections"
    ).fetchall()
    assert stored == [("sleeper_rotowire", "20001", "Joe Star", 4200.0, "rotowire")]

    quarantined = conn.execute(
        "SELECT sleeper_player_id, player_name_raw, reason FROM sleeper_projection_quarantine"
    ).fetchall()
    assert quarantined == [("9999", "No Crosswalk", "no_sleeper_crosswalk_match")]


def test_query_position_survives_mismatched_source_position():
    """A row Sleeper tags with a different `position` than what we queried
    for (multi-eligible/misclassified players) must still be scoped by the
    REQUESTED position, not Sleeper's own field -- otherwise a later WR/TE
    fetch on the same day can be wrongly skipped because a stray row from an
    earlier RB fetch happens to carry position='WR'."""
    conn = _conn_with_ff_playerids()
    conn.execute(
        "INSERT INTO ff_playerids (mfl_id, name, position, team, sleeper_id) VALUES (?,?,?,?,?)",
        ("30001", "Multi Eligible", "WR", "SEA", "5555"),
    )
    conn.commit()
    payload = [{
        "stats": {"gp": 10.0},
        "season": "2026", "season_type": "regular",
        "player": {"first_name": "Multi", "last_name": "Eligible", "position": "WR", "team": "SEA"},
        "player_id": "5555", "company": "rotowire",
    }]
    rows = sp.parse_rows(payload, "RB")  # queried as RB, source reports WR
    sp.store_projections(conn, rows, season=2026, as_of_date="2026-07-29")
    assert sp.already_fetched_today(conn, "RB") is True
    assert sp.already_fetched_today(conn, "WR") is False


def test_store_projections_never_writes_other_projection_source():
    conn = _conn_with_ff_playerids()
    rows = sp.parse_rows(_SAMPLE_PAYLOAD, "QB")
    sp.store_projections(conn, rows, season=2026, as_of_date="2026-07-29")
    sources = {r[0] for r in conn.execute("SELECT DISTINCT projection_source FROM sleeper_projections")}
    assert sources == {"sleeper_rotowire"}


def test_store_projections_called_twice_same_day_overwrites_not_appends():
    conn = _conn_with_ff_playerids()
    rows = sp.parse_rows(_SAMPLE_PAYLOAD, "QB")
    sp.store_projections(conn, rows, season=2026, as_of_date="2026-07-29")
    sp.store_projections(conn, rows, season=2026, as_of_date="2026-07-29")

    stored = conn.execute("SELECT COUNT(*) FROM sleeper_projections").fetchone()[0]
    quarantined = conn.execute("SELECT COUNT(*) FROM sleeper_projection_quarantine").fetchone()[0]
    assert stored == 1
    assert quarantined == 1


def test_as_of_date_is_capture_date_not_source_timestamp():
    conn = _conn_with_ff_playerids()
    rows = sp.parse_rows(_SAMPLE_PAYLOAD, "QB")
    sp.store_projections(conn, rows, season=2026, as_of_date="2026-07-29")
    as_of, last_mod = conn.execute(
        "SELECT as_of_date, source_last_modified FROM sleeper_projections"
    ).fetchone()
    assert as_of == "2026-07-29"
    assert last_mod == 1785311409344
    assert as_of != last_mod


def test_export_snapshot_csv_after_repeated_store_has_no_duplicate_rows(tmp_path):
    conn = _conn_with_ff_playerids()
    rows = sp.parse_rows(_SAMPLE_PAYLOAD, "QB")
    sp.store_projections(conn, rows, season=2026, as_of_date="2026-07-29")
    sp.store_projections(conn, rows, season=2026, as_of_date="2026-07-29")

    db_path = tmp_path / "nfl.db"
    out = sp.export_snapshot_csv(conn, db_path, "2026-07-29", "QB", 2026)
    with out.open(newline="", encoding="utf-8") as f:
        csv_rows = list(csv.DictReader(f))
    assert len(csv_rows) == 1


def test_csv_round_trip_import(tmp_path):
    conn = _conn_with_ff_playerids()
    rows = sp.parse_rows(_SAMPLE_PAYLOAD, "QB")
    sp.store_projections(conn, rows, season=2026, as_of_date="2026-07-29")
    db_path = tmp_path / "nfl.db"
    csv_path = sp.export_snapshot_csv(conn, db_path, "2026-07-29", "QB", 2026)

    conn2 = sqlite3.connect(":memory:")
    n = sp.import_snapshot_csv(conn2, csv_path)
    assert n == 1
    row = conn2.execute("SELECT mfl_id, pass_yd FROM sleeper_projections").fetchone()
    assert row == ("20001", 4200.0)


def test_positions_constant_covers_qb_rb_wr_te():
    assert sp.POSITIONS == ["QB", "RB", "WR", "TE"]
