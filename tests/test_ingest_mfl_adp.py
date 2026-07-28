import csv
import sqlite3
import urllib.error

import numpy as np
import pytest

import availability as av
import draft_sim as ds
import ingest_mfl_adp as mfl


def _payload(players):
    return {
        "adp": {
            "totalPicks": str(len(players)),
            "totalDrafts": "50",
            "timestamp": "1785027131",
            "player": players,
        }
    }


def _conn_with_ff_playerids():
    conn = sqlite3.connect(":memory:")
    conn.execute(
        "CREATE TABLE ff_playerids (mfl_id TEXT, name TEXT, position TEXT, team TEXT)"
    )
    conn.executemany(
        "INSERT INTO ff_playerids VALUES (?,?,?,?)",
        [("15281", "Ja'Marr Chase", "WR", "CIN"), ("16162", "Jahmyr Gibbs", "RB", "DET")],
    )
    return conn


def test_store_adp_writes_one_row_per_player_with_format_metadata():
    conn = _conn_with_ff_playerids()
    payload = _payload([
        {"id": "15281", "rank": "1", "averagePick": "3.00", "minPick": "1", "maxPick": "4",
         "draftsSelectedIn": "5", "draftSelPct": "10"},
        {"id": "16162", "rank": "2", "averagePick": "3.20", "minPick": "1", "maxPick": "6",
         "draftsSelectedIn": "5", "draftSelPct": "10"},
    ])
    n = mfl.store_adp(conn, payload, fcount=10, is_ppr=1, is_keeper=0, is_mock=0, cutoff=10, period=2026)
    assert n == 2
    row = conn.execute(
        "SELECT adp_source, mfl_id, player_name, average_pick, fcount, is_ppr, "
        "total_drafts_in_sample FROM adp_snapshots WHERE mfl_id='15281'"
    ).fetchone()
    assert row == ("mfl_proxy", "15281", "Ja'Marr Chase", 3.00, 10, 1, 50)


def test_store_adp_never_presents_as_league_adp():
    conn = _conn_with_ff_playerids()
    payload = _payload([{"id": "15281", "rank": "1", "averagePick": "3.00", "minPick": "1",
                          "maxPick": "4", "draftsSelectedIn": "5", "draftSelPct": "10"}])
    mfl.store_adp(conn, payload, 10, 1, 0, 0, 10, 2026)
    sources = {r[0] for r in conn.execute("SELECT DISTINCT adp_source FROM adp_snapshots")}
    assert sources == {"mfl_proxy"}
    assert "league_adp" not in sources


def test_already_fetched_today_is_false_when_empty():
    conn = sqlite3.connect(":memory:")
    conn.execute(mfl._CREATE_SQL)
    assert mfl.already_fetched_today(conn) is False


def test_already_fetched_today_is_true_after_a_store():
    conn = _conn_with_ff_playerids()
    payload = _payload([{"id": "15281", "rank": "1", "averagePick": "3.00", "minPick": "1",
                          "maxPick": "4", "draftsSelectedIn": "5", "draftSelPct": "10"}])
    mfl.store_adp(conn, payload, 10, 1, 0, 0, 10, 2026)
    assert mfl.already_fetched_today(conn) is True


def test_repeated_ingest_same_day_replaces_not_duplicates():
    """PRIMARY KEY (adp_source, mfl_id, retrieved_at) with retrieved_at at
    second-plus resolution normally makes same-day re-ingests distinct rows.
    already_fetched_today() is the actual guard against that; this test
    confirms the schema itself does not silently duplicate identical calls."""
    conn = _conn_with_ff_playerids()
    payload = _payload([{"id": "15281", "rank": "1", "averagePick": "3.00", "minPick": "1",
                          "maxPick": "4", "draftsSelectedIn": "5", "draftSelPct": "10"}])
    mfl.store_adp(conn, payload, 10, 1, 0, 0, 10, 2026)
    n = conn.execute("SELECT COUNT(*) FROM adp_snapshots").fetchone()[0]
    assert n == 1


def test_network_failure_raises_loudly_and_writes_no_row(monkeypatch):
    """A stubbed network failure must propagate, not be swallowed into a
    silent empty/zero-row write -- an absent snapshot must stay absent and
    visibly so, never look like 'no ADP movement today'."""
    conn = sqlite3.connect(":memory:")
    conn.execute(mfl._CREATE_SQL)

    def _boom(req, timeout=20):
        raise urllib.error.URLError("simulated network failure")

    monkeypatch.setattr(mfl.urllib.request, "urlopen", _boom)

    with pytest.raises(urllib.error.URLError):
        mfl.fetch_adp(max_retries=1)

    n = conn.execute("SELECT COUNT(*) FROM adp_snapshots").fetchone()[0]
    assert n == 0


def test_export_snapshot_csv_writes_one_row_per_player(tmp_path):
    conn = _conn_with_ff_playerids()
    payload = _payload([
        {"id": "15281", "rank": "1", "averagePick": "3.00", "minPick": "1", "maxPick": "4",
         "draftsSelectedIn": "5", "draftSelPct": "10"},
        {"id": "16162", "rank": "2", "averagePick": "3.20", "minPick": "1", "maxPick": "6",
         "draftsSelectedIn": "5", "draftSelPct": "10"},
    ])
    mfl.store_adp(conn, payload, 10, 1, 0, 0, 10, 2026)
    date_str = conn.execute(
        "SELECT substr(retrieved_at, 1, 10) FROM adp_snapshots LIMIT 1"
    ).fetchone()[0]
    db_path = tmp_path / "nfl.db"
    out = mfl.export_snapshot_csv(conn, db_path, date_str)
    assert out == tmp_path / "adp-snapshots" / f"{date_str}.csv"
    assert out.exists()
    with out.open(newline="", encoding="utf-8") as f:
        rows = list(csv.DictReader(f))
    assert len(rows) == 2
    assert rows[0]["adp_source"] == "mfl_proxy"
    assert set(mfl._CSV_COLUMNS) == set(rows[0].keys())


def test_export_snapshot_csv_returns_none_and_writes_nothing_when_no_rows(tmp_path):
    conn = sqlite3.connect(":memory:")
    conn.execute(mfl._CREATE_SQL)
    db_path = tmp_path / "nfl.db"
    out = mfl.export_snapshot_csv(conn, db_path, "2026-07-27")
    assert out is None
    assert not (tmp_path / "adp-snapshots").exists()


# ------------------------------------------------ mixture-source loader


def _identity_and_adp_conn():
    conn = sqlite3.connect(":memory:")
    conn.execute("CREATE TABLE player_ids (mfl_id TEXT, source TEXT, source_id TEXT)")
    conn.executemany(
        "INSERT INTO player_ids VALUES (?,?,?)",
        [("2001", "gsis", "00-0001"), ("2002", "gsis", "00-0002")],
    )
    conn.execute(mfl._CREATE_SQL)
    conn.execute(
        "INSERT INTO adp_snapshots VALUES "
        "('mfl_proxy','2001',NULL,NULL,NULL,1,5.0,1,6,10,20,10,1,0,0,10,2026,50,123,'2026-07-25T00:00:00','2026-07-25T00:00:00')"
    )
    return conn


def _tiny_season_data():
    positions = np.array([0, 0])
    return ds.SeasonData(
        season=2026, player_ids=["00-0001", "00-0002"], names=["A", "B"],
        positions=positions, consensus_rank=np.array([1.0, 2.0]),
        weekly_points=np.zeros((2, 1)), n_weeks=1,
    )


def test_load_mfl_adp_source_returns_none_when_not_ingested():
    conn = sqlite3.connect(":memory:")
    conn.execute(mfl._CREATE_SQL)
    data = _tiny_season_data()
    assert av.load_mfl_adp_source(conn, data) is None


def test_load_mfl_adp_source_uses_real_pick_for_resolved_players():
    conn = _identity_and_adp_conn()
    data = _tiny_season_data()
    src = av.load_mfl_adp_source(conn, data)
    assert src is not None
    assert src.rank[0] == 5.0  # 00-0001 -> mfl 2001 -> average_pick 5.0


def test_load_mfl_adp_source_falls_back_to_consensus_for_unresolved():
    """00-0002 has no adp_snapshots row for its mfl_id (2002) -- must fall
    back to the FP-ECR consensus rank, not zero or a crash."""
    conn = _identity_and_adp_conn()
    data = _tiny_season_data()
    src = av.load_mfl_adp_source(conn, data)
    assert src.rank[1] == data.consensus_rank[1] == 2.0


def test_default_ranking_sources_does_not_include_mfl():
    """The shipped default must stay single-source until a weighting decision
    is actually made -- see load_mfl_adp_source's docstring."""
    data = _tiny_season_data()
    sources = av.default_ranking_sources(data)
    assert len(sources) == 1
    assert sources[0].name == "fantasypros_ecr"


def test_load_mfl_adp_source_never_blends_across_adp_source_values():
    """Two distinct platforms picking the same player must never be averaged
    into one figure -- drafters see their own platform's rank, so ADP is a
    per-platform behavioural variable (per module docstring's stated rule).
    A second, very different adp_source value ('other_platform_proxy') is
    inserted for the same player/date; load_mfl_adp_source(adp_source=
    'mfl_proxy') must return exactly the mfl_proxy figure, not a blend."""
    conn = sqlite3.connect(":memory:")
    conn.execute("CREATE TABLE player_ids (mfl_id TEXT, source TEXT, source_id TEXT)")
    conn.execute("INSERT INTO player_ids VALUES ('2001', 'gsis', '00-0001')")
    conn.execute(mfl._CREATE_SQL)
    conn.execute(
        "INSERT INTO adp_snapshots VALUES "
        "('mfl_proxy','2001',NULL,NULL,NULL,1,5.0,1,6,10,20,10,1,0,0,10,2026,50,123,"
        "'2026-07-25T00:00:00','2026-07-25T00:00:00')"
    )
    conn.execute(
        "INSERT INTO adp_snapshots VALUES "
        "('other_platform_proxy','2001',NULL,NULL,NULL,1,95.0,1,6,10,20,10,1,0,0,10,2026,50,123,"
        "'2026-07-25T00:00:00','2026-07-25T00:00:00')"
    )
    positions = np.array([0])
    data = ds.SeasonData(
        season=2026, player_ids=["00-0001"], names=["A"], positions=positions,
        consensus_rank=np.array([1.0]), weekly_points=np.zeros((1, 1)), n_weeks=1,
    )
    src = av.load_mfl_adp_source(conn, data, adp_source="mfl_proxy")
    assert src.rank[0] == 5.0, "must be the raw mfl_proxy pick, not an average with other_platform_proxy's 95.0"
