"""
Layer 1 of the narration stack: DETERMINISTIC FACT EXTRACTION.

No LLM. No network. No prose composition. This module turns draft state plus the
Block 7 export artifacts into a list of `Fact` objects, each carrying a stable
id, a resolvable path into the exports, a numeric value, and a plain-language
template.

WHY THE SPLIT EXISTS. A language model asked to narrate a draft will produce
fluent, confident, causal sentences whether or not the underlying data supports
them -- "he's falling because the room is scared of his workload" is exactly the
kind of claim this project spends its effort NOT making. So the model never sees
the data. It sees Facts, and its contract forbids introducing any claim,
comparison, or causal reasoning not already present in one.

THE CONTRACT, in full:
  - Layer 1 (this module) may compute. It may not editorialise.
  - Layer 2 (renderer, later) may reword a Fact's `template`. It may NOT
    introduce a new claim, a comparison between Facts, a cause, a prediction, or
    a recommendation that is not already a Fact.
  - Every rendered sentence must be traceable to exactly one `Fact.id`.
  - Every Fact's `source_path` must resolve against a real field in the exports.
    A Fact whose path does not resolve raises rather than being emitted, so a
    stale export can never silently produce confident fiction.

CONFIDENCE IS PART OF THE FACT. Availability numbers never pass through the
ADR-016 projection curve and are the most reliable output in the project.
Projection- and VBD-derived numbers run through a curve whose R-squared is
0.16-0.27. Facts carry that distinction so the renderer can hedge correctly
instead of flattening everything into the same confident register.
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional, Sequence

EXPORT_DIR = Path(__file__).resolve().parent.parent / "data" / "export"

CONFIDENCE_HIGH = "high"      # availability: no projection curve involved
CONFIDENCE_MEDIUM = "medium"  # structural: arithmetic about league rules
CONFIDENCE_LOW = "low"        # projection/VBD: R-squared 0.16-0.27


class SourcePathError(KeyError):
    """A Fact referenced an export field that does not exist."""


@dataclass(frozen=True)
class Fact:
    """One atomic, sourced, numeric claim.

    `template` is plain language with `{}`-style placeholders drawn from
    `params`. It is a *starting* wording, not a mandated one -- the renderer may
    rephrase it, but may not add anything to it.
    """

    id: str
    kind: str
    source_path: str
    value: Optional[float]
    template: str
    params: Dict[str, Any] = field(default_factory=dict)
    confidence: str = CONFIDENCE_MEDIUM

    def render_template(self) -> str:
        return self.template.format(**self.params)


# --------------------------------------------------------------------------
# Export loading and path resolution
# --------------------------------------------------------------------------


def load_exports(export_dir: Path = EXPORT_DIR) -> Dict[str, Any]:
    out: Dict[str, Any] = {}
    for name in ("board.json", "availability.json", "strategies.json",
                 "opponents.json", "nulls.json", "league.json", "glossary.json"):
        p = export_dir / name
        if p.exists():
            out[name] = json.loads(p.read_text(encoding="utf-8"))
    return out


def resolve_path(exports: Dict[str, Any], source_path: str) -> Any:
    """Resolve `"artifact.json:dotted.path"` against loaded exports.

    Raises SourcePathError rather than returning None, so a Fact can never be
    emitted against a field that has moved or been removed. List indices are
    written as integers in the dotted path.
    """
    if ":" not in source_path:
        raise SourcePathError(f"malformed source_path {source_path!r} (expected 'file.json:path')")
    artifact, _, dotted = source_path.partition(":")
    if artifact not in exports:
        raise SourcePathError(f"artifact {artifact!r} not loaded (path {source_path!r})")
    node: Any = exports[artifact]
    for part in filter(None, dotted.split(".")):
        if isinstance(node, list):
            try:
                node = node[int(part)]
            except (ValueError, IndexError) as e:
                raise SourcePathError(f"cannot index list with {part!r} in {source_path!r}") from e
        elif isinstance(node, dict):
            if part not in node:
                raise SourcePathError(f"key {part!r} missing in {source_path!r}")
            node = node[part]
        else:
            raise SourcePathError(f"cannot descend into {type(node).__name__} at {part!r}")
    return node


def validate_facts(facts: Sequence[Fact], exports: Dict[str, Any]) -> None:
    """Every Fact's source_path must resolve. Raises on the first that does not."""
    for f in facts:
        resolve_path(exports, f.source_path)


# --------------------------------------------------------------------------
# Draft state
# --------------------------------------------------------------------------


@dataclass
class DraftState:
    """Minimal, JSON-friendly view of a draft in progress."""

    pick_number: int
    taken_players: List[str] = field(default_factory=list)
    my_roster: List[str] = field(default_factory=list)
    rosters_by_slot: Dict[int, List[str]] = field(default_factory=dict)
    considering: Optional[str] = None  # player under consideration, for reach cost


# --------------------------------------------------------------------------
# Fact extractors
# --------------------------------------------------------------------------


def _board_index(board: Dict[str, Any]) -> Dict[str, Dict[str, Any]]:
    return {p["player"]: p for p in board.get("players", [])}


def tier_survival_facts(
    state: DraftState, exports: Dict[str, Any], sigma_key: str = "sigma_10"
) -> List[Fact]:
    """How each tier's survival odds shift from this pick to the user's next."""
    avail = exports.get("availability.json")
    if not avail:
        return []
    picks = avail["metadata"]["user_picks"]
    later = [p for p in picks if p > state.pick_number]
    if not later:
        return []
    here = state.pick_number if state.pick_number in picks else None
    nxt = later[0]

    facts: List[Fact] = []
    for pos, tiers in avail.get("by_tier", {}).items():
        for tier, per_pick in tiers.items():
            nxt_key = str(nxt)
            if nxt_key not in per_pick or sigma_key not in per_pick[nxt_key]:
                continue
            p_next = per_pick[nxt_key][sigma_key]
            path = f"availability.json:by_tier.{pos}.{tier}.{nxt_key}.{sigma_key}"
            if here is not None and str(here) in per_pick:
                p_here = per_pick[str(here)][sigma_key]
                drop = p_here - p_next
                facts.append(Fact(
                    id=f"tier_survival_shift.{pos}.{tier}.{here}_to_{nxt}",
                    kind="tier_survival_shift",
                    source_path=path,
                    value=round(drop, 4),
                    template=(
                        "The chance at least one {pos} {tier} player is still available falls "
                        "from {p_here:.0%} now to {p_next:.0%} at your next pick ({nxt})."
                    ),
                    params={"pos": pos, "tier": tier, "p_here": p_here,
                            "p_next": p_next, "nxt": nxt},
                    confidence=CONFIDENCE_HIGH,
                ))
            else:
                facts.append(Fact(
                    id=f"tier_survival.{pos}.{tier}.pick{nxt}",
                    kind="tier_survival",
                    source_path=path,
                    value=round(p_next, 4),
                    template=(
                        "There is a {p_next:.0%} chance at least one {pos} {tier} player is "
                        "still there at pick {nxt}."
                    ),
                    params={"pos": pos, "tier": tier, "p_next": p_next, "nxt": nxt},
                    confidence=CONFIDENCE_HIGH,
                ))
    return facts


def replacement_crossing_facts(state: DraftState, exports: Dict[str, Any]) -> List[Fact]:
    """Positions where the best player left is at or past replacement level.

    Crossing replacement means the next player at that position is worth roughly
    what a waiver pickup is worth -- the position has stopped being scarce.
    """
    board = exports.get("board.json")
    league = exports.get("league.json")
    if not board or not league:
        return []
    levels = league["replacement_levels"]
    taken = set(state.taken_players)
    best: Dict[str, Dict[str, Any]] = {}
    for p in board["players"]:
        if p["player"] in taken or p["positional_rank"] is None:
            continue
        cur = best.get(p["position"])
        if cur is None or p["positional_rank"] < cur["positional_rank"]:
            best[p["position"]] = p

    facts: List[Fact] = []
    for pos, level in levels.items():
        b = best.get(pos)
        if b is None:
            continue
        crossed = b["positional_rank"] > level
        facts.append(Fact(
            id=f"replacement_crossing.{pos}.pick{state.pick_number}",
            kind="replacement_level_crossing",
            source_path=f"league.json:replacement_levels.{pos}",
            value=float(b["positional_rank"] - level),
            template=(
                "The best {pos} left is {label}, and this league's replacement level is "
                "{pos}{level} — so the {pos} position is {status}."
            ),
            params={
                "pos": pos, "label": b["positional_label"], "level": level,
                "status": ("already past the point where the next one is close to "
                           "freely available" if crossed
                           else "still ahead of freely-available quality"),
            },
            confidence=CONFIDENCE_MEDIUM,
        ))
    return facts


def reach_cost_facts(state: DraftState, exports: Dict[str, Any]) -> List[Fact]:
    """What taking `considering` costs against the board's best available."""
    board = exports.get("board.json")
    if not board or not state.considering:
        return []
    idx = _board_index(board)
    target = idx.get(state.considering)
    if target is None:
        return []
    taken = set(state.taken_players)
    remaining = [p for p in board["players"] if p["player"] not in taken]
    if not remaining:
        return []
    best = min(remaining, key=lambda p: p["overall_rank"])
    if best["player"] == target["player"]:
        return [Fact(
            id=f"reach_cost.{target['player']}.pick{state.pick_number}",
            kind="reach_cost",
            source_path=f"board.json:players.{board['players'].index(target)}.vbd",
            value=0.0,
            template="{player} is the top player left on our board, so there is no reach cost.",
            params={"player": target["player"]},
            confidence=CONFIDENCE_LOW,
        )]
    cost = best["vbd"] - target["vbd"]
    return [Fact(
        id=f"reach_cost.{target['player']}.pick{state.pick_number}",
        kind="reach_cost",
        source_path=f"board.json:players.{board['players'].index(target)}.vbd",
        value=round(cost, 2),
        template=(
            "Taking {player} instead of {best} gives up about {cost:.0f} points of value "
            "over replacement on our board. Our projections are weak, so treat this as a "
            "rough size, not a precise price."
        ),
        params={"player": target["player"], "best": best["player"], "cost": cost},
        confidence=CONFIDENCE_LOW,
    )]


def opponent_need_facts(state: DraftState, exports: Dict[str, Any]) -> List[Fact]:
    """Starting slots each opponent has not yet filled, inferred from their picks.

    Inference is from THIS draft only. Seven of nine opponents have no historical
    profile (opponents.json coverage_warning), so no tendency is asserted.
    """
    board = exports.get("board.json")
    opps = exports.get("opponents.json")
    league = exports.get("league.json")
    if not (board and opps and league):
        return []
    idx = _board_index(board)
    starters = {k: v for k, v in league["roster"]["starters"].items()
                if k in ("QB", "RB", "WR", "TE")}

    facts: List[Fact] = []
    for i, opp in enumerate(opps["opponents"]):
        slot = opp["draft_slot_2026"]
        roster = state.rosters_by_slot.get(slot, [])
        counts: Dict[str, int] = {}
        for name in roster:
            p = idx.get(name)
            if p:
                counts[p["position"]] = counts.get(p["position"], 0) + 1
        unfilled = [pos for pos, need in starters.items() if counts.get(pos, 0) < need]
        if not unfilled:
            continue
        label = opp["team_name"] or f"the team at slot {slot}"
        facts.append(Fact(
            id=f"opponent_need.slot{slot}.pick{state.pick_number}",
            kind="opponent_need",
            source_path=f"opponents.json:opponents.{i}.draft_slot_2026",
            value=float(len(unfilled)),
            template=(
                "{label} has not yet filled {unfilled} in their starting lineup, based on "
                "picks made so far in this draft."
            ),
            params={"label": label, "unfilled": ", ".join(unfilled)},
            confidence=CONFIDENCE_MEDIUM,
        ))
    return facts


def null_result_facts(exports: Dict[str, Any]) -> List[Fact]:
    """Registered negative results, so the renderer can say 'no evidence for X'
    instead of improvising a rationale."""
    nulls = exports.get("nulls.json")
    if not nulls:
        return []
    return [
        Fact(
            id=f"registered_null.{n['id']}",
            kind="registered_null",
            source_path=f"nulls.json:findings.{i}.result",
            value=None,
            template="We tested this and found no evidence: {claim}. {summary}",
            params={"claim": n["claim_tested"], "summary": n["plain_language_summary"]},
            confidence=CONFIDENCE_HIGH,
        )
        for i, n in enumerate(nulls.get("findings", []))
    ]


def extract_facts(
    state: DraftState,
    exports: Optional[Dict[str, Any]] = None,
    export_dir: Path = EXPORT_DIR,
    sigma_key: str = "sigma_10",
) -> List[Fact]:
    """The pure function. Deterministic: same inputs, same Facts, same order."""
    exports = exports if exports is not None else load_exports(export_dir)
    facts: List[Fact] = []
    facts.extend(tier_survival_facts(state, exports, sigma_key))
    facts.extend(replacement_crossing_facts(state, exports))
    facts.extend(reach_cost_facts(state, exports))
    facts.extend(opponent_need_facts(state, exports))
    facts.extend(null_result_facts(exports))
    validate_facts(facts, exports)
    return facts


# --------------------------------------------------------------------------
# Layer 2 contract guard (the renderer itself is not built yet)
# --------------------------------------------------------------------------


class RenderContractError(TypeError):
    """The render layer was handed something that is not a list of Facts."""


def validate_render_input(candidate: Any) -> List[Fact]:
    """Gate every renderer entry point.

    The renderer must never receive raw exports, a draft state, a dict, or a
    string -- only Facts. Anything else would let it reason from source data and
    invent claims, which is precisely what this architecture prevents.
    """
    if isinstance(candidate, Fact) or not isinstance(candidate, (list, tuple)):
        raise RenderContractError(
            f"render layer requires a list of Fact objects, got {type(candidate).__name__}"
        )
    bad = [type(x).__name__ for x in candidate if not isinstance(x, Fact)]
    if bad:
        raise RenderContractError(
            f"render layer requires Fact objects; found {sorted(set(bad))} in the list"
        )
    return list(candidate)


def render_reference(facts: Any) -> List[Dict[str, str]]:
    """Reference renderer: pure template substitution, no rewording.

    This is NOT the LLM renderer. It exists so the contract is testable -- every
    sentence it emits carries the id of the single Fact that produced it.
    """
    validated = validate_render_input(facts)
    return [{"fact_id": f.id, "confidence": f.confidence, "sentence": f.render_template()}
            for f in validated]
