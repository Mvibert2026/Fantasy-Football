import pytest

import archetypes as arch


class TestRBArchetype:
    def test_bell_cow(self):
        a, c = arch.assign_rb_archetype(0.60, 0.10, 0.65, 15)
        assert a == "RB_BELL_COW"
        assert c == "high"

    def test_early_down(self):
        a, c = arch.assign_rb_archetype(0.45, 0.03, 0.55, 12)
        assert a == "RB_EARLY_DOWN"

    def test_passing_down(self):
        a, c = arch.assign_rb_archetype(0.20, 0.12, 0.40, 12)
        assert a == "RB_PASSING_DOWN"

    def test_committee(self):
        a, c = arch.assign_rb_archetype(0.35, 0.10, 0.50, 12)
        assert a == "RB_COMMITTEE"

    def test_undetermined_when_nothing_matches(self):
        # carry_share too low for committee, target_share too low for
        # passing-down -- falls through every criterion.
        a, c = arch.assign_rb_archetype(0.10, 0.02, 0.20, 12)
        assert a == "RB_UNDETERMINED"

    def test_undetermined_below_min_games(self):
        a, c = arch.assign_rb_archetype(0.60, 0.10, 0.65, 7)
        assert a == "RB_UNDETERMINED"
        assert c == "undetermined"

    def test_medium_confidence_band(self):
        a, c = arch.assign_rb_archetype(0.60, 0.10, 0.65, 10)
        assert c == "medium"

    def test_bell_cow_checked_before_early_down(self):
        """Evaluation order (taxonomy SS1): a player meeting BOTH BELL_COW and
        what would otherwise look like EARLY_DOWN criteria must get BELL_COW,
        since it is checked first."""
        a, c = arch.assign_rb_archetype(0.60, 0.08, 0.65, 15)  # meets both
        assert a == "RB_BELL_COW"

    def test_handcuff_not_implemented_falls_through_to_undetermined(self):
        """RB_HANDCUFF needs a depth chart (not implemented, ADR-044). A
        player with handcuff-shaped usage (low everything) must NOT be
        silently assigned a label the taxonomy says needs data we don't have."""
        a, c = arch.assign_rb_archetype(0.10, 0.02, 0.15, 12)
        assert a != "RB_HANDCUFF"
        assert a == "RB_UNDETERMINED"


class TestWRArchetype:
    def test_high_volume(self):
        a, c = arch.assign_wr_archetype(0.25, 0.75, 10.0, 15)
        assert a == "WR_HIGH_VOLUME"

    def test_field_stretcher(self):
        a, c = arch.assign_wr_archetype(0.15, 0.60, 14.0, 15)
        assert a == "WR_FIELD_STRETCHER"

    def test_possession(self):
        a, c = arch.assign_wr_archetype(0.15, 0.65, 8.0, 15)
        assert a == "WR_POSSESSION"

    def test_rotational(self):
        a, c = arch.assign_wr_archetype(0.10, 0.40, 9.0, 12)
        assert a == "WR_ROTATIONAL"

    def test_undetermined_mid_mass_gap(self):
        """The taxonomy's own documented risk: thresholds landing mid-mass
        leave a real gap between POSSESSION (needs offense_pct>=0.60) and
        ROTATIONAL (needs offense_pct<0.55). A player at 0.57 with otherwise
        possession-shaped numbers must fall to UNDETERMINED, not the nearest
        label -- observed for real on Keenan Allen's 2025 season this
        session; pinned here as a regression case."""
        a, c = arch.assign_wr_archetype(0.20, 0.57, 8.0, 15)
        assert a == "WR_UNDETERMINED"


class TestTEArchetype:
    def test_primary_receiver(self):
        a, c = arch.assign_te_archetype(0.20, 0.70, 15)
        assert a == "TE_PRIMARY_RECEIVER"

    def test_secondary_receiver(self):
        a, c = arch.assign_te_archetype(0.12, 0.55, 12)
        assert a == "TE_SECONDARY_RECEIVER"

    def test_blocking(self):
        a, c = arch.assign_te_archetype(0.05, 0.50, 12)
        assert a == "TE_BLOCKING"

    def test_undetermined(self):
        a, c = arch.assign_te_archetype(0.05, 0.30, 12)  # too few snaps for BLOCKING too
        assert a == "TE_UNDETERMINED"


def test_confidence_thresholds_exact_boundaries():
    assert arch._confidence(12) == "high"
    assert arch._confidence(11) == "medium"
    assert arch._confidence(8) == "medium"
    assert arch._confidence(7) == "undetermined"
    assert arch._confidence(0) == "undetermined"


def test_assign_for_season_below_data_floor_is_all_undetermined():
    """2013 is the binding floor (snap counts). A target_season of 2013 would
    need 2012 data, which predates offense_pct entirely."""
    results = arch.assign_for_season(
        None, target_season=2013, active_player_ids={"p1": "RB", "p2": "WR"}
    )
    assert len(results) == 2
    assert all(r.archetype.endswith("_UNDETERMINED") for r in results)
    assert all("data floor" in r.reason for r in results)


def test_undetermined_label_is_position_specific():
    a = arch._undetermined("p1", "TE", 2026, "2026-01-01", "rookie")
    assert a.archetype == "TE_UNDETERMINED"
    a2 = arch._undetermined("p2", "", 2026, "2026-01-01", "rookie")
    assert a2.archetype == "UNDETERMINED"  # unknown position -> generic, not a guess


@pytest.mark.requires_db
class TestAgainstRealData:
    def test_assign_for_season_runs_and_produces_a_mix_of_archetypes(self):
        import db as dbmod

        conn = dbmod.connect()
        try:
            results = arch.assign_for_season(conn, 2026)
        finally:
            conn.close()
        assert len(results) > 100
        archetypes_seen = {r.archetype for r in results}
        assert "RB_BELL_COW" in archetypes_seen
        assert "WR_UNDETERMINED" in archetypes_seen

    def test_no_archetype_uses_target_season_data_look_ahead(self):
        """Structural check: every assignment's underlying data season must be
        STRICTLY BEFORE the target season (t-1 labels, CLAUDE.md SS6.1)."""
        import db as dbmod

        conn = dbmod.connect()
        try:
            inputs = arch.compute_player_season_inputs(conn, data_season=2025)
        finally:
            conn.close()
        assert all(i.season == 2025 for i in inputs)  # never 2026

    def test_rookie_with_no_2025_data_is_undetermined_not_absent(self):
        import db as dbmod

        conn = dbmod.connect()
        try:
            results = arch.assign_for_season(
                conn, 2026, active_player_ids={"__fake_rookie_id__": "WR"}
            )
        finally:
            conn.close()
        fake = next(r for r in results if r.player_id == "__fake_rookie_id__")
        assert fake.archetype == "WR_UNDETERMINED"
        assert fake.reason == "rookie"
