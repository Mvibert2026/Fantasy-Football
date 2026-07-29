"""Pass 2 — where in the draft the TE mispricing sits, and whether late TE hits are forecastable.

FR-039. Exploratory. Nothing here is confirmatory and no result may be reported as an edge.

Look-ahead posture, enforced structurally in this file:
  * SEAL = 2025. `_check(season)` raises on any query touching season >= 2025, for features
    OR outcomes. The sealed holdout is never read.
  * The market snapshot is `rankings` where source='fantasypros_ecr' AND is_preseason_final=1,
    whose as_of_date is late August of the target season -- strictly before Week 1.
  * Features for target season N read seasons <= N-1 only (asserted).

Survivorship posture:
  * The universe for season N is *every* TE on that season's pre-draft consensus list. It is
    frozen by construction: the list was published before the season. Players who never took a
    snap score 0 and are RETAINED. Nothing is defined by having scored points.

Usage:  .venv/bin/python experiments/bottomup/pass2_te_adp.py [--db PATH]
"""

from __future__ import annotations

import argparse
import json
import math
import random
import sqlite3
import sys
from collections import defaultdict
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, List, Optional, Sequence, Tuple

_SRC = Path(__file__).resolve().parents[2] / "src"
if str(_SRC) not in sys.path:
    sys.path.insert(0, str(_SRC))
from scoring import score_offensive_game  # noqa: E402

SEAL = 2025                       # never read, features or outcomes
TARGETS = (2021, 2022, 2023, 2024)  # seasons with a pre-draft consensus snapshot
SEED = 20260729
BOOT = 4000


class SealViolation(Exception):
    pass


def _check(season: int) -> int:
    if season >= SEAL:
        raise SealViolation(f"season {season} is at/after the sealed holdout ({SEAL})")
    return season


_SCORING_KEYS = (
    "passing_yards", "passing_tds", "interceptions", "rushing_yards", "rushing_tds",
    "receptions", "receiving_yards", "receiving_tds", "fumbles_lost", "return_tds",
    "two_point_conversions", "offensive_fumble_return_tds",
)

_WEEK_SQL = """
SELECT player_id, position, week, team,
       COALESCE(passing_yards,0) AS passing_yards,
       COALESCE(passing_tds,0) AS passing_tds,
       COALESCE(passing_interceptions,0) AS interceptions,
       COALESCE(rushing_yards,0) AS rushing_yards,
       COALESCE(rushing_tds,0) AS rushing_tds,
       COALESCE(receptions,0) AS receptions,
       COALESCE(receiving_yards,0) AS receiving_yards,
       COALESCE(receiving_tds,0) AS receiving_tds,
       COALESCE(fumbles_lost_total,0) AS fumbles_lost,
       COALESCE(special_teams_tds,0) AS return_tds,
       (COALESCE(passing_2pt_conversions,0)+COALESCE(rushing_2pt_conversions,0)
        +COALESCE(receiving_2pt_conversions,0)) AS two_point_conversions,
       COALESCE(fumble_recovery_tds,0) AS offensive_fumble_return_tds,
       COALESCE(targets,0) AS targets,
       COALESCE(carries,0) AS carries
FROM player_weekly_stats
WHERE season = ? AND season_type = 'REG'
"""


@dataclass
class Season:
    games: int = 0
    points: float = 0.0
    targets: int = 0
    pos_votes: Dict[str, int] = field(default_factory=lambda: defaultdict(int))
    team_votes: Dict[str, int] = field(default_factory=lambda: defaultdict(int))

    @property
    def ppg(self) -> float:
        return self.points / self.games if self.games else 0.0

    @property
    def pos(self) -> str:
        return max(self.pos_votes, key=self.pos_votes.get) if self.pos_votes else ""

    @property
    def team(self) -> str:
        return max(self.team_votes, key=self.team_votes.get) if self.team_votes else ""


class Store:
    def __init__(self, db: Path):
        self.conn = sqlite3.connect(f"file:{db}?mode=ro", uri=True)
        self.conn.row_factory = sqlite3.Row
        self._seasons: Dict[int, Dict[str, Season]] = {}
        self._snaps: Dict[int, Dict[str, float]] = {}
        self._draft: Optional[Dict[str, Tuple[int, int, int]]] = None
        self._birth: Optional[Dict[str, str]] = None

    def season(self, s: int) -> Dict[str, Season]:
        _check(s)
        if s in self._seasons:
            return self._seasons[s]
        agg: Dict[str, Season] = defaultdict(Season)
        for r in self.conn.execute(_WEEK_SQL, (s,)):
            ps = agg[r["player_id"]]
            ps.games += 1
            ps.points += score_offensive_game({k: r[k] for k in _SCORING_KEYS})
            ps.targets += r["targets"]
            if r["position"]:
                ps.pos_votes[r["position"]] += 1
            if r["team"]:
                ps.team_votes[r["team"]] += 1
        self._seasons[s] = dict(agg)
        return self._seasons[s]

    def snap_share(self, s: int) -> Dict[str, float]:
        """Mean offensive snap % over games played, keyed by gsis_id. 2013+ only."""
        _check(s)
        if s in self._snaps:
            return self._snaps[s]
        out: Dict[str, List[float]] = defaultdict(list)
        sql = """SELECT f.gsis_id AS gsis, sc.offense_pct AS pct
                 FROM snap_counts sc JOIN ff_playerids f ON f.pfr_id = sc.pfr_player_id
                 WHERE sc.season = ? AND sc.game_type = 'REG' AND sc.offense_pct IS NOT NULL
                   AND f.gsis_id IS NOT NULL AND f.gsis_id <> ''"""
        for r in self.conn.execute(sql, (s,)):
            out[r["gsis"]].append(r["pct"])
        self._snaps[s] = {k: sum(v) / len(v) for k, v in out.items() if v}
        return self._snaps[s]

    def draft(self) -> Dict[str, Tuple[int, int, int]]:
        """gsis_id -> (draft_season, round, overall pick). Undrafted players absent."""
        if self._draft is None:
            self._draft = {}
            for r in self.conn.execute(
                "SELECT gsis_id, season, round, pick FROM draft_picks "
                "WHERE gsis_id IS NOT NULL AND gsis_id <> ''"
            ):
                self._draft[r["gsis_id"]] = (r["season"], r["round"], r["pick"])
        return self._draft

    def birthdates(self) -> Dict[str, str]:
        if self._birth is None:
            self._birth = {}
            for r in self.conn.execute(
                "SELECT gsis_id, birthdate FROM ff_playerids "
                "WHERE gsis_id IS NOT NULL AND gsis_id <> '' AND birthdate IS NOT NULL"
            ):
                self._birth[r["gsis_id"]] = r["birthdate"]
        return self._birth

    def consensus(self, s: int, position: str) -> List[sqlite3.Row]:
        """Pre-draft consensus list for season s. as_of_date is late August of s."""
        _check(s)
        return list(self.conn.execute(
            "SELECT player_id, player_name, team, adp_rank, adp_value, spread_sd, "
            "       rank_best, rank_worst, as_of_date "
            "FROM rankings WHERE source='fantasypros_ecr' AND is_preseason_final=1 "
            "  AND season=? AND position=? AND adp_rank IS NOT NULL "
            "ORDER BY adp_rank", (s, position)))


# ------------------------------------------------------------------ statistics

def kendall_tau_b(x: Sequence[float], y: Sequence[float]) -> Optional[float]:
    n = len(x)
    if n < 3:
        return None
    conc = disc = tx = ty = 0
    for i in range(n):
        for j in range(i + 1, n):
            dx, dy = x[i] - x[j], y[i] - y[j]
            if dx == 0 and dy == 0:
                tx += 1; ty += 1
            elif dx == 0:
                tx += 1
            elif dy == 0:
                ty += 1
            elif (dx > 0) == (dy > 0):
                conc += 1
            else:
                disc += 1
    n0 = n * (n - 1) / 2
    den = math.sqrt((n0 - tx) * (n0 - ty))
    return (conc - disc) / den if den > 0 else None


def pearson(x: Sequence[float], y: Sequence[float]) -> Optional[float]:
    n = len(x)
    if n < 3:
        return None
    mx, my = sum(x) / n, sum(y) / n
    sxy = sum((a - mx) * (b - my) for a, b in zip(x, y))
    sxx = sum((a - mx) ** 2 for a in x)
    syy = sum((b - my) ** 2 for b in y)
    return sxy / math.sqrt(sxx * syy) if sxx > 0 and syy > 0 else None


def partial_pearson(x, y, z) -> Optional[float]:
    """corr(x, y | z)."""
    rxy, rxz, ryz = pearson(x, y), pearson(x, z), pearson(y, z)
    if None in (rxy, rxz, ryz):
        return None
    den = math.sqrt(max(1e-12, (1 - rxz ** 2) * (1 - ryz ** 2)))
    return (rxy - rxz * ryz) / den


def auc(scores: Sequence[float], labels: Sequence[int]) -> Optional[float]:
    """P(score of a hit > score of a non-hit), ties at 0.5."""
    pos = [s for s, l in zip(scores, labels) if l]
    neg = [s for s, l in zip(scores, labels) if not l]
    if not pos or not neg:
        return None
    tot = 0.0
    for p in pos:
        for q in neg:
            tot += 1.0 if p > q else (0.5 if p == q else 0.0)
    return tot / (len(pos) * len(neg))


def season_bootstrap(by_season: Dict[int, list], stat, n=BOOT, seed=SEED):
    """Resample SEASONS with replacement (guardrails S7), recompute stat on the pooled rows."""
    rng = random.Random(seed)
    seasons = sorted(by_season)
    point = stat([r for s in seasons for r in by_season[s]])
    draws = []
    for _ in range(n):
        pick = [rng.choice(seasons) for _ in seasons]
        rows = [r for s in pick for r in by_season[s]]
        v = stat(rows)
        if v is not None and not (isinstance(v, float) and math.isnan(v)):
            draws.append(v)
    if len(draws) < n * 0.5:
        return point, None, None
    draws.sort()
    return point, draws[int(0.025 * len(draws))], draws[int(0.975 * len(draws))]


def wilson(k: int, n: int, z: float = 1.96) -> Tuple[float, float, float]:
    if n == 0:
        return 0.0, 0.0, 0.0
    p = k / n
    d = 1 + z * z / n
    c = (p + z * z / (2 * n)) / d
    h = z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / d
    return p, max(0.0, c - h), min(1.0, c + h)
