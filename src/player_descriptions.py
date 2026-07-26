"""
Player descriptions: 1-2 sentence plain-English text from an archetype
assignment (archetypes.py) plus the measured stats behind it. ADR-044.

DISPLAY-ONLY -- ENFORCED, NOT JUST DOCUMENTED. See
tests/test_player_descriptions.py's static-scan test: this module must never
be imported by narrate.py, scoring.py, make_board.py, backtest.py,
candidate_rankings.py, or export_contract.py's board-building path. A
description is never a Fact (ADR-027's Fact/Renderer contract has no
`player_description` Fact kind and none should be added), and never a model
input -- nothing here feeds `ReplacementLevels`, VBD, or the rank->points
curve.

DETERMINISTIC, NOT A LIVE LANGUAGE MODEL CALL. "ai_generated" (the
`license_tag` every description carries) describes the CONTENT's nature --
synthetic prose assembled by a program from measured data, never scraped or
adapted from a real scout's copyrighted text -- not a claim that an LLM API
was invoked at generation time. A live model call would make this
non-deterministic and untestable, contradicting "regeneratable from current
data, never hand-frozen" and "test-enforced": the same archetype assignment
must produce byte-identical text every time, which only a template-based
generator (matching ADR-027's precedent: Layer 1 facts are pure and
deterministic, an LLM-based Layer 2 renderer was explicitly deferred) can
guarantee.

UNDETERMINED PRODUCES NO DESCRIPTION. Not a placeholder sentence, not a
generic "not enough data" line attached to the player -- generate_description()
returns None outright. An invented plausible-sounding description for a
player the taxonomy could not classify is exactly the failure mode this
project's whole nulls.json/registered-null apparatus (ADR-027) exists to
avoid in the other direction.

NEVER FROM THIRD-PARTY SCOUTING TEXT. Every sentence here is templated from
archetype + measured stats (archetypes.ArchetypeAssignment) only -- no
external scouting-report text is read, stored, or paraphrased anywhere in
this module.
"""

from __future__ import annotations

import json
import sqlite3
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List, Optional

from archetypes import ArchetypeAssignment, assign_for_season

EXPORT_VERSION = "1.0.0"

LICENSE_TAG = "ai_generated"

# One entry per NON-undetermined archetype. {short_variant} slots are filled
# with the measured stat, rounded for readability -- never invented.
_TEMPLATES: Dict[str, str] = {
    "RB_BELL_COW": (
        "{name} is a true bell-cow back, handling {carry_pct} of his team's carries and "
        "playing {snap_pct} of the offensive snaps last season -- the kind of workload that "
        "makes weekly volume close to guaranteed."
    ),
    "RB_EARLY_DOWN": (
        "{name} is an early-down runner, carrying the ball on {carry_pct} of his team's rush "
        "attempts but drawing few targets ({target_pct} target share) -- his fantasy floor "
        "depends on rushing volume, not receiving work."
    ),
    "RB_PASSING_DOWN": (
        "{name} is a passing-down back: a light rushing role ({carry_pct} carry share) paired "
        "with real receiving usage ({target_pct} target share) makes him more valuable in "
        "reception-friendly formats than his carry count alone would suggest."
    ),
    "RB_COMMITTEE": (
        "{name} shares his backfield in a committee, at {carry_pct} carry share -- a real "
        "role, but one that depends on the rest of the room staying the same to keep its value."
    ),
    "WR_HIGH_VOLUME": (
        "{name} is a high-volume target earner, drawing {target_pct} of his team's targets "
        "while playing {snap_pct} of the offensive snaps -- the receiver a passing offense is "
        "built around."
    ),
    "WR_FIELD_STRETCHER": (
        "{name} is a field-stretcher, averaging {adot} air yards per target -- his role is "
        "built on getting downfield rather than high target volume, which raises his weekly "
        "variance."
    ),
    "WR_POSSESSION": (
        "{name} is a possession receiver, working underneath (aDOT {adot}) on a real target "
        "share ({target_pct}) with a heavy snap role ({snap_pct}) -- reliable, catch-driven "
        "production over big-play upside."
    ),
    "WR_ROTATIONAL": (
        "{name} played a rotational snap share ({snap_pct}) last season -- his role depends on "
        "beating out other receivers for playing time before target volume is even a question."
    ),
    "TE_PRIMARY_RECEIVER": (
        "{name} is his offense's primary receiving tight end, drawing {target_pct} of the "
        "team's targets on a {snap_pct} snap share -- a real receiving weapon at a thin "
        "fantasy position."
    ),
    "TE_SECONDARY_RECEIVER": (
        "{name} is a secondary receiving option at tight end ({target_pct} target share, "
        "{snap_pct} snap share) -- a real but limited passing-game role."
    ),
    "TE_BLOCKING": (
        "{name} plays a snap-heavy role ({snap_pct}) with little receiving usage ({target_pct} "
        "target share) -- his fantasy floor is thin outside of touchdown-dependent weeks."
    ),
}

_UNIMPLEMENTED_NOTE = "; RB_HANDCUFF is not implemented (needs a depth chart, see archetypes.py)"


def _pct(x: Optional[float]) -> str:
    return f"{x:.0%}" if x is not None else "n/a"


def _adot(x: Optional[float]) -> str:
    return f"{x:.1f}" if x is not None else "n/a"


@dataclass
class PlayerDescription:
    player_id: str
    player_name: str
    season: int
    position: str
    archetype: str
    confidence: str
    description: str
    license_tag: str
    generated_at: str
    source_stats: Dict[str, Optional[float]]


def generate_description(assignment: ArchetypeAssignment) -> Optional[PlayerDescription]:
    """None for any UNDETERMINED archetype, by construction -- no fallback
    text, no "we're not sure but" sentence. `generated_at` is the only
    non-deterministic field (a timestamp); `description` itself is a pure
    function of `assignment` and is byte-identical across regenerations
    (test-enforced)."""
    template = _TEMPLATES.get(assignment.archetype)
    if template is None:
        return None

    text = template.format(
        name=assignment.player_name,
        carry_pct=_pct(assignment.carry_share),
        target_pct=_pct(assignment.target_share),
        snap_pct=_pct(assignment.offense_pct),
        adot=_adot(assignment.adot),
    )
    return PlayerDescription(
        player_id=assignment.player_id, player_name=assignment.player_name,
        season=assignment.season, position=assignment.position,
        archetype=assignment.archetype, confidence=assignment.confidence,
        description=text, license_tag=LICENSE_TAG,
        generated_at=datetime.now(timezone.utc).isoformat(),
        source_stats={
            "carry_share": assignment.carry_share, "target_share": assignment.target_share,
            "offense_pct": assignment.offense_pct, "adot": assignment.adot,
            "games_qualified": assignment.games_qualified,
        },
    )


def generate_all_descriptions(
    conn: sqlite3.Connection, season: int, active_player_ids: Optional[Dict[str, str]] = None,
) -> List[PlayerDescription]:
    assignments = assign_for_season(conn, season, active_player_ids=active_player_ids)
    out = []
    for a in assignments:
        d = generate_description(a)
        if d is not None:
            out.append(d)
    return out


def export_player_descriptions_json(
    conn: sqlite3.Connection, season: int, out_path: Path,
    active_player_ids: Optional[Dict[str, str]] = None,
) -> Path:
    """A standalone artifact, deliberately NOT wired into export_contract.py's
    board.json build -- 'never a model input' is easier to keep true when the
    description pipeline has no import path into the board pipeline at all,
    not merely a promise not to read the field. Regeneratable: re-running
    this against the same DB state produces byte-identical `description`
    text for every player (generated_at excluded)."""
    descriptions = generate_all_descriptions(conn, season, active_player_ids=active_player_ids)
    payload = {
        "export_version": EXPORT_VERSION,
        "license_tag": LICENSE_TAG,
        "season": season,
        "generated_utc": datetime.now(timezone.utc).isoformat(),
        "note": (
            "Display-only. Never a Fact, never a model input -- see player_descriptions.py's "
            "module docstring (ADR-044). A player absent from this file has an UNDETERMINED "
            "archetype and no description exists for them; do not render a placeholder."
        ),
        "players": [asdict(d) for d in descriptions],
    }
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(payload, indent=2, allow_nan=False), encoding="utf-8")
    return out_path


def main() -> None:
    import argparse

    import db as dbmod

    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--season", type=int, default=2026)
    ap.add_argument(
        "--out", type=Path,
        default=Path(__file__).resolve().parent.parent / "data" / "export" / "player_descriptions.json",
    )
    args = ap.parse_args()

    conn = dbmod.connect()
    try:
        path = export_player_descriptions_json(conn, args.season, args.out)
    finally:
        conn.close()
    print(f"wrote {path}")


if __name__ == "__main__":
    main()
