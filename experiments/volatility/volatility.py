"""FR-086 -- week-to-week volatility of fantasy points, by position and by
within-position player type, under THIS league's scoring.

Founder's words: *"Do WR's have more or less week to week volatility than other
players, can you rank player types by volatility (it may help identify where to
look for high volatility players or pair them for roster builds)."*

WHY THIS IS NOT A NEUTRAL DESCRIPTOR HERE. `CLAUDE.md` §7 says the stacking
yardage bonuses reward ceiling over floor and should influence how variance is
valued. So this measures the dispersion AND how much of it this league actually
pays for. It also measures the thing that decides whether an archetype can use
any of it: **does volatility persist year over year?** A volatility label that
does not persist describes last season and predicts nothing.

SCOPE. This produces the measurement an archetype would consume. It does not
build the archetype UI or schema -- that is FR-075 and another agent's.

DEFINITIONS, fixed before any number was read
---------------------------------------------
Two dispersion windows, because they answer different questions and the founder's
"pair them for roster builds" needs the second:

  played  weeks in which the player has a stats row. The player trait: how
          variable is he WHEN HE PLAYS.
  all     every week of the season (16 before 2021, 17 from 2021), absences and
          bye weeks scored 0. What a manager who must field a lineup actually
          experiences. Bye weeks are included as zeros and that is deliberate --
          a bye is a zero in your lineup exactly like an injury is.

Scale-free measures, because a high scorer has higher absolute SD almost by
construction:
  CV          SD / mean. Familiar, but it is NOT scale-free in practice: CV falls
              mechanically as the mean rises, so ranking types by CV partly ranks
              them by how good they are.
  excess_sd   residual of log(SD) on log(mean), fitted WITHIN position and
              season. This is the measure to use for cross-type comparison and
              the one reported as decision-relevant. Positive = more variable
              than a player of that scoring level normally is.

Sealed holdout 2025 is excluded in code, not by convention.

Run:
    .venv/bin/python -m experiments.volatility.volatility
"""
from __future__ import annotations

import json
import math
import random
import sqlite3
import statistics
import sys
from collections import defaultdict
from dataclasses import dataclass, asdict
from pathlib import Path
from typing import Dict, List, Optional, Sequence, Tuple

import numpy as np

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO / "src"))

import db  # noqa: E402
from scoring import score_offensive_game  # noqa: E402

DB_PATH = REPO / "data" / "nfl.db"
POSITIONS = ("QB", "RB", "WR", "TE")
HOLDOUT_SEASON = 2025

MIN_GAMES = 8            # matches PR-002 / src/spike_persistence.py's qualifying rule
FIRST_SEASON = 1999      # points need no usage columns
USAGE_FIRST_SEASON = 2009  # targets/air yards only real from 2009 (experiments/bottomup/data.py)
RNG_SEED = 20260730

BOOM = 20.0              # a week that wins you a matchup on its own
BUST = 5.0


def season_weeks(season: int) -> int:
    return 17 if season >= 2021 else 16


# ------------------------------------------------------- bonus-free comparator
def _score_no_bonus(stats: Dict) -> float:
    """Same league, yardage-threshold bonuses removed. The difference against the
    real score is what this league pays for ceiling."""
    g = lambda k: stats.get(k, 0) or 0
    return (g("passing_yards") / 25.0 + g("passing_tds") * 4 - g("interceptions") * 2
            + g("rushing_yards") / 10.0 + g("rushing_tds") * 6
            + g("receptions") * 0.5 + g("receiving_yards") / 10.0 + g("receiving_tds") * 6
            + g("return_tds") * 6 + g("two_point_conversions") * 2
            - g("fumbles_lost") * 2 + g("offensive_fumble_return_tds") * 6)


@dataclass
class PlayerSeason:
    season: int
    player_id: str
    name: str
    position: str
    games: int
    # dispersion, "played" window
    mean_p: float
    sd_p: float
    cv_p: float
    skew_p: float
    # dispersion, "all weeks" window
    mean_a: float
    sd_a: float
    cv_a: float
    total: float
    boom_rate: float
    bust_rate: float
    bonus_points: float
    bonus_share: float
    # usage, that season (for typing)
    targets: float
    carries: float
    air_yards: float
    rec_share_of_touches: Optional[float]
    adot: Optional[float]
    team_target_share: Optional[float]
    rush_points_share: Optional[float]
    # PROXY, labelled as one: offensive snap share is NOT route participation.
    # `CLAUDE.md` §5 says route data is not in nflverse and anything using it is a
    # proxy that must be flagged. A TE who is on the field to block and a TE who
    # runs a route are the same row here. Available 2013+ only.
    snap_share: Optional[float] = None
    excess_sd_p: float = float("nan")
    excess_sd_a: float = float("nan")


SNAP_FIRST_SEASON = 2013


def _snap_share_by_gsis(conn: sqlite3.Connection, season: int) -> Dict[str, float]:
    """Mean offensive snap share, joined pfr_player_id -> mfl_id -> gsis_id.

    PROXY for route participation, not route participation. Flagged everywhere it
    is used, per `CLAUDE.md` §5."""
    if season < SNAP_FIRST_SEASON:
        return {}
    pfr_to_mfl = {p: m for m, p in conn.execute(
        "SELECT mfl_id, source_id FROM player_ids WHERE source='pfr'")}
    mfl_to_gsis = {str(m): g for m, g in conn.execute(
        "SELECT mfl_id, source_id FROM player_ids WHERE source='gsis'")}
    acc: Dict[str, List[float]] = defaultdict(list)
    for pfr, pct in conn.execute(
            "SELECT pfr_player_id, offense_pct FROM snap_counts "
            "WHERE season=? AND game_type='REG' AND offense_pct IS NOT NULL", (season,)):
        mfl = pfr_to_mfl.get(pfr)
        if mfl is None:
            continue
        g = mfl_to_gsis.get(str(mfl))
        if g:
            acc[g].append(float(pct))
    return {g: statistics.fmean(v) for g, v in acc.items() if len(v) >= MIN_GAMES}


def load_player_seasons(conn: sqlite3.Connection, seasons: Sequence[int]) -> List[PlayerSeason]:
    out: List[PlayerSeason] = []
    for season in seasons:
        if season >= HOLDOUT_SEASON:
            raise RuntimeError(f"{season} is at or past the sealed holdout")
        W = season_weeks(season)
        weekly: Dict[str, Dict[int, float]] = defaultdict(dict)
        weekly_nb: Dict[str, Dict[int, float]] = defaultdict(dict)
        meta: Dict[str, Tuple[str, Dict[str, int]]] = {}
        for row in conn.execute(
                f"SELECT * FROM {db.SCORING_VIEW} WHERE season=? AND season_type='REG'",
                (season,)):
            pid = row["player_id"]
            wk = row["week"]
            if wk < 1 or wk > W:
                continue
            stats = {c: row[c] for c in db.SCORING_STAT_COLUMNS}
            weekly[pid][wk] = weekly[pid].get(wk, 0.0) + score_offensive_game(stats)
            weekly_nb[pid][wk] = weekly_nb[pid].get(wk, 0.0) + _score_no_bonus(stats)
            nm, pc = meta.setdefault(pid, (row["player_name"], defaultdict(int)))
            pc[row["position"]] += 1

        usage: Dict[str, Dict[str, float]] = defaultdict(lambda: defaultdict(float))
        team_targets: Dict[str, float] = defaultdict(float)
        player_team: Dict[str, str] = {}
        for pid, team, tg, cr, ay, ry, rushy, rushtd in conn.execute(
                "SELECT player_id, team, SUM(COALESCE(targets,0)), SUM(COALESCE(carries,0)), "
                "SUM(COALESCE(receiving_air_yards,0)), SUM(COALESCE(receiving_yards,0)), "
                "SUM(COALESCE(rushing_yards,0)), SUM(COALESCE(rushing_tds,0)) "
                "FROM player_weekly_stats WHERE season=? AND season_type='REG' "
                "GROUP BY player_id, team", (season,)):
            u = usage[pid]
            u["targets"] += tg or 0
            u["carries"] += cr or 0
            u["air_yards"] += ay or 0
            u["rec_yards"] += ry or 0
            u["rush_yards"] += rushy or 0
            u["rush_tds"] += rushtd or 0
            if team:
                team_targets[team] += tg or 0
                player_team.setdefault(pid, team)

        snaps = _snap_share_by_gsis(conn, season)
        for pid, wk_pts in weekly.items():
            name, pc = meta[pid]
            pos = max(pc.items(), key=lambda kv: kv[1])[0]
            if pos not in POSITIONS:
                continue
            played = np.array([wk_pts[w] for w in sorted(wk_pts)])
            if len(played) < MIN_GAMES:
                continue
            allw = np.zeros(W)
            for w, v in wk_pts.items():
                allw[w - 1] = v
            total = float(played.sum())
            nb_total = float(sum(weekly_nb[pid].values()))
            mean_p = float(played.mean())
            sd_p = float(played.std(ddof=1))
            mean_a = float(allw.mean())
            sd_a = float(allw.std(ddof=1))
            m3 = float(((played - mean_p) ** 3).mean())
            skew = m3 / (sd_p ** 3) if sd_p > 0 else float("nan")
            u = usage[pid]
            touches = u["targets"] + u["carries"]
            tt = team_targets.get(player_team.get(pid, ""), 0.0)
            out.append(PlayerSeason(
                season=season, player_id=pid, name=name, position=pos, games=len(played),
                mean_p=mean_p, sd_p=sd_p, cv_p=sd_p / mean_p if mean_p > 0 else float("nan"),
                skew_p=skew,
                mean_a=mean_a, sd_a=sd_a, cv_a=sd_a / mean_a if mean_a > 0 else float("nan"),
                total=total,
                boom_rate=float((played >= BOOM).mean()),
                bust_rate=float((played <= BUST).mean()),
                bonus_points=total - nb_total,
                bonus_share=(total - nb_total) / total if total > 0 else float("nan"),
                targets=u["targets"], carries=u["carries"], air_yards=u["air_yards"],
                rec_share_of_touches=(u["targets"] / touches) if touches >= 20 else None,
                adot=(u["air_yards"] / u["targets"]) if u["targets"] >= 20 else None,
                team_target_share=(u["targets"] / tt) if tt > 0 and u["targets"] >= 10 else None,
                rush_points_share=((u["rush_yards"] / 10.0 + u["rush_tds"] * 6) / total)
                if (pos == "QB" and total > 0) else None,
                snap_share=snaps.get(pid),
            ))
    return out


# --------------------------------------------------------------- excess volatility
def add_excess_sd(rows: List[PlayerSeason]) -> None:
    """log(SD) regressed on log(mean), fitted WITHIN (position, season).

    Within season as well as within position because the scoring environment
    moves: pooling seasons would let a league-wide scoring shift masquerade as a
    player being volatile."""
    for window in ("p", "a"):
        groups: Dict[Tuple[str, int], List[PlayerSeason]] = defaultdict(list)
        for r in rows:
            groups[(r.position, r.season)].append(r)
        for (_pos, _season), grp in groups.items():
            xs, ys, keep = [], [], []
            for r in grp:
                m = getattr(r, f"mean_{window}")
                s = getattr(r, f"sd_{window}")
                if m > 0.5 and s > 0:
                    xs.append(math.log(m))
                    ys.append(math.log(s))
                    keep.append(r)
            if len(keep) < 10:
                continue
            mx, my = statistics.fmean(xs), statistics.fmean(ys)
            den = sum((x - mx) ** 2 for x in xs)
            b = sum((x - mx) * (y - my) for x, y in zip(xs, ys)) / den if den else 0.0
            a = my - b * mx
            for r, x, y in zip(keep, xs, ys):
                setattr(r, f"excess_sd_{window}", y - (a + b * x))


# ------------------------------------------------------------------ player types
def type_of(r: PlayerSeason, terciles: Dict[Tuple[str, str, int], Tuple[float, float]]
            ) -> Optional[str]:
    """Within-position type. Deliberately position-SPECIFIC: the founder's note
    that 'different factors apply for different positions' applies here directly,
    so RB is typed by how it earns touches, WR/TE by target depth and share, and
    QB by how much of its scoring is rushing."""
    def band(metric: str, value: Optional[float]) -> Optional[str]:
        if value is None:
            return None
        key = (r.position, metric, r.season)
        if key not in terciles:
            return None
        lo, hi = terciles[key]
        return "low" if value <= lo else ("high" if value > hi else "mid")

    if r.position == "RB":
        b = band("rec_share", r.rec_share_of_touches)
        return f"RB receiving-share {b}" if b else None
    if r.position in ("WR", "TE"):
        b = band("adot", r.adot)
        return f"{r.position} aDOT {b}" if b else None
    if r.position == "QB":
        b = band("rush_share", r.rush_points_share)
        return f"QB rushing-share {b}" if b else None
    return None


def type_of_share(r: PlayerSeason, terciles) -> Optional[str]:
    if r.position not in ("WR", "TE", "RB"):
        return None
    key = (r.position, "tshare", r.season)
    if r.team_target_share is None or key not in terciles:
        return None
    lo, hi = terciles[key]
    b = "low" if r.team_target_share <= lo else ("high" if r.team_target_share > hi else "mid")
    return f"{r.position} target-share {b}"


def type_of_snap(r: PlayerSeason, terciles) -> Optional[str]:
    """PROXY dimension. Offensive snap share stands in for route participation,
    which this project does not have (`CLAUDE.md` §5). Reported separately from
    the real dimensions so it can never be mistaken for one."""
    if r.position not in ("WR", "TE", "RB") or r.snap_share is None:
        return None
    key = (r.position, "snap", r.season)
    if key not in terciles:
        return None
    lo, hi = terciles[key]
    b = "low" if r.snap_share <= lo else ("high" if r.snap_share > hi else "mid")
    return f"{r.position} snap-share {b} [PROXY]"


def build_terciles(rows: Sequence[PlayerSeason]) -> Dict[Tuple[str, str, int], Tuple[float, float]]:
    acc: Dict[Tuple[str, str, int], List[float]] = defaultdict(list)
    for r in rows:
        if r.rec_share_of_touches is not None:
            acc[(r.position, "rec_share", r.season)].append(r.rec_share_of_touches)
        if r.adot is not None:
            acc[(r.position, "adot", r.season)].append(r.adot)
        if r.team_target_share is not None:
            acc[(r.position, "tshare", r.season)].append(r.team_target_share)
        if r.rush_points_share is not None:
            acc[(r.position, "rush_share", r.season)].append(r.rush_points_share)
        if r.snap_share is not None:
            acc[(r.position, "snap", r.season)].append(r.snap_share)
    out = {}
    for k, v in acc.items():
        if len(v) >= 9:
            v = sorted(v)
            out[k] = (v[len(v) // 3], v[2 * len(v) // 3])
    return out


# ------------------------------------------------------------------- statistics
def season_bootstrap(values_by_season: Dict[int, List[float]], n_boot: int = 4000,
                     seed: int = RNG_SEED) -> Tuple[float, float, float, int, int]:
    seasons = sorted(values_by_season)
    flat = [v for s in seasons for v in values_by_season[s] if not math.isnan(v)]
    if not flat:
        return float("nan"), float("nan"), float("nan"), 0, 0
    point = statistics.fmean(flat)
    if len(seasons) < 2:
        return point, float("nan"), float("nan"), len(flat), len(seasons)
    rng = random.Random(seed)
    means = []
    for _ in range(n_boot):
        chosen = [rng.choice(seasons) for _ in seasons]
        pooled = [v for s in chosen for v in values_by_season[s] if not math.isnan(v)]
        if pooled:
            means.append(statistics.fmean(pooled))
    means.sort()
    return (point, means[int(0.025 * len(means))],
            means[min(len(means) - 1, int(0.975 * len(means)))], len(flat), len(seasons))


def grade(point: float, lo: float, hi: float) -> str:
    if any(math.isnan(x) for x in (point, lo, hi)):
        return "NO-CI"
    if lo <= 0.0 <= hi:
        return "NULL"
    half = (hi - lo) / 2.0
    if half <= 0:
        return "NO-CI"
    return "SURVIVES" if abs(point) / (half / 1.96) >= 3.0 else "MARGINAL"


def pearson(xs: Sequence[float], ys: Sequence[float]) -> float:
    if len(xs) < 3:
        return float("nan")
    mx, my = statistics.fmean(xs), statistics.fmean(ys)
    num = sum((x - mx) * (y - my) for x, y in zip(xs, ys))
    den = math.sqrt(sum((x - mx) ** 2 for x in xs) * sum((y - my) ** 2 for y in ys))
    return num / den if den else float("nan")


def player_bootstrap_corr(pairs: Sequence[Tuple[str, float, float]], n_boot: int = 4000,
                          seed: int = RNG_SEED) -> Tuple[float, float, float, int]:
    """Correlation with the bootstrap resampling PLAYERS, not player-seasons --
    the same player appears many times and resampling rows would shrink the
    interval by roughly the square root of that autocorrelation."""
    by_player: Dict[str, List[Tuple[float, float]]] = defaultdict(list)
    for pid, a, b in pairs:
        if not (math.isnan(a) or math.isnan(b)):
            by_player[pid].append((a, b))
    players = sorted(by_player)
    flat = [v for p in players for v in by_player[p]]
    if len(flat) < 20:
        return float("nan"), float("nan"), float("nan"), len(flat)
    point = pearson([a for a, _ in flat], [b for _, b in flat])
    rng = random.Random(seed)
    vals = []
    for _ in range(n_boot):
        chosen = [rng.choice(players) for _ in players]
        pooled = [v for p in chosen for v in by_player[p]]
        if len(pooled) >= 20:
            vals.append(pearson([a for a, _ in pooled], [b for _, b in pooled]))
    vals = [v for v in vals if not math.isnan(v)]
    vals.sort()
    if len(vals) < 100:
        return point, float("nan"), float("nan"), len(flat)
    return (point, vals[int(0.025 * len(vals))],
            vals[min(len(vals) - 1, int(0.975 * len(vals)))], len(flat))


# ------------------------------------------------------- does variance win titles?
def variance_title_value(n_teams: int = 10, weeks: int = 15, n_sims: int = 60000,
                         seed: int = RNG_SEED) -> Dict[str, float]:
    """A closed question the founder's 'pair them for roster builds' depends on:
    holding season-long expected points EXACTLY equal, does a higher-variance
    roster win more titles under this league's 4-team / weeks-16-17 /
    no-reseeding structure?

    Nine teams at (mu, sigma); one at (mu, k*sigma). Same mu. Round-robin weeks
    1-15, top 4 by record (points break ties), 1v4 and 2v3 in week 16, final in
    week 17. Pure structure -- no player data, so nothing here can leak."""
    from experiments.strategy.sim import round_robin
    rng = np.random.default_rng(seed)
    sched = round_robin(n_teams, weeks)
    out = {}
    mu, sigma = 110.0, 25.0
    for k in (0.6, 0.8, 1.0, 1.25, 1.5, 2.0):
        sds = np.full(n_teams, sigma)
        sds[0] = sigma * k
        titles = 0
        playoffs = 0
        for _ in range(n_sims):
            scores = rng.normal(mu, sds[:, None], size=(n_teams, weeks + 3))
            wins = np.zeros(n_teams)
            for w, pairs in enumerate(sched):
                for a, b in pairs:
                    if scores[a, w] > scores[b, w]:
                        wins[a] += 1
                    else:
                        wins[b] += 1
            pts = scores[:, :weeks].sum(axis=1)
            seeding = sorted(range(n_teams), key=lambda t: (-wins[t], -pts[t]))
            made = 0 in seeding[:4]
            playoffs += int(made)
            s1, s2, s3, s4 = seeding[:4]
            a = s1 if scores[s1, weeks] >= scores[s4, weeks] else s4
            b = s2 if scores[s2, weeks] >= scores[s3, weeks] else s3
            champ = a if scores[a, weeks + 1] >= scores[b, weeks + 1] else b
            titles += int(champ == 0)
        out[f"sd_x{k}"] = dict(
            p_playoff=playoffs / n_sims, p_title=titles / n_sims,
            # The founder's question in its exact form: does variance hurt you
            # getting in and help you once in? Both halves are reported, because
            # the answer to the combined question can hide an offsetting pair.
            p_title_given_playoff=(titles / playoffs) if playoffs else float("nan"))
    return out


# ------------------------------------------------- volatility PER ROSTER SLOT
def per_slot_volatility(rows: Sequence[PlayerSeason], seasons: Sequence[int],
                        conn: sqlite3.Connection) -> Dict:
    """Per-PLAYER volatility is not what a lineup experiences.

    This league starts 1 QB / 2 RB / 3 WR / 1 TE / 2 FLEX. A position filling
    several slots has its weekly spikes and busts partially cancel inside the
    lineup; a position filling one slot passes its full variance through. So a TE
    and a WR with the same CV do NOT contribute the same risk.

    Effective slots per position use ADR-029's MEASURED flex split (RB 0.52 / WR
    0.48 / TE 0.00 over 26 seasons under this league's rules), not an assumption:
        QB 1.00   RB 2 + 2(0.52) = 3.04   WR 3 + 2(0.48) = 3.96   TE 1 + 0 = 1.00

    Under independence the lineup contribution of a position is k*mu with SD
    sqrt(k)*sigma, so CV_slot = CV_player / sqrt(k). Independence is NOT assumed:
    the mean pairwise weekly correlation between same-position players is
    measured below and reported, and the whole calculation is void if it is far
    from zero."""
    flex_split = {"QB": 0.0, "RB": 0.52, "WR": 0.48, "TE": 0.0}
    starters = {"QB": 1, "RB": 2, "WR": 3, "TE": 1}
    slots = {p: starters[p] + 2 * flex_split[p] for p in POSITIONS}

    # measured same-position weekly correlation, on the top ~36 scorers per
    # position-season (the pool a lineup is actually drawn from)
    corr: Dict[str, List[float]] = defaultdict(list)
    for season in seasons[-10:]:                       # last ten seasons, enough
        W = season_weeks(season)
        mat: Dict[str, List[np.ndarray]] = defaultdict(list)
        wk: Dict[str, Dict[int, float]] = defaultdict(dict)
        pos_of: Dict[str, str] = {}
        for row in conn.execute(
                f"SELECT * FROM {db.SCORING_VIEW} WHERE season=? AND season_type='REG'",
                (season,)):
            if 1 <= row["week"] <= W:
                wk[row["player_id"]][row["week"]] = wk[row["player_id"]].get(row["week"], 0.0) \
                    + score_offensive_game({c: row[c] for c in db.SCORING_STAT_COLUMNS})
                pos_of[row["player_id"]] = row["position"]
        tot = {p: sum(v.values()) for p, v in wk.items()}
        for pos in POSITIONS:
            best = sorted([p for p in wk if pos_of.get(p) == pos and len(wk[p]) >= 12],
                          key=lambda p: -tot[p])[:36]
            for p in best:
                v = np.zeros(W)
                for w, s in wk[p].items():
                    v[w - 1] = s
                mat[pos].append(v)
        for pos, vs in mat.items():
            if len(vs) < 8:
                continue
            M = np.array(vs)
            C = np.corrcoef(M)
            iu = np.triu_indices_from(C, k=1)
            corr[pos].append(float(np.nanmean(C[iu])))

    out = {}
    for pos in POSITIONS:
        sub = [r for r in rows if r.position == pos]
        cv = statistics.fmean(r.cv_p for r in sub if not math.isnan(r.cv_p))
        k = slots[pos]
        out[pos] = dict(cv_player=cv, effective_slots=k,
                        cv_per_slot_group=cv / math.sqrt(k),
                        mean_same_position_weekly_corr=statistics.fmean(corr[pos])
                        if corr[pos] else float("nan"))
    return out


# -------------------------------------------------------------------------- main
def main() -> None:
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute(db._CREATE_SCORING_VIEW_SQL)
    seasons = list(range(FIRST_SEASON, HOLDOUT_SEASON))
    rows = load_player_seasons(conn, seasons)
    add_excess_sd(rows)
    print(f"player-seasons with >= {MIN_GAMES} games, {FIRST_SEASON}-{HOLDOUT_SEASON - 1}: "
          f"{len(rows)}")
    result: Dict = {"n_player_seasons": len(rows), "min_games": MIN_GAMES,
                    "seasons": [seasons[0], seasons[-1]]}
    n_tests = 0

    # ---- 1. position-level table
    print("\n=== 1. Position-level volatility (played weeks / all weeks) ===")
    print(f"{'pos':4s} {'n':>5s} {'PPG':>7s} {'SD':>7s} {'CV':>6s} {'CV all':>7s} "
          f"{'skew':>6s} {'boom%':>6s} {'bust%':>6s} {'bonus%':>7s}")
    pos_tbl = {}
    for pos in POSITIONS:
        sub = [r for r in rows if r.position == pos]
        cv = season_bootstrap({s: [r.cv_p for r in sub if r.season == s] for s in seasons})
        cva = season_bootstrap({s: [r.cv_a for r in sub if r.season == s] for s in seasons})
        n_tests += 2
        pos_tbl[pos] = dict(
            n=len(sub),
            ppg=statistics.fmean(r.mean_p for r in sub),
            sd=statistics.fmean(r.sd_p for r in sub),
            cv_played=dict(mean=cv[0], lo=cv[1], hi=cv[2]),
            cv_all=dict(mean=cva[0], lo=cva[1], hi=cva[2]),
            skew=statistics.fmean(r.skew_p for r in sub if not math.isnan(r.skew_p)),
            boom=statistics.fmean(r.boom_rate for r in sub),
            bust=statistics.fmean(r.bust_rate for r in sub),
            bonus_share=statistics.fmean(r.bonus_share for r in sub if not math.isnan(r.bonus_share)),
        )
        t = pos_tbl[pos]
        print(f"{pos:4s} {t['n']:5d} {t['ppg']:7.2f} {t['sd']:7.2f} {cv[0]:6.3f} {cva[0]:7.3f} "
              f"{t['skew']:6.2f} {t['boom'] * 100:6.1f} {t['bust'] * 100:6.1f} "
              f"{t['bonus_share'] * 100:7.2f}")
    result["position_table"] = pos_tbl

    print("\n  pairwise CV(played) differences, season-clustered bootstrap:")
    pair = {}
    for i, a in enumerate(POSITIONS):
        for b in POSITIONS[i + 1:]:
            da = {s: [r.cv_p for r in rows if r.position == a and r.season == s] for s in seasons}
            dbb = {s: [r.cv_p for r in rows if r.position == b and r.season == s] for s in seasons}
            pa = season_bootstrap(da)
            pb = season_bootstrap(dbb)
            # paired difference: resample seasons jointly
            rng = random.Random(RNG_SEED)
            diffs = []
            for _ in range(4000):
                chosen = [rng.choice(seasons) for _ in seasons]
                x = [v for s in chosen for v in da[s] if not math.isnan(v)]
                y = [v for s in chosen for v in dbb[s] if not math.isnan(v)]
                if x and y:
                    diffs.append(statistics.fmean(x) - statistics.fmean(y))
            diffs.sort()
            pt = pa[0] - pb[0]
            lo, hi = diffs[int(0.025 * len(diffs))], diffs[int(0.975 * len(diffs)) - 1]
            n_tests += 1
            pair[f"{a}-{b}"] = dict(diff=pt, lo=lo, hi=hi, grade=grade(pt, lo, hi))
            print(f"    CV {a} - {b}: {pt:+.4f} [{lo:+.4f},{hi:+.4f}] {grade(pt, lo, hi)}")
    result["position_cv_pairwise"] = pair

    print("\n=== 1b. Volatility PER ROSTER SLOT (1 QB / 2 RB / 3 WR / 1 TE / 2 FLEX) ===")
    slot = per_slot_volatility(rows, seasons, conn)
    print(f"{'pos':4s} {'CV/player':>10s} {'eff. slots':>11s} {'CV/slot group':>14s} "
          f"{'same-pos weekly r':>18s}")
    for pos in POSITIONS:
        e = slot[pos]
        print(f"{pos:4s} {e['cv_player']:10.3f} {e['effective_slots']:11.2f} "
              f"{e['cv_per_slot_group']:14.3f} {e['mean_same_position_weekly_corr']:18.3f}")
    result["per_slot"] = slot

    # ---- 2. type-level table (usage era only)
    usage_rows = [r for r in rows if r.season >= USAGE_FIRST_SEASON]
    terc = build_terciles(usage_rows)
    print(f"\n=== 2. Within-position types, {USAGE_FIRST_SEASON}-{HOLDOUT_SEASON - 1} "
          f"(usage features are only real from {USAGE_FIRST_SEASON}) ===")
    print(f"{'type':28s} {'n':>5s} {'PPG':>7s} {'CV':>7s} {'excessSD':>9s} {'CI':>20s} "
          f"{'boom%':>6s} {'bonus%':>7s} {'grade':>9s}")
    type_tbl = {}
    for fn in (type_of, type_of_share, type_of_snap):
        buckets: Dict[str, List[PlayerSeason]] = defaultdict(list)
        for r in usage_rows:
            t = fn(r, terc)
            if t:
                buckets[t].append(r)
        for t in sorted(buckets):
            sub = buckets[t]
            if len(sub) < 30:
                continue
            ex = season_bootstrap({s: [r.excess_sd_p for r in sub if r.season == s]
                                   for s in range(USAGE_FIRST_SEASON, HOLDOUT_SEASON)})
            n_tests += 1
            type_tbl[t] = dict(n=len(sub),
                               ppg=statistics.fmean(r.mean_p for r in sub),
                               cv=statistics.fmean(r.cv_p for r in sub),
                               excess_sd=dict(mean=ex[0], lo=ex[1], hi=ex[2]),
                               boom=statistics.fmean(r.boom_rate for r in sub),
                               bonus_share=statistics.fmean(
                                   r.bonus_share for r in sub if not math.isnan(r.bonus_share)),
                               grade=grade(ex[0], ex[1], ex[2]))
            type_tbl[t]["pct_sd_vs_level"] = 100 * (math.exp(ex[0]) - 1)
            e = type_tbl[t]
            print(f"{t:28s} {e['n']:5d} {e['ppg']:7.2f} {e['cv']:7.3f} {ex[0]:+9.4f} "
                  f"[{ex[1]:+7.4f},{ex[2]:+7.4f}] {e['boom'] * 100:6.1f} "
                  f"{e['bonus_share'] * 100:7.2f} {e['grade']:>9s} "
                  f"{100 * (math.exp(ex[0]) - 1):+5.1f}%")
    result["type_table"] = type_tbl

    # ---- 3. persistence: can an archetype use any of this?
    print("\n=== 3. Persistence -- year-over-year, resampling PLAYERS ===")
    by_player_season = {(r.player_id, r.season): r for r in rows}
    pers = {}
    for pos in POSITIONS:
        for label, attr in (("excess_sd(played)", "excess_sd_p"), ("CV(played)", "cv_p"),
                            ("boom_rate", "boom_rate"), ("mean PPG (reference)", "mean_p")):
            pairs = []
            for r in rows:
                if r.position != pos:
                    continue
                nxt = by_player_season.get((r.player_id, r.season + 1))
                if nxt is not None and nxt.position == pos:
                    pairs.append((r.player_id, getattr(r, attr), getattr(nxt, attr)))
            c, lo, hi, n = player_bootstrap_corr(pairs)
            n_tests += 1
            pers[f"{pos}:{label}"] = dict(r=c, lo=lo, hi=hi, n=n, grade=grade(c, lo, hi))
            print(f"  {pos:3s} {label:22s} r={c:+.3f} [{lo:+.3f},{hi:+.3f}] n={n:5d} "
                  f"{grade(c, lo, hi)}")
    result["persistence"] = pers

    # ---- 3b. THE test an archetype actually depends on: does a player's type in
    # season N-1 predict his excess volatility in season N? Section 3 shows the
    # player-level label barely persists; if the TYPE label does, an archetype can
    # still work -- it just has to be a statement about the role, not the man.
    print("\n=== 3b. Prior-season type -> NEXT season's excess SD (the archetype-usable form) ===")
    fwd = {}
    for fn, fname in ((type_of, "role"), (type_of_share, "target-share"),
                      (type_of_snap, "snap-share[PROXY]")):
        buckets: Dict[str, List[Tuple[int, float]]] = defaultdict(list)
        for r in usage_rows:
            t = fn(r, terc)
            nxt = by_player_season.get((r.player_id, r.season + 1))
            if t and nxt is not None and nxt.position == r.position \
                    and not math.isnan(nxt.excess_sd_p):
                buckets[t].append((nxt.season, nxt.excess_sd_p))
        for t in sorted(buckets):
            vals = buckets[t]
            if len(vals) < 30:
                continue
            grp: Dict[int, List[float]] = defaultdict(list)
            for s, v in vals:
                grp[s].append(v)
            pt, lo, hi, n, ns = season_bootstrap(grp)
            n_tests += 1
            fwd[t] = dict(mean_next_excess_sd=pt, lo=lo, hi=hi, n=n,
                          pct_sd=100 * (math.exp(pt) - 1), grade=grade(pt, lo, hi))
            print(f"  {t:28s} n={n:5d}  next-season excess SD {pt:+.4f} "
                  f"[{lo:+.4f},{hi:+.4f}]  = {100 * (math.exp(pt) - 1):+5.1f}% SD  "
                  f"{grade(pt, lo, hi)}")
    result["type_predicts_next_season"] = fwd

    # ---- 4. does the LEAGUE pay for volatility?
    print("\n=== 4. Does this league's bonus actually pay for volatility? ===")
    paid = {}
    for pos in POSITIONS:
        sub = [r for r in rows if r.position == pos and not math.isnan(r.excess_sd_p)]
        if len(sub) < 60:
            continue
        vals = sorted(r.excess_sd_p for r in sub)
        lo_c, hi_c = vals[len(vals) // 3], vals[2 * len(vals) // 3]
        groups = {"low": [], "mid": [], "high": []}
        for r in sub:
            k = "low" if r.excess_sd_p <= lo_c else ("high" if r.excess_sd_p > hi_c else "mid")
            groups[k].append(r)
        entry = {}
        for k, g in groups.items():
            entry[k] = dict(n=len(g),
                            ppg=statistics.fmean(r.mean_p for r in g),
                            bonus_share=statistics.fmean(
                                r.bonus_share for r in g if not math.isnan(r.bonus_share)),
                            bonus_pts=statistics.fmean(r.bonus_points for r in g))
        d = {s: [r.bonus_points for r in groups["high"] if r.season == s] for s in seasons}
        e = {s: [r.bonus_points for r in groups["low"] if r.season == s] for s in seasons}
        rng = random.Random(RNG_SEED)
        diffs = []
        for _ in range(4000):
            chosen = [rng.choice(seasons) for _ in seasons]
            x = [v for s in chosen for v in d[s]]
            y = [v for s in chosen for v in e[s]]
            if x and y:
                diffs.append(statistics.fmean(x) - statistics.fmean(y))
        diffs.sort()
        pt = entry["high"]["bonus_pts"] - entry["low"]["bonus_pts"]
        lo, hi = diffs[int(0.025 * len(diffs))], diffs[int(0.975 * len(diffs)) - 1]
        n_tests += 1
        entry["high_minus_low_bonus_points"] = dict(mean=pt, lo=lo, hi=hi,
                                                    grade=grade(pt, lo, hi))
        paid[pos] = entry
        print(f"  {pos}: bonus pts/season  low-excess-SD {entry['low']['bonus_pts']:6.2f}  "
              f"high {entry['high']['bonus_pts']:6.2f}  diff {pt:+.2f} "
              f"[{lo:+.2f},{hi:+.2f}] {grade(pt, lo, hi)}  "
              f"(PPG low {entry['low']['ppg']:.2f} vs high {entry['high']['ppg']:.2f})")
    result["bonus_by_volatility"] = paid

    # ---- 5. structural: does variance win titles at equal expected points?
    print("\n=== 5. Structural -- equal expected points, does variance win titles? ===")
    vt = variance_title_value()
    for k, v in vt.items():
        print(f"  team SD x{k[4:]:>5s} of league SD:  P(playoff)={v['p_playoff']:.3f}  "
              f"P(title)={v['p_title']:.3f}  P(title|playoff)={v['p_title_given_playoff']:.3f}")
    result["variance_title_value"] = vt

    result["n_interval_tests"] = n_tests
    print(f"\n==== {n_tests} interval tests; at 5% that is ~{0.05 * n_tests:.1f} false "
          f"'clears zero' results expected by chance alone. ====")
    dest = REPO / "data" / "qa" / "fr086-volatility-2026-07-30.json"
    dest.parent.mkdir(parents=True, exist_ok=True)
    dest.write_text(json.dumps(result, indent=2, default=str))
    print(f"wrote {dest}")


if __name__ == "__main__":
    main()
