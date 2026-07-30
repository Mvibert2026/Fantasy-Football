import sqlite3
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO / "src"))

import ingest_coordinators_wikipedia as w  # noqa: E402


def test_team_article_name_handles_franchise_moves_and_renames():
    assert w._team_article_name("LA", 2015) == "St. Louis Rams"
    assert w._team_article_name("LA", 2016) == "Los Angeles Rams"
    assert w._team_article_name("LAC", 2016) == "San Diego Chargers"
    assert w._team_article_name("LAC", 2017) == "Los Angeles Chargers"
    assert w._team_article_name("LV", 2019) == "Oakland Raiders"
    assert w._team_article_name("LV", 2020) == "Las Vegas Raiders"
    assert w._team_article_name("WAS", 2019) == "Washington Redskins"
    assert w._team_article_name("WAS", 2020) == "Washington Football Team"
    assert w._team_article_name("WAS", 2022) == "Washington Commanders"


def test_team_article_name_unmapped_team_raises():
    import pytest
    with pytest.raises(KeyError):
        w._team_article_name("XYZ", 2020)


_SAMPLE_WIKITEXT = """
==Staff==
{{NFL final staff
|Year=2024
|TeamName=Atlanta Falcons
|Head Coaches=
*Head coach – [[Raheem Morris]]
*Assistant head coach/defense – [[Jerry Gray]]
|Offensive Coaches=
*Offensive coordinator – [[Zac Robinson]]
*Quarterbacks – [[T. J. Yates]]
|Defensive Coaches=
*Defensive coordinator – [[Jimmy Lake]]
*Defensive line – [[Jay Rodgers]]
}}
"""


def test_parse_staff_extracts_hc_oc_dc_from_wikilinks():
    result = w.parse_staff(_SAMPLE_WIKITEXT)
    assert result["template_found"] is True
    assert result["head_coach"] == "Raheem Morris"
    assert result["oc"] == "Zac Robinson"
    assert result["dc"] == "Jimmy Lake"


def test_parse_staff_no_template_returns_all_none():
    result = w.parse_staff("Some article text with no staff template at all.")
    assert result["template_found"] is False
    assert result["oc"] is None
    assert result["dc"] is None


_COMPOUND_TITLE_WIKITEXT = """
==Staff==
{{NFL final staff
|Year=2023
|TeamName=Washington Commanders
|Head Coaches=
* Head coach – [[Ron Rivera]]
* Assistant head coach/offensive coordinator – [[Eric Bieniemy]]
|Defensive Coaches=
* Defensive coordinator – Ron Rivera (interim)
}}
"""


def test_parse_staff_matches_compound_title_oc():
    """Verified real case, WAS 2023: the OC field can be compounded with
    another title on the same bullet ('Assistant head coach/offensive
    coordinator'), not a standalone 'Offensive coordinator –' line."""
    result = w.parse_staff(_COMPOUND_TITLE_WIKITEXT)
    assert result["oc"] == "Eric Bieniemy"


def test_parse_staff_strips_parenthetical_and_dc_name_survives():
    result = w.parse_staff(_COMPOUND_TITLE_WIKITEXT)
    assert result["dc"] == "Ron Rivera"


def test_clean_name_returns_none_for_junk():
    assert w._clean_name("") is None
    assert w._clean_name("x" * 90) is None


def test_clean_name_prefers_wikilink_display_text():
    assert w._clean_name("[[Kyle Smith (American football)|Kyle Smith]]") == "Kyle Smith"


def _make_conn():
    conn = sqlite3.connect(":memory:")
    return conn


def test_ingest_stores_separate_oc_and_dc_rows_same_team_season(monkeypatch, tmp_path):
    """Regression test for the PK collision found 2026-07-30: OC and DC for
    the same (team, season, start_week) must not overwrite each other."""
    db_path = tmp_path / "test.db"

    def fake_fetch(team, season, refresh=False):
        return _SAMPLE_WIKITEXT

    def fake_season_end(season):
        return "2025-01-05"

    monkeypatch.setattr(w, "_fetch_wikitext", fake_fetch)
    result = w.ingest(range(2024, 2025), teams=["ATL"], db_path=db_path)
    assert result["stored"] == 2  # OC + DC, one row each
    conn = sqlite3.connect(db_path)
    rows = conn.execute(
        "SELECT team, season, play_caller, title FROM play_callers ORDER BY title"
    ).fetchall()
    conn.close()
    assert rows == [
        ("ATL", 2024, "Jimmy Lake", "DC"),
        ("ATL", 2024, "Zac Robinson", "OC"),
    ]


def test_ingest_flags_every_row_as_final_season_snapshot(tmp_path, monkeypatch):
    db_path = tmp_path / "test2.db"
    monkeypatch.setattr(w, "_fetch_wikitext", lambda team, season, refresh=False: _SAMPLE_WIKITEXT)
    w.ingest(range(2024, 2025), teams=["ATL"], db_path=db_path)
    conn = sqlite3.connect(db_path)
    flags = [r[0] for r in conn.execute("SELECT is_final_season_snapshot FROM play_callers")]
    conn.close()
    assert flags == [1, 1]


def test_ingest_quarantines_missing_article(tmp_path, monkeypatch):
    db_path = tmp_path / "test3.db"
    monkeypatch.setattr(w, "_fetch_wikitext", lambda team, season, refresh=False: None)
    result = w.ingest(range(2024, 2025), teams=["ATL"], db_path=db_path)
    assert result["stored"] == 0
    assert result["no_page"] == 1
    conn = sqlite3.connect(db_path)
    reasons = [r[0] for r in conn.execute("SELECT reason FROM coordinator_quarantine")]
    conn.close()
    assert reasons == ["wikipedia_article_not_found"]
