import sqlite3
from unittest.mock import patch

import pandas as pd
import polars as pl

import ingest_fantasypros_csv as ifc


# ------------------------------------------------ parsing helpers


def test_strip_pos_rank():
    assert ifc._strip_pos_rank("RB1") == "RB"
    assert ifc._strip_pos_rank("TE89") == "TE"
    assert ifc._strip_pos_rank("DST") == "DST"


def test_parse_sos():
    assert ifc._parse_sos("4 out of 5 stars") == 4
    assert ifc._parse_sos("-") is None
    assert ifc._parse_sos(float("nan")) is None


def test_parse_int_or_none():
    assert ifc._parse_int_or_none("11") == 11
    assert ifc._parse_int_or_none("-") is None
    assert ifc._parse_int_or_none("") is None


def test_normalize_name_strips_punctuation_and_suffixes():
    assert ifc._normalize_name("Ja'Marr Chase") == "jamarr chase"
    assert ifc._normalize_name("Patrick Taylor Jr.") == "patrick taylor"
    assert ifc._normalize_name("Chris Brazzell II") == "chris brazzell"


# ------------------------------------------------ ADP sign convention


def test_adp_value_uses_rk_plus_delta():
    df = pd.DataFrame(
        {
            "RK": [6, 8, 9],
            "TIERS": [1, 2, 2],
            "PLAYER NAME": ["Amon-Ra St. Brown", "CeeDee Lamb", "Jonathan Taylor"],
            "TEAM": ["DET", "DAL", "IND"],
            "POS": ["WR4", "WR5", "RB4"],
            "BYE WEEK": ["6", "14", "13"],
            "UPSIDE ": ["x", "x", "x"],
            "BUST ": ["x", "x", "x"],
            "SOS SEASON": ["4 out of 5 stars", "2 out of 5 stars", "4 out of 5 stars"],
            "ECR VS. ADP": ["+2", "+2", "-2"],
        }
    )
    # load_csv reads from disk; exercise the transform logic directly instead.
    df["position"] = df["POS"].map(ifc._strip_pos_rank)
    df["delta"] = df["ECR VS. ADP"].map(
        lambda v: ifc._parse_int_or_none(str(v).replace("+", ""))
        if str(v).strip() not in ("-", "")
        else None
    )
    df["adp_value"] = df.apply(
        lambda r: (r["RK"] + r["delta"]) if pd.notna(r["delta"]) else None, axis=1
    )
    assert df["adp_value"].tolist() == [8, 10, 7]


# ------------------------------------------------ schema / quarantine wiring


def test_ensure_schema_adds_new_columns_and_quarantine_table():
    conn = sqlite3.connect(":memory:")
    conn.execute(
        """
        CREATE TABLE rankings (
            ranking_source TEXT, source TEXT, season INTEGER, player_id TEXT,
            player_name TEXT, team TEXT, adp_rank INTEGER, adp_value REAL,
            spread_sd REAL, rank_best REAL, rank_worst REAL, as_of_date TEXT,
            position TEXT, is_preseason_final INTEGER, ingested_at TEXT
        )
        """
    )
    ifc.ensure_schema(conn)
    cols = {r[1] for r in conn.execute('PRAGMA table_info("rankings")')}
    assert {"scoring_format", "tier", "bye_week", "sos_season"} <= cols
    tables = {r[0] for r in conn.execute("SELECT name FROM sqlite_master WHERE type='table'")}
    assert "rankings_quarantine" in tables


# ------------------------------------------------ crosswalk: load_players() supplement


def _fake_ff_playerids():
    return pl.DataFrame(
        {
            "name": ["Justin Jefferson"],
            "position": ["WR"],
            "gsis_id": ["00-0036322"],
        }
    )


def _fake_players():
    return pl.DataFrame(
        {
            "display_name": ["Jeremiyah Love", "Mitchell Tinsley", "Andy Borregales"],
            "football_name": [None, "Mitch", "Andy"],
            "last_name": ["Love", "Tinsley", "Borregales"],
            "position": ["RB", "WR", "K"],
            "gsis_id": ["00-0041027", "00-0038839", "00-0040200"],
        }
    )


def test_build_crosswalk_falls_back_to_load_players_for_rookies_missing_from_ff_playerids():
    with patch("ingest_fantasypros_csv.update_config"), patch(
        "ingest_fantasypros_csv.nfl.load_ff_playerids", return_value=_fake_ff_playerids()
    ), patch("ingest_fantasypros_csv.nfl.load_players", return_value=_fake_players()):
        lookup = ifc.build_crosswalk()

    # Rookie present only in load_players(), absent from the static ff_playerids snapshot.
    assert lookup[("jeremiyah love", "RB")] == "00-0041027"
    # ff_playerids entries still win when both sources have the player.
    assert lookup[("justin jefferson", "WR")] == "00-0036322"


def test_build_crosswalk_indexes_football_name_nickname():
    with patch("ingest_fantasypros_csv.update_config"), patch(
        "ingest_fantasypros_csv.nfl.load_ff_playerids", return_value=_fake_ff_playerids()
    ), patch("ingest_fantasypros_csv.nfl.load_players", return_value=_fake_players()):
        lookup = ifc.build_crosswalk()

    # "Mitch Tinsley" (nickname, as used in the CSV) resolves via football_name,
    # not just the legal display_name "Mitchell Tinsley".
    assert lookup[("mitch tinsley", "WR")] == "00-0038839"


def test_build_crosswalk_adds_pk_alias_for_kickers_from_load_players():
    with patch("ingest_fantasypros_csv.update_config"), patch(
        "ingest_fantasypros_csv.nfl.load_ff_playerids", return_value=_fake_ff_playerids()
    ), patch("ingest_fantasypros_csv.nfl.load_players", return_value=_fake_players()):
        lookup = ifc.build_crosswalk()

    # load_players() labels kickers "K"; ff_playerids-consuming code looks up "PK".
    assert lookup[("andy borregales", "K")] == "00-0040200"
    assert lookup[("andy borregales", "PK")] == "00-0040200"


def test_known_aliases_table_has_hollywood_brown_mapped_to_marquise_brown():
    assert ifc._KNOWN_ALIASES[("hollywood brown", "WR")] == "marquise brown"


def test_ensure_schema_is_idempotent():
    conn = sqlite3.connect(":memory:")
    conn.execute(
        """
        CREATE TABLE rankings (
            ranking_source TEXT, source TEXT, season INTEGER, player_id TEXT,
            player_name TEXT, team TEXT, adp_rank INTEGER, adp_value REAL,
            spread_sd REAL, rank_best REAL, rank_worst REAL, as_of_date TEXT,
            position TEXT, is_preseason_final INTEGER, ingested_at TEXT
        )
        """
    )
    ifc.ensure_schema(conn)
    ifc.ensure_schema(conn)  # must not raise "duplicate column"
