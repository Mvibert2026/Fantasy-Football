"""Batch-D1 model wiring: the v2 component models with the veteran projected-games
channel replaced by a binomial GLM on a NAMED feature list.

One thing differs between an arm and its control: the games feature list. Volumes,
rates, bonus curves and scoring are inherited bit-for-bit from `pos_model`, and the
rookie availability path is untouched (draft capital + age; April-of-N information,
no consensus).

Form note. The incumbent (`G0`, avail arm A) is `clip(OLS(features), 0, 1) x
season_len`. Arm `B0` is the SAME feature list under the binomial GLM fable
introduced in B1. That contrast is registered separately precisely so a gain from
the estimator is never attributed to the new data.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, List, Optional, Tuple

import numpy as np
import pandas as pd

from ..components.pos_model import (
    MODELS, QBComponentModel, RBComponentModel, ReceiverComponentModel,
)
from .availability_features import (
    B0_FEATURES, C_FEATURES, PLACEBO_COL, P_FEATURES, R_FEATURES,
)
from .games_model import GamesGLM

#: arm -> (feature blocks needed by the builder, games feature list)
ARM_SPEC: Dict[str, Tuple[Tuple[str, ...], List[str]]] = {
    # form-only reference: the incumbent feature list under the GLM
    "B0":  ((), B0_FEATURES),
    "B0d": ((), B0_FEATURES),
    # placebos: the same, plus a seeded noise column
    "P0":  ((), B0_FEATURES + [PLACEBO_COL]),
    "P0d": ((), B0_FEATURES + [PLACEBO_COL]),
    # treatments
    "A1":  (("P",), B0_FEATURES + P_FEATURES),
    "A2":  (("C",), B0_FEATURES + C_FEATURES),
    "A3":  (("R",), B0_FEATURES + R_FEATURES),
    "A4":  (("P", "C"), B0_FEATURES + P_FEATURES + C_FEATURES),
    "A5":  (("P", "C", "R"), B0_FEATURES + P_FEATURES + C_FEATURES + R_FEATURES),
    # paired presence controls (batch 5 `routes_known` geometry)
    "A1k": (("P",), B0_FEATURES + ["prac_present_1"]),
    "A3k": (("R",), B0_FEATURES + ["ros_present_1"]),
}

PLACEBO_ARMS = ("P0", "P0d")


class _D1AvailabilityMixin:
    """`games_features`: the exact column list the games GLM consumes."""

    def _games_features(self) -> List[str]:
        return list(self.games_features)

    def fit(self, feats: pd.DataFrame, outs: pd.DataFrame,
            rate_pool: Optional[Tuple[pd.DataFrame, pd.DataFrame]] = None):
        super().fit(feats, outs, rate_pool=rate_pool)
        d = feats.merge(outs, on=["player_id", "season"], suffixes=("", "_y")).copy()
        d["age"] = d["age"].fillna(d["age"].median())
        d["age2"] = d["age"] ** 2
        vet = d[d["entry"] == "veteran"]
        self._games_glm = GamesGLM(self._games_features()).fit(
            vet, vet["games"].to_numpy(dtype=float),
            vet["season_len_y"].to_numpy(dtype=float))
        return self

    def _availability(self, f: pd.DataFrame, is_rk: np.ndarray) -> np.ndarray:
        base = super()._availability(f, is_rk)          # rookie path unchanged
        gshare = self._games_glm.predict_gshare(f)
        vet_games = gshare * f["season_len"].to_numpy(dtype=float)
        return np.where(is_rk, base, vet_games)


@dataclass
class D1ReceiverModel(_D1AvailabilityMixin, ReceiverComponentModel):
    games_features: Tuple[str, ...] = ()


@dataclass
class D1RBModel(_D1AvailabilityMixin, RBComponentModel):
    games_features: Tuple[str, ...] = ()


@dataclass
class D1QBModel(_D1AvailabilityMixin, QBComponentModel):
    games_features: Tuple[str, ...] = ()


D1MODELS = {"WR": D1ReceiverModel, "TE": D1ReceiverModel,
            "RB": D1RBModel, "QB": D1QBModel}


def make_avail_model(position: str, arm: str, **kwargs):
    """`arm='G0'` returns the unmodified incumbent -- the pinned control, exactly
    as `run_c1.py` uses plain `WalkForward`."""
    if arm == "G0":
        return MODELS[position](position=position, avail_arm="A", **kwargs)
    if arm not in ARM_SPEC:
        raise KeyError(f"unknown D1 arm {arm!r}")
    return D1MODELS[position](position=position, avail_arm="A",
                              games_features=tuple(ARM_SPEC[arm][1]), **kwargs)
