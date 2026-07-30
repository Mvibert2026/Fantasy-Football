"""Component models for RB, QB and TE (and a WR re-implementation for the
availability A/B, which has to be run at every position on identical code).

SHAPE OF THE THING: project the raw quantities scoring consumes, then score them.
Nothing here produces a "rank"; a rank is what you get when you sort the output
under a ruleset, and a different ruleset sorts it differently.

EACH POSITION IS ITS OWN COMPONENT SET, NOT A RE-PARAMETERISATION. What is shared
is the fitting machinery -- least squares, empirical-Bayes shrinkage, a binomial
GLM per bonus threshold. What is not shared is the ledger:

  WR/TE   games x targets/game -> receptions -> yards -> TDs        [1 stream ]
  RB      the above PLUS carries/game -> rush yards -> rush TDs     [2 streams]
  QB      games x attempts/game -> pass yards/TDs/INTs, PLUS rushing [2 streams,
          different scoring rate, different bonus thresholds]

BONUS FAMILIES, all stacking, all per-GAME and therefore unrecoverable from a
season total:
  rec  100/150/200   (WR, TE, RB)
  rush 100/150/200   (RB, QB -- a receiver essentially never earns one)
  pass 300/350/400   (QB only, and far more often than any receiving threshold)

Everything is linear least squares or a one-covariate binomial GLM. No
regularisation beyond explicit empirical-Bayes shrinkage with a single constant
per rate, chosen on training seasons only.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List, Optional, Sequence, Tuple

import numpy as np
import pandas as pd

from .pos_features import AVAIL_ARMS

# This league (CLAUDE.md §7), expressed once so a different ruleset is a
# different call rather than a rebuild.
LEAGUE_SCORING: Dict = dict(
    per_reception=0.5,
    rec_yards_per_point=10.0, rec_td=6.0,
    rush_yards_per_point=10.0, rush_td=6.0,
    pass_yards_per_point=25.0, pass_td=4.0, interception=-2.0,
    fumble_lost=-2.0,
    bonuses={
        "rec": ((100, 1.0), (150, 1.5), (200, 2.0)),
        "rush": ((100, 1.0), (150, 1.5), (200, 2.0)),
        "pass": ((300, 1.0), (350, 1.5), (400, 2.0)),
    },
)

ROOKIE_COLS = ["log_draft_pick", "age"]


# ------------------------------------------------------------------ helpers
def ols(X: np.ndarray, y: np.ndarray, w: Optional[np.ndarray] = None) -> np.ndarray:
    """Least squares with an explicit intercept column already in X."""
    if len(X) == 0:
        return np.zeros(X.shape[1] if X.ndim == 2 else 1)
    if w is not None:
        rw = np.sqrt(np.clip(w, 0, None))[:, None]
        X = X * rw
        y = y * rw[:, 0]
    beta, *_ = np.linalg.lstsq(X, y, rcond=None)
    return beta


def binom_glm(x: np.ndarray, succ: np.ndarray, trials: np.ndarray,
              max_iter: int = 100, tol: float = 1e-8,
              ridge: float = 1e-4) -> np.ndarray:
    """Logistic regression on aggregated counts, by ridged IRLS.

    The ridge is not regularisation for its own sake: the top threshold in each
    family is a rare event (order ten games a season league-wide), which makes
    plain IRLS separate and the normal equations singular. A 1e-4 ridge on the
    non-intercept coefficients keeps it finite without materially moving the
    fitted curve at the lower thresholds, where data is plentiful.
    """
    trials = np.asarray(trials, dtype=float)
    succ = np.asarray(succ, dtype=float)
    keep = np.isfinite(trials) & (trials > 0) & np.isfinite(succ) & \
        np.isfinite(x).all(axis=1)
    x, succ, trials = x[keep], succ[keep], trials[keep]
    n, p = x.shape
    beta = np.zeros(p)
    if n == 0:
        beta[0] = -10.0
        return beta
    beta[0] = np.log(max(succ.sum(), 0.5) / max(trials.sum() - succ.sum(), 0.5))
    pen = np.eye(p) * ridge
    pen[0, 0] = 0.0
    for _ in range(max_iter):
        eta = np.clip(x @ beta, -25, 25)
        mu = 1.0 / (1.0 + np.exp(-eta))
        wgt = np.clip(trials * mu * (1 - mu), 1e-8, None)
        z = eta + (succ - trials * mu) / wgt
        XtW = x.T * wgt
        try:
            new = np.linalg.solve(XtW @ x + pen, XtW @ z)
        except np.linalg.LinAlgError:
            break
        if not np.isfinite(new).all():
            break
        step = new - beta
        for _ in range(20):          # step halving keeps a rare-event fit finite
            if np.max(np.abs(step)) <= 5.0:
                break
            step *= 0.5
        beta = beta + step
        if np.max(np.abs(step)) < tol:
            break
    return beta


def _design(df: pd.DataFrame, cols: Sequence[str]) -> np.ndarray:
    X = np.column_stack([np.ones(len(df))] + [
        pd.to_numeric(df[c], errors="coerce").fillna(0.0).to_numpy(dtype=float)
        if c in df.columns else np.zeros(len(df))
        for c in cols])
    return np.nan_to_num(X, nan=0.0, posinf=0.0, neginf=0.0)


@dataclass
class ShrunkRate:
    """Empirical-Bayes rate: (num + k*prior) / (den + k).

    `k` is in units of the DENOMINATOR (targets for catch rate, carries for yards
    per carry, attempts for yards per attempt), so a back with 20 career carries
    is pulled hard toward the population and one with 700 barely moves. `k` is
    picked from a fixed grid by training-season MSE -- one parameter, chosen
    without ever seeing the season being projected.
    """

    name: str
    num_col: str
    den_col: str
    prior: float = 0.0
    k: float = 50.0
    slope: float = 1.0
    intercept: float = 0.0
    k_grid: Tuple[float, ...] = (5, 10, 20, 40, 80, 160, 320)
    recalibrate: bool = True
    # ---- factor-batch-1 arms. Both default OFF, so an unmodified model is
    # bit-for-bit the primary that `component-model-rb-qb-te-pass-1.md` reports.
    #: T1 -- shrink toward a VOLUME-CONDITIONAL mean instead of one pooled
    #: constant: prior_i = a + b*log(1+den_i). The mechanism is that goal-line
    #: role scales with volume, so a 300-carry back and a 40-carry back should
    #: not be pulled toward the same TD/carry.
    volume_prior: bool = False
    vp_beta: Tuple[float, float] = (0.0, 0.0)

    def _prior_vec(self, den: np.ndarray) -> np.ndarray:
        if not self.volume_prior:
            return np.full(len(den), self.prior, dtype=float)
        a, b = self.vp_beta
        return np.clip(a + b * np.log1p(np.clip(den, 0, None)), 0.0, None)

    def raw(self, f: pd.DataFrame, k: Optional[float] = None) -> np.ndarray:
        k = self.k if k is None else k
        num = f[self.num_col].to_numpy(dtype=float)
        den = f[self.den_col].to_numpy(dtype=float)
        return (num + k * self._prior_vec(den)) / (den + k)

    def fit(self, f: pd.DataFrame, y_num: np.ndarray, y_den: np.ndarray,
            pool: Optional[Tuple[pd.DataFrame, np.ndarray, np.ndarray]] = None
            ) -> "ShrunkRate":
        """Fit prior, shrinkage constant and recalibration on training rows.

        `pool` is the TE variant's borrowed WR rows. It informs the population
        PRIOR and the shrinkage constant `k` -- the two quantities a small sample
        estimates worst -- while the linear recalibration below is always fitted
        on the position's OWN rows, so a genuine positional level difference is
        preserved rather than averaged away. That is what "pooled rates with a
        TE intercept" means, mechanically.
        """
        ok = y_den > 0
        if ok.sum() < 10:
            self.prior = float(np.sum(y_num) / max(np.sum(y_den), 1.0))
            return self
        if pool is not None:
            f_p, n_p, d_p = pool
            f_all = pd.concat([f, f_p], ignore_index=True)
            n_all = np.concatenate([y_num, n_p])
            d_all = np.concatenate([y_den, d_p])
        else:
            f_all, n_all, d_all = f, y_num, y_den
        ok_all = d_all > 0
        self.prior = float(np.sum(n_all[ok_all]) / np.sum(d_all[ok_all]))
        if self.volume_prior:
            # WLS of the realised rate on log volume, weighted by volume, on
            # TRAINING rows only. Two parameters, fitted the same way and on the
            # same rows as the pooled constant it replaces.
            dv = d_all[ok_all]
            yv = n_all[ok_all] / dv
            Xv = np.column_stack([np.ones(len(dv)), np.log1p(dv)])
            bv = ols(Xv, yv, w=dv)
            self.vp_beta = (float(bv[0]), float(bv[1]))
        best, best_mse = self.k_grid[0], np.inf
        yt_all = n_all[ok_all] / d_all[ok_all]
        for k in self.k_grid:
            pred = self.raw(f_all, k)[ok_all]
            mse = float(np.average((yt_all - pred) ** 2, weights=d_all[ok_all]))
            if mse < best_mse:
                best, best_mse = k, mse
        self.k = best
        yt = y_num[ok] / y_den[ok]
        if self.recalibrate:
            # one linear recalibration so a systematic level shift (ageing, a
            # rule change) is corrected rather than baked in
            r = self.raw(f, best)[ok]
            if float(np.std(r)) < 1e-12:
                # T2 (k -> infinity) makes every player's raw rate identical, so
                # the recalibration regressor has no variance and least squares
                # is rank deficient. Collapse to the weighted mean rather than
                # letting lstsq return an arbitrary minimum-norm slope: the LEVEL
                # calibration is kept, which is what keeps T2 one change away
                # from the primary instead of two.
                self.intercept = float(np.average(yt, weights=y_den[ok]))
                self.slope = 0.0
            else:
                X = np.column_stack([np.ones(int(ok.sum())), r])
                beta = ols(X, yt, w=y_den[ok])
                self.intercept, self.slope = float(beta[0]), float(beta[1])
        return self

    def predict(self, f: pd.DataFrame) -> np.ndarray:
        return self.intercept + self.slope * self.raw(f)


# --------------------------------------------------------------- base model
@dataclass
class BaseComponentModel:
    """Shared machinery. Subclasses own their component ledger and nothing else.

    `avail_arm` selects one of the three pre-declared availability feature sets
    (`component-model-multipos-precommit.md` §4). The arms differ by exactly one
    block of features and by nothing else in the entire pipeline.
    """

    position: str = "WR"
    avail_arm: str = "A"
    scoring: Dict = field(default_factory=lambda: dict(LEAGUE_SCORING))
    use_bonus_model: bool = True

    vet_games: Optional[np.ndarray] = None
    rk_games: Optional[np.ndarray] = None
    volume: Dict[str, np.ndarray] = field(default_factory=dict)
    rk_volume: Dict[str, np.ndarray] = field(default_factory=dict)
    rates: Dict[str, ShrunkRate] = field(default_factory=dict)
    rookie_rates: Dict[str, float] = field(default_factory=dict)
    bonus_beta: Dict[Tuple[str, int], np.ndarray] = field(default_factory=dict)
    means: Dict[str, float] = field(default_factory=dict)
    train_seasons: Tuple[int, ...] = ()

    # ---- subclass contract -------------------------------------------------
    #: {name: (feature columns, outcome numerator, outcome denominator)}
    VOLUME_SPECS: Dict[str, Tuple[List[str], str, str]] = field(default_factory=dict)
    #: [(rate name, num feature, den feature, outcome num, outcome den)]
    RATE_SPECS: List[Tuple[str, str, str, str, str]] = field(default_factory=list)
    #: which bonus families this position can earn
    BONUS_FAMILIES: Tuple[str, ...] = ()

    # ---- factor-batch-1 arm hooks. Both default empty; an unmodified model is
    # the primary reported in `component-model-rb-qb-te-pass-1.md`.
    #: {volume spec name: replacement feature column list} -- factors #20/#28/#13
    volume_cols: Dict[str, List[str]] = field(default_factory=dict)
    #: {rate name: kwargs handed to ShrunkRate} -- factor #19
    rate_overrides: Dict[str, Dict] = field(default_factory=dict)

    def _apply_arm(self) -> None:
        """Swap in an arm's designs. Called at the END of each subclass's
        __post_init__, so an arm is a change to a declared spec rather than a
        parallel code path that could drift from the primary."""
        for name, cols in self.volume_cols.items():
            if name not in self.VOLUME_SPECS:
                raise KeyError(f"{self.position}: no volume spec {name!r} to override")
            _, ynum, yden = self.VOLUME_SPECS[name]
            self.VOLUME_SPECS[name] = (list(cols), ynum, yden)
        known = {r[0] for r in self.RATE_SPECS}
        for name in self.rate_overrides:
            if name not in known:
                raise KeyError(f"{self.position}: no rate {name!r} to override")

    # family -> (season yards column, per-game count columns by threshold)
    _FAMILY = {
        "rec": ("rec_yards", {100: "g100", 150: "g150", 200: "g200"}),
        "rush": ("rush_yards", {100: "r100", 150: "r150", 200: "r200"}),
        "pass": ("pass_yards", {300: "p300", 350: "p350", 400: "p400"}),
    }

    @property
    def avail_cols(self) -> List[str]:
        return AVAIL_ARMS[self.avail_arm]

    # ------------------------------------------------------------------ fit
    def fit(self, feats: pd.DataFrame, outs: pd.DataFrame,
            rate_pool: Optional[Tuple[pd.DataFrame, pd.DataFrame]] = None
            ) -> "BaseComponentModel":
        d = feats.merge(outs, on=["player_id", "season"], suffixes=("", "_y"))
        d = d.copy()
        d["age"] = d["age"].fillna(d["age"].median())
        d["age2"] = d["age"] ** 2
        self.train_seasons = tuple(sorted(d["season"].unique().tolist()))

        pool_vet = None
        if rate_pool is not None:
            pf, po = rate_pool
            pd_ = pf.merge(po, on=["player_id", "season"], suffixes=("", "_y"))
            pool_vet = pd_[pd_["entry"] == "veteran"]

        vet = d[d["entry"] == "veteran"]
        rk = d[d["entry"] == "rookie"]

        # --- availability: expected share of the season played
        self.vet_games = ols(_design(vet, self.avail_cols),
                             (vet["games"] / vet["season_len_y"]).to_numpy(dtype=float))
        self.rk_games = ols(_design(rk, ROOKIE_COLS),
                            (rk["games"] / rk["season_len_y"]).to_numpy(dtype=float))

        # --- volume: per-game rates, informed only by players who played
        vp = vet[vet["games"] > 0]
        rp = rk[rk["games"] > 0]
        for name, (cols, ynum, yden) in self.VOLUME_SPECS.items():
            y = (vp[ynum] / vp[yden].replace(0, np.nan)).fillna(0.0).to_numpy(dtype=float)
            self.volume[name] = ols(_design(vp, cols), y,
                                    w=vp["games"].to_numpy(dtype=float))
            yr = (rp[ynum] / rp[yden].replace(0, np.nan)).fillna(0.0).to_numpy(dtype=float)
            self.rk_volume[name] = ols(_design(rp, ROOKIE_COLS), yr,
                                       w=rp["games"].to_numpy(dtype=float))

        # --- efficiency rates
        for name, nc, dc, ynum, yden in self.RATE_SPECS:
            sr = ShrunkRate(name, nc, dc, **self.rate_overrides.get(name, {}))
            pool = None
            if pool_vet is not None and ynum in pool_vet.columns:
                pool = (pool_vet, pool_vet[ynum].to_numpy(dtype=float),
                        pool_vet[yden].to_numpy(dtype=float))
            sr.fit(vet, vet[ynum].to_numpy(dtype=float),
                   vet[yden].to_numpy(dtype=float), pool=pool)
            self.rates[name] = sr
            num, den = float(rk[ynum].sum()), float(rk[yden].sum())
            self.rookie_rates[name] = num / den if den > 0 else float(sr.prior)

        self._fit_bonus_all(d, self._realised_ypg(d))
        return self

    # ---- bonus machinery ---------------------------------------------------
    def _realised_ypg(self, d: pd.DataFrame) -> Dict[str, np.ndarray]:
        g = np.where(d["games"] > 0, d["games"], np.nan).astype(float)
        return {fam: np.divide(d[self._FAMILY[fam][0]].to_numpy(dtype=float), g)
                for fam in self.BONUS_FAMILIES}

    @staticmethod
    def _bonus_design(ypg: np.ndarray) -> np.ndarray:
        return np.column_stack([np.ones(len(ypg)), np.log1p(np.clip(ypg, 0, None))])

    def _fit_bonus_all(self, d: pd.DataFrame, ypg_by_fam: Dict[str, np.ndarray]) -> None:
        """P(a game clears threshold t) as a logistic function of MEAN yards per
        game in that family. A threshold bonus is a nonlinear functional of the
        per-game distribution; E[bonus] is not bonus(E[yards])."""
        games = d["games"].to_numpy(dtype=float)
        for fam in self.BONUS_FAMILIES:
            ypg = ypg_by_fam[fam]
            ok = np.isfinite(ypg) & (games > 0)
            sub = d[ok]
            X = self._bonus_design(ypg[ok])
            trials = sub["games"].to_numpy(dtype=float)
            for t, col in self._FAMILY[fam][1].items():
                self.bonus_beta[(fam, t)] = binom_glm(
                    X, sub[col].to_numpy(dtype=float), trials)

    def refit_bonus_on_projections(self, proj: pd.DataFrame,
                                   outs: pd.DataFrame) -> "BaseComponentModel":
        """Refit each exceedance curve against PROJECTED, not realised, ypg.

        Not cosmetic. P(game >= t | ypg) is convex over the range that matters,
        so evaluating it at a SHRUNK point estimate is not the expectation under
        the projection's own uncertainty -- it is systematically too low. Fitting
        on the projections the model will actually feed it absorbs that
        shrinkage, because the training inputs are compressed exactly the way the
        live inputs will be.

        `proj` must be OUT-OF-SAMPLE projections for the training seasons,
        produced by models fitted on seasons strictly earlier still. Passing
        in-sample projections here would make the correction fit its own noise.
        """
        d = proj.merge(outs, on=["player_id", "season"], suffixes=("", "_act"))
        g = np.where(d["proj_games"] > 0, d["proj_games"], np.nan).astype(float)
        colmap = {"rec": "proj_rec_yards", "rush": "proj_rush_yards",
                  "pass": "proj_pass_yards"}
        ypg = {fam: np.divide(d[colmap[fam]].to_numpy(dtype=float), g)
               for fam in self.BONUS_FAMILIES}
        self._fit_bonus_all(d, ypg)
        return self

    def _bonus_points(self, out: pd.DataFrame, games: np.ndarray) -> np.ndarray:
        """Expected stacking-bonus points, and the per-game exceedance
        probabilities that produce them (kept as columns so the same projection
        can be re-scored under a different ruleset without refitting)."""
        colmap = {"rec": "proj_rec_yards", "rush": "proj_rush_yards",
                  "pass": "proj_pass_yards"}
        total = np.zeros(len(out))
        for fam in self.BONUS_FAMILIES:
            yards = out[colmap[fam]].to_numpy(dtype=float)
            ypg = np.nan_to_num(np.divide(yards, np.where(games > 0, games, np.nan)),
                                nan=0.0)
            X = self._bonus_design(ypg)
            per_game = np.zeros(len(out))
            for t, b in self.scoring["bonuses"][fam]:
                key = (fam, t)
                if key not in self.bonus_beta:
                    continue
                p = 1.0 / (1.0 + np.exp(-np.clip(X @ self.bonus_beta[key], -30, 30)))
                out[f"p_{fam}_{t}"] = p
                per_game += b * p
            total += per_game * games
        return total

    # -------------------------------------------------------------- predict
    def _prep(self, feats: pd.DataFrame) -> pd.DataFrame:
        f = feats.copy()
        med = f["age"].median() if f["age"].notna().any() else 25.0
        f["age"] = f["age"].fillna(med)
        f["age2"] = f["age"] ** 2
        return f

    def _availability(self, f: pd.DataFrame, is_rk: np.ndarray) -> np.ndarray:
        gshare = np.where(is_rk,
                          _design(f, ROOKIE_COLS) @ self.rk_games,
                          _design(f, self.avail_cols) @ self.vet_games)
        return np.clip(gshare, 0.0, 1.0) * f["season_len"].to_numpy(dtype=float)

    def _volume(self, name: str, f: pd.DataFrame, is_rk: np.ndarray) -> np.ndarray:
        cols = self.VOLUME_SPECS[name][0]
        v = np.where(is_rk,
                     _design(f, ROOKIE_COLS) @ self.rk_volume[name],
                     _design(f, cols) @ self.volume[name])
        return np.clip(v, 0.0, None)

    def _rate(self, name: str, f: pd.DataFrame, is_rk: np.ndarray,
              lo: float, hi: float) -> np.ndarray:
        v = np.clip(self.rates[name].predict(f), lo, hi)
        v = np.where(is_rk, self.rookie_rates.get(name, self.rates[name].prior), v)
        return np.clip(v, lo, hi)

    def predict(self, feats: pd.DataFrame) -> pd.DataFrame:
        raise NotImplementedError

    def _finalise(self, out: pd.DataFrame, games: np.ndarray) -> pd.DataFrame:
        out["proj_bonus_points"] = (self._bonus_points(out, games)
                                    if self.use_bonus_model else 0.0)
        out["proj_points_base"] = score_components(out, self.scoring, bonuses=False)
        out["proj_points"] = out["proj_points_base"] + out["proj_bonus_points"]
        return out


def score_components(comp: pd.DataFrame, scoring: Dict, bonuses: bool = True) -> np.ndarray:
    """Re-score an existing component projection under a different ruleset.

    THIS IS THE WHOLE POINT of projecting components: the same numbers, a
    different league, no refitting. Bonus probabilities are already per-game, so
    a ruleset with different thresholds needs its own GLM evaluation -- only
    thresholds already modelled can be re-weighted here.
    """
    def g(col):
        return comp[col].to_numpy(dtype=float) if col in comp.columns \
            else np.zeros(len(comp))

    pts = (
        scoring["per_reception"] * g("proj_receptions")
        + g("proj_rec_yards") / scoring["rec_yards_per_point"]
        + scoring["rec_td"] * g("proj_rec_tds")
        + g("proj_rush_yards") / scoring["rush_yards_per_point"]
        + scoring["rush_td"] * g("proj_rush_tds")
        + g("proj_pass_yards") / scoring["pass_yards_per_point"]
        + scoring["pass_td"] * g("proj_pass_tds")
        + scoring["interception"] * g("proj_interceptions")
        + scoring["fumble_lost"] * g("proj_fumbles_lost")
    )
    if bonuses:
        games = g("proj_games")
        for fam, table in scoring["bonuses"].items():
            for t, b in table:
                col = f"p_{fam}_{t}"
                if col in comp.columns:
                    pts = pts + b * comp[col].to_numpy(dtype=float) * games
    return pts


# ------------------------------------------------------------------ RECEIVER
_RECEIVER_VOLUME = ["tpg_w", "tshare_w", "gshare_w", "evidence", "age", "age2",
                    "ppg_w", "experience"]


@dataclass
class ReceiverComponentModel(BaseComponentModel):
    """WR and TE. One usage stream: targets -> receptions -> yards -> TDs.

    Used for both positions unchanged, because the football process is the same;
    what differs is the sample it is fitted on. `pool_with` lets the TE variant
    borrow WR rows for the EFFICIENCY rates only -- see `pos_eval.py`.
    """

    def __post_init__(self):
        self.VOLUME_SPECS = {
            "tpg": (_RECEIVER_VOLUME, "targets", "games"),
            "carries_pg": (["carries_pg_w", "gshare_w", "evidence"], "carries", "games"),
        }
        self.RATE_SPECS = [
            ("catch_rate", "cr_num", "cr_den", "receptions", "targets"),
            ("ypr", "ypr_num", "ypr_den", "rec_yards", "receptions"),
            ("tdpt", "tdpt_num", "tdpt_den", "rec_tds", "targets"),
            ("ypc", "ypc_num", "ypc_den", "rush_yards", "carries"),
            ("tdpc", "tdpc_num", "tdpc_den", "rush_tds", "carries"),
            ("fum_pg", "fumpg_num", "fumpg_den", "fumbles_lost", "games"),
        ]
        self.BONUS_FAMILIES = ("rec",)
        self._apply_arm()

    def predict(self, feats: pd.DataFrame) -> pd.DataFrame:
        f = self._prep(feats)
        is_rk = (f["entry"] == "rookie").to_numpy()
        games = self._availability(f, is_rk)

        tpg = self._volume("tpg", f, is_rk)
        cpg = self._volume("carries_pg", f, is_rk)
        cr = self._rate("catch_rate", f, is_rk, 0.05, 0.95)
        ypr = self._rate("ypr", f, is_rk, 3.0, 25.0)
        tdpt = self._rate("tdpt", f, is_rk, 0.0, 0.30)
        ypc = self._rate("ypc", f, is_rk, 0.0, 15.0)
        tdpc = self._rate("tdpc", f, is_rk, 0.0, 0.20)
        fum = self._rate("fum_pg", f, is_rk, 0.0, 0.5)

        targets = games * tpg
        carries = games * cpg
        out = pd.DataFrame({
            "player_id": f["player_id"].to_numpy(), "season": f["season"].to_numpy(),
            "entry": f["entry"].to_numpy(), "position": self.position,
            "proj_games": games, "proj_tpg": tpg,
            "proj_targets": targets,
            "proj_receptions": targets * cr,
            "proj_rec_yards": targets * cr * ypr,
            "proj_rec_tds": targets * tdpt,
            "proj_carries": carries,
            "proj_rush_yards": carries * ypc,
            "proj_rush_tds": carries * tdpc,
            "proj_fumbles_lost": games * fum,
            "proj_catch_rate": cr, "proj_ypr": ypr, "proj_td_per_target": tdpt,
        })
        return self._finalise(out, games)


# ----------------------------------------------------------------- RUNNING BACK
_RB_CARRY_VOLUME = ["carries_pg_w", "cshare_w", "gshare_w", "evidence", "age",
                    "age2", "ppg_w", "experience"]
_RB_TARGET_VOLUME = ["tgt_pg_w", "tshare_w", "gshare_w", "evidence", "age",
                     "age2", "experience"]
_RB_OPP_VOLUME = ["opp_pg_w", "cshare_w", "tshare_w", "gshare_w", "evidence",
                  "age", "age2", "ppg_w", "experience"]
_RB_SHARE_VOLUME = ["recshare_opp_w", "tshare_w", "cshare_w", "age", "experience"]


@dataclass
class RBComponentModel(BaseComponentModel):
    """Two usage streams that a coach allocates from one budget.

    `opportunity_share=False` (PRIMARY, pre-declared): project carries per game
    and targets per game independently from their own lagged rates.

    `opportunity_share=True` (SECONDARY, reported never selected on): project
    total opportunity (carries + targets) per game, then the receiving SHARE of
    it. The claim being tested is that a back's total touch budget is more
    persistent than either component, and that role change shows up as a share
    shift -- which is the actual RB modelling question rather than a wrapper
    around two receiver models.
    """

    opportunity_share: bool = False

    def __post_init__(self):
        if self.opportunity_share:
            self.VOLUME_SPECS = {
                "opp_pg": (_RB_OPP_VOLUME, "opportunity", "games"),
                "recshare": (_RB_SHARE_VOLUME, "targets", "opportunity"),
            }
        else:
            self.VOLUME_SPECS = {
                "carries_pg": (_RB_CARRY_VOLUME, "carries", "games"),
                "tpg": (_RB_TARGET_VOLUME, "targets", "games"),
            }
        self.RATE_SPECS = [
            ("ypc", "ypc_num", "ypc_den", "rush_yards", "carries"),
            ("tdpc", "tdpc_num", "tdpc_den", "rush_tds", "carries"),
            ("catch_rate", "cr_num", "cr_den", "receptions", "targets"),
            ("ypr", "ypr_num", "ypr_den", "rec_yards", "receptions"),
            ("tdpt", "tdpt_num", "tdpt_den", "rec_tds", "targets"),
            ("fum_pg", "fumpg_num", "fumpg_den", "fumbles_lost", "games"),
        ]
        self.BONUS_FAMILIES = ("rush", "rec")
        self._apply_arm()

    def fit(self, feats: pd.DataFrame, outs: pd.DataFrame,
            rate_pool: Optional[Tuple[pd.DataFrame, pd.DataFrame]] = None
            ) -> "RBComponentModel":
        outs = outs.copy()
        outs["opportunity"] = outs["carries"] + outs["targets"]
        return super().fit(feats, outs, rate_pool=rate_pool)

    def predict(self, feats: pd.DataFrame) -> pd.DataFrame:
        f = self._prep(feats)
        is_rk = (f["entry"] == "rookie").to_numpy()
        games = self._availability(f, is_rk)

        if self.opportunity_share:
            opp = self._volume("opp_pg", f, is_rk)
            share = np.clip(self._volume("recshare", f, is_rk), 0.0, 1.0)
            tpg, cpg = opp * share, opp * (1.0 - share)
        else:
            cpg = self._volume("carries_pg", f, is_rk)
            tpg = self._volume("tpg", f, is_rk)

        ypc = self._rate("ypc", f, is_rk, 1.5, 8.0)
        tdpc = self._rate("tdpc", f, is_rk, 0.0, 0.15)
        cr = self._rate("catch_rate", f, is_rk, 0.20, 0.98)
        ypr = self._rate("ypr", f, is_rk, 2.0, 18.0)
        tdpt = self._rate("tdpt", f, is_rk, 0.0, 0.20)
        fum = self._rate("fum_pg", f, is_rk, 0.0, 0.5)

        carries, targets = games * cpg, games * tpg
        out = pd.DataFrame({
            "player_id": f["player_id"].to_numpy(), "season": f["season"].to_numpy(),
            "entry": f["entry"].to_numpy(), "position": self.position,
            "proj_games": games, "proj_cpg": cpg, "proj_tpg": tpg,
            "proj_carries": carries,
            "proj_rush_yards": carries * ypc,
            "proj_rush_tds": carries * tdpc,
            "proj_targets": targets,
            "proj_receptions": targets * cr,
            "proj_rec_yards": targets * cr * ypr,
            "proj_rec_tds": targets * tdpt,
            "proj_fumbles_lost": games * fum,
            "proj_ypc": ypc, "proj_catch_rate": cr, "proj_ypr": ypr,
        })
        return self._finalise(out, games)


# ------------------------------------------------------------------ QUARTERBACK
_QB_ATT_VOLUME = ["att_pg_w", "gshare_w", "evidence", "age", "age2", "ppg_w",
                  "experience"]
_QB_RUSH_VOLUME = ["carries_pg_w", "rushyds_pg_w", "gshare_w", "evidence",
                   "age", "age2", "experience"]


@dataclass
class QBComponentModel(BaseComponentModel):
    """A different scoring regime, not a receiver with different coefficients.

    Passing yards score at 25/point against 10/point for rushing and receiving,
    so a 4,500-yard passer earns 180 points from yardage where a 1,500-yard
    rusher earns 150 -- and the QB's rushing yards are worth 2.5x his own passing
    yards per yard. That asymmetry makes the rushing stream, not the passing one,
    the place where quarterbacks separate. Both are projected.

    The passing bonus family (300/350/400) sits in a far better-sampled regime
    than any receiving threshold: a starting QB clears 300 several times a year,
    where a 200-yard receiving game happens ~39 times in 1,360 player-seasons.
    """

    def __post_init__(self):
        self.VOLUME_SPECS = {
            "att_pg": (_QB_ATT_VOLUME, "attempts", "games"),
            "carries_pg": (_QB_RUSH_VOLUME, "carries", "games"),
        }
        self.RATE_SPECS = [
            ("ypa", "ypa_num", "ypa_den", "pass_yards", "attempts"),
            ("tdpa", "tdpa_num", "tdpa_den", "pass_tds", "attempts"),
            ("intpa", "intpa_num", "intpa_den", "interceptions", "attempts"),
            ("ypc", "ypc_num", "ypc_den", "rush_yards", "carries"),
            ("tdpc", "tdpc_num", "tdpc_den", "rush_tds", "carries"),
            ("fum_pg", "fumpg_num", "fumpg_den", "fumbles_lost", "games"),
        ]
        self.BONUS_FAMILIES = ("pass", "rush")
        self._apply_arm()

    def predict(self, feats: pd.DataFrame) -> pd.DataFrame:
        f = self._prep(feats)
        is_rk = (f["entry"] == "rookie").to_numpy()
        games = self._availability(f, is_rk)

        apg = self._volume("att_pg", f, is_rk)
        cpg = self._volume("carries_pg", f, is_rk)
        ypa = self._rate("ypa", f, is_rk, 3.0, 10.0)
        tdpa = self._rate("tdpa", f, is_rk, 0.0, 0.12)
        intpa = self._rate("intpa", f, is_rk, 0.0, 0.10)
        ypc = self._rate("ypc", f, is_rk, 0.0, 10.0)
        tdpc = self._rate("tdpc", f, is_rk, 0.0, 0.20)
        fum = self._rate("fum_pg", f, is_rk, 0.0, 1.0)

        attempts, carries = games * apg, games * cpg
        out = pd.DataFrame({
            "player_id": f["player_id"].to_numpy(), "season": f["season"].to_numpy(),
            "entry": f["entry"].to_numpy(), "position": self.position,
            "proj_games": games, "proj_apg": apg,
            "proj_attempts": attempts,
            "proj_pass_yards": attempts * ypa,
            "proj_pass_tds": attempts * tdpa,
            "proj_interceptions": attempts * intpa,
            "proj_carries": carries,
            "proj_rush_yards": carries * ypc,
            "proj_rush_tds": carries * tdpc,
            "proj_fumbles_lost": games * fum,
            "proj_ypa": ypa, "proj_td_per_att": tdpa,
        })
        return self._finalise(out, games)


MODELS = {
    "WR": ReceiverComponentModel,
    "TE": ReceiverComponentModel,
    "RB": RBComponentModel,
    "QB": QBComponentModel,
}
