import sqlite3

import mock_validation_report as mvr


def _seeded_conn():
    conn = sqlite3.connect(":memory:")
    conn.execute(
        "CREATE TABLE players_canonical (mfl_id TEXT, display_name TEXT, position TEXT, "
        "team TEXT, birthdate TEXT)"
    )
    conn.executemany(
        "INSERT INTO players_canonical VALUES (?,?,?,?,?)",
        [
            ("1", "RB One", "RB", "AAA", None),
            ("2", "RB Two", "RB", "AAA", None),
            ("3", "WR One", "WR", "AAA", None),
            ("4", "QB One", "QB", "AAA", None),
        ],
    )
    conn.execute(
        "CREATE TABLE mock_drafts (mock_id TEXT PRIMARY KEY, league_config_id TEXT, "
        "platform TEXT, drafted_at TEXT, source TEXT, is_mock INTEGER, "
        "format_conforms INTEGER, format_conforms_note TEXT, bot_seat_status TEXT, "
        "ingested_at TEXT)"
    )
    conn.execute(
        "CREATE TABLE mock_picks (mock_id TEXT, overall_pick INTEGER, round INTEGER, "
        "team_slot INTEGER, mfl_id TEXT, player_name_raw TEXT, predicted_top TEXT, "
        "predicted_p REAL, timestamp TEXT, resolution_method TEXT)"
    )
    return conn


def _insert_mock(conn, mock_id, conforms, picks):
    conn.execute(
        "INSERT INTO mock_drafts VALUES (?,'primary','p','2026-08-01',NULL,1,?,'note','unknown','now')",
        (mock_id, int(conforms)),
    )
    for overall_pick, mfl_id in picks:
        conn.execute(
            "INSERT INTO mock_picks (mock_id, overall_pick, mfl_id) VALUES (?, ?, ?)",
            (mock_id, overall_pick, mfl_id),
        )


def test_conforming_mock_ids_excludes_non_conforming():
    conn = _seeded_conn()
    _insert_mock(conn, "m1", True, [])
    _insert_mock(conn, "m2", False, [])
    ids = mvr.conforming_mock_ids(conn)
    assert ids == ["m1"]


def test_power_note_zero_mocks():
    note = mvr._power_note(0)
    assert "absence of any measurement" in note


def test_power_note_below_ten():
    note = mvr._power_note(3)
    assert "10 mocks" in note


def test_power_note_at_thirty():
    note = mvr._power_note(30)
    assert "decision-useful" in note
    assert "below" not in note


def test_level1_depletion_report_zero_mocks_is_all_nones():
    conn = _seeded_conn()
    report = mvr.level1_depletion_report(conn)
    assert report["n_conforming_mocks"] == 0
    assert all(c.observed_gone_mean is None for c in report["cells"])
    assert all(c.n_mocks == 0 for c in report["cells"])


def test_level1_depletion_counts_observed_correctly():
    """With one conforming mock where an RB goes at pick 1, observed RB-gone
    at pick 3 should be 1 (RB was taken before pick 3), and at pick 1 itself
    should be 0 (strictly before, not at-or-before)."""
    conn = _seeded_conn()
    _insert_mock(conn, "m1", True, [(1, "1"), (2, "3"), (3, "4")])  # RB, WR, QB
    report = mvr.level1_depletion_report(conn)
    assert report["n_conforming_mocks"] == 1
    pick3_rb = next(c for c in report["cells"] if c.pick == 3 and c.position == "RB")
    assert pick3_rb.observed_gone_mean == 1.0  # the pick-1 RB counts, pick-3 QB does not (not < 3... wait QB)
    pick3_qb = next(c for c in report["cells"] if c.pick == 3 and c.position == "QB")
    assert pick3_qb.observed_gone_mean == 0.0  # the QB at pick 3 itself is NOT "gone before pick 3"


def test_level1_signed_error_is_observed_minus_predicted():
    conn = _seeded_conn()
    _insert_mock(conn, "m1", True, [(1, "1")])
    report = mvr.level1_depletion_report(conn)
    for cell in report["cells"]:
        if cell.observed_gone_mean is not None and cell.predicted_gone is not None:
            assert cell.signed_error == cell.observed_gone_mean - cell.predicted_gone


def test_non_conforming_mock_excluded_from_depletion_counts():
    conn = _seeded_conn()
    _insert_mock(conn, "m1", False, [(1, "1"), (2, "1")])  # would dominate if included
    report = mvr.level1_depletion_report(conn)
    assert report["n_conforming_mocks"] == 0
    assert all(c.n_mocks == 0 for c in report["cells"])


def test_render_report_runs_with_zero_mocks_and_states_no_data():
    conn = _seeded_conn()
    text = mvr.render_report(conn)
    assert "0" in text
    assert "absence of any measurement" in text


def test_render_report_names_scope_cuts():
    conn = _seeded_conn()
    text = mvr.render_report(conn)
    assert "Tertiary" in text
    assert "Brier" in text


def test_depletion_picks_matches_protocol_literal_list():
    """The protocol names picks 3,18,23,38,43,58,63 explicitly. Confirms the
    computed (not hardcoded) version still equals that list for the primary
    league."""
    assert mvr.depletion_picks() == [3, 18, 23, 38, 43, 58, 63]
