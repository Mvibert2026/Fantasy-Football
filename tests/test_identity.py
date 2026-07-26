import sqlite3

import pytest

import identity as idn


def _seeded_conn():
    """In-memory DB with a minimal ff_playerids fixture: one clean row, one
    gsis_id collision (two mfl_ids sharing a gsis_id), one row missing gsis
    entirely."""
    conn = sqlite3.connect(":memory:")
    conn.execute(
        "CREATE TABLE ff_playerids (mfl_id TEXT, name TEXT, position TEXT, team TEXT, "
        "birthdate TEXT, gsis_id TEXT, pfr_id TEXT, espn_id TEXT, yahoo_id TEXT, "
        "sleeper_id TEXT, fantasypros_id TEXT, sportradar_id TEXT)"
    )
    conn.executemany(
        "INSERT INTO ff_playerids VALUES (?,?,?,?,?,?,?,?,?,?,?,?)",
        [
            ("1001", "Clean Player", "WR", "SEA", "1998-01-01",
             "00-0011111", "CleaPl01", "9001", "8001", "7001", "6001", "5001"),
            ("1002", "Collide A", "RB", "DAL", "1997-02-02",
             "00-0022222", None, None, None, None, None, None),
            ("1003", "Collide B", "RB", "NYG", "1996-03-03",
             "00-0022222", None, None, None, None, None, None),
            ("1004", "No Gsis Player", "TE", "KC", "1999-04-04",
             None, "NoGsPl01", None, None, None, None, None),
        ],
    )
    conn.execute(
        "CREATE TABLE rankings (player_name TEXT, source TEXT, season INTEGER)"
    )
    conn.executemany(
        "INSERT INTO rankings VALUES (?, 'fantasypros_ecr', 2026)",
        [("Clean Player",), ("Collide A",), ("Nobody Matches",)],
    )
    return conn


def test_build_creates_canonical_row_per_mfl_id():
    conn = _seeded_conn()
    report = idn.build_identity_tables(conn)
    assert report["canonical_players"] == 4
    n = conn.execute("SELECT COUNT(*) FROM players_canonical").fetchone()[0]
    assert n == 4


def test_clean_crosswalk_resolves_direct():
    conn = _seeded_conn()
    idn.build_identity_tables(conn)
    assert idn.resolve(conn, "gsis", "00-0011111") == "1001"
    assert idn.resolve(conn, "pfr", "CleaPl01") == "1001"


def test_colliding_gsis_id_resolves_to_none_not_a_guess():
    """The core invariant: a source_id shared by two mfl_ids must NEVER
    resolve to either one -- it must be excluded, not decided by a tiebreak."""
    conn = _seeded_conn()
    idn.build_identity_tables(conn)
    assert idn.resolve(conn, "gsis", "00-0022222") is None
    row = conn.execute(
        "SELECT candidate_mfl_ids FROM player_id_collisions WHERE source='gsis' AND source_id=?",
        ("00-0022222",),
    ).fetchone()
    assert row is not None
    import json
    assert sorted(json.loads(row[0])) == ["1002", "1003"]


def test_unresolvable_source_id_is_none():
    conn = _seeded_conn()
    idn.build_identity_tables(conn)
    assert idn.resolve(conn, "gsis", "00-0099999") is None


def test_missing_value_never_produces_a_row():
    """A player with no gsis_id at all must not appear under 'gsis' -- absence
    is not the same as a resolvable empty string."""
    conn = _seeded_conn()
    idn.build_identity_tables(conn)
    assert idn.resolve(conn, "gsis", "") is None
    assert idn.resolve(conn, "pfr", "NoGsPl01") == "1004"


def test_resolve_rejects_unknown_source():
    conn = _seeded_conn()
    idn.build_identity_tables(conn)
    with pytest.raises(ValueError):
        idn.resolve(conn, "not_a_real_source", "x")


def test_depth_chart_reported_as_not_a_distinct_id_space():
    conn = _seeded_conn()
    idn.build_identity_tables(conn)
    cov = idn.coverage_report(conn)
    assert cov["depth_chart"]["resolvable_mfl_ids"] is None
    assert "not a distinct ID space" in cov["depth_chart"]["note"]


def test_collision_excluded_from_coverage_denominator_but_counted():
    conn = _seeded_conn()
    idn.build_identity_tables(conn)
    cov = idn.coverage_report(conn)
    # 4 canonical players; gsis resolves for player 1001 only (1002/1003
    # collided and were excluded, 1004 has no gsis at all).
    assert cov["gsis"]["resolvable_mfl_ids"] == 1
    assert cov["gsis"]["collisions_excluded"] == 1


def test_board_coverage_reports_name_match_rate_and_flags_unmatched():
    conn = _seeded_conn()
    idn.build_identity_tables(conn)
    board = idn.coverage_report_for_board(conn, season=2026)
    assert board["board_players"] == 3
    assert board["name_matched_to_mfl_id"] == 2  # "Nobody Matches" fails
    assert "Nobody Matches" in board["unmatched_names_sample"]


def test_name_match_normalization_strips_suffix_and_punctuation():
    conn = _seeded_conn()
    conn.execute(
        "INSERT INTO ff_playerids VALUES "
        "('1005','D.J. Suffix Jr.','WR','MIA','2000-01-01',NULL,NULL,NULL,NULL,NULL,NULL,NULL)"
    )
    conn.execute("INSERT INTO rankings VALUES ('DJ Suffix', 'fantasypros_ecr', 2026)")
    idn.build_identity_tables(conn)
    board = idn.coverage_report_for_board(conn, season=2026)
    assert board["name_matched_to_mfl_id"] == 3


def test_name_dob_match_candidates_never_writes_player_ids():
    conn = _seeded_conn()
    idn.build_identity_tables(conn)
    before = conn.execute("SELECT COUNT(*) FROM player_ids").fetchone()[0]
    candidates = idn.name_dob_match_candidates(conn, "Clean Player")
    assert len(candidates) == 1
    assert candidates[0].mfl_id == "1001"
    after = conn.execute("SELECT COUNT(*) FROM player_ids").fetchone()[0]
    assert after == before  # candidate-finding must never mutate player_ids


def test_manually_confirm_is_labelled_manual_not_direct_crosswalk():
    conn = _seeded_conn()
    idn.build_identity_tables(conn)
    idn.manually_confirm(conn, "1004", "yahoo", "yahoo999", note="confirmed via roster cross-check")
    assert idn.resolve(conn, "yahoo", "yahoo999") == "1004"
    method = conn.execute(
        "SELECT method, confidence FROM player_ids WHERE source='yahoo' AND source_id='yahoo999'"
    ).fetchone()
    assert method == ("manual", "manual")


def test_build_is_idempotent():
    """Re-running build must not accumulate duplicate rows -- same pattern as
    ingest_reference.py's drop-and-rebuild."""
    conn = _seeded_conn()
    idn.build_identity_tables(conn)
    idn.build_identity_tables(conn)
    n = conn.execute("SELECT COUNT(*) FROM players_canonical").fetchone()[0]
    assert n == 4
