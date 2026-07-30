"""
Raw Yahoo Fantasy API JSON -> provider-agnostic dataclasses (providers/base.py).

WHY THIS IS WRITTEN DEFENSIVELY, NOT AS FIXED-PATH ACCESSORS. Yahoo's
`format=json` responses encode what is fundamentally an XML document, which
produces deeply nested, index-keyed structures ("league" -> a list whose
items are single-key dicts, etc.) that are notoriously inconsistent in depth
across endpoints and have never been read directly in this project --
Yahoo hosts are not fetched here (CLAUDE.md's standing block on `*.yahoo.com`
for research agents, respected in this build too per the dispatch
instruction). Hard-coding exact positional paths against an unread response
would be exactly the "plausible-sounding invention" CLAUDE.md SS11 forbids.

Instead, every extraction here walks the whole structure recursively and
matches on the *signature key-set* a field is known to carry -- a roster
slot has both `position` and `count` together, a stat entry has both
`stat_id` and `value` together, a bonus has both `points` and `target`
together (verified field names, yfpy models.py, research doc SS3.1). This
degrades gracefully if the real nesting differs from any guess: it still
finds the data as long as Yahoo keeps those keys adjacent, which is true of
every documented JSON-from-XML API in this family regardless of depth.

Every parse failure is caught and recorded in `LeagureSettings.parse_warnings`
rather than raised -- a partially-populated result the founder can inspect
against `.raw` is more useful than a crash on the first real response, which
is exactly the response this module has never seen.
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional, Set

from providers.base import (  # noqa: F401  (re-exported for convenience at call sites)
    Bonus,
    DraftPick,
    DraftResult,
    LeagueSettings,
    RosterPositionSpec,
    StatModifier,
)


def _walk_dicts(obj: Any):
    if isinstance(obj, dict):
        yield obj
        for v in obj.values():
            yield from _walk_dicts(v)
    elif isinstance(obj, list):
        for item in obj:
            yield from _walk_dicts(item)


def _find_dicts_with_keys(obj: Any, required: Set[str]) -> List[dict]:
    return [d for d in _walk_dicts(obj) if required <= d.keys()]


def _find_first(obj: Any, key: str) -> Any:
    for d in _walk_dicts(obj):
        if key in d:
            return d[key]
    return None


def _as_int(value: Any, default: int = 0) -> int:
    try:
        return int(value)
    except (TypeError, ValueError):
        return default


def _as_float(value: Any, default: float = 0.0) -> float:
    try:
        return float(value)
    except (TypeError, ValueError):
        return default


def _as_bool(value: Any, default: bool = False) -> bool:
    if isinstance(value, bool):
        return value
    if value in (0, "0", "false", "False", None):
        return False
    if value in (1, "1", "true", "True"):
        return True
    return default


def _bool_strict(value: Any) -> bool:
    """Like _as_bool but raises on an unrecognized value, so callers that
    want a parse warning on genuine garbage (parse_league_settings' `_get`)
    can distinguish "unrecognized" from "legitimately false"."""
    if isinstance(value, bool):
        return value
    if value in (0, "0", "false", "False"):
        return False
    if value in (1, "1", "true", "True"):
        return True
    raise ValueError(f"not a recognized boolean: {value!r}")


def parse_roster_positions(raw: dict) -> List[RosterPositionSpec]:
    out = []
    for d in _find_dicts_with_keys(raw, {"position", "count"}):
        out.append(
            RosterPositionSpec(
                position=str(d.get("position", "")),
                count=_as_int(d.get("count")),
                is_starting_position=_as_bool(d.get("is_starting_position", True)),
                is_bench=str(d.get("position", "")).upper() in ("BN", "BENCH"),
            )
        )
    return out


def parse_stat_modifiers(raw: dict) -> List[StatModifier]:
    out = []
    for d in _find_dicts_with_keys(raw, {"stat_id", "value"}):
        bonuses = [
            Bonus(points=_as_float(b.get("points")), target=_as_float(b.get("target")))
            for b in _find_dicts_with_keys(d, {"points", "target"})
        ]
        out.append(
            StatModifier(
                stat_id=_as_int(d.get("stat_id")),
                name=str(d.get("name", d.get("stat_id", ""))),
                value=_as_float(d.get("value")),
                bonuses=bonuses,
            )
        )
    return out


def parse_league_settings(raw: dict, league_key: str, platform: str = "yahoo") -> LeagueSettings:
    """Best-effort parse. Never raises on a shape mismatch -- see module
    docstring. `raw` is always preserved in full on the result for audit."""
    warnings: List[str] = []

    def _get(key: str, coerce, default):
        val = _find_first(raw, key)
        if val is None:
            warnings.append(f"field '{key}' not found in response")
            return default
        try:
            return coerce(val)
        except (TypeError, ValueError):
            warnings.append(f"field '{key}' found but could not coerce: {val!r}")
            return default

    name = _get("name", str, "")
    max_teams = _get("max_teams", int, 0)
    scoring_type = _get("scoring_type", str, "")
    num_playoff_teams = _get("num_playoff_teams", int, 0)
    playoff_start_week = _get("playoff_start_week", int, 0)
    uses_playoff_reseeding = _get("uses_playoff_reseeding", _bool_strict, False)

    roster_positions = parse_roster_positions(raw)
    if not roster_positions:
        warnings.append("no roster_positions entries found (position+count key pair)")
    stat_modifiers = parse_stat_modifiers(raw)
    if not stat_modifiers:
        warnings.append("no stat_modifiers entries found (stat_id+value key pair)")

    return LeagueSettings(
        league_key=league_key,
        name=name,
        platform=platform,
        max_teams=max_teams,
        scoring_type=scoring_type,
        num_playoff_teams=num_playoff_teams,
        playoff_start_week=playoff_start_week,
        uses_playoff_reseeding=uses_playoff_reseeding,
        roster_positions=roster_positions,
        stat_modifiers=stat_modifiers,
        raw=raw,
        parse_warnings=warnings,
    )


def parse_draft_results(raw: dict, is_live_estimate: bool = False) -> DraftResult:
    """`is_live_estimate=True` marks a fetch made while a draft may still be
    in progress -- see providers/yahoo.py::get_live_draft_picks. The parsing
    logic is identical either way; only the caveat differs."""
    picks = []
    for d in _find_dicts_with_keys(raw, {"pick", "team_key", "player_key"}):
        picks.append(
            DraftPick(
                pick=_as_int(d.get("pick")),
                round=_as_int(d.get("round")),
                team_key=str(d.get("team_key", "")),
                player_key=str(d.get("player_key", "")),
                cost=_as_float(d["cost"]) if d.get("cost") is not None else None,
            )
        )
    caveat = None
    if is_live_estimate:
        caveat = (
            "Fetched during a possibly-in-progress draft. Reading picks mid-draft rests on a "
            "single, undated SDK docstring (docs/research/yahoo-espn-league-connection-"
            "2026-07-30.md SS3.3) -- latency and Yahoo's tolerance for polling are unverified. "
            "Treat as an estimate; do not build auto-pick logic on top of it."
        )
    return DraftResult(picks=picks, is_live_estimate=is_live_estimate, caveat=caveat)


def diff_against_claude_md_westwood(settings: LeagueSettings) -> List[str]:
    """Compare a fetched settings snapshot against CLAUDE.md SS7's
    hand-verified Westwood table. Returns a list of human-readable
    discrepancy lines, empty if everything checked matches. Intended for
    scripts/yahoo_pull_league_settings.py's report output -- the "free
    correctness audit" the research doc recommends running first (SS2.4).
    Only checks fields CLAUDE.md states as verified; does not invent a
    comparison for fields it doesn't cover.
    """
    lines: List[str] = []
    if settings.max_teams and settings.max_teams != 10:
        lines.append(f"max_teams: CLAUDE.md says 10, Yahoo says {settings.max_teams}")
    if settings.num_playoff_teams and settings.num_playoff_teams != 4:
        lines.append(
            f"num_playoff_teams: CLAUDE.md says 4, Yahoo says {settings.num_playoff_teams}"
        )
    if settings.playoff_start_week and settings.playoff_start_week != 16:
        lines.append(
            f"playoff_start_week: CLAUDE.md says 16, Yahoo says {settings.playoff_start_week}"
        )
    if settings.uses_playoff_reseeding:
        lines.append("uses_playoff_reseeding: CLAUDE.md says no reseeding, Yahoo says True")
    bonus_stats = [sm for sm in settings.stat_modifiers if sm.bonuses]
    if settings.stat_modifiers and not bonus_stats:
        lines.append(
            "no stat carries a Bonus entry -- CLAUDE.md's stacking yardage bonuses did not "
            "populate (see research doc gap 4: unconfirmed whether Stat.bonuses populates "
            "for football leagues)"
        )
    return lines
