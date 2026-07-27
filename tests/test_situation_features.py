"""Tests for the V3 vacated/arrived-opportunity features
(experiments/bottomup/situation.py) against the registration in
docs/reviews/FABLE-EXT2-2026-07-27.md.

Synthetic-store tests pin the arithmetic (vacated shares, arrival
self-exclusion, no-early-appearance semantics, franchise canonicalisation
across the 2002/2003 code seam, zero denominators). One DB-backed test pins
the holdout seal on the new early_rosters read.
"""

import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from experiments.bottomup import data as bdata  # noqa: E402
from experiments.bottomup.data import PlayerSeason  # noqa: E402
from experiments.bottomup.situation import N_FEATURES, Situation  # noqa: E402

_CANDIDATES = [
    ROOT.parent.parent.parent / "data" / "nfl.db",
    Path(r"C:\Users\matth\Documents\Personal\Fantasy Football\data\nfl.db"),
]
DB_PATH = next((p for p in _CANDIDATES if p.exists()), None)
needs_db = pytest.mark.skipif(DB_PATH is None, reason="nfl.db not available")


def _ps(pid, team, targets=0, receptions=0, carries=0, attempts=0):
    ps = PlayerSeason(pid, 2019, "WR", team)
    ps.games = 16
    ps.targets = targets
    ps.receptions = receptions
    ps.carries = carries
    ps.attempts = attempts
    return ps


class FakeStore:
    """Duck-typed store: prior-season aggregates + weeks-1-4 rosters."""

    def __init__(self, prior, early):
        self._prior, self._early = prior, early

    def player_seasons(self, season, *, for_target=None):
        assert for_target is None or season < for_target
        return self._prior

    def early_rosters(self, season):
        return self._early


@pytest.fixture
def scenario():
    # 2019 (prior): KC has P1 (WR, stays), P2 (RB, stays), P3 (WR, departs
    # to LV), P4 (QB, retires - no early 2020 appearance). LV has P5 (WR,
    # stays), P6 (RB, departs to KC).
    prior = {
        "P1": _ps("P1", "KC", targets=100, receptions=70),
        "P2": _ps("P2", "KC", targets=20, receptions=15, carries=200),
        "P3": _ps("P3", "KC", targets=80, receptions=50),
        "P4": _ps("P4", "KC", carries=20, attempts=500),
        "P5": _ps("P5", "LV", targets=120, receptions=80),
        "P6": _ps("P6", "LV", targets=10, receptions=8, carries=150),
    }
    early = {"P1": "KC", "P2": "KC", "P3": "LV", "P5": "LV", "P6": "KC"}
    return FakeStore(prior, early)


def test_vacated_shares_usage_arm(scenario):
    sit = Situation(scenario, 2020, usage_arm=True)
    f1 = sit.features_for("P1")  # retained on KC
    # KC 2019: targets 200, carries 220, attempts 500.
    # Vacated from KC: P3 (departed, 80 tgt) + P4 (no early appearance,
    # 20 car, 500 att).
    assert f1.changed_team == 0.0
    assert f1.vac_rec_share == pytest.approx(80 / 200)
    assert f1.vac_carry_share == pytest.approx(20 / 220)
    assert f1.vac_att_share == pytest.approx(1.0)
    # Arrived at KC: P6 (10 tgt, 150 car), P1 is not P6 so no exclusion.
    assert f1.arr_rec_share == pytest.approx(10 / 200)
    assert f1.arr_carry_share == pytest.approx(150 / 220)


def test_arrival_excludes_self(scenario):
    sit = Situation(scenario, 2020, usage_arm=True)
    f6 = sit.features_for("P6")  # moved LV -> KC
    assert f6.changed_team == 1.0
    # P6 is KC's only arrival, so his own arrival shares are zero.
    assert f6.arr_rec_share == 0.0
    assert f6.arr_carry_share == 0.0
    # but he sees KC's vacated shares
    assert f6.vac_rec_share == pytest.approx(80 / 200)


def test_no_early_appearance_counts_vacated_but_keeps_old_team(scenario):
    sit = Situation(scenario, 2020, usage_arm=True)
    f4 = sit.features_for("P4")  # no 2020 appearance
    assert f4.changed_team == 0.0  # per registration: not a team change
    # his OWN features are KC's (old franchise)
    assert f4.vac_att_share == pytest.approx(1.0)
    # and LV's vacated pool contains P6's production
    f5 = sit.features_for("P5")
    assert f5.vac_rec_share == pytest.approx(10 / 130)
    assert f5.vac_carry_share == pytest.approx(1.0)
    assert f5.vac_att_share == 0.0  # 0/0 denominator -> 0 by registration
    assert f5.arr_rec_share == pytest.approx(80 / 130)


def test_long_arm_uses_receptions(scenario):
    sit = Situation(scenario, 2020, usage_arm=False)
    f1 = sit.features_for("P1")
    # KC receptions 2019: 70+15+50 = 135; vacated: P3's 50.
    assert f1.vac_rec_share == pytest.approx(50 / 135)


def test_franchise_canonicalisation_across_code_seam():
    # Prior season uses the 1999-2002 code "OAK"; early roster of the target
    # uses "LV" (as the DB does from 2003). Same franchise: retained.
    prior = {"P7": _ps("P7", "OAK", targets=50, receptions=30)}
    early = {"P7": bdata.canon_team("OAK")}
    sit = Situation(FakeStore(prior, early), 2003, usage_arm=False)
    f7 = sit.features_for("P7")
    assert f7.changed_team == 0.0
    assert f7.vac_rec_share == 0.0


def test_unknown_player_gets_zero_features(scenario):
    sit = Situation(scenario, 2020, usage_arm=True)
    fz = sit.features_for("NOBODY")
    assert fz.as_list() == [0.0] * N_FEATURES


@needs_db
def test_early_rosters_holdout_sealed():
    store = bdata.SeasonStore(DB_PATH)
    with pytest.raises(bdata.HoldoutViolation):
        store.early_rosters(2025)


@needs_db
def test_early_rosters_reads_canonical_codes():
    store = bdata.SeasonStore(DB_PATH)
    teams = set(store.early_rosters(2003).values())
    # 2003+ rows are already modern codes; canon must be a no-op there
    assert not teams & {"OAK", "SD", "STL", "JAC"}
