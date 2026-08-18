"""Rebuild `data/nfl.db` from a clean checkout, in one command, no credentials.

Run in this exact order, measured end-to-end against this database path in this session
(2026-07-29; step 1b added 2026-07-30, see
docs/handoffs/2026-07-30-five-datasets-30-seconds-total-all-measured-toda.md):

  1. ingest_weekly_stats.py
  1b. ingest_pbp.py                 -- play-by-play, 2009-present, slimmed to 24 columns
                                       (see its module docstring). 816,856 rows, ~35s cold /
                                       ~10s warm cache. season/week granularity, no as_of_date
                                       column exists in the source.
  2. ingest_reference.py            -- also carries rosters_weekly (status incl. RES/EXE,
                                       2002-present) and schedules (incl. 2026, unplayed)
                                       as of 2026-07-30.
  3. ingest_league_metrics.py
  4. ingest_rankings.py            -- 2021-2026, re-pulls identically to the committed
                                       rescue CSV (see docs/can-we-rebuild-the-database.md)
  5. ingest_fantasypros_csv.py     -- reads the committed founder export directly
  6. identity.py                   -- builds `players_canonical`. Must run AFTER rankings
                                       exists (its own main()/coverage report queries
                                       `rankings` and exits non-zero on a fresh DB otherwise)
                                       and BEFORE the mock-draft restore (step 7 needs
                                       `players_canonical` to resolve picks -- see below).
  7. ingest_mock_drafts.py data/real_drafts/2025_league_draft.json  -- needs step 6's
                                       players_canonical table to exist; running this before
                                       identity fails with "no such table: players_canonical"
                                       (measured directly this session -- a different, earlier
                                       account of this rebuild's order put identity LAST,
                                       which cannot work for this reason: identity is the only
                                       thing that creates players_canonical at all).
  8. ingest_mfl_adp.py --import-csv-dir data/adp-snapshots   -- restores the committed
                                       point-in-time CSVs; a live --force pull only ever
                                       gets *today's* rolling aggregate, never a past date.
                                       Order-independent relative to the rest.

NOTE on `injuries` and 2025: `load_injuries` returns 2025 rows, but every one of them has a
NULL `date_modified` upstream (verified 2026-07-30, not assumed) -- `ingest_reference.py`
correctly drops rows missing their as_of column (CLAUDE.md Sec6.1: reject, never default) rather
than inventing a date. This means `injuries` has zero 2025 rows in `nfl.db` by design, not by
bug. If a downstream consumer wants a season/week-only substitute for 2025 injury status,
that is a methodology decision for backend/statistician, not something this ingester should
silently do on its own authority.

`identity.py` HAS NO --db FLAG. Any doc that shows one for it is wrong; this script accounts
for that by calling its `build_identity_tables(conn)` function directly against a connection
opened on the given --db, rather than shelling out to a flag that doesn't exist. That also
means this script never calls identity.py's own main() (the part with the `rankings`-dependent
coverage-report print), so it is safe to run at any point after step 4/5 despite that print's
own ordering constraint.

FAILS LOUDLY: after the run, every artifact this rebuild depends on that a *silent* partial
rebuild has actually produced (thread 080's three unreproducible artifacts, plus adp_snapshots'
point-in-time history, which has no other restore path) is checked against an expected row
count. A clean checkout that silently rebuilds a database missing these, with every ingestion
script still exiting 0, is exactly the failure mode this script exists to prevent.

IDEMPOTENT: every underlying ingester already upserts (INSERT OR REPLACE, or delete-then-insert
scoped to the affected key) -- re-running this script is safe.

ENVIRONMENT NOTE, DELIBERATELY NOT WORKED AROUND HERE: in a Claude Code cloud session, outbound
requests to `github.com/dynastyprocess/*` (nflreadpy's source for `ingest_reference.py`'s
`ff_playerids` table, `ingest_rankings.py`, and `ingest_fantasypros_csv.py`'s crosswalk) 403
with a GitHub-App "repository not enabled for this session" message -- a Claude-session-only
restriction that does not affect the founder's machine or GitHub Actions (neither goes through
this proxy). This script does not patch around it: doing so would mean shipping a permanent
base-URL substitution that the real machine and CI never needed and would be wrong to carry.
If a Claude session hits this, it is a real, reportable block, not a bug in this script --
say so and stop rather than silently "fixing" it here.

Usage:
    python scripts/rebuild_database.py [--db PATH] [--skip-network]

`--skip-network` runs only steps 6-8 (identity + the two fixture restores) plus assertions,
against an already-populated --db -- useful for iterating on restore logic alone.
"""

from __future__ import annotations

import argparse
import subprocess
import sqlite3
import sys
import time
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
SRC_DIR = REPO_ROOT / "src"
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

DEFAULT_DB_PATH = REPO_ROOT / "data" / "nfl.db"
REAL_DRAFT_JSON = REPO_ROOT / "data" / "real_drafts" / "2025_league_draft.json"
ADP_SNAPSHOT_DIR = REPO_ROOT / "data" / "adp-snapshots"

# Expected counts / lower bounds for the artifacts a partial or mis-ordered
# rebuild would fail to produce. Sourced from thread 080's commit message,
# docs/can-we-rebuild-the-database.md, and the 2026-07-29 rehearsal.
EXPECTED_MOCK_DRAFTS = 1
EXPECTED_MOCK_PICKS = 145
EXPECTED_MOCK_QUARANTINE = 15
# Was 2540 with the note "re-pull may exceed this if the mirror gains rows;
# never less". That premise was wrong and it blocked every rebuild on
# 2026-08-16 at got=2538, expected>=2540 -- off by two rows out of 2,540
# (0.08%). The mirror can LOSE rows as well as gain them: ingest_rankings.py
# drops any ranking row whose FantasyPros id no longer resolves to a gsis_id,
# so ordinary churn in the upstream ff_playerids crosswalk moves this count in
# both directions, on seasons that are themselves long finished.
#
# A floor pinned to the observed value therefore fails on noise. 2400 keeps the
# failure this check exists to catch -- a missing or half-ingested season is
# ~500 rows, roughly 20%, far below this -- while tolerating crosswalk drift of
# a few players either way. Do not re-tighten it to the latest observed count.
MIN_RANKINGS_2021_2025_ROWS = 2400
MIN_ADP_SNAPSHOT_DATES = 2  # at least the two pre-existing committed CSVs, growing daily
MIN_PBP_ROWS = 800_000  # 2009-2025 measured at 816,856 rows 2026-07-30; grows each season
MIN_ROSTERS_WEEKLY_ROWS = 850_000  # 2002-2025 measured at 888,786 rows 2026-07-30
MIN_SCHEDULES_ROWS = 7_500  # 1999-2026 measured at 7,548 rows 2026-07-30


class RebuildFailure(RuntimeError):
    """Raised to stop the rebuild loudly rather than continue past a gap."""


def _run(cmd: list[str], label: str) -> float:
    print(f"\n=== {label} ===")
    print("  $", " ".join(str(c) for c in cmd))
    t0 = time.monotonic()
    result = subprocess.run(cmd, cwd=REPO_ROOT)
    elapsed = time.monotonic() - t0
    if result.returncode != 0:
        raise RebuildFailure(f"{label} failed (exit {result.returncode})")
    print(f"  done in {elapsed:.1f}s")
    return elapsed


def _table_row_counts(db_path: Path) -> dict[str, int]:
    conn = sqlite3.connect(db_path)
    try:
        tables = [
            r[0]
            for r in conn.execute(
                "SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%'"
            ).fetchall()
        ]
        return {
            t: conn.execute(f'SELECT COUNT(*) FROM "{t}"').fetchone()[0] for t in sorted(tables)
        }
    finally:
        conn.close()


def _print_counts(db_path: Path) -> dict[str, int]:
    counts = _table_row_counts(db_path)
    for t, n in counts.items():
        print(f"    {t:<32} {n:>10,}")
    return counts


# ---------------------------------------------------------------------------
# Steps 1-5, 7: public ingestion / restore, all support --db
# ---------------------------------------------------------------------------


def run_public_ingestion(db_path: Path, python_exe: str) -> None:
    _run(
        [python_exe, str(SRC_DIR / "ingest_weekly_stats.py"), "--db", str(db_path)],
        "1/9 ingest_weekly_stats.py",
    )
    _run(
        [python_exe, str(SRC_DIR / "ingest_pbp.py"), "--db", str(db_path)],
        "1b/9 ingest_pbp.py",
    )
    # `participation` was missing from this list until 2026-08-16, and the gap
    # was invisible on any machine that already had a database. On a clean
    # rebuild it took down the whole factor campaign: batch C1 crashed with
    # "sqlite3.OperationalError: no such table: participation" on every GitHub
    # Actions run for ~24 hours, and because the workflow only warned on a
    # non-zero sweep exit, every one of those runs still reported success.
    # It feeds route participation and YPRR (test-registry #16/#17) and the
    # red-zone snap share block, so several C1/C2 factors cannot be graded
    # without it.
    _run(
        [python_exe, str(SRC_DIR / "ingest_participation.py"), "--db", str(db_path)],
        "1c/9 ingest_participation.py",
    )
    _run(
        [python_exe, str(SRC_DIR / "ingest_reference.py"), "--db", str(db_path)],
        "2/9 ingest_reference.py",
    )
    # 2b-2d. Tables the factor campaign reads that this script never built.
    # Every one of these was discovered the same way: a batch reached for a
    # table, crashed with "no such table", and cost a full 5-hour run. The gap
    # is invisible on any machine that already has a database. Enumerated in
    # one pass 2026-08-17 rather than one crash at a time -- ff_opportunity
    # (C1), odds_snapshots (C2), pfr_advstats_rush (C4).
    _run(
        [python_exe, str(SRC_DIR / "ingest_ff_opportunity.py"), "--db", str(db_path)],
        "2b/9 ingest_ff_opportunity.py",
    )
    # odds derives from schedules, so it must follow ingest_reference.
    _run(
        [python_exe, str(SRC_DIR / "ingest_odds.py"), "--db", str(db_path)],
        "2c/9 ingest_odds.py",
    )
    _run(
        [python_exe, str(SRC_DIR / "ingest_pfr_advstats.py"), "--db", str(db_path)],
        "2d/9 ingest_pfr_advstats.py",
    )
    # play_callers_preseason. src/ingest_play_callers.py is parked and builds a
    # DIFFERENT table (`play_callers`) -- assuming otherwise cost a rebuild on
    # 2026-08-17. The table batches C5/CT1 actually read is built by
    # experiments/bottomup/factors/coord_preseason.py from Wikipedia navbox
    # revisions dated before each season's Week 1, which is what produced the
    # 992 rows in the working database. The raw captures are NOT committed, so
    # this refetches.
    #
    # Non-fatal by design. Those coordinator factors are already dispositioned
    # BLOCKED, so real rows are a bonus and a Wikipedia outage must not take the
    # whole campaign down. On any failure the table is created EMPTY, because a
    # missing table raises where an empty one returns no rows -- the difference
    # between a factor reporting blocked and a five-hour run dying.
    print("\n=== 2e/9 coord_preseason.py (play_callers_preseason) ===")
    import importlib.util as _ilu
    _spec = _ilu.spec_from_file_location(
        "_cp", REPO_ROOT / "experiments/bottomup/factors/coord_preseason.py")
    _cp = _ilu.module_from_spec(_spec)
    try:
        _spec.loader.exec_module(_cp)
        _cp.ingest(range(2010, 2026), db_path=db_path)
    except Exception as exc:                                # noqa: BLE001
        print(f"  coordinator fetch failed ({type(exc).__name__}: {exc}); "
              f"creating the table empty and continuing -- these factors are "
              f"dispositioned BLOCKED, so this is a known gap, not a new one")
        _conn = sqlite3.connect(db_path)
        try:
            _conn.execute(_cp._CREATE_SQL)
            _conn.execute(_cp._QUAR_SQL)
            _conn.commit()
        finally:
            _conn.close()
    _conn = sqlite3.connect(db_path)
    try:
        n = _conn.execute("SELECT COUNT(*) FROM play_callers_preseason").fetchone()[0]
        print(f"  play_callers_preseason: {n} rows")
    finally:
        _conn.close()

    _run(
        [python_exe, str(SRC_DIR / "ingest_league_metrics.py"), "--db", str(db_path)],
        "3/9 ingest_league_metrics.py",
    )
    _run(
        [python_exe, str(SRC_DIR / "ingest_rankings.py"), "--db", str(db_path)],
        "4/9 ingest_rankings.py",
    )
    _run(
        [python_exe, str(SRC_DIR / "ingest_fantasypros_csv.py"), "--db", str(db_path)],
        "5/9 ingest_fantasypros_csv.py",
    )


def run_identity(db_path: Path) -> None:
    """identity.py's main() has no argparse and always writes db.DB_PATH -- a
    documented --db flag for it does not exist. This calls its
    `build_identity_tables(conn)` function directly against a connection
    opened on the given --db instead, which sidesteps that hardcoding
    entirely (and also skips the trailing coverage-report print in main(),
    the part that requires `rankings` to already exist -- moot here since
    this runs after steps 4/5 anyway).

    MUST run before the mock-draft restore: it is the only thing that
    creates `players_canonical`, which ingest_mock_drafts.py needs to
    resolve picks. Measured directly this session -- running mock-draft
    restore first fails with `sqlite3.OperationalError: no such table:
    players_canonical`."""
    print("\n=== 6/8 identity.build_identity_tables ===")
    t0 = time.monotonic()
    import identity as idn  # noqa: E402

    conn = sqlite3.connect(db_path)
    try:
        report = idn.build_identity_tables(conn)
        print(f"  {report}")
    finally:
        conn.close()
    print(f"  done in {time.monotonic() - t0:.1f}s")


def restore_real_draft(db_path: Path, python_exe: str) -> None:
    if not REAL_DRAFT_JSON.exists():
        raise RebuildFailure(f"missing fixture: {REAL_DRAFT_JSON}")
    _run(
        [python_exe, str(SRC_DIR / "ingest_mock_drafts.py"), str(REAL_DRAFT_JSON), "--db", str(db_path)],
        "7/8 ingest_mock_drafts.py (2025 real draft)",
    )


def restore_adp_history(db_path: Path, python_exe: str) -> None:
    if not ADP_SNAPSHOT_DIR.exists():
        raise RebuildFailure(f"missing directory: {ADP_SNAPSHOT_DIR}")
    _run(
        [
            python_exe, str(SRC_DIR / "ingest_mfl_adp.py"),
            "--db", str(db_path), "--import-csv-dir", str(ADP_SNAPSHOT_DIR),
        ],
        "8/8 ingest_mfl_adp.py --import-csv-dir (restore committed point-in-time ADP)",
    )


# ---------------------------------------------------------------------------
# Assertions -- the thing that makes a partial rebuild fail loudly
# ---------------------------------------------------------------------------


def assert_restored(db_path: Path) -> None:
    conn = sqlite3.connect(db_path)
    try:
        checks: list[tuple[str, int, int, str]] = []

        def scalar(sql: str, params: tuple = ()) -> int:
            row = conn.execute(sql, params).fetchone()
            return row[0] if row else 0

        checks.append((
            "mock_drafts (2025 real draft)",
            scalar("SELECT COUNT(*) FROM mock_drafts WHERE mock_id='2025_league_draft_real'"),
            EXPECTED_MOCK_DRAFTS, "==",
        ))
        checks.append((
            "mock_picks (2025 real draft)",
            scalar("SELECT COUNT(*) FROM mock_picks WHERE mock_id='2025_league_draft_real'"),
            EXPECTED_MOCK_PICKS, "==",
        ))
        checks.append((
            "mock_pick_quarantine (2025 real draft)",
            scalar("SELECT COUNT(*) FROM mock_pick_quarantine WHERE mock_id='2025_league_draft_real'"),
            EXPECTED_MOCK_QUARANTINE, "==",
        ))
        checks.append((
            "rankings (fantasypros_ecr, 2021-2025)",
            scalar(
                "SELECT COUNT(*) FROM rankings WHERE source='fantasypros_ecr' "
                "AND season BETWEEN 2021 AND 2025"
            ),
            MIN_RANKINGS_2021_2025_ROWS, ">=",
        ))
        checks.append((
            "rankings (founder 2026 half-PPR csv)",
            scalar("SELECT COUNT(*) FROM rankings WHERE source='fantasypros_csv_2026draft'"),
            1, ">=",
        ))
        checks.append((
            "adp_snapshots (distinct captured dates)",
            scalar("SELECT COUNT(DISTINCT substr(retrieved_at, 1, 10)) FROM adp_snapshots"),
            MIN_ADP_SNAPSHOT_DATES, ">=",
        ))
        checks.append((
            "pbp (2009-present)",
            scalar("SELECT COUNT(*) FROM pbp"),
            MIN_PBP_ROWS, ">=",
        ))
        checks.append((
            "rosters_weekly (2002-present)",
            scalar("SELECT COUNT(*) FROM rosters_weekly"),
            MIN_ROSTERS_WEEKLY_ROWS, ">=",
        ))
        checks.append((
            "schedules (1999-present)",
            scalar("SELECT COUNT(*) FROM schedules"),
            MIN_SCHEDULES_ROWS, ">=",
        ))
        # Every table the factor campaign reads. This exists because four
        # separate "no such table" crashes each cost a full 5-hour Actions run
        # before anyone knew: participation, ff_opportunity, and two more
        # behind them. A row-count check cannot catch a table that was never
        # created, and checking one table at a time turns one bug into N round
        # trips. This reports ALL of them at once.
        required = [
            "player_weekly_stats", "pbp", "participation", "ff_opportunity",
            "odds_snapshots", "pfr_advstats_rush", "play_callers_preseason",
            "combine", "contracts", "injuries", "depth_charts_weekly",
            "snap_counts", "draft_picks", "rosters_weekly", "schedules",
            "ff_playerids", "rankings", "league_season_metrics",
        ]
        have = {r[0] for r in conn.execute(
            "SELECT name FROM sqlite_master WHERE type='table'")}
        for t in required:
            checks.append((f"table `{t}` exists", 1 if t in have else 0, 1, ">="))
    finally:
        conn.close()

    failures = []
    for label, actual, expected, op in checks:
        ok = actual == expected if op == "==" else actual >= expected
        print(f"    {'OK ' if ok else 'FAIL'} {label}: got {actual}, expected {op} {expected}")
        if not ok:
            failures.append(f"{label}: got {actual}, expected {op} {expected}")
    if failures:
        raise RebuildFailure("post-rebuild assertion failed:\n  " + "\n  ".join(failures))


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------


def main() -> None:
    parser = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter
    )
    parser.add_argument("--db", type=Path, default=DEFAULT_DB_PATH)
    parser.add_argument(
        "--skip-network", action="store_true",
        help="Skip steps 1-5 (the network-dependent public ingestion); only run the "
             "fixture-restore steps (6, 7, identity) plus assertions against an "
             "already-populated --db.",
    )
    parser.add_argument(
        "--python", default=sys.executable,
        help="Python interpreter to shell out to for each step (default: this one).",
    )
    args = parser.parse_args()

    db_path: Path = args.db
    db_path.parent.mkdir(parents=True, exist_ok=True)

    t_start = time.monotonic()
    print(f"Rebuilding {db_path}")
    print(f"skip_network={args.skip_network}")

    try:
        if not args.skip_network:
            run_public_ingestion(db_path, args.python)
        else:
            print("\n=== skipping steps 1-5 (--skip-network) ===")

        run_identity(db_path)
        restore_real_draft(db_path, args.python)
        restore_adp_history(db_path, args.python)

        print("\n=== post-rebuild assertions ===")
        assert_restored(db_path)

    except RebuildFailure as e:
        print(f"\nREBUILD FAILED: {e}", file=sys.stderr)
        sys.exit(1)

    elapsed = time.monotonic() - t_start
    print(f"\n=== done in {elapsed:.1f}s ===")
    print("Row counts by table:")
    _print_counts(db_path)


if __name__ == "__main__":
    main()
