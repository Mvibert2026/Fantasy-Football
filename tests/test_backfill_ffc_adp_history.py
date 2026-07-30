import sqlite3
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO / "tools"))
sys.path.insert(0, str(REPO / "src"))

import backfill_ffc_adp_history as bf  # noqa: E402
import ingest_ffc_adp as ffc  # noqa: E402


def test_parse_window_end_date_extracts_trailing_date():
    assert bf._parse_window_end_date("September 2, 2013 to September 4, 2013") == "2013-09-04"
    assert bf._parse_window_end_date("August 28, 2018 to  September 4, 2018") == "2018-09-04"


def test_parse_window_end_date_returns_none_when_unparseable():
    assert bf._parse_window_end_date("") is None
    assert bf._parse_window_end_date(None) is None
    assert bf._parse_window_end_date("nonsense with no dates") is None


def test_gate_fail_seasons_never_in_the_fetch_plan():
    """2007-2009, 2011, 2012 fail the look-ahead gate and must never be
    fetched (CLAUDE.md SS6.1) -- confirm they are excluded from the season
    lists driving the plan, not merely dropped after a fetch."""
    for y in (2007, 2008, 2009, 2011, 2012):
        assert y not in bf.NON_PPR_SEASONS


def test_content_invalid_2010_excluded_despite_passing_date_gate():
    assert 2010 not in bf.NON_PPR_SEASONS
    assert 2010 in bf.NON_PPR_CONTENT_INVALID


def test_half_ppr_seasons_start_2018_no_earlier_archive():
    assert bf.HALF_PPR_SEASONS == list(range(2018, 2025))


def test_non_ppr_seasons_are_2013_through_2024_minus_exclusions():
    excluded = set(bf.NON_PPR_GATE_FAIL) | set(bf.NON_PPR_CONTENT_INVALID)
    expected = [y for y in range(2013, 2025) if y not in excluded]
    assert bf.NON_PPR_SEASONS == expected


def test_ppr_seasons_are_2013_through_2024_minus_exclusions():
    """Added 2026-07-30 (FR-087): PPR shares the non-PPR season-level gate
    (kickoff dates are format-independent) plus its own independently
    re-verified content-validity exclusion for 2010."""
    excluded = set(bf.PPR_GATE_FAIL) | set(bf.PPR_CONTENT_INVALID)
    expected = [y for y in range(2013, 2025) if y not in excluded]
    assert bf.PPR_SEASONS == expected


def test_ppr_content_invalid_2010_excluded_despite_passing_date_gate():
    assert 2010 not in bf.PPR_SEASONS
    assert 2010 in bf.PPR_CONTENT_INVALID


def test_ppr_format_key_is_registered():
    assert "ppr" in bf.FORMAT_SLUGS
    assert bf.FORMAT_SLUGS["ppr"] == "ppr"


_SAMPLE_HTML = """
<table class="table adp freeze2">
    <tr>
      <th>#</th><th>Name</th><th>Pos</th><th>Team</th><th>Bye</th>
      <th>Overall</th><th>Std.Dev</th><th>High</th><th>Low</th><th>Times</th><th>Graph</th>
    </tr>
    <tr class='RB'>
        <td>1</td>
        <td class="!text-left adp-player-name">
          <a href="/players/jahmyr-gibbs">Jahmyr Gibbs</a>
        </td>
        <td>RB</td>
        <td>DET</td>
        <td>6</td>
        <td class="d-none d-sm-table-cell">1.4</td>
        <td class="d-none d-sm-table-cell">0.6</td>
        <td class="d-none d-sm-table-cell">1.01</td>
        <td class="d-none d-sm-table-cell">1.03</td>
        <td class="d-none d-sm-table-cell">132</td>
        <td></td>
    </tr>
</table>
<p>Data from 992 fantasy football mock drafts between September 2, 2013 and September 4, 2013.</p>
"""


def _conn_with_ff_playerids():
    conn = sqlite3.connect(":memory:")
    conn.execute(
        "CREATE TABLE ff_playerids (mfl_id TEXT, name TEXT, position TEXT, team TEXT, "
        "birthdate TEXT, gsis_id TEXT, pfr_id TEXT, espn_id TEXT, yahoo_id TEXT, "
        "sleeper_id TEXT, fantasypros_id TEXT, sportradar_id TEXT)"
    )
    conn.executemany(
        "INSERT INTO ff_playerids (mfl_id, name, position, team) VALUES (?,?,?,?)",
        [("16162", "Jahmyr Gibbs", "RB", "DET")],
    )
    conn.commit()
    return conn


def test_backfill_one_stores_with_window_end_as_of_date(tmp_path, monkeypatch):
    conn = _conn_with_ff_playerids()
    monkeypatch.setattr(bf, "_fetch_cached", lambda format_key, season, refresh: _SAMPLE_HTML)
    db_path = tmp_path / "nfl.db"
    result = bf.backfill_one(conn, db_path, "non_ppr", 2013, refresh=False)

    assert result["dropped_no_data"] is False
    assert result["as_of_date"] == "2013-09-04"  # window END date, not "today"
    assert result["adp_source"] == "ffc_non_ppr_12team"

    row = conn.execute(
        "SELECT as_of_date, sample_window, teams, format FROM ffc_adp_snapshots "
        "WHERE adp_source='ffc_non_ppr_12team'"
    ).fetchone()
    assert row[0] == "2013-09-04"
    assert row[1] == "September 2, 2013 to September 4, 2013"
    assert row[2] == 12
    assert row[3] == "standard"


def test_backfill_one_never_blends_12team_into_10team_source(tmp_path, monkeypatch):
    conn = _conn_with_ff_playerids()
    monkeypatch.setattr(bf, "_fetch_cached", lambda format_key, season, refresh: _SAMPLE_HTML)
    db_path = tmp_path / "nfl.db"
    bf.backfill_one(conn, db_path, "non_ppr", 2013, refresh=False)
    sources = {r[0] for r in conn.execute("SELECT DISTINCT adp_source FROM ffc_adp_snapshots")}
    assert sources == {"ffc_non_ppr_12team"}
    assert "ffc_non_ppr_10team" not in sources


def test_backfill_one_drops_when_window_unparseable(tmp_path, monkeypatch):
    bad_html = _SAMPLE_HTML.replace(
        "Data from 992 fantasy football mock drafts between September 2, 2013 and September 4, 2013.",
        "",
    )
    conn = _conn_with_ff_playerids()
    monkeypatch.setattr(bf, "_fetch_cached", lambda format_key, season, refresh: bad_html)
    db_path = tmp_path / "nfl.db"
    result = bf.backfill_one(conn, db_path, "non_ppr", 2013, refresh=False)
    assert result["dropped_no_data"] is True
    assert "dropped, not dated" in result["reason"]
    has_table = conn.execute(
        "SELECT 1 FROM sqlite_master WHERE type='table' AND name='ffc_adp_snapshots'"
    ).fetchone()
    assert has_table is None or conn.execute(
        "SELECT COUNT(*) FROM ffc_adp_snapshots"
    ).fetchone()[0] == 0
