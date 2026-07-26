"""
Player archetype assignment, per archetype_taxonomy.md (the Strategist's
brief, supplied by the user 2026-07-26). ADR-044.

ARCHETYPES ARE t-1 LABELS. An archetype for DRAFT season S is computed from
season S-1's actual usage -- assigning a 2026 archetype from 2026 data would
be look-ahead (CLAUDE.md SS6.1). `assign_for_season(target_season)` only ever
reads `target_season - 1`.

ROOKIES ARE UNDETERMINED BY CONSTRUCTION. No prior season exists to compute
usage from. `assign_for_season()` returns UNDETERMINED with reason='rookie'
for any player absent from the prior season's data entirely -- not a
zero-share player, which is a different (and real) case.

EVERY ENUM CLOSES WITH UNDETERMINED. A player meeting no criteria gets that
label, never the nearest-looking one -- per the taxonomy's own SS0: "Forcing
assignment is how a taxonomy becomes vibes."

DATA FLOOR: 2013 (offense_pct/snap_counts start then; the taxonomy's own
"binding floor for any archetype using both targets and snaps"). Any
target_season where target_season-1 < 2013 refuses outright, UNDETERMINED
with reason='data_floor' for every player -- not zero-filled, not skipped
silently.

CONFIDENCE, per the taxonomy's SS4 output schema: high if games_qualified>=12,
medium if 8-11, forced UNDETERMINED below 8 regardless of what the shares
would otherwise indicate.

NOT IMPLEMENTED, NAMED NOT PATCHED: RB_HANDCUFF. The taxonomy itself flags it
as needing a preseason depth chart, unavailable on any development season,
and explicitly says "treat separately from the other five." A player who
would otherwise qualify as a handcuff (offense_pct<0.25, low volume) falls
through to RB_UNDETERMINED here rather than a guessed HANDCUFF label. Building
the depth-chart-linked check (including "is the rank-1 teammate BELL_COW")
is real, scoped-out remaining work.

THRESHOLDS ARE THE TAXONOMY'S CONVENTIONS, NOT INDEPENDENTLY VERIFIED HERE.
The brief says so itself (SS1): "I have not measured those breaks... before
use, plot the actual distributions and check the thresholds land in valleys
rather than mid-mass." That verification pass was not performed this
session -- implemented exactly as specified, not re-derived.
"""

from __future__ import annotations

import sqlite3
from dataclasses import dataclass
from datetime import date, datetime, timezone
from typing import Dict, List, Optional, Tuple

DATA_FLOOR_SEASON = 2013
MIN_GAMES_FOR_ANY_CONFIDENCE = 8
MIN_GAMES_FOR_HIGH_CONFIDENCE = 12

RB_ARCHETYPES = (
    "RB_BELL_COW", "RB_EARLY_DOWN", "RB_PASSING_DOWN", "RB_COMMITTEE",
    "RB_HANDCUFF", "RB_UNDETERMINED",
)
WR_ARCHETYPES = ("WR_HIGH_VOLUME", "WR_FIELD_STRETCHER", "WR_POSSESSION",
                  "WR_ROTATIONAL", "WR_UNDETERMINED")
TE_ARCHETYPES = ("TE_PRIMARY_RECEIVER", "TE_SECONDARY_RECEIVER", "TE_BLOCKING",
                  "TE_UNDETERMINED")


@dataclass
class PlayerSeasonInputs:
    player_id: str
    player_name: str
    position: str
    season: int  # the DATA season (target_season - 1)
    carry_share: Optional[float]
    target_share: Optional[float]
    offense_pct: Optional[float]
    adot: Optional[float]
    games_qualified: int


@dataclass
class ArchetypeAssignment:
    """Exactly the taxonomy's SS4 output schema."""
    player_id: str
    player_name: str
    season: int  # the DRAFT/target season the archetype applies to
    position: str
    archetype: str
    confidence: str  # "high" | "medium" | "undetermined"
    games_qualified: int
    carry_share: Optional[float]
    target_share: Optional[float]
    offense_pct: Optional[float]
    adot: Optional[float]
    depth_rank: Optional[int]  # always None -- RB_HANDCUFF not implemented
    cutoff_date: str
    reason: Optional[str] = None  # populated for UNDETERMINED: why


def _gsis_to_pfr(conn: sqlite3.Connection) -> Dict[str, str]:
    """gsis_id -> pfr_id, via the ADR-036 identity hub -- collision-excluded
    on both legs, same as every other cross-source join in this project."""
    rows = conn.execute(
        "SELECT g.source_id, p.source_id FROM player_ids g "
        "JOIN player_ids p ON g.mfl_id = p.mfl_id "
        "WHERE g.source='gsis' AND p.source='pfr'"
    ).fetchall()
    return {gsis: pfr for gsis, pfr in rows}


def compute_player_season_inputs(
    conn: sqlite3.Connection, data_season: int, positions: Tuple[str, ...] = ("RB", "WR", "TE"),
) -> List[PlayerSeasonInputs]:
    """Usage shares for every RB/WR/TE active in `data_season`. This is the
    DATA season, not the draft season -- callers wanting a 2026 archetype
    pass data_season=2025 (assign_for_season() does this translation).
    """
    if data_season < DATA_FLOOR_SEASON:
        return []

    weekly = conn.execute(
        "SELECT player_id, player_display_name, position, team, week, carries, targets, "
        "receiving_air_yards FROM player_weekly_stats "
        "WHERE season=? AND season_type='REG' AND position IN (%s)"
        % ",".join("?" * len(positions)),
        (data_season, *positions),
    ).fetchall()
    if not weekly:
        return []

    # Team-week totals (denominators), summed across EVERY offensive player
    # on the roster that week, not just RB/WR/TE -- a QB's carries/targets
    # still count toward the team total a back's carry_share is measured
    # against.
    team_week_totals = conn.execute(
        "SELECT team, week, SUM(carries) c, SUM(targets) t FROM player_weekly_stats "
        "WHERE season=? AND season_type='REG' GROUP BY team, week",
        (data_season,),
    ).fetchall()
    team_carries: Dict[Tuple[str, int], float] = {}
    team_targets: Dict[Tuple[str, int], float] = {}
    for team, week, c, t in team_week_totals:
        team_carries[(team, week)] = c or 0
        team_targets[(team, week)] = t or 0

    gsis_to_pfr = _gsis_to_pfr(conn)
    pfr_ids = set(gsis_to_pfr.values())
    snaps = conn.execute(
        "SELECT pfr_player_id, week, offense_pct FROM snap_counts WHERE season=? "
        "AND game_type='REG'",
        (data_season,),
    ).fetchall()
    offense_pct_by_pfr_week: Dict[Tuple[str, int], float] = {
        (pfr, wk): pct for pfr, wk, pct in snaps if pfr in pfr_ids
    }

    by_player: Dict[str, dict] = {}
    for player_id, name, pos, team, week, carries, targets, air_yards in weekly:
        agg = by_player.setdefault(player_id, {
            "name": name, "position": pos, "carries": 0.0, "targets": 0.0,
            "air_yards": 0.0, "team_carries": 0.0, "team_targets": 0.0,
            "offense_pcts": [],
        })
        agg["carries"] += carries or 0
        agg["targets"] += targets or 0
        agg["air_yards"] += air_yards or 0
        agg["team_carries"] += team_carries.get((team, week), 0)
        agg["team_targets"] += team_targets.get((team, week), 0)
        pfr = gsis_to_pfr.get(player_id)
        if pfr:
            pct = offense_pct_by_pfr_week.get((pfr, week))
            if pct is not None:
                agg["offense_pcts"].append(pct)

    out = []
    for player_id, agg in by_player.items():
        carry_share = agg["carries"] / agg["team_carries"] if agg["team_carries"] else None
        target_share = agg["targets"] / agg["team_targets"] if agg["team_targets"] else None
        adot = agg["air_yards"] / agg["targets"] if agg["targets"] else None
        offense_pct = (
            sum(agg["offense_pcts"]) / len(agg["offense_pcts"]) if agg["offense_pcts"] else None
        )
        games_qualified = sum(1 for p in agg["offense_pcts"] if p > 0)
        out.append(PlayerSeasonInputs(
            player_id=player_id, player_name=agg["name"], position=agg["position"],
            season=data_season, carry_share=carry_share, target_share=target_share,
            offense_pct=offense_pct, adot=adot, games_qualified=games_qualified,
        ))
    return out


def _confidence(games_qualified: int) -> str:
    if games_qualified >= MIN_GAMES_FOR_HIGH_CONFIDENCE:
        return "high"
    if games_qualified >= MIN_GAMES_FOR_ANY_CONFIDENCE:
        return "medium"
    return "undetermined"


def assign_rb_archetype(carry_share, target_share, offense_pct, games_qualified) -> Tuple[str, str]:
    """Evaluation order matters (taxonomy SS1): BELL_COW -> PASSING_DOWN ->
    EARLY_DOWN -> COMMITTEE -> HANDCUFF. HANDCUFF is not implemented (needs a
    depth chart) -- a player who would qualify falls through to UNDETERMINED."""
    conf = _confidence(games_qualified)
    if conf == "undetermined" or None in (carry_share, target_share, offense_pct):
        return "RB_UNDETERMINED", "undetermined"
    if offense_pct >= 0.60 and carry_share >= 0.55 and target_share >= 0.07:
        return "RB_BELL_COW", conf
    if carry_share < 0.30 and target_share >= 0.09:
        return "RB_PASSING_DOWN", conf
    if carry_share >= 0.40 and target_share < 0.06:
        return "RB_EARLY_DOWN", conf
    if 0.25 <= carry_share < 0.55:
        return "RB_COMMITTEE", conf
    return "RB_UNDETERMINED", conf


def assign_wr_archetype(target_share, offense_pct, adot, games_qualified) -> Tuple[str, str]:
    conf = _confidence(games_qualified)
    if conf == "undetermined" or None in (target_share, offense_pct, adot):
        return "WR_UNDETERMINED", "undetermined"
    if target_share >= 0.22 and offense_pct >= 0.70:
        return "WR_HIGH_VOLUME", conf
    if adot >= 13.0 and target_share < 0.22:
        return "WR_FIELD_STRETCHER", conf
    if adot < 9.5 and target_share >= 0.13 and offense_pct >= 0.60:
        return "WR_POSSESSION", conf
    if offense_pct < 0.55:
        return "WR_ROTATIONAL", conf
    return "WR_UNDETERMINED", conf


def assign_te_archetype(target_share, offense_pct, games_qualified) -> Tuple[str, str]:
    conf = _confidence(games_qualified)
    if conf == "undetermined" or None in (target_share, offense_pct):
        return "TE_UNDETERMINED", "undetermined"
    if target_share >= 0.18 and offense_pct >= 0.65:
        return "TE_PRIMARY_RECEIVER", conf
    if 0.08 <= target_share < 0.18 and offense_pct >= 0.50:
        return "TE_SECONDARY_RECEIVER", conf
    if target_share < 0.08 and offense_pct >= 0.45:
        return "TE_BLOCKING", conf
    return "TE_UNDETERMINED", conf


def _assign_one(inputs: PlayerSeasonInputs, target_season: int, cutoff_date: str) -> ArchetypeAssignment:
    if inputs.position == "RB":
        archetype, confidence = assign_rb_archetype(
            inputs.carry_share, inputs.target_share, inputs.offense_pct, inputs.games_qualified
        )
    elif inputs.position == "WR":
        archetype, confidence = assign_wr_archetype(
            inputs.target_share, inputs.offense_pct, inputs.adot, inputs.games_qualified
        )
    elif inputs.position == "TE":
        archetype, confidence = assign_te_archetype(
            inputs.target_share, inputs.offense_pct, inputs.games_qualified
        )
    else:
        raise ValueError(f"no taxonomy for position {inputs.position!r}")

    reason = None
    if confidence == "undetermined":
        reason = f"insufficient games ({inputs.games_qualified} < {MIN_GAMES_FOR_ANY_CONFIDENCE})"

    return ArchetypeAssignment(
        player_id=inputs.player_id, player_name=inputs.player_name, season=target_season,
        position=inputs.position, archetype=archetype, confidence=confidence,
        games_qualified=inputs.games_qualified, carry_share=inputs.carry_share,
        target_share=inputs.target_share, offense_pct=inputs.offense_pct, adot=inputs.adot,
        depth_rank=None, cutoff_date=cutoff_date, reason=reason,
    )


_UNDETERMINED_LABEL = {"RB": "RB_UNDETERMINED", "WR": "WR_UNDETERMINED", "TE": "TE_UNDETERMINED"}


def _undetermined(player_id: str, position: str, target_season: int, cutoff_date: str, reason: str) -> ArchetypeAssignment:
    return ArchetypeAssignment(
        player_id=player_id, player_name="", season=target_season, position=position,
        archetype=_UNDETERMINED_LABEL.get(position, "UNDETERMINED"), confidence="undetermined",
        games_qualified=0, carry_share=None, target_share=None, offense_pct=None, adot=None,
        depth_rank=None, cutoff_date=cutoff_date, reason=reason,
    )


def assign_for_season(
    conn: sqlite3.Connection, target_season: int,
    active_player_ids: Optional[Dict[str, str]] = None,
    cutoff_date: Optional[str] = None,
) -> List[ArchetypeAssignment]:
    """Archetypes for `target_season`, computed from `target_season - 1`
    actuals (t-1 labels). `active_player_ids` ({player_id: position}, e.g.
    this season's board) lets a caller include ROOKIES explicitly as
    UNDETERMINED-by-construction rather than silently absent -- a rookie has
    no row in the prior season at all, a real and different case from a
    returning player with low exposure.
    """
    data_season = target_season - 1
    cutoff_date = cutoff_date or date.today().isoformat()

    if data_season < DATA_FLOOR_SEASON:
        return [
            _undetermined(pid, pos, target_season, cutoff_date,
                          f"data floor: {data_season} < {DATA_FLOOR_SEASON}")
            for pid, pos in (active_player_ids or {}).items()
        ]

    inputs = compute_player_season_inputs(conn, data_season)
    assigned = [_assign_one(i, target_season, cutoff_date) for i in inputs]

    if active_player_ids is not None:
        seen = {a.player_id for a in assigned}
        for pid, pos in active_player_ids.items():
            if pid not in seen:
                assigned.append(_undetermined(pid, pos, target_season, cutoff_date, "rookie"))
    return assigned
