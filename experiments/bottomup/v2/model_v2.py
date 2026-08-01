"""v2 component models: the existing per-position ledgers with the veteran
games projection swapped for the GamesGLM. Rookie path untouched (own
sub-model, draft capital + age — April-of-N information, no consensus).

The subclasses change exactly one thing (batch-B1 arm discipline): where
veteran `proj_games` comes from. Volumes, rates, bonus curves, scoring — all
inherited bit-for-bit, so a G1-vs-G0 contrast isolates the games channel.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Optional, Tuple

import numpy as np
import pandas as pd

from ..components.pos_model import (
    MODELS, QBComponentModel, RBComponentModel, ReceiverComponentModel,
)
from .features_v2 import ARM_FEATURES
from .games_model import GamesGLM


class _V2AvailabilityMixin:
    """games_arm: 'G1' | 'G1a' | 'G2a' — see features_v2.ARM_FEATURES."""

    def _games_features(self):
        return ARM_FEATURES[self.games_arm]

    def fit(self, feats: pd.DataFrame, outs: pd.DataFrame,
            rate_pool: Optional[Tuple[pd.DataFrame, pd.DataFrame]] = None):
        super().fit(feats, outs, rate_pool=rate_pool)
        d = feats.merge(outs, on=["player_id", "season"], suffixes=("", "_y"))
        d = d.copy()
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
class V2ReceiverModel(_V2AvailabilityMixin, ReceiverComponentModel):
    games_arm: str = "G1"


@dataclass
class V2RBModel(_V2AvailabilityMixin, RBComponentModel):
    games_arm: str = "G1"


@dataclass
class V2QBModel(_V2AvailabilityMixin, QBComponentModel):
    games_arm: str = "G1"


V2MODELS = {"WR": V2ReceiverModel, "TE": V2ReceiverModel,
            "RB": V2RBModel, "QB": V2QBModel}


def make_model(position: str, arm: str, **kwargs):
    """G0 = the unmodified incumbent (avail arm A). G1/G2 = v2 classes."""
    if arm == "G0":
        return MODELS[position](position=position, avail_arm="A", **kwargs)
    if arm in ("G1", "G1a", "G2a"):
        return V2MODELS[position](position=position, avail_arm="A",
                                  games_arm=arm, **kwargs)
    raise KeyError(f"unknown games arm {arm!r}")
