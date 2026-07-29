import csv
import sqlite3
import urllib.error

import pytest

import ingest_ffc_adp as ffc

_SAMPLE_TABLE_HTML = """
<table class="table adp freeze2">
    <tr>
      <th>#</th><th>Name</th><th>Pos</th><th>Team</th><th>Bye</th>
      <th>Overall</th><th>Std.Dev</th><th>High</th><th>Low</th><th>Times</th><th>Graph</th>
    </tr>
    <tr class='RB'>
        <td>1</td>
        <td class="!text-left adp-player-name" data-graph="5672:Jahmyr Gibbs">
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
        <td><input onclick="updatePlayer(5672, &quot;Jahmyr Gibbs&quot;);" type='checkbox' value='5672' /></td>
    </tr>
    <tr class='DEF'>
        <td>2</td>
        <td class="!text-left adp-player-name" >
          <a href="/players/seattle-defense">Seattle Defense</a>
        </td>
        <td>DEF</td>
        <td>SEA</td>
        <td class="d-none d-sm-table-cell">150.2</td>
        <td class="d-none d-sm-table-cell">5.6</td>
        <td class="d-none d-sm-table-cell">12.01</td>
        <td class="d-none d-sm-table-cell">14.03</td>
        <td class="d-none d-sm-table-cell">9</td>
        <td><input onclick="updatePlayer(9001, &quot;Seattle Defense&quot;);" type='checkbox' value='9001' /></td>
    </tr>
</table>
<p>Data from 1,187 fantasy football mock drafts between July 24, 2026 and  July 29, 2026.</p>
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


def test_parse_adp_table_extracts_rows_and_ffc_id():
    rows = ffc.parse_adp_table(_SAMPLE_TABLE_HTML)
    assert len(rows) == 2
    gibbs = rows[0]
    assert gibbs["player_name"] == "Jahmyr Gibbs"
    assert gibbs["position"] == "RB"
    assert gibbs["team"] == "DET"
    assert gibbs["bye"] == 6
    assert gibbs["average_pick"] == 1.4
    assert gibbs["ffc_player_id"] == "5672"


def test_parse_sample_window():
    total, window = ffc.parse_sample_window(_SAMPLE_TABLE_HTML)
    assert total == 1187
    assert window == "July 24, 2026 to July 29, 2026"


def test_parse_adp_table_empty_html_returns_empty_list():
    assert ffc.parse_adp_table("<html>no table here</html>") == []


def test_store_adp_resolves_matched_player_and_quarantines_unmatched():
    conn = _conn_with_ff_playerids()
    rows = ffc.parse_adp_table(_SAMPLE_TABLE_HTML)
    result = ffc.store_adp(
        conn, rows, period=2026, teams=10, fmt="half-ppr",
        is_retrospective_aggregate=False, as_of_date="2026-07-29",
        total_drafts_in_sample=1187, sample_window="July 24, 2026 to July 29, 2026",
    )
    assert result["stored"] == 1
    assert result["quarantined"] == 1

    stored = conn.execute(
        "SELECT adp_source, mfl_id, player_name, average_pick FROM ffc_adp_snapshots"
    ).fetchall()
    assert stored == [("ffc_half_ppr_10team", "16162", "Jahmyr Gibbs", 1.4)]

    quarantined = conn.execute(
        "SELECT player_name_raw, position, reason FROM ffc_adp_quarantine"
    ).fetchall()
    assert quarantined == [("Seattle Defense", "DEF", "no_name_match")]


def test_store_adp_never_writes_league_adp_or_mfl_proxy_source():
    """Never-blend rule: FFC rows carry only ffc_half_ppr_10team, never
    mfl_proxy or any merged/consensus value. CLAUDE.md SS4."""
    conn = _conn_with_ff_playerids()
    rows = ffc.parse_adp_table(_SAMPLE_TABLE_HTML)
    ffc.store_adp(
        conn, rows, period=2026, teams=10, fmt="half-ppr",
        is_retrospective_aggregate=False, as_of_date="2026-07-29",
        total_drafts_in_sample=1187, sample_window="w",
    )
    sources = {r[0] for r in conn.execute("SELECT DISTINCT adp_source FROM ffc_adp_snapshots")}
    assert sources == {"ffc_half_ppr_10team"}
    assert "mfl_proxy" not in sources
    assert "league_adp" not in sources


def test_retrospective_aggregate_is_flagged():
    conn = _conn_with_ff_playerids()
    rows = ffc.parse_adp_table(_SAMPLE_TABLE_HTML)
    ffc.store_adp(
        conn, rows, period=2023, teams=10, fmt="half-ppr",
        is_retrospective_aggregate=True, as_of_date="2026-07-29",
        total_drafts_in_sample=500, sample_window="w",
    )
    flag = conn.execute(
        "SELECT is_retrospective_aggregate FROM ffc_adp_snapshots"
    ).fetchone()[0]
    assert flag == 1


def test_already_fetched_today_false_when_empty():
    conn = sqlite3.connect(":memory:")
    conn.execute(ffc._CREATE_SQL)
    assert ffc.already_fetched_today(conn) is False


def test_already_fetched_today_true_after_store():
    conn = _conn_with_ff_playerids()
    rows = ffc.parse_adp_table(_SAMPLE_TABLE_HTML)
    ffc.store_adp(
        conn, rows, period=2026, teams=10, fmt="half-ppr",
        is_retrospective_aggregate=False, as_of_date="2026-07-29",
        total_drafts_in_sample=1187, sample_window="w",
    )
    assert ffc.already_fetched_today(conn, period=2026) is True
    assert ffc.already_fetched_today(conn, period=2019) is False


def test_network_failure_raises_loudly_and_writes_no_row(monkeypatch):
    def _boom(req, timeout=20):
        raise urllib.error.URLError("simulated network failure")

    monkeypatch.setattr(ffc.urllib.request, "urlopen", _boom)
    with pytest.raises(urllib.error.URLError):
        ffc.fetch_html(2026, max_retries=1)


def test_export_snapshot_csv_writes_one_row_per_stored_player(tmp_path):
    conn = _conn_with_ff_playerids()
    rows = ffc.parse_adp_table(_SAMPLE_TABLE_HTML)
    ffc.store_adp(
        conn, rows, period=2026, teams=10, fmt="half-ppr",
        is_retrospective_aggregate=False, as_of_date="2026-07-29",
        total_drafts_in_sample=1187, sample_window="w",
    )
    date_str = conn.execute(
        "SELECT substr(retrieved_at, 1, 10) FROM ffc_adp_snapshots LIMIT 1"
    ).fetchone()[0]
    db_path = tmp_path / "nfl.db"
    out = ffc.export_snapshot_csv(conn, db_path, date_str, period=2026)
    assert out == tmp_path / "adp-snapshots-ffc" / f"{date_str}.csv"
    assert out.exists()
    with out.open(newline="", encoding="utf-8") as f:
        csv_rows = list(csv.DictReader(f))
    assert len(csv_rows) == 1
    assert csv_rows[0]["adp_source"] == "ffc_half_ppr_10team"
    assert set(ffc._CSV_COLUMNS) == set(csv_rows[0].keys())


def test_export_snapshot_csv_returns_none_when_no_rows(tmp_path):
    conn = sqlite3.connect(":memory:")
    conn.execute(ffc._CREATE_SQL)
    db_path = tmp_path / "nfl.db"
    out = ffc.export_snapshot_csv(conn, db_path, "2026-07-27", period=2026)
    assert out is None
    assert not (tmp_path / "adp-snapshots-ffc").exists()


def test_import_snapshot_csv_round_trips_export(tmp_path):
    conn = _conn_with_ff_playerids()
    rows = ffc.parse_adp_table(_SAMPLE_TABLE_HTML)
    ffc.store_adp(
        conn, rows, period=2026, teams=10, fmt="half-ppr",
        is_retrospective_aggregate=False, as_of_date="2026-07-29",
        total_drafts_in_sample=1187, sample_window="w",
    )
    date_str = conn.execute(
        "SELECT substr(retrieved_at, 1, 10) FROM ffc_adp_snapshots LIMIT 1"
    ).fetchone()[0]
    db_path = tmp_path / "nfl.db"
    out = ffc.export_snapshot_csv(conn, db_path, date_str, period=2026)

    fresh_conn = sqlite3.connect(":memory:")
    n = ffc.import_snapshot_csv(fresh_conn, out)
    assert n == 1
    restored = fresh_conn.execute(
        "SELECT adp_source, mfl_id, player_name, average_pick FROM ffc_adp_snapshots"
    ).fetchall()
    original = conn.execute(
        "SELECT adp_source, mfl_id, player_name, average_pick FROM ffc_adp_snapshots"
    ).fetchall()
    assert restored == original


def test_import_all_snapshot_csvs_imports_every_file(tmp_path):
    conn = _conn_with_ff_playerids()
    rows = ffc.parse_adp_table(_SAMPLE_TABLE_HTML)
    ffc.store_adp(
        conn, rows, period=2026, teams=10, fmt="half-ppr",
        is_retrospective_aggregate=False, as_of_date="2026-07-29",
        total_drafts_in_sample=1187, sample_window="w",
    )
    date_str = conn.execute(
        "SELECT substr(retrieved_at, 1, 10) FROM ffc_adp_snapshots LIMIT 1"
    ).fetchone()[0]
    db_path = tmp_path / "nfl.db"
    ffc.export_snapshot_csv(conn, db_path, date_str, period=2026)
    snap_dir = ffc.snapshot_dir_for_db(db_path)

    fresh_conn = sqlite3.connect(":memory:")
    results = ffc.import_all_snapshot_csvs(fresh_conn, snap_dir)
    assert sum(results.values()) == 1
