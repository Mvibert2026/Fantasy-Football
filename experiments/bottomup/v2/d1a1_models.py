"""Batch D1 Amendment 1 — model wiring for Q0 / Q0w / Q1 / Q2 / PG0.

Registration: `docs/ranking/factor-campaign-manifest/batch-D1-amendment-1.md`
(strategist, 2026-08-01, before any arm was fitted).

The finding under test: the incumbent games model (G0's OLS availability, avail
arm A) is unbiased on the full veteran universe it is FITTED on (−0.14 games)
and −2.41 games low on the board population it is USED on. Three registered
arms, each one change:

  Q0   population refit — the INCUMBENT feature list, veteran availability OLS
       refit with the training population RESTRICTED to board (M-panel ppr12)
       members. No new features, no estimator change.
  Q0w  the registered weighting variant of the same arm (weight toward the
       board rather than restrict to it). CO-REPORTED, not separately graded —
       m_b = 12 counts three arms, and grading two Q0 variants would spend an
       unregistered multiplicity slot. Weight fixed a priori at 4.0.
  Q1   quality block appended to the veteran availability spec.
  Q2   Q1 minus `ppg_w` (role + draft capital only) — the arm that cannot
       double-count quality into points.
  PG0  standing placebo on this endpoint (seeded noise column appended to the
       availability spec). Calibration instrument, 0 tests (registry accounting
       per the M-1..M-6 thread), graded through the full rule with the §6.2(c)
       registered prediction: 0 INCLUDE / 0 EXCLUDE.

THE NULL FOR Q0 (decision D3, `docs/ranking/adr070-tier2-execution.md`): Q0 adds
no column, so §4.1's block permutation does not apply (the F6 precedent). Its
matched null is a WITHIN-SEASON PERMUTATION OF THE BOARD-MEMBERSHIP INDICATOR
over the veteran training rows — same restriction size per season, same
estimator, same feature list, provably no player-level information. Seed =
sha256(f"Q0|{position}|{season}|{k}").

LOOK-AHEAD. Board membership for a TRAINING season s is the season-s pre-draft
ppr12 ADP board — information dated strictly before Week 1 of season s, and
every training season satisfies s <= target − 1, so nothing here reads anything
the target season would not already know. `adp_baseline.load_adp` re-asserts the
pre-kickoff gate on every file it serves; boards exist 2013–2024, and a training
season with no board contributes no restricted rows (restrict mode) or weight-1
rows (weight mode). The Q0 fit ASSERTS it retains >= 2 distinct board seasons,
so a window with too little board history fails loudly rather than silently
reproducing the incumbent.
"""

from __future__ import annotations

import hashlib
from dataclasses import dataclass
from typing import Dict, FrozenSet, List, Optional, Tuple

import numpy as np
import pandas as pd

from ..components import adp_baseline as adp
from ..components.pos_model import (
    MODELS, QBComponentModel, RBComponentModel, ReceiverComponentModel,
    _design, ols,
)

ADP_FMT = "ppr_12team"
BOARD_SEASONS = tuple(range(2013, 2025))

#: registered quality block (amendment §2). All columns already exist in the
#: base feature frame; none is an expert ranking, a market ranking, or ADP.
QUALITY_BLOCK: List[str] = ["ppg_w", "tshare_w", "cshare_w",
                            "depth_first_share_1", "log_draft_pick",
                            "undrafted", "experience"]
QUALITY_BLOCK_NO_PPG: List[str] = [c for c in QUALITY_BLOCK if c != "ppg_w"]

AVAIL_PLACEBO_COL = "avail_placebo"

Q0_WEIGHT = 4.0     # fixed a priori; never tuned against any result


def _seed(s: str) -> int:
    return int.from_bytes(hashlib.sha256(s.encode()).digest()[:8], "big")


_BOARD_CACHE: Dict[str, Dict[int, FrozenSet[str]]] = {}


def board_map(position: str) -> Dict[int, FrozenSet[str]]:
    """season -> frozenset of gsis ids on that season's ppr12 board at the
    position. Loaded once per process."""
    if position not in _BOARD_CACHE:
        out: Dict[int, FrozenSet[str]] = {}
        for s in BOARD_SEASONS:
            b = adp.load_adp(s, fmt=ADP_FMT, position=position)
            ids = (b.loc[~b["unmatched"], "player_id"].dropna().unique().tolist()
                   if len(b) else [])
            out[s] = frozenset(ids)
        _BOARD_CACHE[position] = out
    return _BOARD_CACHE[position]


# ---------------------------------------------------------------- Q0 mixin
class _Q0Mixin:
    """Refit ONLY the veteran availability OLS on the restricted/weighted
    population. Everything else — volumes, rates, bonus curves, rookie path —
    is the incumbent, inherited bit-for-bit from `super().fit`."""

    def fit(self, feats: pd.DataFrame, outs: pd.DataFrame,
            rate_pool: Optional[Tuple[pd.DataFrame, pd.DataFrame]] = None):
        super().fit(feats, outs, rate_pool=rate_pool)
        d = feats.merge(outs, on=["player_id", "season"], suffixes=("", "_y"))
        d = d.copy()
        d["age"] = d["age"].fillna(d["age"].median())
        d["age2"] = d["age"] ** 2
        vet = d[d["entry"] == "veteran"].reset_index(drop=True)

        bm = board_map(self.position)
        onb = np.zeros(len(vet), dtype=bool)
        for s in sorted(vet["season"].unique()):
            mask = (vet["season"] == s).to_numpy()
            memb = vet.loc[mask, "player_id"].isin(bm.get(int(s), frozenset())) \
                .to_numpy()
            if self.q0_perm_k > 0:
                rng = np.random.default_rng(
                    _seed(f"Q0|{self.position}|{int(s)}|{int(self.q0_perm_k)}"))
                memb = rng.permutation(memb)
            onb[mask] = memb

        # The walk-forward's bonus calibration refits this model on EARLY
        # sub-windows (expanding window inside training) where no board exists
        # yet. Those inner fits keep the incumbent availability; the OUTER fit
        # (every Q0 target is >= 2015, so >= 2 board training seasons exist)
        # MUST apply the refit — asserted against the seasons the window
        # actually contains, so an empty/broken board load still fails loudly
        # instead of silently reproducing the control.
        n_expected = int(sum(1 for s in vet["season"].unique()
                             if int(s) in bm and len(bm[int(s)])))
        n_with_rows = int(sum(1 for s in vet["season"].unique() if int(s) >= 2013))
        if n_with_rows >= 2:
            assert n_expected >= 2, (
                f"Q0/{self.position}: window has {n_with_rows} seasons >= 2013 "
                f"but only {n_expected} with a loadable board — board archive "
                f"broken, refusing to fall back silently")
        if n_expected < 2:
            return self          # inner early window: incumbent availability

        y = (vet["games"] / vet["season_len_y"]).to_numpy(dtype=float)
        if self.q0_mode == "restrict":
            sub = vet[onb]
            assert int(sub["season"].nunique()) >= 2, (
                f"Q0/{self.position}: board seasons present but no matched "
                f"board rows in training — crosswalk failure")
            self.vet_games = ols(_design(sub, self.avail_cols),
                                 (sub["games"] / sub["season_len_y"])
                                 .to_numpy(dtype=float))
        elif self.q0_mode == "weight":
            w = np.where(onb, Q0_WEIGHT, 1.0)
            self.vet_games = ols(_design(vet, self.avail_cols), y, w=w)
        else:
            raise KeyError(f"unknown q0_mode {self.q0_mode!r}")
        return self


@dataclass
class Q0ReceiverModel(_Q0Mixin, ReceiverComponentModel):
    q0_mode: str = "restrict"
    q0_perm_k: int = 0


@dataclass
class Q0RBModel(_Q0Mixin, RBComponentModel):
    q0_mode: str = "restrict"
    q0_perm_k: int = 0


@dataclass
class Q0QBModel(_Q0Mixin, QBComponentModel):
    q0_mode: str = "restrict"
    q0_perm_k: int = 0


_Q0MODELS = {"WR": Q0ReceiverModel, "TE": Q0ReceiverModel,
             "RB": Q0RBModel, "QB": Q0QBModel}


# ------------------------------------------------- Q1/Q2/PG0: extended spec
class _ExtraAvailColsMixin:
    """Append a declared block to the veteran availability spec. The incumbent
    OLS estimator is unchanged; `avail_cols` is the one thing that differs."""

    @property
    def avail_cols(self) -> List[str]:
        from ..components.pos_model import AVAIL_ARMS
        return list(AVAIL_ARMS[self.avail_arm]) + list(self.extra_avail_cols)


@dataclass
class QXReceiverModel(_ExtraAvailColsMixin, ReceiverComponentModel):
    extra_avail_cols: Tuple[str, ...] = ()


@dataclass
class QXRBModel(_ExtraAvailColsMixin, RBComponentModel):
    extra_avail_cols: Tuple[str, ...] = ()


@dataclass
class QXQBModel(_ExtraAvailColsMixin, QBComponentModel):
    extra_avail_cols: Tuple[str, ...] = ()


_QXMODELS = {"WR": QXReceiverModel, "TE": QXReceiverModel,
             "RB": QXRBModel, "QB": QXQBModel}


def model_factory(arm: str, position: str, perm_k: int = 0):
    """Returns a zero-arg factory for `Run070WalkForward.model_factory`.
    perm_k > 0 only applies to Q0/Q0w (the membership-permutation null)."""
    if arm in ("Q0", "Q0w"):
        mode = "restrict" if arm == "Q0" else "weight"

        def make():
            return _Q0MODELS[position](position=position, avail_arm="A",
                                       q0_mode=mode, q0_perm_k=perm_k)
        return make
    if arm in ("Q1", "Q2", "PG0"):
        block = {"Q1": tuple(QUALITY_BLOCK),
                 "Q2": tuple(QUALITY_BLOCK_NO_PPG),
                 "PG0": (AVAIL_PLACEBO_COL,)}[arm]

        def make():
            return _QXMODELS[position](position=position, avail_arm="A",
                                       extra_avail_cols=block)
        return make
    raise KeyError(f"unknown D1A1 arm {arm!r}")
