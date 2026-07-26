import pathlib

import pytest

import player_descriptions as pdesc
from archetypes import ArchetypeAssignment

SRC = pathlib.Path(__file__).resolve().parent.parent / "src"

# Modules that must NEVER import player_descriptions -- the enforcement of
# "display-only, never a Fact, never a model input" (ADR-044).
FORBIDDEN_IMPORTERS = (
    "narrate.py", "scoring.py", "make_board.py", "backtest.py",
    "candidate_rankings.py", "draft_sim.py", "availability.py",
)


def _assignment(archetype, **overrides):
    base = dict(
        player_id="p1", player_name="Test Player", season=2026, position="RB",
        archetype=archetype, confidence="high", games_qualified=15,
        carry_share=0.6, target_share=0.1, offense_pct=0.65, adot=1.0,
        depth_rank=None, cutoff_date="2026-01-01", reason=None,
    )
    base.update(overrides)
    return ArchetypeAssignment(**base)


def test_undetermined_produces_no_description():
    for pos, arch in (("RB", "RB_UNDETERMINED"), ("WR", "WR_UNDETERMINED"),
                       ("TE", "TE_UNDETERMINED")):
        a = _assignment(arch, position=pos, confidence="undetermined")
        assert pdesc.generate_description(a) is None


def test_generic_undetermined_produces_no_description():
    a = _assignment("UNDETERMINED", position="", confidence="undetermined")
    assert pdesc.generate_description(a) is None


def test_every_non_undetermined_archetype_has_a_template():
    """If archetypes.py's enum ever grows, this fails loudly instead of
    silently emitting None for a real (non-undetermined) archetype."""
    from archetypes import RB_ARCHETYPES, WR_ARCHETYPES, TE_ARCHETYPES

    all_real = [
        a for a in (*RB_ARCHETYPES, *WR_ARCHETYPES, *TE_ARCHETYPES)
        if not a.endswith("_UNDETERMINED") and a != "RB_HANDCUFF"  # named gap, not implemented
    ]
    for archetype in all_real:
        assert archetype in pdesc._TEMPLATES, f"no template for {archetype}"


def test_license_tag_always_ai_generated():
    a = _assignment("RB_BELL_COW")
    d = pdesc.generate_description(a)
    assert d.license_tag == "ai_generated"


def test_description_is_deterministic_across_calls():
    """Regeneratable, never hand-frozen: the SAME assignment must produce
    BYTE-IDENTICAL description text every time -- only generated_at may
    differ."""
    a = _assignment("RB_BELL_COW")
    d1 = pdesc.generate_description(a)
    d2 = pdesc.generate_description(a)
    assert d1.description == d2.description
    assert d1.source_stats == d2.source_stats


def test_description_uses_only_measured_stats_never_invents_a_number():
    a = _assignment("RB_BELL_COW", carry_share=0.601, target_share=0.071, offense_pct=0.652)
    d = pdesc.generate_description(a)
    assert "60%" in d.description
    assert "65%" in d.description


def test_source_stats_carried_for_audit():
    a = _assignment("WR_HIGH_VOLUME", position="WR", target_share=0.25, offense_pct=0.71)
    d = pdesc.generate_description(a)
    assert d.source_stats["target_share"] == 0.25
    assert d.source_stats["offense_pct"] == 0.71


def test_never_reads_or_stores_third_party_text():
    """The module source itself must not contain any mechanism for fetching
    external text -- no requests/httpx/urllib import anywhere in the file."""
    source = (SRC / "player_descriptions.py").read_text(encoding="utf-8")
    for banned_import in ("import requests", "import urllib", "import httpx"):
        assert banned_import not in source


class TestDisplayOnlySeparationEnforced:
    """Static scan, same pattern as test_seed_stability.py's hash() ban --
    the property is enforced by CI, not by convention."""

    def test_no_forbidden_module_imports_player_descriptions(self):
        offenders = []
        for name in FORBIDDEN_IMPORTERS:
            path = SRC / name
            if not path.exists():
                continue
            text = path.read_text(encoding="utf-8")
            if "player_descriptions" in text or "archetypes" in text:
                offenders.append(name)
        assert not offenders, (
            f"forbidden module(s) reference player_descriptions/archetypes: {offenders} -- "
            f"descriptions must never be a Fact or a model input (ADR-044)"
        )

    def test_no_player_description_fact_kind_exists(self):
        """ADR-027's Fact.kind enum must never grow a description-shaped
        entry -- that would route unverified/templated prose through the
        Facts pipeline, exactly what ADR-027 built the Fact/Renderer wall to
        prevent."""
        narrate_source = (SRC / "narrate.py").read_text(encoding="utf-8")
        assert "player_description" not in narrate_source.lower()
        assert "archetype" not in narrate_source.lower()


@pytest.mark.requires_db
class TestAgainstRealData:
    def test_generate_all_descriptions_runs(self):
        import db as dbmod

        conn = dbmod.connect()
        try:
            descriptions = pdesc.generate_all_descriptions(conn, 2026)
        finally:
            conn.close()
        assert len(descriptions) > 50
        assert all(d.license_tag == "ai_generated" for d in descriptions)
        assert all(d.description for d in descriptions)

    def test_no_description_for_undetermined_players_in_real_run(self):
        import db as dbmod

        import archetypes as arch

        conn = dbmod.connect()
        try:
            assignments = arch.assign_for_season(conn, 2026)
            descriptions = pdesc.generate_all_descriptions(conn, 2026)
        finally:
            conn.close()
        undetermined_ids = {a.player_id for a in assignments if a.archetype.endswith("_UNDETERMINED")}
        described_ids = {d.player_id for d in descriptions}
        assert not (undetermined_ids & described_ids)


@pytest.mark.requires_db
class TestExport:
    def test_export_is_deterministic_modulo_timestamps(self, tmp_path):
        import db as dbmod

        conn = dbmod.connect()
        try:
            p1 = pdesc.export_player_descriptions_json(conn, 2026, tmp_path / "a.json")
            p2 = pdesc.export_player_descriptions_json(conn, 2026, tmp_path / "b.json")
        finally:
            conn.close()
        import json as _json

        d1 = _json.loads(p1.read_text())
        d2 = _json.loads(p2.read_text())
        for p in (d1, d2):
            for player in p["players"]:
                player.pop("generated_at")
            p.pop("generated_utc")
        assert d1 == d2

    def test_export_is_strict_json(self, tmp_path):
        import db as dbmod

        conn = dbmod.connect()
        try:
            path = pdesc.export_player_descriptions_json(conn, 2026, tmp_path / "out.json")
        finally:
            conn.close()

        def strict(c):
            raise ValueError(c)

        import json as _json

        _json.loads(path.read_text(), parse_constant=strict)  # must not raise

    def test_export_note_states_display_only(self, tmp_path):
        import db as dbmod

        conn = dbmod.connect()
        try:
            path = pdesc.export_player_descriptions_json(conn, 2026, tmp_path / "out.json")
        finally:
            conn.close()
        import json as _json

        d = _json.loads(path.read_text())
        assert "never a model input" in d["note"]
        assert d["license_tag"] == "ai_generated"
