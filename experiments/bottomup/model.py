"""Two-stage bottom-up model (S1 volume / S2 shrunk efficiency / S3 scoring).

Follows ADR-E's architecture with the prototype simplifications registered in
docs/reviews/fable-ranking-design-2026-07-27.md:

- S1: per-position ridge regression on per-game volume components, features
  standardised with training-fold means/sds (fold-local, ADR-E §3.2).
- Games: 2-parameter per-position regression (prior games, age) — a base
  rate, no injury-proneness term (ADR-E §2).
- S2: player prior rates shrunk to the training-fold positional mean with
  w = n/(n+k); k is ESTIMATED per stat per fold by grid search on
  next-season prediction error *within the training pairs* (never the test
  fold), then capped: w<=0.60 yards-type, w<=0.20 TD/INT-type (ADR-E §1).
  Cap binds are counted and reported.
- S3: per-game points = linear scoring on projected components + bonus
  expectation from a position x yards-per-game-bin table built on training
  seasons (position x volume-tier, never per player — PR-002's null).

No consensus feature anywhere in this pipeline (ADR-E §4.1 Market row).
"""

from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Sequence, Tuple

import numpy as np

from .data import (AIR_YARDS_RELIABLE, POSITIONS, TARGET_RELIABLE, PlayerSeason,
                   SeasonStore)

RIDGE_LAMBDA = 1.0  # on standardised features; registered constant, not tuned
K_GRID = (10.0, 25.0, 50.0, 100.0, 200.0, 400.0, 800.0)
W_CAP_YARDS = 0.60
W_CAP_TD = 0.20

# S2 stats: (numerator attr fn, opportunity attr fn, cap)
#   rate = num / opp ; shrunk toward positional mean rate.


@dataclass
class FeatureRow:
    pid: str
    position: str
    x: np.ndarray                  # S1 feature vector
    prior: PlayerSeason            # N-1 aggregate
    prior2: Optional[PlayerSeason]  # N-2 aggregate (may be None)


def _pg(total: float, games: int) -> float:
    return total / games if games else 0.0


def build_features(store: SeasonStore, feature_season: int, pids: Sequence[str],
                   positions: Dict[str, str], usage_arm: bool,
                   target_season: int, situation=None) -> List[FeatureRow]:
    """Feature vectors from seasons feature_season (=target-1) and -1 more.
    `situation`: an optional situation.Situation for target_season (V3);
    when present its 6 features are appended to every vector."""
    prior = store.player_seasons(feature_season, for_target=target_season)
    prior2 = (store.player_seasons(feature_season - 1, for_target=target_season)
              if feature_season - 1 >= 1999 else {})
    team_tot = store.team_totals(feature_season)
    rows: List[FeatureRow] = []
    for pid in pids:
        ps = prior.get(pid)
        if ps is None:
            continue
        p2 = prior2.get(pid)
        g = ps.games or 1
        team = team_tot.get(ps.team, {})
        t_targets = team.get("targets", 0.0) or 1.0
        t_carries = team.get("carries", 0.0) or 1.0
        t_attempts = team.get("attempts", 0.0) or 1.0
        # F1 fix: the receptions share must use TEAM RECEPTIONS, not team
        # targets — team targets are ~0 in 2003-2008, and dividing by them
        # poisons the long arm across the availability boundary (the exact
        # ADR-E §4.3 hazard; discovered as the fold-2004 R^2 blowup).
        t_receptions = team.get("receptions", 0.0) or 1.0
        age = store.age_at(pid, target_season)
        age = age if age is not None else 27.0  # positional prior, ~median
        feats = [
            _pg(ps.attempts, g), _pg(ps.carries, g), _pg(ps.receptions, g),
            _pg(ps.rush_yards, g), _pg(ps.rec_yards, g), _pg(ps.pass_yards, g),
            ps.games,
            ps.carries / t_carries, ps.receptions / t_receptions,
            ps.attempts / t_attempts,
            age, age * age,
        ]
        # usage trend (N-1 minus N-2, per-game) — 0 when N-2 absent
        if p2 is not None and p2.games:
            feats += [
                _pg(ps.carries, g) - _pg(p2.carries, p2.games),
                _pg(ps.receptions, g) - _pg(p2.receptions, p2.games),
                _pg(ps.attempts, g) - _pg(p2.attempts, p2.games),
            ]
        else:
            feats += [0.0, 0.0, 0.0]
        if usage_arm:
            if not TARGET_RELIABLE(feature_season):
                raise AssertionError(
                    f"usage arm run on target-unreliable season {feature_season}"
                )
            feats += [
                _pg(ps.targets, g),
                ps.targets / t_targets,
                _pg(ps.air_yards, g) if AIR_YARDS_RELIABLE(feature_season) else 0.0,
                (ps.air_yards / ps.targets) if ps.targets else 0.0,  # aDOT proxy
            ]
        if situation is not None:
            feats += situation.features_for(pid).as_list()
        rows.append(FeatureRow(pid, positions.get(pid, ps.position),
                               np.array(feats, dtype=float), ps, p2))
    return rows


# ------------------------------------------------------------------ S1 ridge
@dataclass
class Ridge:
    mean: np.ndarray
    sd: np.ndarray
    beta: np.ndarray
    intercept: float

    def predict(self, X: np.ndarray) -> np.ndarray:
        Z = (X - self.mean) / self.sd
        return Z @ self.beta + self.intercept


def fit_ridge(X: np.ndarray, y: np.ndarray, lam: float = RIDGE_LAMBDA) -> Ridge:
    mean = X.mean(axis=0)
    sd = X.std(axis=0)
    sd[sd == 0] = 1.0
    Z = (X - mean) / sd
    yc = y - y.mean()
    A = Z.T @ Z + lam * np.eye(Z.shape[1])
    beta = np.linalg.solve(A, Z.T @ yc)
    return Ridge(mean, sd, beta, float(y.mean()))


# ------------------------------------------------------- S2 shrinkage machinery
@dataclass
class Shrinker:
    """rate_hat = w * player_prior_rate + (1-w) * pos_mean, w = n/(n+k)."""

    pos_mean: Dict[str, float]
    k: float
    cap: float
    cap_binds: int = 0

    def predict(self, position: str, num: float, opp: float) -> float:
        mean = self.pos_mean.get(position, 0.0)
        if opp <= 0:
            return mean
        w = opp / (opp + self.k)
        if w > self.cap:
            w = self.cap
            self.cap_binds += 1
        return w * (num / opp) + (1 - w) * mean


def fit_shrinker(train_pairs: List[Tuple[PlayerSeason, PlayerSeason]],
                 num_attr: str, opp_attr: str, cap: float,
                 positions: Sequence[str]) -> Shrinker:
    """Estimate k by grid search on opportunity-weighted next-season rate MSE
    over training pairs (prior-season -> next-season), fold-local."""
    # positional mean rate from the PRIOR side of the pairs (training info only)
    num_by_pos: Dict[str, float] = defaultdict(float)
    opp_by_pos: Dict[str, float] = defaultdict(float)
    for prior, _nxt in train_pairs:
        if prior.position in positions:
            num_by_pos[prior.position] += getattr(prior, num_attr)
            opp_by_pos[prior.position] += getattr(prior, opp_attr)
    pos_mean = {p: (num_by_pos[p] / opp_by_pos[p]) if opp_by_pos[p] else 0.0
                for p in positions}

    best_k, best_err = K_GRID[0], float("inf")
    for k in K_GRID:
        err = wsum = 0.0
        for prior, nxt in train_pairs:
            if prior.position not in positions:
                continue
            opp_n = getattr(nxt, opp_attr)
            if opp_n <= 0:
                continue
            opp_p = getattr(prior, opp_attr)
            mean = pos_mean.get(prior.position, 0.0)
            w = opp_p / (opp_p + k) if opp_p > 0 else 0.0
            w = min(w, cap)
            pred = w * (getattr(prior, num_attr) / opp_p if opp_p else 0.0) \
                + (1 - w) * mean
            actual = getattr(nxt, num_attr) / opp_n
            err += opp_n * (pred - actual) ** 2
            wsum += opp_n
        if wsum and err / wsum < best_err:
            best_err, best_k = err / wsum, k
    return Shrinker(pos_mean, best_k, cap)


# ---------------------------------------------------------- S3 bonus tables
_BIN_EDGES = {
    "pass": np.array([0, 100, 150, 200, 225, 250, 275, 300, 1000]),
    "rush": np.array([0, 10, 20, 30, 40, 55, 70, 85, 100, 1000]),
    "rec": np.array([0, 10, 20, 30, 40, 55, 70, 85, 100, 1000]),
}


@dataclass
class BonusTable:
    """position x yards-per-game-bin -> mean bonus points per game (training)."""

    kind: str
    table: Dict[str, np.ndarray]
    global_mean: np.ndarray

    def expect(self, position: str, ypg: float) -> float:
        edges = _BIN_EDGES[self.kind]
        idx = int(np.clip(np.searchsorted(edges, ypg, side="right") - 1,
                          0, len(edges) - 2))
        arr = self.table.get(position)
        if arr is None or np.isnan(arr[idx]):
            arr = self.global_mean
        v = arr[idx]
        return float(v) if not np.isnan(v) else 0.0


def fit_bonus_table(train_seasons: List[Dict[str, PlayerSeason]], kind: str
                    ) -> BonusTable:
    ypg_attr = {"pass": "pass_yards", "rush": "rush_yards", "rec": "rec_yards"}[kind]
    bp_attr = {"pass": "bonus_pts_pass", "rush": "bonus_pts_rush",
               "rec": "bonus_pts_rec"}[kind]
    edges = _BIN_EDGES[kind]
    nbins = len(edges) - 1
    sums: Dict[str, np.ndarray] = defaultdict(lambda: np.zeros(nbins))
    counts: Dict[str, np.ndarray] = defaultdict(lambda: np.zeros(nbins))
    gsum, gcount = np.zeros(nbins), np.zeros(nbins)
    for season in train_seasons:
        for ps in season.values():
            if ps.games < 4 or ps.position not in POSITIONS:
                continue
            ypg = getattr(ps, ypg_attr) / ps.games
            bpg = getattr(ps, bp_attr) / ps.games
            idx = int(np.clip(np.searchsorted(edges, ypg, side="right") - 1,
                              0, nbins - 1))
            sums[ps.position][idx] += bpg
            counts[ps.position][idx] += 1
            gsum[idx] += bpg
            gcount[idx] += 1
    table = {}
    for pos in POSITIONS:
        with np.errstate(invalid="ignore"):
            table[pos] = np.where(counts[pos] >= 5, sums[pos] / counts[pos], np.nan)
    with np.errstate(invalid="ignore"):
        gmean = np.where(gcount > 0, gsum / gcount, np.nan)
    return BonusTable(kind, table, gmean)


# --------------------------------------------------------------- full model
@dataclass
class FittedModel:
    usage_arm: bool
    s1: Dict[Tuple[str, str], Ridge]        # (position, component) -> model
    games: Dict[str, Ridge]                 # position -> games model
    shrinkers: Dict[str, Shrinker]
    bonus: Dict[str, BonusTable]
    cap_bind_counts: Dict[str, int] = field(default_factory=dict)
    qb_direct: Optional[Ridge] = None       # V4: QB season-points ridge


def _qb_extra(r: FeatureRow) -> List[float]:
    """V4's three QB-only features: prior points, prior ppg, prior-2 ppg."""
    ppg = r.prior.ppg or 0.0
    p2 = (r.prior2.ppg or 0.0) if r.prior2 is not None else 0.0
    return [r.prior.points, ppg, p2]


def _qb_direct_X(rows: List[FeatureRow]) -> np.ndarray:
    return np.hstack([np.vstack([r.x for r in rows]),
                      np.array([_qb_extra(r) for r in rows], dtype=float)])


S1_COMPONENTS = {
    "QB": ("attempts", "carries"),
    "RB": ("carries", "rec_vol"),
    "WR": ("rec_vol", "carries"),
    "TE": ("rec_vol", "carries"),
}
# "rec_vol" = targets/g (usage arm) or receptions/g (long arm)


def _rec_vol(ps: PlayerSeason, usage_arm: bool) -> float:
    tot = ps.targets if usage_arm else ps.receptions
    return _pg(tot, ps.games)


def _component_value(ps: PlayerSeason, comp: str, usage_arm: bool) -> float:
    if comp == "rec_vol":
        return _rec_vol(ps, usage_arm)
    return _pg(getattr(ps, comp), ps.games)


def fit(store: SeasonStore, train_pair_seasons: List[int], usage_arm: bool,
        target_season: int, qb_td_cap: float = W_CAP_TD,
        vacated: bool = False, qb_direct: bool = False) -> FittedModel:
    """train_pair_seasons: seasons s such that (features s-1 -> outcome s) is a
    training pair. All must be < target_season (asserted via data layer).
    vacated: V3 situation features. qb_direct: V4 QB season-points ridge."""
    # Assemble training pairs
    pairs: List[Tuple[FeatureRow, PlayerSeason]] = []
    ps_pairs: List[Tuple[PlayerSeason, PlayerSeason]] = []
    train_season_aggs: List[Dict[str, PlayerSeason]] = []
    from .data import frozen_universe  # local import to avoid cycle
    from .situation import Situation  # local import to avoid cycle
    for s in train_pair_seasons:
        assert s < target_season, "training pair season >= target"
        universe = frozen_universe(store, s)
        outcome = store.player_seasons(s, for_target=target_season)
        positions = {pid: pos for pos, pids in universe.items() for pid in pids}
        sit = Situation(store, s, usage_arm) if vacated else None
        rows = build_features(store, s - 1, list(positions), positions,
                              usage_arm, target_season=s, situation=sit)
        for r in rows:
            out = outcome.get(r.pid)
            if out is None:
                out = PlayerSeason(r.pid, s, r.position, "")  # zero season
            pairs.append((r, out))
            ps_pairs.append((r.prior, out))
        train_season_aggs.append(store.player_seasons(s, for_target=target_season))

    m = FittedModel(usage_arm, {}, {}, {}, {})

    # ---- S1 per position/component + games model
    for pos in POSITIONS:
        rows = [(r, out) for r, out in pairs if r.position == pos]
        if len(rows) < 30:
            continue
        X = np.vstack([r.x for r, _ in rows])
        for comp in S1_COMPONENTS[pos]:
            y = np.array([
                _component_value(out, comp, usage_arm) for _, out in rows
            ])
            m.s1[(pos, comp)] = fit_ridge(X, y)
        yg = np.array([float(out.games) for _, out in rows])
        Xg = np.vstack([[r.prior.games, r.x[10]] for r, _ in rows])  # games, age
        m.games[pos] = fit_ridge(Xg, yg, lam=1e-6)

    # ---- S2 shrinkers (fold-local k estimation)
    recv_pos = ("RB", "WR", "TE")
    if usage_arm:
        m.shrinkers["ypt"] = fit_shrinker(ps_pairs, "rec_yards", "targets",
                                          W_CAP_YARDS, recv_pos)
        m.shrinkers["catch"] = fit_shrinker(ps_pairs, "receptions", "targets",
                                            W_CAP_YARDS, recv_pos)
        m.shrinkers["rec_td"] = fit_shrinker(ps_pairs, "rec_tds", "targets",
                                             W_CAP_TD, recv_pos)
    else:
        m.shrinkers["ypr"] = fit_shrinker(ps_pairs, "rec_yards", "receptions",
                                          W_CAP_YARDS, recv_pos)
        m.shrinkers["rec_td"] = fit_shrinker(ps_pairs, "rec_tds", "receptions",
                                             W_CAP_TD, recv_pos)
    m.shrinkers["ypc"] = fit_shrinker(ps_pairs, "rush_yards", "carries",
                                      W_CAP_YARDS, ("QB",) + recv_pos)
    m.shrinkers["rush_td"] = fit_shrinker(ps_pairs, "rush_tds", "carries",
                                          W_CAP_TD, ("QB",) + recv_pos)
    m.shrinkers["ypa"] = fit_shrinker(ps_pairs, "pass_yards", "attempts",
                                      W_CAP_YARDS, ("QB",))
    m.shrinkers["pass_td"] = fit_shrinker(ps_pairs, "pass_tds", "attempts",
                                          qb_td_cap, ("QB",))
    m.shrinkers["int"] = fit_shrinker(ps_pairs, "interceptions", "attempts",
                                      W_CAP_TD, ("QB",))

    # ---- S3 bonus tables
    for kind in ("pass", "rush", "rec"):
        m.bonus[kind] = fit_bonus_table(train_season_aggs, kind)

    # ---- V4: QB direct season-points ridge (replaces S1/S2/S3 at QB only)
    if qb_direct:
        qb_rows = [(r, out) for r, out in pairs if r.position == "QB"]
        if len(qb_rows) >= 30:
            Xq = _qb_direct_X([r for r, _ in qb_rows])
            yq = np.array([out.points for _, out in qb_rows])
            m.qb_direct = fit_ridge(Xq, yq)
    return m


def predict(m: FittedModel, rows: List[FeatureRow]
            ) -> Dict[str, Tuple[float, float, float]]:
    """{pid: (season_points, ppg, games)} for target-season universe rows."""
    out: Dict[str, Tuple[float, float, float]] = {}
    by_pos: Dict[str, List[FeatureRow]] = defaultdict(list)
    for r in rows:
        by_pos[r.position].append(r)
    for pos, prows in by_pos.items():
        if pos not in POSITIONS or (pos, S1_COMPONENTS[pos][0]) not in m.s1:
            continue
        X = np.vstack([r.x for r in prows])
        comp_pred = {
            comp: np.clip(m.s1[(pos, comp)].predict(X), 0, None)
            for comp in S1_COMPONENTS[pos]
        }
        Xg = np.vstack([[r.prior.games, r.x[10]] for r in prows])
        games = np.clip(m.games[pos].predict(Xg), 1.0, 17.0)
        if pos == "QB" and m.qb_direct is not None:
            pts = np.clip(m.qb_direct.predict(_qb_direct_X(prows)), 0, None)
            for i, r in enumerate(prows):
                g = float(games[i])
                out[r.pid] = (float(pts[i]), float(pts[i]) / g, g)
            continue
        for i, r in enumerate(prows):
            p = r.prior
            ppg = 0.0
            if pos == "QB":
                att = comp_pred["attempts"][i]
                car = comp_pred["carries"][i]
                ypa = m.shrinkers["ypa"].predict(pos, p.pass_yards, p.attempts)
                ptd = m.shrinkers["pass_td"].predict(pos, p.pass_tds, p.attempts)
                irate = m.shrinkers["int"].predict(pos, p.interceptions, p.attempts)
                ypc = m.shrinkers["ypc"].predict(pos, p.rush_yards, p.carries)
                rtd = m.shrinkers["rush_td"].predict(pos, p.rush_tds, p.carries)
                pass_ypg = att * ypa
                rush_ypg = car * ypc
                ppg = (pass_ypg / 25.0 + att * ptd * 4.0 + att * irate * -2.0
                       + rush_ypg / 10.0 + car * rtd * 6.0
                       + m.bonus["pass"].expect(pos, pass_ypg)
                       + m.bonus["rush"].expect(pos, rush_ypg))
            else:
                car = comp_pred["carries"][i]
                rv = comp_pred["rec_vol"][i]
                ypc = m.shrinkers["ypc"].predict(pos, p.rush_yards, p.carries)
                rtd = m.shrinkers["rush_td"].predict(pos, p.rush_tds, p.carries)
                rush_ypg = car * ypc
                if m.usage_arm:
                    catch = m.shrinkers["catch"].predict(pos, p.receptions, p.targets)
                    ypt = m.shrinkers["ypt"].predict(pos, p.rec_yards, p.targets)
                    rectd = m.shrinkers["rec_td"].predict(pos, p.rec_tds, p.targets)
                    rec_pg = rv * catch
                    rec_ypg = rv * ypt
                    rec_td_pg = rv * rectd
                else:
                    ypr = m.shrinkers["ypr"].predict(pos, p.rec_yards, p.receptions)
                    rectd = m.shrinkers["rec_td"].predict(pos, p.rec_tds, p.receptions)
                    rec_pg = rv
                    rec_ypg = rv * ypr
                    rec_td_pg = rv * rectd
                ppg = (rush_ypg / 10.0 + car * rtd * 6.0
                       + rec_pg * 0.5 + rec_ypg / 10.0 + rec_td_pg * 6.0
                       + m.bonus["rush"].expect(pos, rush_ypg)
                       + m.bonus["rec"].expect(pos, rec_ypg))
            g = float(games[i])
            out[r.pid] = (ppg * g, ppg, g)
    return out
