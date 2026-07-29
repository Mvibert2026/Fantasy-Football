"""T5 -- snapshot freshness tripwire (fable-draft-day-premortem-2026-07-27.md
finding #2).

Nothing previously recorded or bounded how old the live ECR snapshot backing
the board was. `rankings.as_of_date` is captured at ingest time (it already
exists in the schema -- see `rankings` DDL), but the board builder never read
it back to ask "is this too old to trust." This module is that read-back:
a pure function over the DB plus a small gate the board builder can call.

Design choices, stated so they are not re-litigated:
 - Age is measured from the MOST RECENT `as_of_date` for the source/season,
   not the oldest -- a snapshot ingested across multiple days is as fresh as
   its newest row.
 - A season/source with NO rows at all is treated as stale (age_days=None,
   stale=True) rather than silently passing -- an absent snapshot is a worse
   state than an old one, and must not build a board silently.
 - `check_freshness` never raises -- it is the always-surfaced report (used
   for the "under threshold but still shown" warning). `require_fresh` is the
   hard gate that raises `StaleSnapshotError`. Two functions instead of one
   with a raise flag, so a caller cannot accidentally suppress the warning by
   getting the flag wrong.
 - `today` is an injectable parameter (defaults to real UTC today) so this is
   testable without freezing the system clock.
"""

from __future__ import annotations

import sqlite3
from datetime import date, datetime, timezone
from typing import Optional, TypedDict


class StaleSnapshotError(Exception):
    """Raised by require_fresh() when the live snapshot is older than the
    configured threshold (or entirely absent)."""


class FreshnessResult(TypedDict):
    as_of_date: Optional[str]
    age_days: Optional[int]
    max_age_days: int
    stale: bool


def _today(today: Optional[date]) -> date:
    return today if today is not None else datetime.now(timezone.utc).date()


def snapshot_age_days(
    conn: sqlite3.Connection,
    season: int,
    source: str,
    today: Optional[date] = None,
) -> Optional[int]:
    """Days between `today` and the most recent as_of_date on file for this
    source/season. None if there are no rows at all -- an honest "we don't
    know", never a fabricated 0 or an old default."""
    row = conn.execute(
        "SELECT MAX(as_of_date) FROM rankings WHERE source = ? AND season = ?",
        (source, season),
    ).fetchone()
    as_of = row[0] if row else None
    if not as_of:
        return None
    as_of_date = date.fromisoformat(as_of)
    return (_today(today) - as_of_date).days


def historical_snapshot_date(
    conn: sqlite3.Connection,
    season: int,
    source: str,
    on_or_before: str,
) -> Optional[str]:
    """Like `snapshot_age_days`'s MAX(as_of_date) lookup, but anchored to a
    PAST cutoff date instead of "today" -- the look-ahead-bias-safe query for
    computing what board a historical/backfilled record (e.g. a mock draft)
    could actually have seen (CLAUDE.md SS6.1, ADR-054). Returns the most
    recent as_of_date that is <= `on_or_before`, or None if no such snapshot
    exists on file at all. Never falls back to the latest/current snapshot --
    that would leak future information into a historical record, which is
    exactly the bug this function exists to prevent."""
    row = conn.execute(
        "SELECT MAX(as_of_date) FROM rankings WHERE source = ? AND season = ? "
        "AND as_of_date <= ?",
        (source, season, on_or_before),
    ).fetchone()
    return row[0] if row and row[0] else None


def check_freshness(
    conn: sqlite3.Connection,
    season: int,
    source: str,
    max_age_days: int,
    today: Optional[date] = None,
) -> FreshnessResult:
    """Non-raising report: always computed, always surfaced (even when the
    snapshot is comfortably fresh) so a caller can print/log the age
    unconditionally -- the founder should see snapshot age every time a
    board is built, not only when it crosses the line."""
    row = conn.execute(
        "SELECT MAX(as_of_date) FROM rankings WHERE source = ? AND season = ?",
        (source, season),
    ).fetchone()
    as_of = row[0] if row else None
    age = snapshot_age_days(conn, season, source, today=today)
    stale = age is None or age > max_age_days
    return FreshnessResult(
        as_of_date=as_of, age_days=age, max_age_days=max_age_days, stale=stale
    )


def require_fresh(
    conn: sqlite3.Connection,
    season: int,
    source: str,
    max_age_days: int,
    today: Optional[date] = None,
) -> FreshnessResult:
    """The hard gate: raises StaleSnapshotError if the snapshot is stale or
    absent. Returns the same report check_freshness would, on success, so a
    caller can log it either way."""
    result = check_freshness(conn, season, source, max_age_days, today=today)
    if result["stale"]:
        if result["age_days"] is None:
            raise StaleSnapshotError(
                f"no {source!r} snapshot on file for season {season} -- "
                f"refusing to build a board with no recorded as_of_date"
            )
        raise StaleSnapshotError(
            f"{source!r} snapshot for season {season} is {result['age_days']} "
            f"day(s) old (as_of={result['as_of_date']}), exceeding the "
            f"{max_age_days}-day freshness threshold -- re-pull before "
            f"building the board, or raise league_config's "
            f"freshness_max_age_days if this is deliberate"
        )
    return result
