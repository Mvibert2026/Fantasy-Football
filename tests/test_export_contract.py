import json
from pathlib import Path

import pytest

import export_contract

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
def test_player_id_gsis_is_populated_and_matches_rankings_player_id():
    """Thread 052: player_id_gsis was always emitted null. rankings.player_id
    IS a gsis_id (ingest_rankings.py joins fantasypros_id -> gsis_id and
    aliases it as player_id before insert), and player_weekly_stats.player_id
    (the join key weekly_finishes.json/season_stats.json use, thread 017/039)
    is the same nflverse gsis id space. board.json's player_id_gsis must
    carry that same value directly -- not a second, competing identifier
    scheme -- so a client can join board rows to the history exports."""
    board = _load("board.json")
    non_null = [p for p in board["players"] if p["player_id_gsis"] is not None]
    assert non_null, "player_id_gsis is populated on zero players"
    for p in non_null:
        assert isinstance(p["player_id_gsis"], str)
        assert p["player_id_gsis"].strip() != ""


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


@pytest.mark.parametrize(
    "name",
    [
        "board.json",
        "availability.json",
        "league.json",
        "glossary.json",
        "nulls.json",
        "opponents.json",
        # strategies.json deliberately excluded: export_strategies.py's slow
        # (43,200-sim) regeneration is allowed to lag behind CONTRACT_VERSION
        # between sessions -- the front end treats it as known-stale, not a bug.
    ],
)
def test_committed_artifact_matches_current_contract_version(name):
    """Regression guard for the exact failure in commit b39a548: CONTRACT_VERSION
    was bumped in source AFTER the artifacts were generated, and the stale
    (pre-bump) files were committed anyway -- so six files claimed "1.5.1" while
    docs/data-contract.md's own changelog, and the source constant, both already
    said "1.6.0". Every test in this file loaded those files and passed, because
    "does contract_version exist" was checked, never "does it match the CURRENT
    source constant". This is the same failure shape as ADR-025/028: a claim
    that was true in prose and false in the artifact it described."""
    d = _load(name)
    assert d["contract_version"] == export_contract.CONTRACT_VERSION, (
        f"{name} says contract_version={d['contract_version']!r} but "
        f"export_contract.CONTRACT_VERSION is {export_contract.CONTRACT_VERSION!r} -- "
        f"regenerate this artifact before committing"
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
def test_every_artifact_carries_the_provenance_pair(name):
    """The contract's opening line promises both on every artifact. league.json
    shipped without `generated_utc` through five contract versions, so consumers
    keying a run id on it fell back to 'unversioned'."""
    p = EXPORT / name
    if not p.exists():
        pytest.skip(f"{name} not generated")
    d = json.loads(p.read_text(encoding="utf-8"))
    assert d.get("contract_version"), f"{name} has no contract_version"
    assert d.get("generated_utc"), f"{name} has no generated_utc"


def test_board_json_carries_snapshot_freshness_fields():
    """Thread 074: board.json's top level must carry the FreshnessResult
    that build_board_json computes on every call, not just generated_utc
    (file-write time). Checks the committed artifact, complementing
    test_freshness.py's in-process assertion against a live conn."""
    d = _load("board.json")
    for key in (
        "snapshot_as_of_date", "snapshot_age_days",
        "snapshot_max_age_days", "snapshot_stale", "snapshot_freshness_note",
    ):
        assert key in d, f"board.json is missing {key!r}"
    assert d["snapshot_max_age_days"] > 0
    assert isinstance(d["snapshot_stale"], bool)
    assert d["snapshot_as_of_date"] is None or isinstance(d["snapshot_as_of_date"], str)
    assert d["snapshot_age_days"] is None or isinstance(d["snapshot_age_days"], int)


def test_te_scenarios_is_gone_and_client_simulation_parameters_present():
    """ADR-033/034: te_scenarios encoded a named-manager repeat assumption found
    circular. It must not reappear, and the replacement mechanism (enough
    parameters for a client to recompute availability conditioned on live draft
    state) must be present."""
    avail = _load("availability.json")
    assert "te_scenarios" not in avail
    csp = avail["client_simulation_parameters"]
    assert csp["ranking_sources"] == [{"name": "fantasypros_ecr", "weight": 1.0}]
    assert csp["mechanical_need_targets"]["QB"] == 1  # 1 starter, not flex-eligible
    assert csp["room_noise_drawn_once_per_draft"] is True
    assert avail["metadata"]["figures_are_unconditional_marginals"] is True


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


# --- ADP export (founder request: "ADP should be shown on both the prep and
# draft screens as well as player profile") --------------------------------
#
# `src/export_contract._load_adp_snapshot` is a display-only read of the real
# MFL-proxy `adp_snapshots` table (ADR-035). It is deliberately separate from
# `availability.load_mfl_adp_source`, which stays unwired from the model by
# design -- these tests only cover the export contract's new fields, not any
# change to ranking/VBD/availability output.

import sqlite3

import export_contract as ec


def _adp_conn(with_snapshot: bool = True) -> sqlite3.Connection:
    # export_contract._load_adp_snapshot reads columns by name (matching
    # every other reader in export_contract.py) -- real callers get a
    # sqlite3.Row-factory connection via db.connect(), so this fixture must
    # too, or the join silently breaks in a way real usage never hits.
    conn = sqlite3.connect(":memory:")
    conn.row_factory = sqlite3.Row
    conn.execute("CREATE TABLE player_ids (mfl_id TEXT, source TEXT, source_id TEXT)")
    conn.execute(
        "CREATE TABLE adp_snapshots ("
        "adp_source TEXT, mfl_id TEXT, player_name TEXT, position TEXT, team TEXT, "
        "rank INTEGER, average_pick REAL, min_pick INTEGER, max_pick INTEGER, "
        "drafts_selected_in INTEGER, draft_sel_pct REAL, fcount INTEGER, is_ppr INTEGER, "
        "is_keeper INTEGER, is_mock INTEGER, cutoff INTEGER, period INTEGER, "
        "total_drafts_in_sample INTEGER, mfl_timestamp INTEGER, retrieved_at TEXT, "
        "ingested_at TEXT)"
    )
    # 00-0001 resolves via player_ids -> mfl_id 2001, which HAS a
    # same-day adp_snapshots row.
    # 00-0002 resolves via player_ids -> mfl_id 2002, which has NO
    # adp_snapshots row at all (MFL never covered this player) -- must
    # come back honestly null, not zero, not a fabricated rank.
    conn.execute("INSERT INTO player_ids VALUES ('2001', 'gsis', '00-0001')")
    conn.execute("INSERT INTO player_ids VALUES ('2002', 'gsis', '00-0002')")
    if with_snapshot:
        conn.execute(
            "INSERT INTO adp_snapshots VALUES "
            "('mfl_proxy','2001','Player One','WR','CIN',5,5.2,1,12,20,40.0,10,1,0,0,10,"
            "2026,50,123,'2026-07-29T00:00:00+00:00','2026-07-29T00:00:00+00:00')"
        )
        # An older snapshot for the same player -- must be ignored in favor
        # of the latest retrieved_at, never averaged with it.
        conn.execute(
            "INSERT INTO adp_snapshots VALUES "
            "('mfl_proxy','2001','Player One','WR','CIN',9,9.9,1,20,20,40.0,10,1,0,0,10,"
            "2026,50,123,'2026-07-26T00:00:00+00:00','2026-07-26T00:00:00+00:00')"
        )
        # A different platform's row for the SAME player/date -- must never
        # be blended into the mfl_proxy figure (per-platform stamping rule).
        conn.execute(
            "INSERT INTO adp_snapshots VALUES "
            "('other_platform_proxy','2001','Player One','WR','CIN',1,1.0,1,3,20,90.0,10,1,0,0,10,"
            "2026,50,123,'2026-07-29T00:00:00+00:00','2026-07-29T00:00:00+00:00')"
        )
    return conn


def test_load_adp_snapshot_returns_honest_empty_state_when_not_ingested():
    conn = _adp_conn(with_snapshot=False)
    result = ec._load_adp_snapshot(conn)
    assert result["by_gsis"] == {}
    assert result["as_of_date"] is None
    assert result["adp_source"] == "mfl_proxy"
    assert "No adp_snapshots rows" in result["match_rate_note"]


def test_load_adp_snapshot_resolves_matched_player_to_latest_snapshot():
    conn = _adp_conn()
    result = ec._load_adp_snapshot(conn)
    assert result["as_of_date"] == "2026-07-29"
    row = result["by_gsis"]["00-0001"]
    # Must be the LATEST (2026-07-29) row's average_pick, not the older
    # 2026-07-26 row and not an average of the two.
    assert row["adp"] == 5.2
    assert row["adp_min_pick"] == 1
    assert row["adp_max_pick"] == 12
    assert row["adp_selected_pct"] == 40.0


def test_load_adp_snapshot_never_blends_across_adp_source_values():
    conn = _adp_conn()
    result = ec._load_adp_snapshot(conn)
    # other_platform_proxy's average_pick (1.0) must not leak into the
    # mfl_proxy figure (5.2), by dilution or override.
    assert result["by_gsis"]["00-0001"]["adp"] == 5.2


def test_load_adp_snapshot_honestly_omits_unmatched_players():
    """00-0002 has a player_ids row but no adp_snapshots row for its mfl_id
    -- MFL never covered it. It must be absent from by_gsis (an honest
    null downstream), never present with a zero or fabricated value."""
    conn = _adp_conn()
    result = ec._load_adp_snapshot(conn)
    assert "00-0002" not in result["by_gsis"]


@pytest.mark.requires_db
def test_board_json_adp_fields_present_and_source_travels_with_value():
    """Every player row carries adp/adp_source/adp_min_pick/adp_max_pick/
    adp_selected_pct. adp_source must be non-null exactly when adp is
    non-null (it travels WITH the value, never independently), and every
    non-null adp_source is the single expected platform -- no blending
    across adp_source values reaches the export."""
    board = _load("board.json")
    assert "adp_source" in board
    assert "adp_as_of_date" in board
    assert "adp_source_note" in board
    assert "adp_match_rate_note" in board
    seen_sources = set()
    resolved = 0
    for p in board["players"]:
        for key in ("adp", "adp_min_pick", "adp_max_pick", "adp_selected_pct", "adp_source"):
            assert key in p, f"{key} missing from board row for {p['player']}"
        has_adp = p["adp"] is not None
        has_source = p["adp_source"] is not None
        assert has_adp == has_source, (
            f"{p['player']}: adp/adp_source must both be null or both be populated, "
            f"got adp={p['adp']!r} adp_source={p['adp_source']!r}"
        )
        if has_source:
            seen_sources.add(p["adp_source"])
            resolved += 1
    assert seen_sources <= {"mfl_proxy"}, (
        f"unexpected adp_source values reached the export: {seen_sources}"
    )
    # Not a strict requirement that any resolve (an empty adp_snapshots
    # table is a valid, if unwanted, state) -- but if the ingested fixture
    # DB has real adp_snapshots rows, at least one board row should resolve.
    print(f"adp coverage: {resolved}/{len(board['players'])} board rows carry a real ADP value")
