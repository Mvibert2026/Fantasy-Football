"""Guard the three artifacts a from-scratch rebuild of `data/nfl.db` cannot reproduce.

Thread 080. Measured 2026-07-29 (`docs/can-we-rebuild-the-database.md`): 99.3% of the
database rebuilds from public sources in ~4 minutes, but these three do not come back at
all. The dangerous property is that their absence is *silent* -- every other script still
runs green against a database missing them, because nothing asserted they existed.

These tests read the committed fixtures, never `data/nfl.db`, so they pass in a fresh clone
with no database present -- which is exactly the situation they are meant to protect.
"""
from __future__ import annotations

import csv
import json
from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parent.parent
FIXTURES = REPO / "tests" / "fixtures" / "real_draft_2025"
RANKINGS = REPO / "data" / "rankings-history"
FOUNDER_EXPORT = REPO / "data" / "raw" / "founder-export" / "2026-07-27"

# The n behind DEFAULT_LAMBDA = 0.352 (live_availability.py, conditional logit,
# se=0.070, z=5.04). 145 accepted picks + 15 quarantined = 160.
EXPECTED_PICKS = 145
EXPECTED_QUARANTINE = 15
EXPECTED_TOTAL = 160


def _rows(path: Path) -> list[dict]:
    with path.open(newline="", encoding="utf-8") as fh:
        return list(csv.DictReader(fh))


class TestRealDraft2025:
    """The sole empirical basis for the roster-need parameter."""

    def test_bundle_exists(self):
        assert (FIXTURES / "real_draft_2025.json").exists(), (
            "The 2025 real draft fixture is missing. It was hand-transcribed from "
            "screenshots and exists in no public source -- it cannot be regenerated. "
            "See docs/can-we-rebuild-the-database.md and handoff thread 080."
        )

    def test_pick_count_is_160(self):
        bundle = json.loads((FIXTURES / "real_draft_2025.json").read_text(encoding="utf-8"))
        counts = bundle["counts"]
        assert counts["mock_picks"] == EXPECTED_PICKS
        assert counts["mock_pick_quarantine"] == EXPECTED_QUARANTINE
        total = counts["mock_picks"] + counts["mock_pick_quarantine"]
        assert total == EXPECTED_TOTAL, (
            f"Expected the n=160 that DEFAULT_LAMBDA=0.352 was fit from, got {total}. "
            "If this changed deliberately, lambda's provenance note needs updating too."
        )

    def test_csv_mirrors_match_the_bundle(self):
        bundle = json.loads((FIXTURES / "real_draft_2025.json").read_text(encoding="utf-8"))
        assert len(_rows(FIXTURES / "mock_picks.csv")) == bundle["counts"]["mock_picks"]
        assert len(_rows(FIXTURES / "mock_drafts.csv")) == bundle["counts"]["mock_drafts"]

    def test_provenance_is_recorded(self):
        bundle = json.loads((FIXTURES / "real_draft_2025.json").read_text(encoding="utf-8"))
        draft = bundle["mock_drafts"][0]
        assert draft["mock_id"] == "2025_league_draft_real"
        assert draft["source"] == "user_provided_screenshots", (
            "Provenance matters: this is manually transcribed data, not an API pull."
        )


class TestRankingsHistory:
    """2021-2025 expert consensus. The mirror serves only the current scrape."""

    def test_history_exists(self):
        assert (RANKINGS / "rankings_2021_2025.csv").exists(), (
            "Rankings history 2021-2025 is missing. The DynastyProcess mirror serves "
            "only the current scrape, so this cannot be re-pulled at any price. "
            "Without it, CLAUDE.md 6.5's required consensus-ADP baseline is unavailable "
            "for those seasons and no backtest can be run on them."
        )

    def test_all_five_seasons_present(self):
        seasons = {int(r["season"]) for r in _rows(RANKINGS / "rankings_2021_2025.csv")}
        assert seasons == {2021, 2022, 2023, 2024, 2025}, f"got seasons {sorted(seasons)}"

    def test_dispersion_columns_survived(self):
        """ingest_rankings.py:76-79 -- once dispersion is dropped it is permanently
        unrecoverable for that date, and VONA needs a distribution, not a point."""
        rows = _rows(RANKINGS / "rankings_2021_2025.csv")
        for col in ("spread_sd", "rank_best", "rank_worst"):
            assert col in rows[0], f"{col} missing; dispersion is unrecoverable once lost"
        assert any(r.get("spread_sd") for r in rows), "spread_sd is present but entirely empty"

    def test_row_count_is_plausible(self):
        rows = _rows(RANKINGS / "rankings_2021_2025.csv")
        assert len(rows) > 2000, f"only {len(rows)} rows; expected ~2540 across five seasons"


class TestFounderExport:
    """The only half-PPR-native ranking input in the project."""

    def test_board_source_csv_is_committed(self):
        target = FOUNDER_EXPORT / "FantasyPros_2026_Draft_ALL_Rankings.csv"
        assert target.exists(), (
            "The founder FantasyPros export is missing. ingest_fantasypros_csv.py reads "
            "it directly (DEFAULT_CSV_PATH), and it is the only half-PPR-native ranking "
            "input -- ingest_rankings.py deliberately stays on the non-half-PPR mirror "
            "because the FantasyPros free tier caps responses at 10 rows."
        )

    @pytest.mark.parametrize("name", [
        "FantasyPros_2026_Draft_ALL_Rankings.csv",
        "fantasypros-all-rankings.csv",
        "three-analyst-rankings.csv",
        "underdog-adp.csv",
    ])
    def test_all_four_exports_present(self, name):
        assert (FOUNDER_EXPORT / name).exists(), f"{name} missing from the founder export"
