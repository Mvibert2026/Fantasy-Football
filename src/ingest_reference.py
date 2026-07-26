"""
Ingest nflverse reference/context sources into data/nfl.db.

Ingestion-only. No feature computation here (that is Task 8) -- these tables are
raw caches, reshaped as little as possible.

KEY DESIGN, VERIFIED NOT ASSUMED. Every primary key below was checked
empirically for nullability and uniqueness before being chosen, because SQLite
does not treat NULL as equal to NULL in a composite key: one nullable key column
silently duplicates rows on every re-ingest. Two tables (depth charts, contracts)
have NO clean natural key in the source, so they use a deterministic row-content
hash rather than a fabricated one.

as_of_date is added ONLY where the source carries a genuine timestamp
(`injuries.date_modified`, `depth_charts.dt`). The remaining tables are keyed by
season/week with no finer resolution, and inventing a date for them would
manufacture precision that does not exist.

TWO STACKED DEPTH-CHART FORMATS. `load_depth_charts` returns two incompatible
datasets in one frame:
  - season/week-labelled rows, 2001-2024 (869,185 rows)
  - dt-timestamped snapshots with NULL season/week, 2025-08-03 to 2026-07-25
    (923,162 rows across 348 distinct snapshots)
They are split into two tables. Stacking them would produce a column set that is
half-null in every row and a season column that is null for the most recent and
most decision-relevant data.
"""

from __future__ import annotations

import argparse
import datetime as dt
import hashlib
import json
import sqlite3
from dataclasses import dataclass, field
from pathlib import Path
from typing import Callable, Dict, List, Optional, Sequence, Tuple

import nflreadpy as nfl
import polars as pl
from nflreadpy.config import update_config

DEFAULT_DB_PATH = Path(__file__).resolve().parent.parent / "data" / "nfl.db"


@dataclass
class SourceSpec:
    table: str
    loader: Callable[..., pl.DataFrame]
    loader_kwargs: Dict[str, object] = field(default_factory=dict)
    # None => use a deterministic row-content hash as the PK.
    primary_key: Optional[Tuple[str, ...]] = None
    # Column to sort by (descending) when collapsing duplicate keys.
    dedupe_prefer: Optional[str] = None
    # Rows are restricted to those matching this filter before writing.
    row_filter: Optional[Callable[[pl.DataFrame], pl.DataFrame]] = None
    as_of_column: Optional[str] = None
    notes: str = ""


def _old_depth_charts(df: pl.DataFrame) -> pl.DataFrame:
    return df.filter(pl.col("season").is_not_null())


def _new_depth_charts(df: pl.DataFrame) -> pl.DataFrame:
    keep = [c for c in df.columns if c not in ("season", "week", "game_type")]
    return df.filter(pl.col("season").is_null()).select(keep)


SPECS: List[SourceSpec] = [
    SourceSpec(
        table="injuries",
        loader=nfl.load_injuries,
        loader_kwargs={"seasons": True},
        primary_key=("season", "game_type", "team", "week", "gsis_id"),
        dedupe_prefer="date_modified",
        as_of_column="date_modified",
        notes="practice_status vs report_status have different histories; see docs",
    ),
    SourceSpec(
        table="depth_charts_weekly",
        loader=nfl.load_depth_charts,
        loader_kwargs={"seasons": True},
        primary_key=None,  # `week` is nullable (5,760 rows) and the key duplicates
        row_filter=_old_depth_charts,
        notes="OLD format, season/week labelled, 2001-2024",
    ),
    SourceSpec(
        table="depth_charts_snapshots",
        loader=nfl.load_depth_charts,
        loader_kwargs={"seasons": True},
        primary_key=None,  # gsis_id is nullable (8,038 rows)
        row_filter=_new_depth_charts,
        as_of_column="dt",
        notes="NEW format, dt-timestamped, 2025-08-03 onward",
    ),
    SourceSpec(
        table="snap_counts",
        loader=nfl.load_snap_counts,
        loader_kwargs={"seasons": True},
        primary_key=("game_id", "pfr_player_id"),
    ),
    SourceSpec(
        table="ngs_receiving",
        loader=nfl.load_nextgen_stats,
        loader_kwargs={"seasons": True, "stat_type": "receiving"},
        primary_key=("season", "season_type", "week", "player_gsis_id"),
    ),
    SourceSpec(
        table="ngs_rushing",
        loader=nfl.load_nextgen_stats,
        loader_kwargs={"seasons": True, "stat_type": "rushing"},
        primary_key=("season", "season_type", "week", "player_gsis_id"),
    ),
    SourceSpec(
        table="ngs_passing",
        loader=nfl.load_nextgen_stats,
        loader_kwargs={"seasons": True, "stat_type": "passing"},
        primary_key=("season", "season_type", "week", "player_gsis_id"),
    ),
    SourceSpec(
        table="draft_picks",
        loader=nfl.load_draft_picks,
        loader_kwargs={"seasons": True},
        primary_key=("season", "round", "pick"),
    ),
    SourceSpec(
        table="combine",
        loader=nfl.load_combine,
        loader_kwargs={"seasons": True},
        # pfr_id has 1,531 nulls, so it cannot be part of the key
        primary_key=("season", "player_name", "pos"),
    ),
    SourceSpec(
        table="contracts",
        loader=nfl.load_contracts,
        loader_kwargs={},
        primary_key=None,  # multiple contracts per player-year; no natural key
    ),
    SourceSpec(
        table="ff_playerids",
        loader=nfl.load_ff_playerids,
        loader_kwargs={},
        primary_key=("mfl_id",),
        notes="gsis_id is NOT unique here -- 10 collisions; see docs",
    ),
]


def _flatten_nested(df: pl.DataFrame) -> Tuple[pl.DataFrame, List[str]]:
    """JSON-encode nested (List/Struct/Array) columns so SQLite can store them.

    `contracts.cols` holds per-year cap detail as a nested list. Dropping it
    would silently discard the year-by-year structure of every contract; storing
    it as JSON text preserves the data at the cost of needing a parse on read.
    Which columns were encoded is returned so it can be documented rather than
    discovered later by someone confused about why a column is a string.
    """
    nested = [
        name
        for name, dtype in zip(df.columns, df.dtypes)
        if isinstance(dtype, (pl.List, pl.Struct, pl.Array))
    ]
    if not nested:
        return df, []
    def _encode(v):
        # polars hands a Series to the UDF for List columns, not a plain list.
        if v is None:
            return None
        if hasattr(v, "to_list"):
            v = v.to_list()
        return json.dumps(v, default=str)

    return (
        df.with_columns(
            [pl.col(c).map_elements(_encode, return_dtype=pl.String).alias(c) for c in nested]
        ),
        nested,
    )


def _polars_dtype_to_sqlite(dtype: pl.DataType) -> str:
    if dtype.is_integer() or dtype == pl.Boolean:
        return "INTEGER"
    if dtype.is_float():
        return "REAL"
    return "TEXT"


def _row_hash(row: Sequence) -> str:
    joined = "\x1f".join("" if v is None else str(v) for v in row)
    return hashlib.sha1(joined.encode("utf-8")).hexdigest()


def build_create_table_sql(
    table: str,
    df: pl.DataFrame,
    pk: Optional[Sequence[str]],
    as_of_column: Optional[str] = None,
) -> str:
    cols = []
    for n, t in zip(df.columns, df.dtypes):
        col_sql = f'"{n}" {_polars_dtype_to_sqlite(t)}'
        if as_of_column is not None and n == as_of_column:
            # Structural enforcement (CLAUDE.md Sec6.1): prepare() already drops
            # undated rows, but the table itself must also refuse one -- a
            # spec change or a direct INSERT bypassing prepare() must not be
            # able to slip a null as_of value in.
            col_sql += " NOT NULL"
        cols.append(col_sql)
    if pk is None:
        cols.insert(0, '"row_hash" TEXT')
        key = '"row_hash"'
    else:
        key = ", ".join(f'"{c}"' for c in pk)
    cols.append('"ingested_at" TEXT NOT NULL')
    body = ",\n    ".join(cols)
    return f'CREATE TABLE IF NOT EXISTS "{table}" (\n    {body},\n    PRIMARY KEY ({key})\n)'


def prepare(spec: SourceSpec) -> Tuple[pl.DataFrame, Dict[str, int]]:
    """Load, filter, drop null-key rows, and dedupe. Returns (df, report)."""
    df = spec.loader(**spec.loader_kwargs)
    report = {"loaded": df.height}

    if spec.row_filter is not None:
        df = spec.row_filter(df)
        report["after_format_filter"] = df.height

    df, nested = _flatten_nested(df)
    if nested:
        report["json_encoded_columns"] = len(nested)
        spec.notes = (spec.notes + f" | JSON-encoded nested cols: {nested}").strip(" |")

    if spec.as_of_column is not None:
        if spec.as_of_column not in df.columns:
            raise ValueError(
                f"{spec.table}: as_of_column '{spec.as_of_column}' absent from source -- "
                "cannot ingest without a real as_of_date (CLAUDE.md Sec6.1); fix the spec or "
                "skip this table, do not default the date"
            )
        before = df.height
        # A row with no as_of value is worse than no row: it looks usable to a
        # future historical rebuild and silently contaminates it with
        # look-ahead knowledge (CLAUDE.md Sec6.1, handoff 024). Reject, don't
        # default. Reported, never silent.
        df = df.filter(pl.col(spec.as_of_column).is_not_null())
        report["dropped_missing_as_of_date"] = before - df.height

    if spec.primary_key:
        missing = [c for c in spec.primary_key if c not in df.columns]
        if missing:
            raise ValueError(f"{spec.table}: key columns absent from source: {missing}")
        before = df.height
        # Drop rows with a NULL in any key column. NULL != NULL in a SQLite
        # composite PK, so these would duplicate on every re-ingest instead of
        # being replaced. Reported, never silent.
        df = df.drop_nulls(list(spec.primary_key))
        report["dropped_null_key"] = before - df.height

        before = df.height
        if spec.dedupe_prefer and spec.dedupe_prefer in df.columns:
            df = df.sort(spec.dedupe_prefer, descending=True, nulls_last=True).unique(
                subset=list(spec.primary_key), keep="first", maintain_order=True
            )
        else:
            df = df.unique(subset=list(spec.primary_key), keep="first", maintain_order=True)
        report["dropped_duplicate_key"] = before - df.height

    return df, report


def write(conn: sqlite3.Connection, spec: SourceSpec, df: pl.DataFrame) -> int:
    conn.execute(f'DROP TABLE IF EXISTS "{spec.table}"')
    conn.execute(build_create_table_sql(spec.table, df, spec.primary_key, spec.as_of_column))
    if df.height == 0:
        return 0
    ingested_at = dt.datetime.now(dt.timezone.utc).isoformat()
    cols = list(df.columns)
    if spec.primary_key is None:
        out_cols = ["row_hash"] + cols + ["ingested_at"]
        rows = [(_row_hash(r),) + tuple(r) + (ingested_at,) for r in df.iter_rows()]
    else:
        out_cols = cols + ["ingested_at"]
        rows = [tuple(r) + (ingested_at,) for r in df.iter_rows()]
    placeholders = ", ".join("?" for _ in out_cols)
    col_sql = ", ".join(f'"{c}"' for c in out_cols)
    conn.executemany(
        f'INSERT OR REPLACE INTO "{spec.table}" ({col_sql}) VALUES ({placeholders})', rows
    )
    return len(rows)


def ingest_all(db_path: Path, only: Optional[Sequence[str]] = None) -> Dict[str, dict]:
    update_config(cache_mode="filesystem")
    db_path.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(db_path)
    results: Dict[str, dict] = {}
    try:
        for spec in SPECS:
            if only and spec.table not in only:
                continue
            df, report = prepare(spec)
            n = write(conn, spec, df)
            conn.commit()
            report["written"] = n
            report["columns"] = df.width
            results[spec.table] = report
            extras = "  ".join(
                f"{k}={v}" for k, v in report.items()
                if k not in ("written", "columns") and v
            )
            print(f"  {spec.table:<24} rows={n:>8}  cols={df.width:<4} {extras}")
    finally:
        conn.close()
    return results


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--db", type=Path, default=DEFAULT_DB_PATH)
    parser.add_argument("--only", nargs="+", default=None)
    args = parser.parse_args()
    print("Ingesting nflverse reference sources")
    ingest_all(args.db, only=args.only)
    print("done")


if __name__ == "__main__":
    main()
