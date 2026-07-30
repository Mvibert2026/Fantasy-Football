"""Season board construction for the FR-085 draft-strategy simulation.

Rules are those fixed in `docs/ranking/fr085-strategy-sim-precommit.md` before any
simulation ran. Read that first; this module implements it and adds nothing.

LOOK-AHEAD. Everything used to *order* the board comes from the pre-season market
snapshot or from seasons strictly before the target. `season_outcomes()` is the
one function that reads the target season, it is named so that calling it is
deliberate, and it refuses seasons >= the sealed 2025 holdout.
"""
from __future__ import annotations

import sqlite3
import sys
from collections import defaultdict
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List, Optional, Sequence, Tuple

import numpy as np

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO / "src"))

import db  # noqa: E402
from scoring import score_offensive_game, ReplacementLevels  # noqa: E402

DB_PATH = REPO / "data" / "nfl.db"
POSITIONS = ("QB", "RB", "WR", "TE")
HOLDOUT_SEASON = 2025

LEVELS = ReplacementLevels()          # 10-team, this league's measured flex split
BASELINES = LEVELS.baselines()        # {'QB':10,'RB':30,'WR':40,'TE':10}

CURVE_LOOKBACK = 5                    # seasons; declared in the pre-commitment
CURVE_SMOOTH = 3                      # moving-average width; declared


def scheduled_games(season: int) -> int:
    return 17 if season >= 2021 else 16


# --------------------------------------------------------------------- outcomes
@dataclass
class SeasonOutcomes:
    season: int
    n_weeks: int
    points: Dict[str, np.ndarray]     # gsis_id -> (n_weeks+1,) fantasy points
    appeared: Dict[str, np.ndarray]   # gsis_id -> (n_weeks+1,) bool: had a stat row
    position: Dict[str, str]          # modal position that season
    totals: Dict[str, float]


def season_outcomes(conn: sqlite3.Connection, season: int) -> SeasonOutcomes:
    """TARGET-SEASON READ. Evaluation only. Never call from board ordering."""
    if season >= HOLDOUT_SEASON:
        raise RuntimeError(
            f"season {season} is at or past the sealed holdout {HOLDOUT_SEASON}")
    n_weeks = conn.execute(
        "SELECT MAX(week) FROM player_weekly_stats WHERE season=? AND season_type='REG'",
        (season,)).fetchone()[0] or 17
    pts: Dict[str, np.ndarray] = {}
    app: Dict[str, np.ndarray] = {}
    pos_counts: Dict[str, Dict[str, int]] = defaultdict(lambda: defaultdict(int))
    for row in db.actual_season_outcomes(conn, season, season_type="REG"):
        pid = row["player_id"]
        if pid not in pts:
            pts[pid] = np.zeros(n_weeks + 1)
            app[pid] = np.zeros(n_weeks + 1, dtype=bool)
        stats = {c: row[c] for c in db.SCORING_STAT_COLUMNS}
        wk = row["week"]
        if 0 <= wk <= n_weeks:
            pts[pid][wk] += score_offensive_game(stats)
            app[pid][wk] = True
        pos_counts[pid][row["position"]] += 1
    position = {pid: max(c.items(), key=lambda kv: kv[1])[0] for pid, c in pos_counts.items()}
    totals = {pid: float(v.sum()) for pid, v in pts.items()}
    return SeasonOutcomes(season, n_weeks, pts, app, position, totals)


# ----------------------------------------------------------------- value curves
def _season_finish_curve(conn: sqlite3.Connection, season: int) -> Dict[str, List[float]]:
    """Descending SEASON-TOTAL finish curve for one season, per position.

    Season totals, not points per game: the object being estimated is "what does
    the player you draft at positional rank k return over a season", and missing
    games are part of that, not a nuisance to be divided out. The 16->17 game
    expansion is handled by the caller, which rescales each source season onto
    the target season's scheduled length."""
    tot: Dict[str, float] = defaultdict(float)
    pos_counts: Dict[str, Dict[str, int]] = defaultdict(lambda: defaultdict(int))
    sql = (f"SELECT * FROM {db.SCORING_VIEW} WHERE season=? AND season_type='REG'")
    for row in conn.execute(sql, (season,)):
        pid = row["player_id"]
        stats = {c: row[c] for c in db.SCORING_STAT_COLUMNS}
        tot[pid] += score_offensive_game(stats)
        pos_counts[pid][row["position"]] += 1
    out: Dict[str, List[float]] = {p: [] for p in POSITIONS}
    for pid, t in tot.items():
        pos = max(pos_counts[pid].items(), key=lambda kv: kv[1])[0]
        if pos in POSITIONS:
            out[pos].append(t)
    for p in out:
        out[p].sort(reverse=True)
    return out


class ValueCurves:
    """Positional-rank -> expected season points, fitted on prior seasons ONLY."""

    def __init__(self, conn: sqlite3.Connection, target_season: int,
                 lookback: int = CURVE_LOOKBACK):
        self.target_season = target_season
        self.seasons_used = [s for s in range(target_season - lookback, target_season)
                             if s >= 1999]
        if any(s >= target_season for s in self.seasons_used):
            raise RuntimeError("value curve would read the target season")
        n_games = scheduled_games(target_season)
        per_season = []
        for s in self.seasons_used:
            d = _season_finish_curve(conn, s)
            scale = n_games / scheduled_games(s)
            per_season.append({p: [v * scale for v in vs] for p, vs in d.items()})
        self.curve: Dict[str, np.ndarray] = {}
        for pos in POSITIONS:
            length = max(len(d[pos]) for d in per_season)
            acc = np.zeros(length)
            cnt = np.zeros(length)
            for d in per_season:
                v = d[pos]
                acc[:len(v)] += np.array(v)
                cnt[:len(v)] += 1
            mean_total = np.divide(acc, np.maximum(cnt, 1))
            k = CURVE_SMOOTH
            pad = np.pad(mean_total, (k // 2, k // 2), mode="edge")
            self.curve[pos] = np.convolve(pad, np.ones(k) / k, mode="valid")

    def expected_points(self, pos: str, pos_rank: int) -> float:
        c = self.curve[pos]
        return float(c[min(max(pos_rank, 1) - 1, len(c) - 1)])

    def vbd(self, pos: str, pos_rank: int) -> float:
        return self.expected_points(pos, pos_rank) - self.expected_points(
            pos, BASELINES.get(pos, 24))


# ----------------------------------------------------------------------- boards
@dataclass
class Board:
    season: int
    source: str
    gsis: List[Optional[str]]
    names: List[str]
    pos_idx: np.ndarray           # index into POSITIONS
    consensus_rank: np.ndarray    # float, 1..n, the market ordering
    pick_sd: np.ndarray           # per-player measured pick sd (nan where unknown)
    vbd: np.ndarray               # value estimate every strategy shares
    vbd_rank: np.ndarray          # 1..n, descending VBD; the strategies' own board
    layer: np.ndarray             # 1 = primary market, 2 = same-provider fill, 3 = tail
    n_weeks: int
    weekly: np.ndarray            # (n, n_weeks+1)
    appeared: np.ndarray          # (n, n_weeks+1) bool


def _mfl_to_gsis(conn) -> Dict[str, str]:
    return {str(m): g for m, g in conn.execute(
        "SELECT mfl_id, source_id FROM player_ids WHERE source='gsis'")}


def _prior_season_points(conn: sqlite3.Connection, season: int) -> Dict[str, Tuple[str, float]]:
    """(position, points) for season-1 under this league's scoring. Pre-draft
    observable; used only to order the layer-3 tail."""
    prior = season - 1
    tot: Dict[str, float] = defaultdict(float)
    pos_counts: Dict[str, Dict[str, int]] = defaultdict(lambda: defaultdict(int))
    for row in conn.execute(f"SELECT * FROM {db.SCORING_VIEW} WHERE season=? AND season_type='REG'",
                            (prior,)):
        pid = row["player_id"]
        tot[pid] += score_offensive_game({c: row[c] for c in db.SCORING_STAT_COLUMNS})
        pos_counts[pid][row["position"]] += 1
    out = {}
    for pid, t in tot.items():
        pos = max(pos_counts[pid].items(), key=lambda kv: kv[1])[0]
        if pos in POSITIONS:
            out[pid] = (pos, t)
    return out


def _interp_rank(other_rank: float, common_other: Sequence[float],
                 common_primary: Sequence[float]) -> float:
    return float(np.interp(other_rank, common_other, common_primary))


def build_board(conn: sqlite3.Connection, season: int, source: str,
                min_players: int) -> Board:
    curves = ValueCurves(conn, season)
    out = season_outcomes(conn, season)

    rows: List[dict] = []
    if source == "ffc":
        m2g = _mfl_to_gsis(conn)
        half = conn.execute(
            "SELECT mfl_id, player_name, position, rank, std_dev FROM ffc_adp_snapshots "
            "WHERE adp_source='ffc_half_ppr_12team' AND period=? AND position IN "
            "('QB','RB','WR','TE') ORDER BY rank", (season,)).fetchall()
        seen = set()
        for mfl, name, pos, rank, sd in half:
            if mfl is None:
                continue
            rows.append(dict(gsis=m2g.get(str(mfl)), name=name, pos=pos, rank=float(rank),
                             sd=float(sd) if sd is not None else float("nan"), layer=1))
            seen.add(str(mfl))
        # layer 2: same provider, non-PPR board, rank mapped onto the half-PPR scale
        non = conn.execute(
            "SELECT mfl_id, player_name, position, rank, std_dev FROM ffc_adp_snapshots "
            "WHERE adp_source='ffc_non_ppr_12team' AND period=? AND position IN "
            "('QB','RB','WR','TE') ORDER BY rank", (season,)).fetchall()
        half_by_mfl = {str(m): float(r) for m, _, _, r, _ in half if m is not None}
        non_by_mfl = {str(m): float(r) for m, _, _, r, _ in non if m is not None}
        common = sorted(set(half_by_mfl) & set(non_by_mfl), key=lambda k: non_by_mfl[k])
        c_non = [non_by_mfl[k] for k in common]
        c_half = [half_by_mfl[k] for k in common]
        for mfl, name, pos, rank, sd in non:
            if mfl is None or str(mfl) in seen:
                continue
            mapped = _interp_rank(float(rank), c_non, c_half) if len(common) >= 5 else float(rank)
            rows.append(dict(gsis=m2g.get(str(mfl)), name=name, pos=pos, rank=mapped,
                             sd=float(sd) if sd is not None else float("nan"), layer=2))
            seen.add(str(mfl))
    elif source == "ecr":
        got = conn.execute(
            "SELECT player_id, player_name, position, adp_rank FROM rankings "
            "WHERE source='fantasypros_ecr' AND season=? AND position IN ('QB','RB','WR','TE') "
            "ORDER BY adp_rank", (season,)).fetchall()
        for pid, name, pos, rank in got:
            rows.append(dict(gsis=pid, name=name, pos=pos, rank=float(rank),
                             sd=float("nan"), layer=1))
    else:
        raise ValueError(source)

    rows.sort(key=lambda r: r["rank"])

    # layer 3: prior-season points tail, only if the market board is too short
    if len(rows) < min_players:
        have = {r["gsis"] for r in rows if r["gsis"]}
        prior = _prior_season_points(conn, season)
        tail = sorted(((pid, v) for pid, v in prior.items() if pid not in have),
                      key=lambda kv: -kv[1][1])
        names = {}
        for pid, nm in conn.execute(
                "SELECT DISTINCT player_id, player_name FROM player_weekly_stats WHERE season=?",
                (season - 1,)):
            names[pid] = nm
        base = rows[-1]["rank"] if rows else 0.0
        for i, (pid, (pos, _pts)) in enumerate(tail):
            if len(rows) >= min_players:
                break
            rows.append(dict(gsis=pid, name=names.get(pid, pid), pos=pos,
                             rank=base + 1 + i, sd=float("nan"), layer=3))

    n = len(rows)
    pos_idx = np.array([POSITIONS.index(r["pos"]) for r in rows])
    consensus = np.arange(1, n + 1, dtype=float)     # ordinal, gaps removed
    sd = np.array([r["sd"] for r in rows])
    layer = np.array([r["layer"] for r in rows])

    pos_rank_counter: Dict[str, int] = defaultdict(int)
    vbd = np.zeros(n)
    for i, r in enumerate(rows):
        pos_rank_counter[r["pos"]] += 1
        vbd[i] = curves.vbd(r["pos"], pos_rank_counter[r["pos"]])

    # The strategies' own board: VBD converted to a rank, so the positional-need
    # penalty (in rank units, inherited from src/draft_sim.py) applies to user and
    # opponents in the same currency.
    vbd_rank = np.empty(n, dtype=float)
    vbd_rank[np.argsort(-vbd, kind="stable")] = np.arange(1, n + 1, dtype=float)

    weekly = np.zeros((n, out.n_weeks + 1))
    appeared = np.zeros((n, out.n_weeks + 1), dtype=bool)
    for i, r in enumerate(rows):
        g = r["gsis"]
        if g and g in out.points:
            weekly[i] = out.points[g]
            appeared[i] = out.appeared[g]

    return Board(season, source, [r["gsis"] for r in rows], [r["name"] for r in rows],
                 pos_idx, consensus, sd, vbd, vbd_rank, layer, out.n_weeks, weekly, appeared)
