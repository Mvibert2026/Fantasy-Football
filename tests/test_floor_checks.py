"""Table-stakes floor checks T3 + T10 (session-1 table-stakes review; built
under the extended mandate). Executable versions of two floor items:

T3  — positive bye coverage: every board row carries a non-null bye week.
      The bye lookup fails open to "unknown" by design (honest display), so
      only a positive-coverage check catches a team-code mismatch that
      silently strips byes from a whole roster.
T10 — ranking uniqueness: the live-season consensus rows are unique per
      player; a duplicate row is the same silent-corruption family as a name
      collision.

Both run against the repo's real artifacts (board.json is tracked; nfl.db is
not — the DB-backed test skips cleanly when the DB is absent, e.g. in a
worktree checkout).
"""

import json
import sqlite3
from collections import Counter
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
BOARD = ROOT / "data" / "export" / "board.json"
_DB_CANDIDATES = [
    ROOT / "data" / "nfl.db",
    Path(r"C:\Users\matth\Documents\Personal\Fantasy Football\data\nfl.db"),
]
DB_PATH = next((p for p in _DB_CANDIDATES if p.exists()), None)


def test_t3_every_board_player_has_a_bye_week():
    """A null bye on the export is honest DISPLAY, but at build time it means
    the schedule join failed for that team (e.g. a FantasyPros/nflverse team
    code mismatch like JAC/JAX) — and it fails silently for the team's entire
    roster. Positive coverage converts fail-open into fail-loud."""
    board = json.loads(BOARD.read_text(encoding="utf-8"))
    rows = board["players"] if isinstance(board, dict) and "players" in board else board
    assert isinstance(rows, list) and rows, "board.json has no player rows"
    missing = [
        (r.get("player_name") or r.get("name"), r.get("team"))
        for r in rows
        # 'FA' / empty team = genuinely teamless player; a null bye there is
        # an honest null, not a join miss. Every REAL team code must resolve.
        if r.get("bye_week") is None and r.get("team") not in (None, "", "FA")
    ]
    teams = sorted({t for _, t in missing if t})
    assert not missing, (
        f"{len(missing)} board players have no bye week; affected team codes "
        f"{teams}. Each code is a schedule-join miss for that team's entire "
        f"roster — resolve the code mapping, do not null-fill. (Found live "
        f"2026-07-27: JAC and LAR — FantasyPros codes that nflverse spells "
        f"JAX and LA — stripped byes from both full rosters on the shipped "
        f"board. This test stays red until the mapping is fixed.)"
    )


@pytest.mark.skipif(DB_PATH is None, reason="nfl.db not available")
def test_t10_live_season_consensus_rows_are_unique_per_player():
    conn = sqlite3.connect(f"file:{DB_PATH}?mode=ro", uri=True)
    try:
        season = conn.execute(
            "SELECT MAX(season) FROM rankings WHERE source='fantasypros_ecr'"
        ).fetchone()[0]
        dupes_by_id = [
            r for r in conn.execute(
                "SELECT player_id, COUNT(*) c FROM rankings "
                "WHERE source='fantasypros_ecr' AND season=? AND player_id IS NOT NULL "
                "GROUP BY player_id HAVING c > 1", (season,))
        ]
        dupes_by_name = [
            r for r in conn.execute(
                "SELECT player_name, position, COUNT(*) c FROM rankings "
                "WHERE source='fantasypros_ecr' AND season=? "
                "GROUP BY player_name, position HAVING c > 1", (season,))
        ]
    finally:
        conn.close()
    assert not dupes_by_id, (
        f"Duplicate consensus rows for season {season} by player_id: "
        f"{dupes_by_id} — a duplicated player ranks twice and silently "
        f"corrupts the board."
    )
    assert not dupes_by_name, (
        f"Duplicate consensus rows for season {season} by (name, position): "
        f"{dupes_by_name}"
    )
