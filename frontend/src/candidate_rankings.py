"""
Candidate ranking-config builders for the Phase 1 baseline backtest runs
(test-registry.md #44/#45/#46).

All three configurations are built from prior-season (2024) actual
performance, routed through CutoffEnforcedStore so they can never see the
season being backtested -- same structural guarantee backtest.py's own
internal baselines get.

Team count for VBD: 10 (this league's settled parameter -- see
docs/decisions.md 2026-07-25 session 3 entry; NOT the 12-team figure
mentioned in the original task, which conflicted with test-registry.md's
own league context and was corrected after asking).
"""

from __future__ import annotations

import sqlite3
from typing import Dict, List, Optional, Tuple

import db
from backtest import RankingConfig
from scoring import ReplacementLevels, compute_vbd, score_offensive_game


def prior_season_vbd_values(
    store: "db.CutoffEnforcedStore", prior_season: int, levels: ReplacementLevels
) -> Tuple[Dict[str, float], Dict[str, str]]:
    """(player_id -> VBD value, player_id -> position) from prior_season's
    actual games -- every player who recorded a stat that season."""
    totals: Dict[str, float] = {}
    pos_counts: Dict[str, Dict[str, int]] = {}
    for row in store.player_week_rows(seasons=[prior_season]):
        stats = {col: row[col] for col in db.SCORING_STAT_COLUMNS}
        pid = row["player_id"]
        totals[pid] = totals.get(pid, 0.0) + score_offensive_game(stats)
        counts = pos_counts.setdefault(pid, {})
        counts[row["position"]] = counts.get(row["position"], 0) + 1

    positions = {pid: max(c.items(), key=lambda kv: kv[1])[0] for pid, c in pos_counts.items()}

    by_position: Dict[str, List[Tuple[str, float]]] = {}
    for pid, total in totals.items():
        pos = positions.get(pid)
        if pos is None:
            continue
        by_position.setdefault(pos, []).append((pid, total))

    vbd = compute_vbd(by_position, levels)
    return vbd, positions


def vbd_baseline_ranking(values: Dict[str, float]) -> RankingConfig:
    """Config #1 (test-registry.md #44's BPA arm): rank all players by
    descending prior-season VBD, across positions."""
    ranked = sorted(values.items(), key=lambda kv: -kv[1])
    return {pid: i + 1 for i, (pid, _) in enumerate(ranked)}


def hero_rb_ranking(
    values: Dict[str, float],
    positions: Dict[str, str],
    top_n: int = 24,
    bonus: float = 0.30,
) -> Tuple[RankingConfig, List[str]]:
    """Config #2 (test-registry.md #44): top-`top_n` RBs by base VBD value
    get a `bonus` multiplier applied to their value; every other player
    (including lower RBs) is untouched. Re-ranking the whole pool by the
    adjusted value is what lets the boosted RBs climb the overall order --
    "other positions BPA" falls out naturally since their values don't move.
    """
    rbs = sorted(
        (pid for pid, pos in positions.items() if pos == "RB" and pid in values),
        key=lambda pid: -values[pid],
    )
    boosted_ids = rbs[:top_n]
    adjusted = dict(values)
    for pid in boosted_ids:
        adjusted[pid] = values[pid] * (1 + bonus)
    return vbd_baseline_ranking(adjusted), boosted_ids


def _rerank_with_forced_positions(base_ranking: RankingConfig, forced: Dict[str, int]) -> RankingConfig:
    """base_ranking's total order, with `forced` players relocated to
    specific target overall ranks and everyone else keeping relative order,
    filling in around them."""
    n = len(base_ranking)
    forced_ranks = set(forced.values())
    if len(forced_ranks) != len(forced):
        raise ValueError("forced target ranks must be unique")
    free_ranks = [r for r in range(1, n + 1) if r not in forced_ranks]
    remaining = sorted((pid for pid in base_ranking if pid not in forced), key=lambda pid: base_ranking[pid])
    new_ranking: RankingConfig = dict(forced)
    for pid, rank in zip(remaining, free_ranks):
        new_ranking[pid] = rank
    return new_ranking


def find_player_id(conn: sqlite3.Connection, name_fragment: str, position: str, season: int) -> Optional[str]:
    row = conn.execute(
        "SELECT DISTINCT player_id FROM player_weekly_stats "
        "WHERE position = ? AND season = ? AND player_name LIKE ?",
        (position, season, f"%{name_fragment}%"),
    ).fetchone()
    return row[0] if row else None


def elite_te_ranking(
    base_ranking: RankingConfig,
    elite_player_ids: List[str],
    elite_target_ranks: List[int],
    positions: Dict[str, str],
    bottom_n: int = 30,
) -> RankingConfig:
    """Config #3 (test-registry.md #45): `elite_player_ids` forced to
    `elite_target_ranks` (top-15 band). Every OTHER TE that would otherwise
    rank well enough to tempt a pick -- the best `bottom_n` of them by the
    base ranking -- gets pushed into the worst `bottom_n` overall rank slots.
    TEs already ranked near the bottom naturally are left alone; forcing
    them further down would be a no-op. "Other positions BPA" means nothing
    else in `base_ranking` is touched.
    """
    n = len(base_ranking)
    other_tes = sorted(
        (pid for pid, pos in positions.items() if pos == "TE" and pid in base_ranking and pid not in elite_player_ids),
        key=lambda pid: base_ranking[pid],
    )
    to_demote = other_tes[:bottom_n]
    bottom_targets = list(range(n - bottom_n + 1, n + 1))[: len(to_demote)]

    forced = dict(zip(elite_player_ids, elite_target_ranks))
    forced.update(dict(zip(to_demote, bottom_targets)))
    return _rerank_with_forced_positions(base_ranking, forced)
