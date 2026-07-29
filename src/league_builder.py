"""
Real league creation (thread 040 item 1).

WHY THIS EXISTS. The app previously offered two ways to get a LeagueConfig:
(1) `lc.CURRENT_LEAGUE`, the founder's own hardcoded league, or (2) one of the
24 pre-generated combinations in `generate_config_matrix.py`. Neither is
"define a league" -- a founder in a fifth real league with an odd roster
shape had no path to it short of hand-writing a LeagueConfig() call. This
module is that path: friendly parameters in (name, team count, roster shape,
scoring rules, draft slot), a saved, loadable LeagueConfig out, and an export
entrypoint that recomputes the board -- including replacement levels -- for
that config specifically.

THE CONSEQUENCE THIS MODULE MUST NOT GET WRONG. Replacement levels are
measured per format (ADR-029): RB30/WR40/TE10/QB10 is the founder's league's
answer, not a universal one. This module does not compute replacement levels
itself -- `scoring.ReplacementLevels.from_league_config` already does that
per-config arithmetic correctly (verified in tests/test_league_builder.py and
tests/test_multi_league_export.py) -- it exists so that path is reachable
from names and numbers a person would actually type into a form, instead of
only from a hand-built LeagueConfig in a Python REPL.

WHAT THIS DOES NOT DO. No API layer, no job queue, no polling, no tier-1/
tier-2 distinction, no "shadow recompute with atomic apply" -- that is the
Settings editor UI's contract (docs/design-handoff/settings/
SETTINGS-EDITOR-SPEC.md SS7), and no frontend agent is building that screen
this round. `export_league()` below is a synchronous, blocking recompute
(~7-10s per the existing config-matrix timing) -- exactly what `write_all`
already does for the 24 pre-generated configs -- not the background-job
contract the spec describes for an eventual API. A future API layer wraps
this function in a job; it does not replace it.
"""

from __future__ import annotations

import copy
import re
import sqlite3
from pathlib import Path
from typing import Dict, List, Optional, Tuple

import export_contract as ec
import export_static as es
import league_config as lc
from scoring import LEAGUE as _BASE_LEAGUE

_SLUG_DROP_RE = re.compile(r"['’]")  # apostrophes: drop, don't split on them
_SLUG_STRIP_RE = re.compile(r"[^a-z0-9]+")


def slugify(name: str) -> str:
    """Lowercase, underscore-joined identifier from a human-entered name."""
    s = _SLUG_DROP_RE.sub("", name.strip().lower())
    s = _SLUG_STRIP_RE.sub("_", s).strip("_")
    if not s:
        raise ValueError(f"name {name!r} has no usable characters for a league_id")
    return s


def unique_league_id(name: str, directory: Path = lc.LEAGUES_DIR) -> str:
    """Slug of `name`, disambiguated against existing saved configs in
    `directory` by an incrementing suffix. Never returns the reserved
    'primary' id -- that identity is the founder's own hardcoded league
    (`lc.CURRENT_LEAGUE`) and is not available to a newly created one."""
    base = slugify(name)
    if base == lc.PRIMARY_LEAGUE_ID:
        raise ValueError(
            f"league_id {base!r} derived from name {name!r} collides with the "
            f"reserved primary league id -- choose a different name"
        )
    directory = Path(directory)
    candidate = base
    n = 2
    while (directory / f"{candidate}.json").exists():
        candidate = f"{base}_{n}"
        n += 1
    return candidate


def build_scoring(ppr: float, scoring_overrides: Optional[Dict] = None) -> dict:
    """This project's existing scoring ruleset (`scoring.LEAGUE`) with the
    reception value swapped for `ppr` and any explicit `scoring_overrides`
    shallow-merged into the offense block. Deep-copied -- never mutates the
    shared `LEAGUE` module constant that every other league (including the
    primary one) still reads by reference."""
    cfg = copy.deepcopy(_BASE_LEAGUE)
    cfg["offense"]["receptions"] = ppr
    if scoring_overrides:
        for key, value in scoring_overrides.items():
            if key not in cfg["offense"]:
                raise ValueError(
                    f"scoring_overrides has unknown offense field {key!r}; valid "
                    f"fields are {sorted(cfg['offense'])}"
                )
            cfg["offense"][key] = value
    return cfg


def create_league(
    name: str,
    teams: int,
    starters: Dict[str, int],
    flex_slots: int,
    flex_eligible: Tuple[str, ...],
    bench: int,
    ir: int,
    user_draft_slot: int,
    *,
    platform: str = "other",
    draft_type: str = "snake",
    ppr: float = 0.5,
    scoring_overrides: Optional[Dict] = None,
    playoff_teams: int = 4,
    playoff_weeks: Tuple[int, ...] = (16, 17),
    reseeding: bool = False,
    trade_deadline: Optional[str] = None,
    faab_budget: Optional[int] = None,
    league_id: Optional[str] = None,
    directory: Path = lc.LEAGUES_DIR,
) -> lc.LeagueConfig:
    """Define and save a new league from founder-facing parameters.

    Deliberately does NOT accept `flex_split`: a new league's true flex split
    has not been measured (ADR-029 measured the founder's league specifically,
    over 26 seasons under ITS scoring). Leaving it unset means
    `ReplacementLevels.from_league_config` takes the explicit, flagged
    placeholder path (`measured=False`) rather than this module silently
    presenting a borrowed number as the new league's own.

    Raises ValueError (via LeagueConfig.validate()) for an inconsistent
    roster shape or an out-of-range draft slot -- no separate validation
    layer, the dataclass's own is authoritative and already tested.
    """
    resolved_id = league_id or unique_league_id(name, directory=directory)
    if resolved_id == lc.PRIMARY_LEAGUE_ID:
        raise ValueError(
            f"league_id {resolved_id!r} is reserved for the primary league"
        )

    cfg = lc.LeagueConfig(
        league_id=resolved_id,
        name=name,
        platform=platform,
        teams=teams,
        scoring=build_scoring(ppr, scoring_overrides),
        starters=dict(starters),
        flex_slots=flex_slots,
        flex_eligible=tuple(flex_eligible),
        bench=bench,
        ir=ir,
        user_draft_slot=user_draft_slot,
        draft_type=draft_type,
        playoff_teams=playoff_teams,
        playoff_weeks=tuple(playoff_weeks),
        reseeding=reseeding,
        trade_deadline=trade_deadline,
        faab_budget=faab_budget,
        # flex_split intentionally omitted -- see docstring.
    )
    cfg.save(directory=directory)
    return cfg


def export_league(
    cfg: lc.LeagueConfig, out_dir: Optional[Path], conn: sqlite3.Connection
) -> List[Path]:
    """Recompute and write board.json/league.json/availability.json/
    rosters.json for `cfg`, exactly the same pipeline the 24-config matrix
    and the primary league use (`export_contract.write_all`) -- so a newly
    created league's replacement levels, VBD, and tiers are computed for ITS
    format, not copied from any other league.

    ALSO writes glossary.json/nulls.json/opponents.json (`export_static.
    write_static_artifacts`) -- these are the three hand-authored/prose
    artifacts ADR-041 puts in every non-primary league's six-artifact
    directory (board/availability/league/glossary/nulls/opponents). This
    function used to skip them entirely, which is exactly the bug the
    founder hit switching to Ethan's Expert League 2026-07-29 (the frontend
    loader requires all six unconditionally, and only rosters/strategies are
    genuinely optional) -- see docs/handoffs/ and ADR-041 for the required
    set. No strategies.json (Monte Carlo) -- same scope line the 24-config
    matrix already draws, not a new limitation introduced here."""
    resolved_out = out_dir or ec.export_dir_for(cfg.league_id)
    written = ec.write_all(resolved_out, conn, cfg=cfg)
    written += es.write_static_artifacts(resolved_out, cfg)
    return written


def create_and_export_league(
    *,
    conn: sqlite3.Connection,
    out_dir: Optional[Path] = None,
    directory: Path = lc.LEAGUES_DIR,
    **create_kwargs,
) -> Tuple[lc.LeagueConfig, List[Path]]:
    """Convenience wrapper: create_league() then export_league() in one call.
    Kept separate underneath so callers needing just the config (e.g. a
    Settings-editor "preview my roster shape" step, tier-1 in the spec, which
    is instant/client-side and does not need a board recompute) can call
    create_league() alone."""
    cfg = create_league(directory=directory, **create_kwargs)
    written = export_league(cfg, out_dir, conn)
    return cfg, written
