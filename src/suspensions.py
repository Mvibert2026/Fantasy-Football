"""T4 (interim) -- known-suspension deduction. Deterministic, NOT a
probability model, per the founder's explicit instruction (FR-014,
FR-007) and thread 057's still-open status on whether a structured
suspension source exists at all.

This module has two independent pieces on purpose:
 1. A hand-curated fixture loader (`load_suspensions`) -- the interim data
    source. `tests/fixtures/suspensions_2026.json` is the current instance,
    and it is SYNTHETIC (see the fixture's own _comment): this session had
    no way to verify a real 2026 suspension list against the pipeline
    (post-training-cutoff, no ingested source), and the project's own rule
    ("do not fill gaps with plausible-sounding invention") forbids
    fabricating one. Whoever populates the real list (founder or
    researcher, per thread 057) plugs it in without changing anything
    below this point.
 2. The deterministic games-adjustment math, which does not care where the
    suspension list came from.

SEASON_GAMES=17 is the NFL's regular-season game count -- a schedule fact,
not a measured statistical constant, so it needs no SE/n.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Dict, Iterable, List, Optional, Tuple

SEASON_GAMES = 17

# Appeal statuses under which it is safe to apply a deterministic deduction:
# the games count is settled. "pending" (or anything else unrecognized)
# means the number could still change -- flag it, do not adjust.
_SETTLED_APPEAL_STATUSES = frozenset({"upheld", "confirmed", "served"})


def load_suspensions(fixture_path: Path) -> Dict[str, dict]:
    """Loads the suspension fixture, keyed by gsis_id."""
    data = json.loads(Path(fixture_path).read_text(encoding="utf-8"))
    return {row["gsis_id"]: row for row in data["suspensions"]}


def adjust_for_suspension(
    projected_points: float, games_missed: int, appeal_status: str
) -> Tuple[Optional[float], str]:
    """Returns (adjusted_points_or_None, reason). Deterministic: adjusted =
    projected * (games_played / SEASON_GAMES), floored at 0 games played.
    Only applied when appeal_status is settled -- a pending appeal is
    flagged upstream but the number is deliberately left None rather than
    guessing at a games count that could still change."""
    if appeal_status not in _SETTLED_APPEAL_STATUSES:
        return None, "not_adjusted_pending_appeal"
    games_played = max(SEASON_GAMES - games_missed, 0)
    adjusted = projected_points * (games_played / SEASON_GAMES)
    return adjusted, "games_adjusted"


def apply_suspension_flags(
    rows: Iterable[dict],
    suspensions: Dict[str, dict],
    gsis_key: str = "player_id_gsis",
    projected_key: str = "projected_points",
) -> List[dict]:
    """Adds suspension_flag / suspension_games /
    projected_points_suspension_adjusted / suspension_adjustment_note to
    every row (mutates a copy, returns a new list). Every row gets the same
    keys regardless of whether it's suspended -- an absent key on
    non-suspended rows would be exactly the kind of silent, conditional
    shape this project's export contract forbids elsewhere."""
    out = []
    for r in rows:
        r = dict(r)
        entry = suspensions.get(r.get(gsis_key))
        if entry is None:
            r["suspension_flag"] = False
            r["suspension_games"] = None
            r["projected_points_suspension_adjusted"] = None
            r["suspension_adjustment_note"] = "not_suspended"
        else:
            adjusted, reason = adjust_for_suspension(
                r.get(projected_key, 0.0), entry["games"], entry["appeal_status"]
            )
            r["suspension_flag"] = True
            r["suspension_games"] = entry["games"]
            r["projected_points_suspension_adjusted"] = adjusted
            r["suspension_adjustment_note"] = reason
        out.append(r)
    return out
