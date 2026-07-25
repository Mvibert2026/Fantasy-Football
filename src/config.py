"""
Versioned, tunable configuration. Per CLAUDE.md §4, weights live here and are
never hardcoded into model code, so every model version stays reproducible and
comparable.

Season weighting is deliberately a *parameter*, not a constant. How far back to
weight is an empirical question (statistical-guardrails.md §4: "test whether
adding older seasons improves or degrades holdout performance, per position"),
so this module supplies the knob and the backtest supplies the answer. Nothing
here encodes a belief about the right lookback.
"""

from __future__ import annotations

import math
from dataclasses import dataclass, field
from typing import Dict, Iterable, Literal

WeightingScheme = Literal["uniform", "exponential", "linear"]


@dataclass(frozen=True)
class SeasonWeighting:
    """Relative weight of historical seasons when building a ranking input.

    `reference_season` is the season being predicted; a season N years before it
    gets weight per `scheme`. Weights are returned normalised to sum to 1.

    Attributes:
        scheme: "uniform" (flat -- the known failure mode, kept as a baseline to
            beat), "exponential" (half-life decay), or "linear" (linear taper to
            zero at `max_lookback`).
        half_life_seasons: for "exponential" -- seasons until weight halves.
        max_lookback: hard cap on seasons considered. None means unbounded by
            config, but callers remain bounded by each feature's real
            availability (docs/data-availability.md) -- this cap is a modelling
            choice, not a data-availability statement. Do not use it to paper
            over the 2003-2008 receiver-attribution gap; exclude those seasons
            explicitly instead.
    """

    scheme: WeightingScheme = "exponential"
    half_life_seasons: float = 3.0
    max_lookback: int | None = None

    def __post_init__(self) -> None:
        if self.half_life_seasons <= 0:
            raise ValueError("half_life_seasons must be positive")
        if self.max_lookback is not None and self.max_lookback < 1:
            raise ValueError("max_lookback must be >= 1 season")

    def _raw_weight(self, season: int, reference_season: int) -> float:
        age = reference_season - season
        if age < 0:
            raise ValueError(
                f"season {season} is not before reference_season {reference_season}; "
                "ranking inputs may only use prior seasons (CLAUDE.md §6.1)"
            )
        if self.max_lookback is not None and age > self.max_lookback:
            return 0.0
        if self.scheme == "uniform":
            return 1.0
        if self.scheme == "exponential":
            return math.pow(0.5, age / self.half_life_seasons)
        if self.scheme == "linear":
            if self.max_lookback is None:
                raise ValueError("linear scheme requires max_lookback")
            return max(0.0, 1.0 - age / self.max_lookback)
        raise ValueError(f"unknown scheme {self.scheme!r}")

    def weights(self, seasons: Iterable[int], reference_season: int) -> Dict[int, float]:
        """Normalised weights per season. Seasons weighted to zero are dropped.

        Rejects `reference_season` itself and anything later: weighting the
        season you are predicting is look-ahead leakage, not a weighting choice
        (CLAUDE.md §6.1). `_raw_weight` stays mathematically defined at age 0 so
        the decay curve remains directly testable; the policy lives here.
        """
        seasons = list(seasons)
        leaking = [s for s in seasons if s >= reference_season]
        if leaking:
            raise ValueError(
                f"season(s) {sorted(leaking)} are at or after reference_season "
                f"{reference_season}; ranking inputs may only use prior seasons "
                "(CLAUDE.md §6.1)"
            )
        raw = {s: self._raw_weight(s, reference_season) for s in seasons}
        total = sum(raw.values())
        if total == 0:
            return {}
        return {s: w / total for s, w in raw.items() if w > 0}


@dataclass(frozen=True)
class ProjectConfig:
    """Top-level tunable config for a model version."""

    season_weighting: SeasonWeighting = field(default_factory=SeasonWeighting)
    # Seeded RNG for every bootstrap/simulation. statistical-guardrails.md §7:
    # unreproducible results are not results.
    random_seed: int = 20260725

    def describe(self) -> Dict[str, object]:
        """Flat dict for embedding in result output, so any reported metric
        carries the config that produced it."""
        return {
            "season_weighting.scheme": self.season_weighting.scheme,
            "season_weighting.half_life_seasons": self.season_weighting.half_life_seasons,
            "season_weighting.max_lookback": self.season_weighting.max_lookback,
            "random_seed": self.random_seed,
        }


DEFAULT_CONFIG = ProjectConfig()
