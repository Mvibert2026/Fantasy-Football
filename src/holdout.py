"""
Locked holdout season (Task 7).

WHY THIS IS CODE AND NOT A CONVENTION. A system that is tested repeatedly
against fixed data manufactures false positives with certainty. Good intentions
do not survive twenty iterations of "let me just check whether that helped".
So the holdout is enforced: reads raise unless they happen inside an explicit,
logged final-evaluation context.

WHICH SEASON, AND THE TRADEOFF (documented because it was a real decision):

  2025 is simultaneously the truest out-of-sample test for a 2026 draft and the
  single most informative season for projecting 2026. Locking it looks like it
  costs real predictive information.

  It mostly does not, because LOCKING GOVERNS SELECTION, NOT FITTING. The
  holdout constrains which seasons may inform decisions about *which factors to
  use*. Once those decisions are frozen, the chosen model is refit on all
  available seasons -- including the holdout -- to produce the live 2026 board.
  `release_for_final_fit()` marks that transition explicitly.

  The alternatives were worse. 2021 cannot serve as a holdout at all: the
  primary baseline (the re-scored consensus board) needs a prior consensus
  season and cannot be built for the first year of coverage. A middle season
  such as 2024 would mean tuning on 2025 data to evaluate 2024 -- using the
  future to predict the past.

POWER WARNING, STATED UP FRONT. One held-out season is N=1. Given the observed
season-to-season variance (consensus RB1 outcomes have ranged 40 to 366 points),
a single-season result cannot confirm an edge. A win on the holdout is weak
evidence; a loss is meaningfully bad news. This asymmetry is the honest reading.
Use `walk_forward_splits()` during development to get several genuinely
forward-looking evaluations instead of relying on the one final test.
"""

from __future__ import annotations

import datetime as dt
import json
import threading
from contextlib import contextmanager
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable, Iterator, List, Optional, Sequence, Tuple

# The locked season. Changing this value invalidates every prior holdout claim
# and must be recorded in docs/decisions.md.
HOLDOUT_SEASON = 2025

# Seasons with consensus coverage (docs/data-availability.md §5).
CONSENSUS_SEASONS = (2021, 2022, 2023, 2024, 2025)

DEFAULT_LOG_PATH = (
    Path(__file__).resolve().parent.parent / "docs" / "preregistration" / "holdout_access_log.jsonl"
)


class HoldoutViolation(Exception):
    """Raised when development code tries to read the locked holdout season."""


_state = threading.local()


def _unlocked_reason() -> Optional[str]:
    return getattr(_state, "reason", None)


@dataclass
class HoldoutLock:
    season: int = HOLDOUT_SEASON
    log_path: Path = DEFAULT_LOG_PATH

    # -------------------------------------------------------------- logging
    def _log(self, event: str, seasons: Sequence[int], reason: str) -> None:
        self.log_path.parent.mkdir(parents=True, exist_ok=True)
        entry = {
            "timestamp_utc": dt.datetime.now(dt.timezone.utc).isoformat(),
            "event": event,
            "holdout_season": self.season,
            "seasons_requested": list(seasons),
            "reason": reason,
        }
        with self.log_path.open("a", encoding="utf-8") as f:
            f.write(json.dumps(entry) + "\n")

    def access_log(self) -> List[dict]:
        if not self.log_path.exists():
            return []
        with self.log_path.open(encoding="utf-8") as f:
            return [json.loads(line) for line in f if line.strip()]

    # -------------------------------------------------------------- guarding
    def is_locked(self, season: int) -> bool:
        return season == self.season and _unlocked_reason() is None

    def guard(self, seasons: Iterable[int], purpose: str = "unspecified") -> List[int]:
        """Assert that `seasons` may be read now. Returns them unchanged.

        Raises HoldoutViolation outside a final-evaluation context. Inside one,
        the access is permitted and logged.
        """
        seasons = list(seasons)
        if self.season not in seasons:
            return seasons
        reason = _unlocked_reason()
        if reason is None:
            self._log("DENIED", seasons, purpose)
            raise HoldoutViolation(
                f"season {self.season} is the LOCKED HOLDOUT and may not be read for "
                f"{purpose!r}. Development must use "
                f"{[s for s in CONSENSUS_SEASONS if s != self.season]}. If this is the "
                f"one-time final evaluation of a pre-registered test, wrap it in "
                f"holdout.final_evaluation(reason=...); if selection is complete and this "
                f"is the production refit, use holdout.release_for_final_fit(reason=...)."
            )
        self._log("ALLOWED", seasons, f"{purpose} :: {reason}")
        return seasons

    def development_seasons(self, seasons: Optional[Sequence[int]] = None) -> List[int]:
        """`seasons` minus the holdout. The safe default for development."""
        pool = list(seasons if seasons is not None else CONSENSUS_SEASONS)
        return [s for s in pool if s != self.season]

    # -------------------------------------------------------------- unlocking
    @contextmanager
    def final_evaluation(self, reason: str) -> Iterator[None]:
        """The ONLY path that may read the holdout during evaluation.

        Every entry is logged with a timestamp and the stated reason. Use once,
        per pre-registered test, at the end. The log exists so that "used once"
        is auditable rather than asserted.
        """
        if not reason or not reason.strip():
            raise ValueError("final_evaluation requires a non-empty reason for the audit log")
        previous = getattr(_state, "reason", None)
        _state.reason = reason
        self._log("FINAL_EVALUATION_OPENED", [self.season], reason)
        try:
            yield
        finally:
            _state.reason = previous
            self._log("FINAL_EVALUATION_CLOSED", [self.season], reason)

    @contextmanager
    def release_for_final_fit(self, reason: str) -> Iterator[None]:
        """Permit holdout reads for PRODUCTION REFIT, not evaluation.

        Distinct from `final_evaluation` on purpose. Once factor selection is
        frozen, refitting the chosen model on every available season (holdout
        included) is correct and costs nothing statistically -- no selection
        decision is being made from it. Logged separately so the audit trail
        distinguishes "we measured on the holdout" from "we trained the shipped
        model on everything".
        """
        if not reason or not reason.strip():
            raise ValueError("release_for_final_fit requires a non-empty reason")
        previous = getattr(_state, "reason", None)
        _state.reason = f"FINAL_FIT: {reason}"
        self._log("FINAL_FIT_OPENED", [self.season], reason)
        try:
            yield
        finally:
            _state.reason = previous
            self._log("FINAL_FIT_CLOSED", [self.season], reason)


def walk_forward_splits(
    seasons: Sequence[int] = CONSENSUS_SEASONS,
    holdout_season: int = HOLDOUT_SEASON,
    min_train: int = 2,
) -> List[Tuple[List[int], int]]:
    """[(train_seasons, test_season), ...] for rolling-origin evaluation.

    Every split trains strictly on the past and tests on the next season, so
    development decisions rest on forward-looking evaluations rather than
    in-sample fit. The holdout is excluded entirely.

    This is the answer to "one holdout season is N=1": it does not manufacture
    more data, but it does let several out-of-sample observations inform
    development without ever touching the locked season.
    """
    pool = sorted(s for s in seasons if s != holdout_season)
    splits = []
    for i in range(min_train, len(pool)):
        splits.append((pool[:i], pool[i]))
    return splits


DEFAULT_LOCK = HoldoutLock()
