import sqlite3

import polars as pl
import pytest

import ingest_rankings as ir


# ------------------------------------------------ resolve_snapshot_date


def test_resolve_snapshot_date_picks_latest_in_window():
    dates = ["2021-08-01", "2021-08-27", "2021-09-15", "2022-08-20"]
    chosen, is_final = ir.resolve_snapshot_date(dates, 2021)
    assert chosen == "2021-08-27"


def test_resolve_snapshot_date_raises_when_no_snapshot_in_window():
    dates = ["2020-08-27", "2022-08-27"]
    with pytest.raises(ValueError):
        ir.resolve_snapshot_date(dates, 2021)


def test_resolve_snapshot_date_marks_past_seasons_as_final():
    # 2021's Aug 31 cutoff is long past "today" in this codebase's test env.
    dates = ["2021-08-27"]
    _, is_final = ir.resolve_snapshot_date(dates, 2021)
    assert is_final is True


# ------------------------------------------------ ensure_table / upsert


def _row(season: int, player_id: str, as_of_date: str) -> dict:
    return dict(
        ranking_source="expert",
        source=ir.SOURCE,
        season=season,
        player_id=player_id,
        player_name=f"Player {player_id}",
        team="XXX",
        adp_rank=1,
        adp_value=1.0,
        spread_sd=0.5,
        rank_best=1.0,
        rank_worst=2.0,
        as_of_date=as_of_date,
        position="RB",
        is_preseason_final=1,
    )


def _df(rows: list[dict]) -> pl.DataFrame:
    return pl.DataFrame(rows)


def test_upsert_writes_rows_and_every_row_carries_as_of_date():
    conn = sqlite3.connect(":memory:")
    ir.ensure_table(conn)
    df = _df([_row(2021, "p1", "2021-08-27"), _row(2021, "p2", "2021-08-27")])
    n = ir.upsert_dataframe(conn, df)
    assert n == 2
    rows = conn.execute(f'SELECT as_of_date FROM "{ir.TABLE_NAME}"').fetchall()
    assert len(rows) == 2
    assert all(r[0] == "2021-08-27" for r in rows)


def test_upsert_empty_dataframe_is_a_noop():
    conn = sqlite3.connect(":memory:")
    ir.ensure_table(conn)
    df = pl.DataFrame(
        schema={c: pl.Utf8 for c in ir.PRIMARY_KEY},
    )
    assert ir.upsert_dataframe(conn, df) == 0


# ------------------------------------------------ multi-season ingest loop


def test_ingest_backfills_multiple_seasons(tmp_path, monkeypatch):
    """Thread 018: looping over seasons must actually populate distinct
    per-season rows, not just the most recently requested season."""
    seasons_seen = []

    def fake_fetch(season):
        seasons_seen.append(season)
        df = _df([_row(season, f"p-{season}", f"{season}-08-27")])
        return df, f"{season}-08-27", True

    monkeypatch.setattr(ir, "fetch_preseason_rankings", fake_fetch)

    db_path = tmp_path / "nfl.db"
    results = ir.ingest([2021, 2022, 2023, 2024], db_path)

    assert seasons_seen == [2021, 2022, 2023, 2024]
    assert set(results.keys()) == {2021, 2022, 2023, 2024}
    for season, (n, as_of, is_final) in results.items():
        assert n == 1
        assert as_of == f"{season}-08-27"

    conn = sqlite3.connect(db_path)
    counts = dict(
        conn.execute(f'SELECT season, COUNT(*) FROM "{ir.TABLE_NAME}" GROUP BY season').fetchall()
    )
    assert counts == {2021: 1, 2022: 1, 2023: 1, 2024: 1}
    # No row anywhere lacks an as_of_date.
    missing = conn.execute(
        f'SELECT COUNT(*) FROM "{ir.TABLE_NAME}" WHERE as_of_date IS NULL'
    ).fetchone()[0]
    assert missing == 0


def test_ingest_skips_season_with_no_snapshot_in_window_without_crashing(tmp_path, monkeypatch):
    def fake_fetch(season):
        if season == 2099:
            raise ValueError("No snapshot for season 2099")
        df = _df([_row(season, f"p-{season}", f"{season}-08-27")])
        return df, f"{season}-08-27", True

    monkeypatch.setattr(ir, "fetch_preseason_rankings", fake_fetch)
    db_path = tmp_path / "nfl.db"
    results = ir.ingest([2021, 2099], db_path)
    assert set(results.keys()) == {2021}
