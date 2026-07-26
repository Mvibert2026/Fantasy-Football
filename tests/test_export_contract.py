import json
from pathlib import Path

import pytest

EXPORT = Path(__file__).resolve().parent.parent / "data" / "export"


def _load(name):
    p = EXPORT / name
    if not p.exists():
        pytest.skip(f"{name} not generated")
    return json.loads(p.read_text(encoding="utf-8"))


@pytest.mark.requires_db
def test_attribution_is_exactly_additive():
    """The design handoff's hard requirement: the player panel renders
    consensus_rank - structural - evaluative = overall_rank. If these do not
    reconcile the differentiating feature reads as broken, so it is asserted
    here rather than trusted."""
    board = _load("board.json")
    assert board["attribution_is_additive"] is True
    for p in board["players"]:
        lhs = p["consensus_rank"] - p["structural_adjustment"] - p["evaluative_adjustment"]
        assert lhs == p["overall_rank"], (
            f"attribution does not reconcile for {p['player']}: "
            f"{p['consensus_rank']} - {p['structural_adjustment']} - "
            f"{p['evaluative_adjustment']} != {p['overall_rank']}"
        )


@pytest.mark.requires_db
def test_structural_breakdown_sums_to_structural_adjustment():
    board = _load("board.json")
    for p in board["players"]:
        b = p["structural_breakdown"]
        assert b["replacement_levels"] + b["scoring_and_vbd_method"] == p["structural_adjustment"]


@pytest.mark.requires_db
def test_evaluative_is_zero_and_flagged_unavailable():
    """Zero keeps the additivity identity true; the flag stops the UI rendering
    a meaningless '+0 evaluative' row for every player."""
    board = _load("board.json")
    for p in board["players"]:
        assert p["evaluative_adjustment"] == 0
        assert p["evaluative_adjustment_available"] is False
        assert "SUPPRESS" in p["evaluative_adjustment_note"]


@pytest.mark.requires_db
def test_consensus_rank_is_unique_across_players():
    """Design note: ties break the sort and the delta column."""
    board = _load("board.json")
    ranks = [p["consensus_rank"] for p in board["players"]]
    assert len(ranks) == len(set(ranks))


@pytest.mark.requires_db
def test_delta_matches_its_definition():
    board = _load("board.json")
    for p in board["players"]:
        assert p["delta_vs_consensus"] == p["consensus_rank"] - p["overall_rank"]


@pytest.mark.requires_db
def test_player_ids_are_unique_integers():
    board = _load("board.json")
    ids = [p["id"] for p in board["players"]]
    assert all(isinstance(i, int) for i in ids)
    assert len(ids) == len(set(ids))


@pytest.mark.requires_db
def test_tier_is_an_integer_as_the_contract_expects():
    board = _load("board.json")
    for p in board["players"]:
        assert isinstance(p["tier"], int)


@pytest.mark.requires_db
def test_every_displayable_projection_ships_with_a_confidence_interval():
    """Design requirement: never ship a projection without ci_low/ci_high.

    We satisfy the INTENT rather than the letter. The rank->points curve is
    fitted only within draft-relevant depth; past that a projection is an
    extrapolation with no honest interval. Rather than fabricate a CI, those
    players are flagged `projection_within_fitted_range: false` and the UI must
    suppress the number. So the invariant is: inside the fitted range, a CI is
    mandatory."""
    board = _load("board.json")
    missing = [
        p["player"] for p in board["players"]
        if p["projection_within_fitted_range"]
        and (p["ci_low"] is None or p["ci_high"] is None)
    ]
    assert not missing, f"in-range projections without a CI: {missing[:5]}"


@pytest.mark.requires_db
def test_out_of_range_projections_are_flagged_and_explained():
    board = _load("board.json")
    out = [p for p in board["players"] if not p["projection_within_fitted_range"]]
    assert out, "expected some players beyond the fitted curve depth"
    for p in out:
        assert p["ci_low"] is None and p["ci_high"] is None
        assert "do not display" in p["projection_note"].lower()


@pytest.mark.requires_db
def test_ci_bounds_bracket_the_value_they_apply_to():
    board = _load("board.json")
    for p in board["players"]:
        if p["ci_low"] is None:
            continue
        assert p["ci_applies_to"] == "vbd"
        assert p["ci_low"] <= p["vbd"] <= p["ci_high"]


@pytest.mark.requires_db
def test_single_consensus_source_is_declared_not_implied_as_a_blend():
    """The design example showed 'blend:4'. We have one source and must say so."""
    board = _load("board.json")
    assert board["consensus_source_count"] == 1
    assert "not" in board["consensus_source_note"].lower()


@pytest.mark.requires_db
def test_def_is_declared_unsupported():
    """DEF's replacement RANK is structural and IS published (league.json). Its
    replacement POINTS are not, because no DST data is ingested -- so the board
    carries no DEF row and `replacement_levels_used` (the levels this board was
    actually built from) still excludes DEF."""
    board = _load("board.json")
    assert board["def_supported"] is False
    assert "DEF" not in board["replacement_levels_used"]
    assert not any(p["position"] == "DEF" for p in board["players"])


def test_def_exclusion_is_declared_not_merely_absent():
    """The front end read roster.starters declaring DEF:1 against a
    replacement_levels with no DEF key as a contradiction. It is a decision:
    DEF is permanently excluded for lack of DST data. The field makes that
    legible without needing the docs."""
    league = _load("league.json")
    assert league["roster"]["starters"]["DEF"] == 1
    assert league["positions_without_replacement_levels"] == ["DEF"]
    assert "DEF" not in league["replacement_levels"]
    assert "permanently" in league["positions_without_replacement_levels_note"]


@pytest.mark.requires_db
def test_no_def_value_of_any_kind_exists_in_the_exports():
    """The invariant behind the exclusion: no DEF level, points, curve or board
    row anywhere, so nothing downstream can pair a rank with a value and
    manufacture a DEF number."""
    board = _load("board.json")
    league = _load("league.json")
    assert not any(p["position"] == "DEF" for p in board["players"])
    assert "DEF" not in board["replacement_levels_used"]
    assert "DEF" not in board.get("curve_fits", {})
    assert "DEF" not in league["replacement_levels"]


def test_flex_split_is_described_as_measured_not_assumed():
    """ADR-029 measured the split over 26 seasons; the note said 'not a
    measurement' for two contract versions after that stopped being true."""
    league = _load("league.json")
    note = league["flex_split_note"]
    assert "MEASURED" in note
    assert "not a measurement" not in note


def _reject_python_only_constants(constant: str):
    raise AssertionError(
        f"export contains the bare token `{constant}`, which is valid Python and "
        f"INVALID JSON (RFC 8259). JSON.parse and fetch().json() both throw on it."
    )


@pytest.mark.parametrize(
    "name",
    [
        "board.json",
        "availability.json",
        "league.json",
        "strategies.json",
        "glossary.json",
        "nulls.json",
        "opponents.json",
    ],
)
def test_every_export_is_parseable_by_a_non_python_consumer(name):
    """Python's json module accepts Infinity/-Infinity/NaN on BOTH sides by
    default, so a round-trip inside Python cannot catch this -- league.json
    shipped a bare `Infinity` for six commits while every Python test passed.
    `parse_constant` is the hook that makes the reader as strict as a browser."""
    p = EXPORT / name
    if not p.exists():
        pytest.skip(f"{name} not generated")
    json.loads(p.read_text(encoding="utf-8"), parse_constant=_reject_python_only_constants)


def test_open_ended_points_allowed_tier_is_null_not_infinity():
    """The top DEF points-allowed tier has no upper bound. It is emitted as null
    and labelled, because null means 'not available' everywhere else in the
    contract and the difference matters to a consumer."""
    league = _load("league.json")
    tiers = league["scoring"]["defense"]["points_allowed"]
    assert tiers[-1][0] is None, "open-ended tier must carry a null ceiling"
    assert all(t[0] is not None for t in tiers[:-1]), "only the last tier is open-ended"
    assert "NO UPPER BOUND" in league["scoring"]["defense"]["points_allowed_note"]
