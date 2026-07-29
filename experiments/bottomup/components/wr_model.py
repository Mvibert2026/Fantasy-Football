"""The WR component model.

Shape of the thing: project the raw quantities scoring consumes, then score
them. Nothing here produces a "rank"; a rank is what you get when you sort the
output under a ruleset, and a different ruleset sorts it differently.

  games        E[games played]                       -> availability
  tpg          E[targets | game played]              -> volume
  catch_rate   E[receptions / target]                -> efficiency
  ypr          E[receiving yards / reception]        -> efficiency
  tdpt         E[receiving TD / target]              -> scoring rate
  rush_*       small WR rushing terms
  fum_pg       E[fumbles lost / game]
  P(>=100/150/200 receiving yards in a game)         -> the stacking bonuses

The last line is the one no season-total projection can produce. A threshold
bonus is a nonlinear functional of the per-game distribution; E[bonus] is not
bonus(E[yards]). It is modelled here as a binomial GLM on log mean yards per
game, fitted on training seasons only.

Everything is linear least squares or a one-covariate binomial GLM. No
regularisation beyond explicit empirical-Bayes shrinkage with a single constant
per rate, and that constant is chosen on training seasons only.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List, Optional, Sequence, Tuple

import numpy as np
import pandas as pd

# League scoring constants that this model's point assembly consumes.
# Kept explicit here so a different ruleset is a different call, not a rebuild.
HALF_PPR = dict(
    per_reception=0.5, yards_per_point=10.0, rec_td=6.0, rush_td=6.0,
    fumble_lost=-2.0,
    rec_yard_bonuses=((100, 1.0), (150, 1.5), (200, 2.0)),
)


# ------------------------------------------------------------------ helpers
def ols(X: np.ndarray, y: np.ndarray, w: Optional[np.ndarray] = None) -> np.ndarray:
    """Least squares with an explicit intercept column already in X."""
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

    The ridge is not regularisation for its own sake: the 200-yard threshold is
    a rare event (order 10 games a season league-wide), which makes the plain
    IRLS separate and the normal equations singular. A 1e-4 ridge on the
    non-intercept coefficients keeps it finite without materially moving the
    fitted curve at the 100- and 150-yard thresholds, where data is plentiful.
    """
    trials = np.asarray(trials, dtype=float)
    succ = np.asarray(succ, dtype=float)
    keep = np.isfinite(trials) & (trials > 0) & np.isfinite(succ) & \
        np.isfinite(x).all(axis=1)
    x, succ, trials = x[keep], succ[keep], trials[keep]
    n, p = x.shape
    beta = np.zeros(p)
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
        # step halving keeps a rare-event fit from walking off to infinity
        for _ in range(20):
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
        for c in cols])
    return np.nan_to_num(X, nan=0.0, posinf=0.0, neginf=0.0)


# ------------------------------------------------------------- shrunk rates
@dataclass
class ShrunkRate:
    """Empirical-Bayes rate: (num + k*prior) / (den + k).

    `k` is in units of the denominator (targets for catch rate, receptions for
    yards per catch), so a player with 20 career targets is pulled hard toward
    the population and a player with 400 barely moves. `k` is picked from a
    fixed grid by training-season MSE -- one parameter, chosen without ever
    seeing the season being projected.
    """

    name: str
    num_col: str
    den_col: str
    prior: float = 0.0
    k: float = 50.0
    slope: float = 1.0
    intercept: float = 0.0
    k_grid: Tuple[float, ...] = (5, 10, 20, 40, 80, 160, 320)

    def raw(self, f: pd.DataFrame, k: Optional[float] = None) -> np.ndarray:
        k = self.k if k is None else k
        num = f[self.num_col].to_numpy(dtype=float)
        den = f[self.den_col].to_numpy(dtype=float)
        return (num + k * self.prior) / (den + k)

    def fit(self, f: pd.DataFrame, y_num: np.ndarray, y_den: np.ndarray) -> "ShrunkRate":
        ok = y_den > 0
        self.prior = float(np.sum(y_num[ok]) / np.sum(y_den[ok]))
        best, best_mse = self.k_grid[0], np.inf
        yt = y_num[ok] / y_den[ok]
        for k in self.k_grid:
            pred = self.raw(f, k)[ok]
            mse = float(np.average((yt - pred) ** 2, weights=y_den[ok]))
            if mse < best_mse:
                best, best_mse = k, mse
        self.k = best
        # one linear recalibration so a systematic level shift (ageing, rule
        # change) is corrected rather than baked in
        X = np.column_stack([np.ones(ok.sum()), self.raw(f, best)[ok]])
        beta = ols(X, yt, w=y_den[ok])
        self.intercept, self.slope = float(beta[0]), float(beta[1])
        return self

    def predict(self, f: pd.DataFrame) -> np.ndarray:
        return self.intercept + self.slope * self.raw(f)


# --------------------------------------------------------------- the model
VET_VOLUME_COLS = ["tpg_w", "tshare_w", "gshare_w", "evidence", "age", "age2",
                   "ppg_w", "experience"]
VET_GAMES_COLS = ["gshare_w", "gshare_1", "present_1", "age", "age2", "evidence"]
ROOKIE_COLS = ["log_draft_pick", "age"]


@dataclass
class WRComponentModel:
    """Fitted on outcome seasons strictly before the projected season."""

    scoring: Dict = field(default_factory=lambda: dict(HALF_PPR))
    use_bonus_model: bool = True
    bonus_covariate: Optional[str] = None   # e.g. "adot_hat"; None = mean only

    # fitted state
    vet_games: Optional[np.ndarray] = None
    vet_tpg: Optional[np.ndarray] = None
    rk_games: Optional[np.ndarray] = None
    rk_tpg: Optional[np.ndarray] = None
    rates: Dict[str, ShrunkRate] = field(default_factory=dict)
    rookie_rates: Dict[str, float] = field(default_factory=dict)
    bonus_beta: Dict[int, np.ndarray] = field(default_factory=dict)
    means: Dict[str, float] = field(default_factory=dict)
    train_seasons: Tuple[int, ...] = ()

    # ------------------------------------------------------------------ fit
    def fit(self, feats: pd.DataFrame, outs: pd.DataFrame) -> "WRComponentModel":
        d = feats.merge(outs, on=["player_id", "season"], suffixes=("", "_y"))
        d = d.copy()
        d["age"] = d["age"].fillna(d["age"].median())
        d["age2"] = d["age"] ** 2
        self.train_seasons = tuple(sorted(d["season"].unique().tolist()))

        vet = d[d["entry"] == "veteran"]
        rk = d[d["entry"] == "rookie"]

        # --- availability: expected share of the season played
        y_g = (d["games"] / d["season_len_y"]).to_numpy(dtype=float)
        self.vet_games = ols(_design(vet, VET_GAMES_COLS),
                             (vet["games"] / vet["season_len_y"]).to_numpy(dtype=float))
        self.rk_games = ols(_design(rk, ROOKIE_COLS),
                            (rk["games"] / rk["season_len_y"]).to_numpy(dtype=float))

        # --- volume: targets per game played (only players who played inform it)
        vp = vet[vet["games"] > 0]
        self.vet_tpg = ols(_design(vp, VET_VOLUME_COLS),
                           (vp["targets"] / vp["games"]).to_numpy(dtype=float),
                           w=vp["games"].to_numpy(dtype=float))
        rp = rk[rk["games"] > 0]
        self.rk_tpg = ols(_design(rp, ROOKIE_COLS),
                          (rp["targets"] / rp["games"]).to_numpy(dtype=float),
                          w=rp["games"].to_numpy(dtype=float))

        # --- efficiency rates, veterans
        specs = [
            ("catch_rate", "cr_num", "cr_den", "receptions", "targets"),
            ("ypr", "ypr_num", "ypr_den", "rec_yards", "receptions"),
            ("tdpt", "tdpt_num", "tdpt_den", "rec_tds", "targets"),
            ("adot", "adot_num", "adot_den", None, None),
            ("carries_pg", None, None, "carries", "games"),
            ("ypc", "ypc_num", "ypc_den", "rush_yards", "carries"),
            ("fum_pg", "fumpg_num", "fumpg_den", "fumbles_lost", "games"),
        ]
        for name, nc, dc, ynum, yden in specs:
            if nc is None or ynum is None:
                continue
            sr = ShrunkRate(name, nc, dc)
            sr.fit(vet, vet[ynum].to_numpy(dtype=float),
                   vet[yden].to_numpy(dtype=float))
            self.rates[name] = sr
        # aDOT has no outcome column of its own; it is a covariate, so shrink
        # it toward the population mean without recalibration.
        ad = ShrunkRate("adot", "adot_num", "adot_den")
        ad.prior = float(vet["adot_num"].sum() / max(vet["adot_den"].sum(), 1))
        ad.k = 40.0
        self.rates["adot"] = ad
        # carries per game: modelled as a shrunk lagged rate, no recalibration
        cpg = ShrunkRate("carries_pg", "carries_pg_w", "carries_pg_w")
        self.means["carries_pg"] = float(vet["carries"].sum() / max(vet["games"].sum(), 1))
        self.means["rush_td_per_carry"] = float(
            vet["rush_tds"].sum() / max(vet["carries"].sum(), 1))

        # --- rookie rates: population means for the rookie cohort
        for col, den in [("receptions", "targets"), ("rec_yards", "receptions"),
                         ("rec_tds", "targets"), ("carries", "games"),
                         ("rush_yards", "carries"), ("fumbles_lost", "games")]:
            num = float(rk[col].sum())
            dd = float(rk[den].sum())
            self.rookie_rates[f"{col}/{den}"] = num / dd if dd > 0 else 0.0

        # --- the stacking-bonus model: P(game >= t) as a function of mean ypg
        self._fit_bonus(d, np.divide(
            d["rec_yards"].to_numpy(dtype=float),
            np.where(d["games"] > 0, d["games"], np.nan).astype(float)))
        return self

    def _bonus_design(self, ypg: np.ndarray, adot: np.ndarray) -> np.ndarray:
        cols = [np.ones(len(ypg)), np.log1p(np.clip(ypg, 0, None))]
        if self.bonus_covariate == "adot":
            a = np.nan_to_num(adot, nan=float(self.means.get("adot_bar", 11.0)))
            cols.append(a)
        return np.column_stack(cols)

    def _fit_bonus(self, d: pd.DataFrame, ypg: np.ndarray) -> None:
        """P(a game clears threshold t) as a logistic function of mean yards
        per game, optionally plus a player trait (aDOT).

        `ypg` is passed in rather than derived, because the calibrated variant
        fits this curve on PROJECTED yards per game -- see
        `refit_bonus_on_projections` for why that matters.
        """
        ok = np.isfinite(ypg) & (d["games"].to_numpy(dtype=float) > 0)
        sub = d[ok]
        adot = np.where(sub["adot_den"] > 0,
                        sub["adot_num"] / sub["adot_den"].replace(0, np.nan), np.nan)
        self.means["adot_bar"] = float(np.nanmedian(adot)) if np.isfinite(adot).any() else 11.0
        adot_sh = self.rates["adot"].raw(sub) if "adot" in self.rates else adot
        X = self._bonus_design(ypg[ok], adot_sh)
        trials = sub["games"].to_numpy(dtype=float)
        for t, col in [(100, "g100"), (150, "g150"), (200, "g200")]:
            self.bonus_beta[t] = binom_glm(X, sub[col].to_numpy(dtype=float), trials)

    def refit_bonus_on_projections(self, proj: pd.DataFrame,
                                   feats: pd.DataFrame,
                                   outs: pd.DataFrame) -> "WRComponentModel":
        """Refit the exceedance curve against PROJECTED, not realised, ypg.

        Why this is not a cosmetic change. The curve P(game >= 100 | ypg) is
        convex over the range that matters, so E[bonus] evaluated at a shrunk
        point estimate is not E[bonus] under the projection's own uncertainty --
        it is systematically too low, and measurably so: the first cut
        under-predicted league-wide WR bonus points by 10-50% every season.
        Fitting the curve on the projections the model will actually feed it
        absorbs that shrinkage, because the training inputs are compressed in
        exactly the same way the live inputs will be.

        `proj` must be OUT-OF-SAMPLE projections for the training seasons --
        produced by models fitted on seasons strictly earlier still. Passing
        in-sample projections here would make the correction fit its own noise.
        """
        d = proj.merge(outs, on=["player_id", "season"], suffixes=("", "_act"))
        d = d.merge(feats[["player_id", "season", "adot_num", "adot_den"]],
                    on=["player_id", "season"], how="left")
        ypg = np.divide(d["proj_rec_yards"].to_numpy(dtype=float),
                        np.where(d["proj_games"] > 0, d["proj_games"], np.nan).astype(float))
        self._fit_bonus(d, ypg)
        return self

    # -------------------------------------------------------------- predict
    def predict(self, feats: pd.DataFrame) -> pd.DataFrame:
        f = feats.copy()
        f["age"] = f["age"].fillna(f["age"].median() if f["age"].notna().any() else 25.0)
        f["age2"] = f["age"] ** 2
        is_rk = (f["entry"] == "rookie").to_numpy()

        gshare = np.where(is_rk,
                          _design(f, ROOKIE_COLS) @ self.rk_games,
                          _design(f, VET_GAMES_COLS) @ self.vet_games)
        gshare = np.clip(gshare, 0.0, 1.0)
        games = gshare * f["season_len"].to_numpy(dtype=float)

        tpg = np.where(is_rk,
                       _design(f, ROOKIE_COLS) @ self.rk_tpg,
                       _design(f, VET_VOLUME_COLS) @ self.vet_tpg)
        tpg = np.clip(tpg, 0.0, None)

        cr = np.clip(self.rates["catch_rate"].predict(f), 0.05, 0.95)
        ypr = np.clip(self.rates["ypr"].predict(f), 3.0, 25.0)
        tdpt = np.clip(self.rates["tdpt"].predict(f), 0.0, 0.30)
        adot = self.rates["adot"].raw(f)
        fum_pg = np.clip(self.rates["fum_pg"].predict(f), 0.0, 0.5)

        for key, arr in [("receptions/targets", cr), ("rec_yards/receptions", ypr),
                         ("rec_tds/targets", tdpt)]:
            arr[is_rk] = self.rookie_rates[key]
        fum_pg[is_rk] = self.rookie_rates["fumbles_lost/games"]

        carries_pg = np.where(is_rk, self.rookie_rates["carries/games"],
                              np.clip(f["carries_pg_w"].fillna(0).to_numpy(dtype=float), 0, None))
        ypc = np.where(is_rk, self.rookie_rates["rush_yards/carries"],
                       np.clip(self.rates["ypc"].predict(f), 0.0, 15.0))

        targets = games * tpg
        receptions = targets * cr
        rec_yards = receptions * ypr
        rec_tds = targets * tdpt
        carries = games * carries_pg
        rush_yards = carries * ypc
        rush_tds = carries * self.means["rush_td_per_carry"]
        fumbles = games * fum_pg

        out = pd.DataFrame({
            "player_id": f["player_id"].to_numpy(),
            "season": f["season"].to_numpy(),
            "entry": f["entry"].to_numpy(),
            "proj_games": games,
            "proj_tpg": tpg,
            "proj_targets": targets,
            "proj_receptions": receptions,
            "proj_rec_yards": rec_yards,
            "proj_rec_tds": rec_tds,
            "proj_carries": carries,
            "proj_rush_yards": rush_yards,
            "proj_rush_tds": rush_tds,
            "proj_fumbles_lost": fumbles,
            "proj_adot": adot,
            "proj_catch_rate": cr,
            "proj_ypr": ypr,
            "proj_td_per_target": tdpt,
        })

        # ---- per-game bonus expectation
        ypg = np.divide(rec_yards, np.where(games > 0, games, np.nan))
        ypg = np.nan_to_num(ypg, nan=0.0)
        p = {}
        Xb = self._bonus_design(ypg, adot)
        bonus_pg = np.zeros(len(f))
        for t, b in self.scoring["rec_yard_bonuses"]:
            pt = 1.0 / (1.0 + np.exp(-np.clip(Xb @ self.bonus_beta[t], -30, 30)))
            p[t] = pt
            bonus_pg += b * pt
        out["p_100yd_game"] = p[100]
        out["p_150yd_game"] = p[150]
        out["p_200yd_game"] = p[200]
        out["proj_bonus_points"] = bonus_pg * games if self.use_bonus_model else 0.0

        s = self.scoring
        out["proj_points_base"] = (
            s["per_reception"] * receptions
            + rec_yards / s["yards_per_point"]
            + s["rec_td"] * rec_tds
            + rush_yards / s["yards_per_point"]
            + s["rush_td"] * rush_tds
            + s["fumble_lost"] * fumbles
        )
        out["proj_points"] = out["proj_points_base"] + out["proj_bonus_points"]
        return out


def score_components(comp: pd.DataFrame, scoring: Dict) -> np.ndarray:
    """Re-score an existing component projection under a different ruleset.

    This is the whole point of projecting components: the same numbers, a
    different league. Bonus probabilities are already per-game, so a ruleset
    with different thresholds needs its own GLM evaluation -- only thresholds
    already modelled (100/150/200) can be re-weighted here.
    """
    bonus = np.zeros(len(comp))
    for t, b in scoring.get("rec_yard_bonuses", ()):
        col = f"p_{t}yd_game"
        if col not in comp.columns:
            raise KeyError(f"threshold {t} not modelled; refit with it")
        bonus += b * comp[col].to_numpy(dtype=float) * comp["proj_games"].to_numpy(dtype=float)
    return (
        scoring["per_reception"] * comp["proj_receptions"].to_numpy(dtype=float)
        + comp["proj_rec_yards"].to_numpy(dtype=float) / scoring["yards_per_point"]
        + scoring["rec_td"] * comp["proj_rec_tds"].to_numpy(dtype=float)
        + comp["proj_rush_yards"].to_numpy(dtype=float) / scoring["yards_per_point"]
        + scoring["rush_td"] * comp["proj_rush_tds"].to_numpy(dtype=float)
        + scoring["fumble_lost"] * comp["proj_fumbles_lost"].to_numpy(dtype=float)
        + bonus
    )
