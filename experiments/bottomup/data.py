"""Feature/target assembly for the bottom-up prototype.

Registration: docs/reviews/fable-ranking-design-2026-07-27.md ("Prototype
registration"). Frozen before any fitting.

Look-ahead discipline, enforced structurally in this module:
- `SeasonStore.features_for(target_season)` refuses to touch any row from
  `season >= target_season` (assertion, not convention).
- `HOLDOUT_SEASON = 2025` is hard-sealed: any attempt to *evaluate* a target
  season >= 2025 raises. The holdout is never read by this experiment.

The scoring convention deliberately mirrors src/db.py's scoring view aliases so
actual points here equal the backtest harness's actuals (same
score_offensive_game, same column mapping).
"""

from __future__ import annotations

import sqlite3
import sys
from collections import defaultdict
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, List, Optional, Tuple

_SRC = Path(__file__).resolve().parents[2] / "src"
if str(_SRC) not in sys.path:
    sys.path.insert(0, str(_SRC))

from scoring import score_offensive_game  # noqa: E402

HOLDOUT_SEASON = 2025  # sealed; never evaluated, never featured
POSITIONS = ("QB", "RB", "WR", "TE")
# ADR-016 draft-relevant depths (make_board.py RELEVANT_DEPTH) — universe rule.
UNIVERSE_DEPTH = {"QB": 20, "RB": 45, "WR": 60, "TE": 20}

# Per-season target-data reliability, measured 2026-07-27 (WR REG targets sum):
# 1999-2002 ok; 2003-2008 effectively zero; 2009+ ok. Air yards real 2009+ only.
TARGET_RELIABLE = lambda s: (1999 <= s <= 2002) or (s >= 2009)  # noqa: E731
AIR_YARDS_RELIABLE = lambda s: s >= 2009  # noqa: E731


class HoldoutViolation(Exception):
    pass


class CutoffViolation(Exception):
    pass


_WEEK_SQL = """
SELECT player_id, position, week, team,
       COALESCE(passing_yards,0)  AS passing_yards,
       COALESCE(passing_tds,0)    AS passing_tds,
       COALESCE(passing_interceptions,0) AS interceptions,
       COALESCE(rushing_yards,0)  AS rushing_yards,
       COALESCE(rushing_tds,0)    AS rushing_tds,
       COALESCE(receptions,0)     AS receptions,
       COALESCE(receiving_yards,0) AS receiving_yards,
       COALESCE(receiving_tds,0)  AS receiving_tds,
       COALESCE(fumbles_lost_total,0) AS fumbles_lost,
       COALESCE(special_teams_tds,0)  AS return_tds,
       (COALESCE(passing_2pt_conversions,0)+COALESCE(rushing_2pt_conversions,0)
        +COALESCE(receiving_2pt_conversions,0)) AS two_point_conversions,
       COALESCE(fumble_recovery_tds,0) AS offensive_fumble_return_tds,
       COALESCE(attempts,0)       AS attempts,
       COALESCE(carries,0)        AS carries,
       COALESCE(targets,0)        AS targets,
       COALESCE(receiving_air_yards,0) AS receiving_air_yards
FROM player_weekly_stats
WHERE season = ? AND season_type = 'REG'
"""

_SCORING_KEYS = (
    "passing_yards", "passing_tds", "interceptions", "rushing_yards",
    "rushing_tds", "receptions", "receiving_yards", "receiving_tds",
    "fumbles_lost", "return_tds", "two_point_conversions",
    "offensive_fumble_return_tds",
)


@dataclass
class PlayerSeason:
    """One player's aggregated REG season."""

    player_id: str
    season: int
    position: str            # modal weekly position
    team: str                # modal team
    games: int = 0
    points: float = 0.0      # league scoring, per-game engine, summed
    # volume totals
    attempts: int = 0
    carries: int = 0
    targets: int = 0
    receptions: int = 0
    pass_yards: float = 0.0
    rush_yards: float = 0.0
    rec_yards: float = 0.0
    air_yards: float = 0.0
    pass_tds: int = 0
    rush_tds: int = 0
    rec_tds: int = 0
    interceptions: int = 0
    # per-game bonus points actually earned (for the S3 bonus tables)
    bonus_pts_pass: float = 0.0
    bonus_pts_rush: float = 0.0
    bonus_pts_rec: float = 0.0

    @property
    def ppg(self) -> Optional[float]:
        return self.points / self.games if self.games else None


def _bonus_points(yards: float, thresholds) -> float:
    return sum(b for t, b in thresholds if yards >= t)


_PASS_BONUS = ((300, 1.0), (350, 1.5), (400, 2.0))
_YDS_BONUS = ((100, 1.0), (150, 1.5), (200, 2.0))


class SeasonStore:
    """Read-only aggregate store with structural cutoff enforcement."""

    def __init__(self, db_path: Path):
        # mode=ro so this experiment cannot write to the shared DB, and cannot
        # take a write lock against agents running on master.
        self.conn = sqlite3.connect(f"file:{db_path}?mode=ro", uri=True)
        self.conn.row_factory = sqlite3.Row
        self._season_cache: Dict[int, Dict[str, PlayerSeason]] = {}
        self._team_cache: Dict[int, Dict[str, Dict[str, float]]] = {}
        self._birthdates: Optional[Dict[str, str]] = None

    # ----------------------------------------------------------- aggregation
    def _load_season(self, season: int) -> Dict[str, PlayerSeason]:
        if season in self._season_cache:
            return self._season_cache[season]
        if season >= HOLDOUT_SEASON:
            raise HoldoutViolation(
                f"season {season} is at/after the sealed holdout ({HOLDOUT_SEASON})"
            )
        agg: Dict[str, PlayerSeason] = {}
        pos_votes: Dict[str, Dict[str, int]] = defaultdict(lambda: defaultdict(int))
        team_votes: Dict[str, Dict[str, int]] = defaultdict(lambda: defaultdict(int))
        team_week: Dict[Tuple[str, int], Dict[str, float]] = defaultdict(
            lambda: {"attempts": 0.0, "carries": 0.0, "targets": 0.0,
                     "receptions": 0.0, "plays": 0.0}
        )
        for row in self.conn.execute(_WEEK_SQL, (season,)):
            pid = row["player_id"]
            ps = agg.get(pid)
            if ps is None:
                ps = agg[pid] = PlayerSeason(pid, season, "", "")
            ps.games += 1
            ps.points += score_offensive_game({k: row[k] for k in _SCORING_KEYS})
            ps.attempts += row["attempts"]
            ps.carries += row["carries"]
            ps.targets += row["targets"]
            ps.receptions += row["receptions"]
            ps.pass_yards += row["passing_yards"]
            ps.rush_yards += row["rushing_yards"]
            ps.rec_yards += row["receiving_yards"]
            ps.air_yards += row["receiving_air_yards"]
            ps.pass_tds += row["passing_tds"]
            ps.rush_tds += row["rushing_tds"]
            ps.rec_tds += row["receiving_tds"]
            ps.interceptions += row["interceptions"]
            ps.bonus_pts_pass += _bonus_points(row["passing_yards"], _PASS_BONUS)
            ps.bonus_pts_rush += _bonus_points(row["rushing_yards"], _YDS_BONUS)
            ps.bonus_pts_rec += _bonus_points(row["receiving_yards"], _YDS_BONUS)
            if row["position"]:
                pos_votes[pid][row["position"]] += 1
            if row["team"]:
                team_votes[pid][row["team"]] += 1
            tw = team_week[(row["team"], row["week"])]
            tw["attempts"] += row["attempts"]
            tw["carries"] += row["carries"]
            tw["targets"] += row["targets"]
            tw["receptions"] += row["receptions"]
            tw["plays"] += row["attempts"] + row["carries"]
        for pid, ps in agg.items():
            if pos_votes[pid]:
                ps.position = max(pos_votes[pid].items(), key=lambda kv: kv[1])[0]
            if team_votes[pid]:
                ps.team = max(team_votes[pid].items(), key=lambda kv: kv[1])[0]
        # team-season per-game aggregates
        team_tot: Dict[str, Dict[str, float]] = defaultdict(
            lambda: {"attempts": 0.0, "carries": 0.0, "targets": 0.0,
                     "receptions": 0.0, "plays": 0.0, "weeks": 0.0}
        )
        for (team, _week), tw in team_week.items():
            if not team:
                continue
            tt = team_tot[team]
            for k in ("attempts", "carries", "targets", "receptions", "plays"):
                tt[k] += tw[k]
            tt["weeks"] += 1
        self._team_cache[season] = {
            t: {k: (v[k] / v["weeks"] if v["weeks"] else 0.0)
                for k in ("attempts", "carries", "targets", "receptions",
                          "plays")}
            for t, v in team_tot.items()
        }
        if not hasattr(self, "_team_totals"):
            self._team_totals: Dict[int, Dict[str, Dict[str, float]]] = {}
        self._team_totals[season] = {
            t: {"targets": v["targets"], "carries": v["carries"],
                "attempts": v["attempts"], "receptions": v["receptions"]}
            for t, v in team_tot.items()
        }
        self._season_cache[season] = agg
        return agg

    def team_totals(self, season: int) -> Dict[str, Dict[str, float]]:
        self._load_season(season)
        return self._team_totals[season]

    # ------------------------------------------------------------ public API
    def player_seasons(self, season: int, *, for_target: Optional[int] = None
                       ) -> Dict[str, PlayerSeason]:
        """Aggregates for `season`. When used as FEATURES for `for_target`,
        the cutoff assertion runs: season must be < for_target."""
        if for_target is not None and season >= for_target:
            raise CutoffViolation(
                f"feature season {season} >= target season {for_target}"
            )
        return self._load_season(season)

    def actuals(self, target_season: int) -> Dict[str, PlayerSeason]:
        """Evaluation-only read of the target season itself."""
        if target_season >= HOLDOUT_SEASON:
            raise HoldoutViolation(
                f"evaluation of season {target_season} is sealed "
                f"(holdout {HOLDOUT_SEASON})"
            )
        return self._load_season(target_season)

    def birthdates(self) -> Dict[str, str]:
        if self._birthdates is None:
            self._birthdates = {
                r["gsis_id"]: r["birthdate"]
                for r in self.conn.execute(
                    "SELECT gsis_id, birthdate FROM ff_playerids "
                    "WHERE gsis_id IS NOT NULL AND birthdate IS NOT NULL"
                )
            }
        return self._birthdates

    def age_at(self, player_id: str, season: int) -> Optional[float]:
        bd = self.birthdates().get(player_id)
        if not bd:
            return None
        try:
            y, m, d = (int(x) for x in bd.split("-"))
        except ValueError:
            return None
        # age at Sept 1 of the season year
        return (season - y) + ((9 - m) * 30 - d + 1) / 365.0

    def consensus_ranks(self, season: int) -> Dict[str, Tuple[str, int]]:
        """Pre-season ECR positional ranks: {gsis_id: (position, pos_rank)}.
        Only pre-season-final snapshots. Descriptive baseline (2021-2024)."""
        if season >= HOLDOUT_SEASON:
            raise HoldoutViolation(f"consensus for sealed season {season}")
        rows = list(self.conn.execute(
            "SELECT player_id, position, adp_rank FROM rankings "
            "WHERE source='fantasypros_ecr' AND season=? AND is_preseason_final=1 "
            "AND player_id IS NOT NULL ORDER BY adp_rank",
            (season,),
        ))
        out: Dict[str, Tuple[str, int]] = {}
        counters: Dict[str, int] = defaultdict(int)
        for r in rows:
            pos = r["position"]
            if pos not in POSITIONS:
                continue
            counters[pos] += 1
            out[r["player_id"]] = (pos, counters[pos])
        return out


def frozen_universe(store: SeasonStore, target_season: int
                    ) -> Dict[str, List[str]]:
    """Pre-season-frozen universe for `target_season`: prior-season positional
    finish within ADR-016 depths. Rookies excluded by construction (v0,
    registered). Returns {position: [player_id ranked by prior points]}."""
    prior = store.player_seasons(target_season - 1, for_target=target_season)
    by_pos: Dict[str, List[Tuple[float, str]]] = defaultdict(list)
    for pid, ps in prior.items():
        if ps.position in POSITIONS:
            by_pos[ps.position].append((-ps.points, pid))
    out: Dict[str, List[str]] = {}
    for pos in POSITIONS:
        ranked = sorted(by_pos.get(pos, []))
        out[pos] = [pid for _, pid in ranked[: UNIVERSE_DEPTH[pos]]]
    return out
