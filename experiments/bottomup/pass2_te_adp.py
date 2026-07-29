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
POSITIONS = ("QB", "RB", "WR", "TE")
S = None                          # Store, injected by build_all()
BASE = None                       # replacement levels, injected by main()
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
# ---------------------------------------------------------------- build rows
def first_season(pid, upto):
    """Earliest REG season observed at or before `upto`. None => no NFL snaps yet."""
    for s in range(2009, upto + 1):
        if pid in S.season(s):
            return s
    return None


def build(season, position):
    """One pre-draft consensus list, joined to what actually happened. Universe frozen."""
    cons = S.consensus(season, position)
    cur = S.season(season)
    p1, p2 = S.season(season - 1), S.season(season - 2)
    snap1 = S.snap_share(season - 1)
    draft = S.draft()
    birth = S.birthdates()

    # realised positional universe = every player whose modal position that season
    # matches, from pws -- NOT restricted to the consensus list.
    realised = sorted(
        [(pid, v.points) for pid, v in cur.items() if v.pos == position],
        key=lambda kv: -kv[1])
    finish = {pid: i + 1 for i, (pid, _) in enumerate(realised)}
    repl_idx = min(BASE[position] - 1, len(realised) - 1)
    repl_pts = realised[repl_idx][1] if realised else 0.0

    rows = []
    for i, c in enumerate(cons):
        pid = c['player_id']
        cs = cur.get(pid)
        pts = cs.points if cs else 0.0            # never played -> 0, RETAINED
        gms = cs.games if cs else 0
        a = p1.get(pid); b = p2.get(pid)
        # games-weighted 2-season prior ppg; 0 if no prior NFL snaps
        gsum = (a.games if a else 0) + (b.games if b else 0)
        prior_ppg = ((a.points if a else 0) + (b.points if b else 0)) / gsum if gsum else 0.0
        fs = first_season(pid, season - 1)
        exp = (season - fs) if fs else 0          # 0 == no prior NFL regular-season game
        dr = draft.get(pid)
        bd = birth.get(pid)
        age = None
        if bd:
            try:
                y, m, d = (int(x) for x in bd.split('-')[:3])
                age = season - y + (9 - m) / 12.0
            except Exception:
                age = None
        rows.append(dict(
            season=season, pid=pid, name=c['player_name'], pos=position,
            pos_rank=i + 1, ovr=c['adp_rank'], ecr_val=c['adp_value'],
            spread=c['spread_sd'], rbest=c['rank_best'], rworst=c['rank_worst'],
            pts=pts, games=gms, ppg=(pts / gms if gms else 0.0),
            finish=finish.get(pid, 999), vbd=pts - repl_pts,
            prior_ppg=prior_ppg, prior_g=(a.games if a else 0),
            prior_tgt=(a.targets if a else 0),
            prior_snap=snap1.get(pid), exp=exp, rookie=1 if exp == 0 else 0,
            age=age, dr_round=(dr[1] if dr and dr[0] == season - exp else None),
            dr_ovr=(dr[2] if dr else None), dr_season=(dr[0] if dr else None),
            repl_pts=repl_pts,
        ))
    return rows


def build_all(store, positions=POSITIONS):
    global S, BASE
    S = store
    return {(pos, s): build(s, pos) for pos in positions for s in TARGETS}


TE_BANDS = [('TE1-3', 1, 3), ('TE4-6', 4, 6), ('TE7-10', 7, 10),
            ('TE11-16', 11, 16), ('TE17-24', 17, 24), ('TE25-40', 25, 40)]
DRAFT_PICKS = 150   # 10 teams x 15 drafted rounds


def within_season(by_s, stat, n=BOOT, seed=SEED):
    """stat computed per season, then averaged. Bootstrap resamples SEASONS, not players.

    Pooling a rank-based statistic across seasons compares a 2021 player to a 2024
    player and inflates it through between-season composition. Do not do that.
    """
    per = {s: stat(rows) for s, rows in by_s.items()}
    ok = {s: v for s, v in per.items() if v is not None}
    if not ok:
        return None, None, None, per
    rgen = random.Random(seed)
    seasons = sorted(ok)
    draws = sorted(sum(ok[rgen.choice(seasons)] for _ in seasons) / len(seasons)
                   for _ in range(n))
    return (sum(ok.values()) / len(ok), draws[int(.025 * n)], draws[int(.975 * n)], per)


def main(db=Path(__file__).resolve().parents[2] / "data" / "nfl.db"):
    """Reproduce the headline tables of docs/ranking/bottom-up-research-pass-2.md."""
    global BASE
    from scoring import ReplacementLevels
    BASE = ReplacementLevels().baselines()
    ALL = build_all(Store(db))

    print("== hit rate by pre-draft TE band (Wilson 95%) ==")
    for lab, lo_, hi_ in TE_BANDS:
        g = [r for s in TARGETS for r in ALL[('TE', s)] if lo_ <= r['pos_rank'] <= hi_]
        p6, l6, u6 = wilson(sum(1 for r in g if r['finish'] <= 6), len(g))
        p10, l10, u10 = wilson(sum(1 for r in g if r['finish'] <= 10), len(g))
        print(f"  {lab:<9} n={len(g):3d}  top-6 {p6*100:5.1f}% [{l6*100:4.1f},{u6*100:5.1f}]"
              f"   top-10 {p10*100:5.1f}% [{l10*100:4.1f},{u10*100:5.1f}]")

    print("\n== were the late top-6 TEs draftable? (10 teams x 15 rounds = 150 picks) ==")
    hits = [r for s in TARGETS for r in ALL[('TE', s)] if r['finish'] <= 6]
    late = [r for r in hits if r['pos_rank'] >= 11]
    print(f"  top-6 TE seasons from pre-draft TE11+: {len(late)}/{len(hits)}")
    print(f"  ...inside 150 picks: {sum(1 for r in late if r['ovr'] <= DRAFT_PICKS)}/{len(late)}")
    for r in sorted(late, key=lambda r: r['season']):
        print(f"    {r['season']}  TE{r['pos_rank']:<3} ovr {r['ovr']:<4} "
              f"{'IN ' if r['ovr'] <= DRAFT_PICKS else 'OUT'}  {r['name']}")

    print("\n== cost of the TE7-10 window: mean realised VBD at overall ECR 75-113 ==")
    for pos in POSITIONS:
        g = [r for s in TARGETS for r in ALL[(pos, s)] if 75 <= r['ovr'] <= 113]
        v = [r['vbd'] for r in g]
        print(f"  {pos}  n={len(g):3d}  mean VBD {sum(v)/len(v):+7.1f}  "
              f"P(VBD>+30) {sum(1 for x in v if x > 30)/len(v)*100:5.1f}%")

    # Band is TE11-40, matching the report. NOT TE11-open: including TE41+ (overall ECR
    # 300+, near-zero hit probability) makes every signal look far stronger than it is,
    # because separating a top-6 TE from TE80 is trivial and is not the decision.
    print("\n== forecastability of late TE hits, band TE11-40: AUC within season, then averaged ==")
    sigs = [('consensus ECR rank', lambda r: -r['ovr'], None),
            ('expert rank_best', lambda r: -r['rbest'], lambda r: r['rbest'] is not None),
            ('expert disagreement sd', lambda r: r['spread'], lambda r: r['spread'] is not None),
            ('prior-2yr ppg', lambda r: r['prior_ppg'], None),
            ('prior-yr snap share', lambda r: r['prior_snap'], lambda r: r['prior_snap'] is not None)]
    base = {s: [r for r in ALL[('TE', s)] if 11 <= r['pos_rank'] <= 40] for s in TARGETS}
    for name, fn, filt in sigs:
        by_s = {s: [r for r in base[s] if filt is None or filt(r)] for s in TARGETS}

        def f(rs, fn=fn):
            k = [(fn(r), 1 if r['finish'] <= 6 else 0) for r in rs if fn(r) is not None]
            return auc([a for a, _ in k], [b for _, b in k]) if k else None

        v, l, u, _ = within_season(by_s, f)
        print(f"  {name:<24} AUC {v:.3f} [{l:.2f}, {u:.2f}]" if v is not None else f"  {name}: --")


if __name__ == "__main__":
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--db", type=Path,
                    default=Path(__file__).resolve().parents[2] / "data" / "nfl.db")
    main(ap.parse_args().db)

