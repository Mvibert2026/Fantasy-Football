"""
Versioned, first-class league configuration (ADR-041).

WHY THIS EXISTS. Everything from replacement levels through the draft
simulator's opponent model was written for one specific league: 10 teams,
half-PPR, this exact roster shape. The user is drafting multiple leagues in
2026. `LeagueConfig` is the single object every downstream computation should
derive from instead of reading module-level constants.

WHAT THIS DOES NOT DO. Live ingestion of a league's settings from
Yahoo/ESPN/Sleeper (`platform` below is metadata, not a working adapter) is
explicitly out of scope -- CLAUDE.md SS1 names this "eventual scope, design for
it, do not build it yet." A LeagueConfig is currently hand-authored or loaded
from a saved JSON file, never fetched live.

SCHEMA VERSIONING. `schema_version` is this dataclass's own shape version,
separate from the front-end data CONTRACT_VERSION in export_contract.py. A
schema change here (a new required field) is a different kind of event from a
contract change (a new export field) and the two must not be conflated.
"""

from __future__ import annotations

import json
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Dict, List, Optional, Tuple

LEAGUE_CONFIG_SCHEMA_VERSION = "1.0.0"

LEAGUES_DIR = Path(__file__).resolve().parent.parent / "data" / "leagues"

PRIMARY_LEAGUE_ID = "primary"

VALID_PLATFORMS = {"yahoo", "espn", "sleeper", "mfl", "other"}
VALID_DRAFT_TYPES = {"snake", "auction"}
VALID_POSITIONS = ("QB", "RB", "WR", "TE", "K", "DEF")


@dataclass
class LeagueConfig:
    league_id: str
    name: str
    platform: str  # metadata only -- see module docstring
    teams: int
    scoring: dict  # same shape as scoring.LEAGUE
    starters: Dict[str, int]  # e.g. {"QB":1,"RB":2,"WR":3,"TE":1,"DEF":1} -- NOT incl. flex
    flex_slots: int
    flex_eligible: Tuple[str, ...]
    bench: int
    ir: int
    user_draft_slot: int
    draft_type: str = "snake"
    rounds: Optional[int] = None  # None => derived; see __post_init__
    playoff_teams: int = 4
    playoff_weeks: Tuple[int, ...] = (16, 17)
    reseeding: bool = False
    trade_deadline: Optional[str] = None
    faab_budget: Optional[int] = None
    schema_version: str = LEAGUE_CONFIG_SCHEMA_VERSION
    # Flex-split is a MEASURED quantity (ADR-029) for the primary league, over
    # 26 seasons under ITS exact scoring rules. A new league's true split has
    # not been measured -- this field defaults to None and callers must either
    # supply a measured value or accept the explicitly-flagged placeholder in
    # ReplacementLevels.from_league_config().
    flex_split: Optional[Dict[str, float]] = None
    # T5 (fable-draft-day-premortem-2026-07-27.md finding #2): board build
    # refuses a live snapshot older than this. Founder-tunable per league --
    # 3 days is the suggested default for in-season-of-draft-prep pulls, not
    # a measured constant.
    freshness_max_age_days: int = 3

    def __post_init__(self) -> None:
        if self.rounds is None:
            self.rounds = self.drafted_rounds()
        self.validate()

    def drafted_rounds(self) -> int:
        """starters + flex + bench. IR is deliberately NOT counted: it is a
        bonus roster slot filled off waivers, not a drafted round -- verified
        against the primary league's actual numbers (7 QB/RB/WR/TE starters +
        1 DEF + 2 flex + 6 bench = 16 = N_ROUNDS, with `ir=1` outside that
        entirely). An earlier draft of this formula included `ir` and produced
        17, which is wrong; this docstring exists so that mistake is not
        repeated."""
        return sum(self.starters.values()) + self.flex_slots + self.bench

    def validate(self) -> None:
        errors: List[str] = []
        if self.teams <= 0:
            errors.append(f"teams must be positive, got {self.teams}")
        if not (1 <= self.user_draft_slot <= self.teams):
            errors.append(
                f"user_draft_slot {self.user_draft_slot} outside [1, {self.teams}]"
            )
        if self.draft_type not in VALID_DRAFT_TYPES:
            errors.append(f"draft_type {self.draft_type!r} not in {VALID_DRAFT_TYPES}")
        if self.platform not in VALID_PLATFORMS:
            errors.append(f"platform {self.platform!r} not in {VALID_PLATFORMS}")
        for pos in self.starters:
            if pos not in VALID_POSITIONS:
                errors.append(f"starters has unknown position {pos!r}")
        for pos in self.flex_eligible:
            if pos not in self.starters:
                errors.append(
                    f"flex_eligible position {pos!r} is not a starter position at all"
                )
        expected_rounds = self.drafted_rounds()
        if self.rounds != expected_rounds:
            errors.append(
                f"rounds={self.rounds} does not equal starters+flex+bench (IR excluded, "
                f"it is not a drafted round)={expected_rounds} -- pass rounds=None to "
                f"derive it, or fix the mismatch"
            )
        if self.flex_split is not None:
            for pos in self.flex_split:
                if pos not in self.flex_eligible:
                    errors.append(
                        f"flex_split has {pos!r}, which is not in flex_eligible"
                    )
        if errors:
            raise ValueError(
                f"LeagueConfig {self.league_id!r} is invalid:\n  " + "\n  ".join(errors)
            )

    # ------------------------------------------------------------ (de)serialization
    def to_dict(self) -> dict:
        d = asdict(self)
        d["playoff_weeks"] = list(d["playoff_weeks"])
        d["flex_eligible"] = list(d["flex_eligible"])
        return d

    @classmethod
    def from_dict(cls, d: dict) -> "LeagueConfig":
        d = dict(d)
        d["playoff_weeks"] = tuple(d.get("playoff_weeks", (16, 17)))
        d["flex_eligible"] = tuple(d["flex_eligible"])
        return cls(**d)

    def save(self, directory: Path = LEAGUES_DIR) -> Path:
        directory.mkdir(parents=True, exist_ok=True)
        path = directory / f"{self.league_id}.json"
        path.write_text(json.dumps(self.to_dict(), indent=2), encoding="utf-8")
        return path

    @classmethod
    def load(cls, league_id: str, directory: Path = LEAGUES_DIR) -> "LeagueConfig":
        path = directory / f"{league_id}.json"
        if not path.exists():
            raise FileNotFoundError(
                f"no saved league config for {league_id!r} at {path}"
            )
        return cls.from_dict(json.loads(path.read_text(encoding="utf-8")))

    @property
    def is_primary(self) -> bool:
        return self.league_id == PRIMARY_LEAGUE_ID


def _current_league_scoring() -> dict:
    # Imported lazily to avoid a circular import (scoring.py does not import
    # this module).
    from scoring import LEAGUE

    return LEAGUE


def build_current_league() -> LeagueConfig:
    """The existing 10-team half-PPR league, as a LeagueConfig -- the first
    real instance, constructed from today's previously-hardcoded constants so
    nothing regresses."""
    return LeagueConfig(
        league_id=PRIMARY_LEAGUE_ID,
        name="Primary league (10-team half-PPR)",
        platform="other",
        teams=10,
        scoring=_current_league_scoring(),
        starters={"QB": 1, "RB": 2, "WR": 3, "TE": 1, "DEF": 1},
        flex_slots=2,
        flex_eligible=("RB", "WR", "TE"),
        bench=6,
        ir=1,
        user_draft_slot=3,
        draft_type="snake",
        playoff_teams=4,
        playoff_weeks=(16, 17),
        reseeding=False,
        trade_deadline="2026-11-28",
        faab_budget=100,
        # Measured, ADR-029: RB 0.52 / WR 0.48 / TE 0.00 over 26 seasons under
        # this exact league's scoring rules.
        flex_split={"RB": 0.52, "WR": 0.48, "TE": 0.00},
    )


CURRENT_LEAGUE = build_current_league()
