import sqlite3

import polars as pl
import pytest

import ingest_reference as ir


def _spec(loader, **kwargs):
    return ir.SourceSpec(table="t", loader=loader, **kwargs)


# ------------------------------------------------ prepare(): as_of_column enforcement


def test_prepare_drops_rows_with_missing_as_of_value():
    df = pl.DataFrame(
        {
            "gsis_id": ["a", "b", "c"],
            "week": [1, 1, 1],
            "date_modified": ["2024-09-06", None, "2024-09-07"],
        }
    )
    spec = _spec(lambda: df, primary_key=("gsis_id", "week"), as_of_column="date_modified")
    out, report = ir.prepare(spec)
    assert out.height == 2
    assert report["dropped_missing_as_of_date"] == 1
    assert None not in out["date_modified"].to_list()


def test_prepare_raises_when_as_of_column_entirely_absent():
    df = pl.DataFrame({"gsis_id": ["a"], "week": [1]})
    spec = _spec(lambda: df, primary_key=("gsis_id", "week"), as_of_column="date_modified")
    with pytest.raises(ValueError):
        ir.prepare(spec)


def test_prepare_without_as_of_column_is_unaffected_by_the_new_check():
    df = pl.DataFrame({"gsis_id": ["a", "b"], "week": [1, 1]})
    spec = _spec(lambda: df, primary_key=("gsis_id", "week"))
    out, report = ir.prepare(spec)
    assert out.height == 2
    assert "dropped_missing_as_of_date" not in report


# ------------------------------------------------ build_create_table_sql(): NOT NULL


def test_create_table_sql_marks_as_of_column_not_null():
    df = pl.DataFrame({"gsis_id": ["a"], "date_modified": ["2024-09-06"]})
    sql = ir.build_create_table_sql("t", df, ("gsis_id",), as_of_column="date_modified")
    assert '"date_modified" TEXT NOT NULL' in sql


def test_create_table_sql_leaves_other_columns_nullable():
    df = pl.DataFrame({"gsis_id": ["a"], "date_modified": ["2024-09-06"]})
    sql = ir.build_create_table_sql("t", df, ("gsis_id",), as_of_column="date_modified")
    assert '"gsis_id" TEXT NOT NULL' not in sql


# ------------------------------------------------ end to end: no row can land undated


def test_write_end_to_end_refuses_a_null_as_of_row_at_the_db_level():
    """The DB CHECK/NOT NULL constraint is the last line of defense: even if a
    future caller bypasses prepare()'s row-drop, the table itself rejects an
    undated insert."""
    conn = sqlite3.connect(":memory:")
    df = pl.DataFrame(
        {"gsis_id": ["a"], "week": [1], "date_modified": ["2024-09-06"]}
    )
    spec = _spec(lambda: df, primary_key=("gsis_id", "week"), as_of_column="date_modified")
    ir.write(conn, spec, df)
    with pytest.raises(sqlite3.IntegrityError):
        conn.execute(
            'INSERT INTO "t" (gsis_id, week, date_modified, ingested_at) '
            "VALUES ('b', 1, NULL, '2026-07-26T00:00:00')"
        )


def test_write_end_to_end_no_row_ever_lacks_an_as_of_date_through_prepare_and_write():
    conn = sqlite3.connect(":memory:")
    df = pl.DataFrame(
        {
            "gsis_id": ["a", "b", "c"],
            "week": [1, 1, 1],
            "date_modified": ["2024-09-06", None, "2024-09-07"],
        }
    )
    spec = _spec(lambda: df, primary_key=("gsis_id", "week"), as_of_column="date_modified")
    prepared, _ = ir.prepare(spec)
    n = ir.write(conn, spec, prepared)
    assert n == 2
    missing = conn.execute('SELECT COUNT(*) FROM "t" WHERE date_modified IS NULL').fetchone()[0]
    assert missing == 0
