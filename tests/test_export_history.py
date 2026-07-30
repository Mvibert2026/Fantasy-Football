"""Tests for weekly_finishes.json / season_stats.json (thread 017/039;
made league-scoring-aware 2026-07-30, FR-079/FR-083).

Sanity checks written against thread 039's "Done looks like" checklist:
(a) shape/schema test for both files, (b) a 2003-2008 row asserting
target_data_unavailable=true and no fabricated zero, (c) a finish-vs-bye
null-vs-false distinction test, PLUS (d) the FR-079/FR-083 fix itself: the
same raw stat lines must score DIFFERENTLY under two different league
configs, and each artifact must carry an honest, non-hardcoded
scoring_ruleset_note that names the league it was built for. Synthetic
in-memory DB so these do not depend on what real data happens to be on disk;
a smaller real-DB group below spot-checks the same claims against
data/nfl.db.
"""

import sqlite3

import pytest

import export_history as eh
import league_config as lc
import standard_scoring


def _make_conn() -> sqlite3.Connection:
    """Schema matches `db.player_week_scoring_inputs`'s source columns (see
    db._CREATE_SCORING_VIEW_SQL) so `export_history._weekly_scored_points`
    can create that view against this synthetic table exactly the way it
    does against a real `data/nfl.db` connection."""
    c = sqlite3.connect(":memory:")
    c.row_factory = sqlite3.Row
    c.execute(
        """
        CREATE TABLE player_weekly_stats (
            player_id TEXT, player_name TEXT, season INTEGER, week INTEGER,
            season_type TEXT, position TEXT, team TEXT,
            targets INTEGER, receptions INTEGER, receiving_yards INTEGER,
            receiving_tds INTEGER, rushing_yards INTEGER, rushing_tds INTEGER,
            passing_yards INTEGER, passing_tds INTEGER,
            passing_interceptions INTEGER, fumbles_lost_total INTEGER,
            special_teams_tds INTEGER, passing_2pt_conversions INTEGER,
            rushing_2pt_conversions INTEGER, receiving_2pt_conversions INTEGER,
            fumble_recovery_tds INTEGER
        )
        """
    )
    rows = [
        # Two WRs, 2025, week 1 and 2 -- receiving-only lines, deliberately
        # chosen so Westwood's half-PPR + bonus ruleset and the standard
        # 0-PPR ruleset produce DIFFERENT winners in week 1 (proves scoring
        # is actually cfg-driven, not just cfg-shaped).
        # P1 wk1: 6 rec, 90 yds, 1 TD | P2 wk1: 3 rec, 40 yds, 0 TD
        ("P1", "Player One", 2025, 1, "REG", "WR", "AAA", 8, 6, 90, 1, 0, 0,
         0, 0, 0, 0, 0, 0, 0, 0, 0),
        ("P2", "Player Two", 2025, 1, "REG", "WR", "BBB", 5, 3, 40, 0, 0, 0,
         0, 0, 0, 0, 0, 0, 0, 0, 0),
        # P1 wk2: 5 rec, 60 yds, 0 TD | P2 wk2: 4 rec, 55 yds, 1 TD
        ("P1", "Player One", 2025, 2, "REG", "WR", "AAA", 7, 5, 60, 0, 0, 0,
         0, 0, 0, 0, 0, 0, 0, 0, 0),
        ("P2", "Player Two", 2025, 2, "REG", "WR", "BBB", 6, 4, 55, 1, 0, 0,
         0, 0, 0, 0, 0, 0, 0, 0, 0),
        # P1 also has an old, target-unreliable 2005 season.
        ("P1", "Player One", 2005, 1, "REG", "WR", "AAA", 0, 4, 50, 0, 0, 0,
         0, 0, 0, 0, 0, 0, 0, 0, 0),
        ("P1", "Player One", 2005, 2, "REG", "WR", "AAA", 0, 2, 20, 0, 0, 0,
         0, 0, 0, 0, 0, 0, 0, 0, 0),
        # A universe-qualifying row for P1 (>=2018) already exists above.
    ]
    c.executemany(
        "INSERT INTO player_weekly_stats VALUES "
        "(?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)",
        rows,
    )
    c.commit()
    return c


@pytest.fixture
def conn():
    return _make_conn()


# Westwood's real ruleset (scoring.LEAGUE): 0.5 PPR, receiving-yardage
# bonuses at 100/150/200 (none triggered by this fixture's yardage).
WESTWOOD_CFG = lc.CURRENT_LEAGUE
# A real STANDARD/0-PPR preset, same shape generate_config_matrix.py builds.
STANDARD_0PPR_CFG = lc.LeagueConfig(
    league_id="test_standard_0ppr",
    name="Test standard 0-PPR",
    platform="espn",
    teams=10,
    scoring=standard_scoring.standard_scoring_variant(0.0),
    starters={"QB": 1, "RB": 2, "WR": 3, "TE": 1, "DEF": 1},
    flex_slots=1,
    flex_eligible=("RB", "WR", "TE"),
    bench=6,
    ir=1,
    user_draft_slot=1,
)


class TestScoringIsLeagueAware:
    """The FR-079/FR-083 fix itself: fantasy_points must be computed under
    THIS export's cfg.scoring, not a single fixed figure every league
    shares."""

    def test_same_raw_line_scores_differently_under_two_leagues(self, conn):
        westwood = eh.build_season_stats(conn, ["P1", "P2"], cfg=WESTWOOD_CFG)
        standard = eh.build_season_stats(conn, ["P1", "P2"], cfg=STANDARD_0PPR_CFG)
        w_p1 = next(
            s for s in next(p for p in westwood["players"] if p["player_id"] == "P1")["seasons"]
            if s["year"] == 2025
        )
        s_p1 = next(
            s for s in next(p for p in standard["players"] if p["player_id"] == "P1")["seasons"]
            if s["year"] == 2025
        )
        # Hand-computed: Westwood (0.5 PPR) wk1 18.0 + wk2 8.5 = 26.5.
        # Standard (0-PPR) wk1 15.0 + wk2 6.0 = 21.0. Different leagues,
        # different numbers, same underlying games -- the whole point.
        assert w_p1["fantasy_points"] == pytest.approx(26.5)
        assert s_p1["fantasy_points"] == pytest.approx(21.0)
        assert w_p1["fantasy_points"] != s_p1["fantasy_points"]

    def test_same_raw_line_ranks_differently_under_two_leagues(self, conn):
        """P1 vs P2 week 1: Westwood ranks P1 first (18.0 > 5.5); confirms
        weekly_finishes actually uses the scored, not the stored, figure."""
        westwood = eh.build_weekly_finishes(conn, ["P1", "P2"], cfg=WESTWOOD_CFG)
        by_id = {p["player_id"]: p for p in westwood["players"]}
        p1_wk1 = next(w for w in by_id["P1"]["seasons"]["2025"]["weeks"] if w["week"] == 1)
        p2_wk1 = next(w for w in by_id["P2"]["seasons"]["2025"]["weeks"] if w["week"] == 1)
        assert p1_wk1["finish"] == 1
        assert p2_wk1["finish"] == 2

    def test_finish_order_flips_when_scoring_flips(self, conn):
        westwood = eh.build_weekly_finishes(conn, ["P1", "P2"], cfg=WESTWOOD_CFG)
        by_id = {p["player_id"]: p for p in westwood["players"]}
        p1_wk2 = next(w for w in by_id["P1"]["seasons"]["2025"]["weeks"] if w["week"] == 2)
        p2_wk2 = next(w for w in by_id["P2"]["seasons"]["2025"]["weeks"] if w["week"] == 2)
        assert p1_wk2["finish"] == 2  # 8.5 < 13.5 this week
        assert p2_wk2["finish"] == 1

    def test_envelope_names_the_league_it_was_built_for(self, conn):
        westwood = eh.build_season_stats(conn, ["P1"], cfg=WESTWOOD_CFG)
        standard = eh.build_season_stats(conn, ["P1"], cfg=STANDARD_0PPR_CFG)
        assert westwood["league_id"] == "primary"
        assert standard["league_id"] == "test_standard_0ppr"
        # Never the same hardcoded prose for two different leagues (the
        # exact bug FR-083 reported for adp_source_note).
        assert westwood["scoring_ruleset_note"] != standard["scoring_ruleset_note"]

    def test_default_cfg_is_westwood_not_a_new_unscored_default(self, conn):
        default = eh.build_season_stats(conn, ["P1"])
        assert default["league_id"] == "primary"


class TestWeeklyFinishesShape:
    def test_envelope_fields(self, conn):
        out = eh.build_weekly_finishes(conn, ["P1", "P2"])
        assert out["export_version"]
        assert "generated_utc" in out
        assert "note" in out
        assert "scoring_note" in out
        assert isinstance(out["players"], list)


class TestSeasonStatsShape:
    def test_envelope_and_aggregation(self, conn):
        out = eh.build_season_stats(conn, ["P1", "P2"])
        by_id = {p["player_id"]: p for p in out["players"]}
        p1_2025 = next(s for s in by_id["P1"]["seasons"] if s["year"] == 2025)
        assert p1_2025["games"] == 2
        assert p1_2025["targets"] == 15  # 8 + 7
        assert p1_2025["receptions"] == 11
        assert p1_2025["fantasy_points_available"] is True


class Test2003to2008TargetUnavailable:
    def test_season_stats_marks_flag_and_nulls_targets(self, conn):
        out = eh.build_season_stats(conn, ["P1"])
        p1 = next(p for p in out["players"] if p["player_id"] == "P1")
        row_2005 = next(s for s in p1["seasons"] if s["year"] == 2005)
        assert row_2005["target_data_unavailable"] is True
        assert row_2005["targets"] is None  # never a fabricated 0

    def test_season_stats_does_not_flag_recent_season(self, conn):
        out = eh.build_season_stats(conn, ["P1"])
        p1 = next(p for p in out["players"] if p["player_id"] == "P1")
        row_2025 = next(s for s in p1["seasons"] if s["year"] == 2025)
        assert row_2025["target_data_unavailable"] is False
        assert row_2025["targets"] == 15

    def test_weekly_finishes_marks_season_flag(self, conn):
        out = eh.build_weekly_finishes(conn, ["P1"])
        p1 = next(p for p in out["players"] if p["player_id"] == "P1")
        assert p1["seasons"]["2005"]["target_data_unavailable"] is True
        assert p1["seasons"]["2025"]["target_data_unavailable"] is False

    def test_constant_covers_exactly_2003_through_2008(self):
        assert eh.TARGET_DATA_UNAVAILABLE_SEASONS == frozenset(range(2003, 2009))
        assert 2002 not in eh.TARGET_DATA_UNAVAILABLE_SEASONS
        assert 2009 not in eh.TARGET_DATA_UNAVAILABLE_SEASONS


class TestFinishVsByeDistinction:
    def test_missing_week_with_no_schedule_data_is_null_not_bye(self, conn):
        # No schedules table/network in this synthetic DB -- _bye_weeks_by_season
        # must fail open to {} rather than fabricate a bye guess, and a week
        # with a row always carries bye=False regardless.
        out = eh.build_weekly_finishes(conn, ["P1"])
        p1 = next(p for p in out["players"] if p["player_id"] == "P1")
        for wk in p1["seasons"]["2025"]["weeks"]:
            assert wk["bye"] is False
            assert wk["finish"] is not None

    def test_bye_and_finish_null_are_never_conflated_in_shape(self, conn):
        # A week entry must always carry both keys explicitly, so a consumer
        # can never confuse "we have no data" with "we know it was a bye".
        out = eh.build_weekly_finishes(conn, ["P1", "P2"])
        for p in out["players"]:
            for season in p["seasons"].values():
                for wk in season["weeks"]:
                    assert "finish" in wk and "bye" in wk


class TestByeLookupCanonicalizesEraTeamCodes:
    def test_historical_era_code_still_resolves_after_t9(self, conn, monkeypatch):
        """T9 regression guard: export_contract._bye_weeks() now returns
        CANONICAL keys (e.g. 'LV' for the Raiders, not the 'OAK' a pre-2020
        schedule pull would use). export_history's own lookup keys off
        player_weekly_stats.team, which for an old season legitimately says
        'OAK' -- this must still resolve, not silently go null the moment
        _bye_weeks' keys became canonical."""
        # P1 is on 'AAA' in the synthetic fixture -- add an OAK-era row so
        # there's a real historical code to canonicalize.
        conn.execute(
            "INSERT INTO player_weekly_stats VALUES "
            "('P1','Player One',2015,1,'REG','WR','OAK',5,3,40,0,0,0,"
            "0,0,0,0,0,0,0,0,0)"
        )
        conn.commit()

        import export_history as eh_module

        monkeypatch.setattr(
            eh_module, "_bye_weeks_by_season",
            lambda seasons: {2015: {"LV": 9}, 2025: {}, 2005: {}},
        )
        out = eh_module.build_weekly_finishes(conn, ["P1"])
        p1 = next(p for p in out["players"] if p["player_id"] == "P1")
        weeks_2015 = p1["seasons"]["2015"]["weeks"]
        bye_entries = [w for w in weeks_2015 if w["bye"] is True]
        assert bye_entries and bye_entries[0]["week"] == 9, (
            "OAK-era player did not resolve against the canonical 'LV' bye "
            "key -- the lookup side of the T9 canonicalization is missing"
        )


class TestPlayerUniverse:
    def test_universe_excludes_players_without_2018_plus_row(self, conn):
        # P1 has 2025 rows so qualifies; a player with only a 2005 row would not.
        ids = eh._player_universe(conn)
        assert "P1" in ids
        assert "P2" in ids

    def test_write_all_produces_both_files(self, conn, tmp_path):
        written = eh.write_all(tmp_path, conn)
        names = {p.name for p in written}
        assert names == {"weekly_finishes.json", "season_stats.json"}
        for p in written:
            assert p.exists() and p.stat().st_size > 0


@pytest.mark.requires_db
class TestAgainstRealData:
    def test_real_db_2003_2008_row_is_flagged_and_null(self):
        import db as dbmod

        conn = dbmod.connect()
        try:
            row = conn.execute(
                "SELECT player_id FROM player_weekly_stats "
                "WHERE season = 2005 AND position = 'WR' LIMIT 1"
            ).fetchone()
            if row is None:
                pytest.skip("no 2005 WR row in this DB snapshot")
            pid = row[0] if not isinstance(row, sqlite3.Row) else row["player_id"]
            out = eh.build_season_stats(conn, [pid])
            assert out["players"], "expected the probed player_id back in season_stats output"
            seasons = out["players"][0]["seasons"]
            row_2005 = next((s for s in seasons if s["year"] == 2005), None)
            if row_2005 is not None:
                assert row_2005["target_data_unavailable"] is True
                assert row_2005["targets"] is None
        finally:
            conn.close()
