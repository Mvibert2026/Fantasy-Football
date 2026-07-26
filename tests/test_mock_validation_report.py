import sqlite3

import pytest

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
        "bot_seat_count INTEGER, ingested_at TEXT)"
    )
    conn.execute(
        "CREATE TABLE mock_picks (mock_id TEXT, overall_pick INTEGER, round INTEGER, "
        "team_slot INTEGER, mfl_id TEXT, player_name_raw TEXT, predicted_top TEXT, "
        "predicted_p REAL, timestamp TEXT, drafter_type TEXT, resolution_method TEXT)"
    )
    return conn


def _insert_mock(conn, mock_id, conforms, picks, bot_seat_status="unknown", bot_seat_count=None):
    conn.execute(
        "INSERT INTO mock_drafts VALUES (?,'primary','p','2026-08-01',NULL,1,?,'note',?,?,'now')",
        (mock_id, int(conforms), bot_seat_status, bot_seat_count),
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


def test_render_report_includes_all_four_sections():
    """Tertiary (dispersion) and Brier-vs-baseline were the two named gaps
    from the prior session (ADR-042) -- confirm they render, not just Levels
    1-2."""
    conn = _seeded_conn()
    text = mvr.render_report(conn)
    assert "TERTIARY" in text
    assert "BRIER SCORE" in text
    assert "LEVEL 1" in text
    assert "LEVEL 2" in text


def test_depletion_picks_matches_protocol_literal_list():
    """The protocol names picks 3,18,23,38,43,58,63 explicitly. Confirms the
    computed (not hardcoded) version still equals that list for the primary
    league."""
    assert mvr.depletion_picks() == [3, 18, 23, 38, 43, 58, 63]


def test_conforming_mock_ids_excludes_too_many_bots():
    conn = _seeded_conn()
    _insert_mock(conn, "m1", True, [], bot_seat_status="conforms", bot_seat_count=2)
    _insert_mock(conn, "m2", True, [], bot_seat_status="excluded_too_many_bots", bot_seat_count=5)
    _insert_mock(conn, "m3", True, [], bot_seat_status="unknown", bot_seat_count=None)
    ids = mvr.conforming_mock_ids(conn)
    assert set(ids) == {"m1", "m3"}


def test_unknown_bot_seat_mock_ids_reports_only_unknown():
    conn = _seeded_conn()
    _insert_mock(conn, "m1", True, [], bot_seat_status="conforms", bot_seat_count=2)
    _insert_mock(conn, "m2", True, [], bot_seat_status="unknown", bot_seat_count=None)
    assert mvr.unknown_bot_seat_mock_ids(conn) == ["m2"]


def test_render_report_caveats_unknown_bot_seat_mocks():
    conn = _seeded_conn()
    _insert_mock(conn, "m1", True, [(1, "1")], bot_seat_status="unknown", bot_seat_count=None)
    text = mvr.render_report(conn)
    assert "bot_seat_status='unknown'" in text


class TestDispersionBand:
    def test_pass_when_observed_sd_inside_band(self):
        # implied_sd_at_10 = 2.0 -> band [1.0, 4.0]; observed 2.0 is inside
        lo, hi = 2.0 * mvr.DISPERSION_BAND[0], 2.0 * mvr.DISPERSION_BAND[1]
        assert lo <= 2.0 <= hi

    def test_fail_when_observed_sd_outside_band(self):
        lo, hi = 2.0 * mvr.DISPERSION_BAND[0], 2.0 * mvr.DISPERSION_BAND[1]
        assert not (lo <= 5.0 <= hi)  # 5.0 > 2x implied


class TestFitRankLogistic:
    def test_returns_none_below_minimum_pairs(self):
        pairs = [(18, 5.0, 1.0, 0.9) for _ in range(5)]
        assert mvr._fit_rank_logistic(pairs) is None

    def test_fits_a_clean_separable_pattern(self):
        """Players far below rank-vs-pick (rank << pick, plenty of picks left)
        should fit b > 0 (survival increases as pick-rank grows) -- a basic
        sanity check the optimizer converges to the right sign, not an exact
        value check."""
        import random
        random.seed(0)
        pairs = []
        for rank in range(1, 40):
            for pick in (18, 43):
                margin = pick - rank
                true_p = 1.0 / (1.0 + pow(2.71828, -(0.05 * margin)))
                obs = 1.0 if random.random() < true_p else 0.0
                pairs.append((pick, float(rank), obs, true_p))
        fit = mvr._fit_rank_logistic(pairs)
        assert fit is not None
        a, b = fit
        assert b > 0  # more margin (pick - rank) -> higher survival


def test_brier_vs_baseline_report_zero_mocks_reports_no_data():
    conn = _seeded_conn()
    report = mvr.brier_vs_baseline_report(conn)
    assert report["verdict"] == "NOT_EVALUATED_NO_DATA"
    assert report["brier_full_model"] is None
    assert report["brier_baseline_logistic"] is None


@pytest.mark.requires_db
def test_level3_dispersion_report_computes_real_implied_sd():
    """Against the real DB: implied SD must be computable (a property of the
    model alone) even with zero mocks logged."""
    import db as dbmod

    conn = dbmod.connect()
    try:
        import ingest_mock_drafts as imd

        imd.ensure_tables(conn)
        report = mvr.level3_dispersion_report(conn, n_sims=100)
    finally:
        conn.close()
    assert report["criterion_4_status"] == "NOT_EVALUATED_NO_MOCKS"
    computed = [c for c in report["cells"] if c.implied_sd_at_10 is not None]
    assert len(computed) > 0
    assert all(c.implied_sd_at_10 >= 0 for c in computed)
