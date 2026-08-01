"""The v2 projected-games component (batch-B1 arms G1/G2) and the GN baseline.

Form: binomial GLM with logit link on (games, season_len) — the existing ridged
IRLS `binom_glm`, k covariates, features standardised on training rows. Chosen
over the incumbent OLS for three stated reasons: (1) games/season_len is a
bounded proportion and the logistic respects the bounds instead of clipping;
(2) the binomial weighting makes a 17-game season more informative than a
3-game one without a separate weight column; (3) it is the machinery the bonus
curves already use — no new estimator class enters the project.

Simple, transparent, 13–15 parameters per position. Not ML (CLAUDE.md §6.3).
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import List, Optional

import numpy as np
import pandas as pd

from ..components.pos_model import binom_glm


@dataclass
class GamesGLM:
    features: List[str]
    beta: Optional[np.ndarray] = None
    mu: Optional[np.ndarray] = None
    sd: Optional[np.ndarray] = None

    def _raw(self, f: pd.DataFrame) -> np.ndarray:
        cols = []
        for c in self.features:
            if c in f.columns:
                cols.append(pd.to_numeric(f[c], errors="coerce")
                            .fillna(0.0).to_numpy(dtype=float))
            else:
                cols.append(np.zeros(len(f)))
        X = np.column_stack(cols)
        return np.nan_to_num(X, nan=0.0, posinf=0.0, neginf=0.0)

    def _design(self, f: pd.DataFrame) -> np.ndarray:
        Z = (self._raw(f) - self.mu) / self.sd
        return np.column_stack([np.ones(len(f)), Z])

    def fit(self, feats: pd.DataFrame, games: np.ndarray,
            season_len: np.ndarray) -> "GamesGLM":
        raw = self._raw(feats)
        self.mu = raw.mean(axis=0)
        sd = raw.std(axis=0)
        sd[sd < 1e-9] = 1.0
        self.sd = sd
        X = np.column_stack([np.ones(len(feats)), (raw - self.mu) / self.sd])
        self.beta = binom_glm(X, np.asarray(games, dtype=float),
                              np.asarray(season_len, dtype=float))
        return self

    def predict_gshare(self, f: pd.DataFrame) -> np.ndarray:
        eta = np.clip(self._design(f) @ self.beta, -25, 25)
        return 1.0 / (1.0 + np.exp(-eta))


def naive_persistence_games(d: pd.DataFrame) -> np.ndarray:
    """GN: last season's own games count, 0 where no N−1 season. The honest
    zero-work baseline, and the bar the mandate names (v1 failed it)."""
    g1 = d["games_1"] if "games_1" in d.columns else pd.Series(0.0, index=d.index)
    return g1.fillna(0.0).to_numpy(dtype=float)
