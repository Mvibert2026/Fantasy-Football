import json

import pytest

import narrate
from narrate import (CONFIDENCE_HIGH, DraftState, Fact, RenderContractError,
                     SourcePathError)


# ----------------------------------------------------------------- fixtures


@pytest.fixture
def exports():
    """Minimal but structurally faithful stand-in for the Block 7 artifacts."""
    return {
        "board.json": {
            "players": [
                {"player": "Alpha Back", "position": "RB", "positional_rank": 1,
                 "positional_label": "RB1", "overall_rank": 1, "vbd": 168.7,
                 "consensus_rank": 2, "delta_vs_consensus": 1},
                {"player": "Beta Wideout", "position": "WR", "positional_rank": 1,
                 "positional_label": "WR1", "overall_rank": 2, "vbd": 153.0,
                 "consensus_rank": 1, "delta_vs_consensus": -1},
                {"player": "Gamma Tight", "position": "TE", "positional_rank": 30,
                 "positional_label": "TE30", "overall_rank": 200, "vbd": 5.0,
                 "consensus_rank": 190, "delta_vs_consensus": -10},
            ]
        },
        "availability.json": {
            "metadata": {"user_picks": [3, 18, 23, 38]},
            "by_tier": {
                "RB": {"T1": {"3": {"sigma_10": 1.0}, "18": {"sigma_10": 0.46},
                              "23": {"sigma_10": 0.10}}},
                "TE": {"T1": {"3": {"sigma_10": 1.0}, "18": {"sigma_10": 0.80},
                              "23": {"sigma_10": 0.59}}},
            },
        },
        "league.json": {
            "replacement_levels": {"QB": 10, "RB": 28, "WR": 41, "TE": 11},
            "roster": {"starters": {"QB": 1, "RB": 2, "WR": 3, "TE": 1,
                                    "FLEX": 2, "DEF": 1}},
        },
        "opponents.json": {
            "opponents": [
                {"team_name": "Shit Leopards", "draft_slot_2026": 2},
                {"team_name": None, "draft_slot_2026": 5},
            ]
        },
        "nulls.json": {
            "findings": [
                {"id": "PR-002", "claim_tested": "Spike-week ability persists",
                 "result": "NULL", "plain_language_summary": "It does not persist."},
            ]
        },
    }


# ----------------------------------------------------------------- path resolution


def test_resolve_path_reaches_a_nested_value(exports):
    assert narrate.resolve_path(exports, "league.json:replacement_levels.RB") == 28


def test_resolve_path_indexes_lists(exports):
    assert narrate.resolve_path(exports, "board.json:players.0.player") == "Alpha Back"


def test_missing_key_raises(exports):
    with pytest.raises(SourcePathError, match="missing"):
        narrate.resolve_path(exports, "league.json:replacement_levels.KICKER")


def test_missing_artifact_raises(exports):
    with pytest.raises(SourcePathError, match="not loaded"):
        narrate.resolve_path(exports, "nonexistent.json:a.b")


def test_malformed_path_raises(exports):
    with pytest.raises(SourcePathError, match="malformed"):
        narrate.resolve_path(exports, "no_colon_here")


def test_a_fact_with_no_matching_export_field_raises(exports):
    """The core safety property: a Fact can never be emitted against a field
    that does not exist, so a stale export cannot produce confident fiction."""
    bogus = Fact(id="x", kind="k", source_path="board.json:players.99.vbd",
                 value=1.0, template="t")
    with pytest.raises(SourcePathError):
        narrate.validate_facts([bogus], exports)


# ----------------------------------------------------------------- extractors


def test_tier_survival_shift_is_computed_between_consecutive_user_picks(exports):
    state = DraftState(pick_number=18)
    facts = narrate.tier_survival_facts(state, exports)
    rb = next(f for f in facts if f.id == "tier_survival_shift.RB.T1.18_to_23")
    assert rb.value == pytest.approx(0.36)  # 0.46 -> 0.10
    assert rb.confidence == CONFIDENCE_HIGH
    assert "46%" in rb.render_template() and "10%" in rb.render_template()


def test_tier_survival_uses_plain_level_when_current_pick_is_not_a_user_pick(exports):
    facts = narrate.tier_survival_facts(DraftState(pick_number=7), exports)
    assert any(f.kind == "tier_survival" for f in facts)
    assert not any(f.kind == "tier_survival_shift" for f in facts)


def test_availability_facts_are_high_confidence(exports):
    """They never pass through the projection curve."""
    facts = narrate.tier_survival_facts(DraftState(pick_number=18), exports)
    assert facts and all(f.confidence == CONFIDENCE_HIGH for f in facts)


def test_replacement_crossing_detects_a_position_past_replacement(exports):
    # only Gamma Tight (TE30) is left at TE; replacement is TE11
    state = DraftState(pick_number=18, taken_players=[])
    facts = narrate.replacement_crossing_facts(state, exports)
    te = next(f for f in facts if f.id.startswith("replacement_crossing.TE"))
    assert te.value == pytest.approx(30 - 11)
    assert "freely available" in te.render_template()


def test_replacement_crossing_reports_a_position_still_ahead_of_replacement(exports):
    facts = narrate.replacement_crossing_facts(DraftState(pick_number=1), exports)
    rb = next(f for f in facts if f.id.startswith("replacement_crossing.RB"))
    assert rb.value == pytest.approx(1 - 28)
    assert "still ahead" in rb.render_template()


def test_replacement_crossing_respects_players_already_taken(exports):
    state = DraftState(pick_number=5, taken_players=["Alpha Back"])
    facts = narrate.replacement_crossing_facts(state, exports)
    assert not any(f.id.startswith("replacement_crossing.RB") for f in facts)


def test_reach_cost_is_zero_for_the_top_player_left(exports):
    state = DraftState(pick_number=3, considering="Alpha Back")
    fact = narrate.reach_cost_facts(state, exports)[0]
    assert fact.value == 0.0
    assert "no reach cost" in fact.render_template()


def test_reach_cost_prices_a_reach_against_the_best_available(exports):
    state = DraftState(pick_number=3, considering="Gamma Tight")
    fact = narrate.reach_cost_facts(state, exports)[0]
    assert fact.value == pytest.approx(168.7 - 5.0)
    assert fact.confidence == narrate.CONFIDENCE_LOW  # runs through the weak curve


def test_reach_cost_hedges_because_projections_are_weak(exports):
    state = DraftState(pick_number=3, considering="Gamma Tight")
    text = narrate.reach_cost_facts(state, exports)[0].render_template()
    assert "weak" in text or "rough" in text


def test_reach_cost_absent_when_nothing_is_under_consideration(exports):
    assert narrate.reach_cost_facts(DraftState(pick_number=3), exports) == []


def test_opponent_need_infers_unfilled_starting_slots(exports):
    state = DraftState(pick_number=25, rosters_by_slot={2: ["Alpha Back"]})
    facts = narrate.opponent_need_facts(state, exports)
    leopards = next(f for f in facts if "slot2" in f.id)
    text = leopards.render_template()
    assert "Shit Leopards" in text
    assert "QB" in text and "WR" in text and "TE" in text


def test_opponent_need_falls_back_to_slot_when_no_team_name_is_known(exports):
    state = DraftState(pick_number=25, rosters_by_slot={5: []})
    facts = narrate.opponent_need_facts(state, exports)
    unknown = next(f for f in facts if "slot5" in f.id)
    assert "slot 5" in unknown.render_template()


def test_null_results_become_facts(exports):
    facts = narrate.null_result_facts(exports)
    assert facts[0].id == "registered_null.PR-002"
    assert "no evidence" in facts[0].render_template()


# ----------------------------------------------------------------- determinism


def test_extract_facts_is_deterministic(exports):
    state = DraftState(pick_number=18, considering="Alpha Back",
                       rosters_by_slot={2: ["Beta Wideout"]})
    a = narrate.extract_facts(state, exports)
    b = narrate.extract_facts(state, exports)
    assert [f.id for f in a] == [f.id for f in b]
    assert [f.value for f in a] == [f.value for f in b]


def test_extract_facts_covers_every_required_kind(exports):
    state = DraftState(pick_number=18, considering="Gamma Tight",
                       rosters_by_slot={2: ["Beta Wideout"]})
    kinds = {f.kind for f in narrate.extract_facts(state, exports)}
    for required in ("tier_survival_shift", "replacement_level_crossing",
                     "reach_cost", "opponent_need", "registered_null"):
        assert required in kinds, f"missing required fact kind {required}"


def test_extract_facts_validates_every_source_path(exports):
    """extract_facts must not return a Fact whose path does not resolve."""
    facts = narrate.extract_facts(DraftState(pick_number=18), exports)
    for f in facts:
        narrate.resolve_path(exports, f.source_path)


# ----------------------------------------------------------------- render contract


def test_render_layer_rejects_a_dict():
    with pytest.raises(RenderContractError, match="list of Fact"):
        narrate.validate_render_input({"facts": []})


def test_render_layer_rejects_a_string():
    with pytest.raises(RenderContractError):
        narrate.validate_render_input("some prose")


def test_render_layer_rejects_a_bare_fact_not_in_a_list():
    f = Fact(id="x", kind="k", source_path="a.json:b", value=1.0, template="t")
    with pytest.raises(RenderContractError):
        narrate.validate_render_input(f)


def test_render_layer_rejects_a_list_containing_non_facts():
    f = Fact(id="x", kind="k", source_path="a.json:b", value=1.0, template="t")
    with pytest.raises(RenderContractError, match="dict"):
        narrate.validate_render_input([f, {"id": "y"}])


def test_render_layer_accepts_a_list_of_facts():
    f = Fact(id="x", kind="k", source_path="a.json:b", value=1.0, template="t")
    assert narrate.validate_render_input([f]) == [f]


def test_every_rendered_sentence_resolves_to_a_fact_id(exports):
    """The traceability property: no sentence may exist without a Fact behind it."""
    state = DraftState(pick_number=18, considering="Gamma Tight",
                       rosters_by_slot={2: ["Beta Wideout"]})
    facts = narrate.extract_facts(state, exports)
    rendered = narrate.render_reference(facts)
    fact_ids = {f.id for f in facts}
    assert len(rendered) == len(facts)
    for r in rendered:
        assert r["fact_id"] in fact_ids
        assert r["sentence"].strip()
    assert {r["fact_id"] for r in rendered} == fact_ids


def test_rendered_sentences_carry_confidence(exports):
    facts = narrate.extract_facts(DraftState(pick_number=18), exports)
    for r in narrate.render_reference(facts):
        assert r["confidence"] in ("high", "medium", "low")


# ----------------------------------------------------------------- snapshots


SNAPSHOTS = {
    "tier_survival_shift.RB.T1.18_to_23": (
        "The chance at least one RB T1 player is still available falls from 46% now "
        "to 10% at your next pick (23)."
    ),
    "replacement_crossing.TE.pick18": (
        "The best TE left is TE30, and this league's replacement level is TE11 — so the "
        "TE position is already past the point where the next one is close to freely "
        "available."
    ),
    "registered_null.PR-002": (
        "We tested this and found no evidence: Spike-week ability persists. It does not "
        "persist."
    ),
}


@pytest.mark.parametrize("fact_id,expected", sorted(SNAPSHOTS.items()))
def test_template_snapshots(exports, fact_id, expected):
    """Wording is part of the contract. If a template changes, this fails and the
    change has to be deliberate -- the renderer and the guide both depend on it."""
    state = DraftState(pick_number=18, considering="Gamma Tight")
    facts = {f.id: f for f in narrate.extract_facts(state, exports)}
    assert fact_id in facts, f"{fact_id} no longer produced"
    assert facts[fact_id].render_template() == expected


# ----------------------------------------------------------------- real exports


@pytest.mark.requires_db
def test_runs_against_the_real_shipped_exports():
    exports = narrate.load_exports()
    if "board.json" not in exports:
        pytest.skip("exports not generated")
    state = DraftState(pick_number=18)
    facts = narrate.extract_facts(state, exports)
    assert facts
    narrate.validate_facts(facts, exports)
    rendered = narrate.render_reference(facts)
    assert all(r["sentence"] for r in rendered)
