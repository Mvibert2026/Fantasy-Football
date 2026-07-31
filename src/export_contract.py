"""
Front-end data contract: emit stable JSON artifacts to data/export/.

The UI codes against these files, never against data/nfl.db. Schemas are
documented and versioned in docs/data-contract.md.

ON THE STRUCTURAL / EVALUATIVE SPLIT. The contract asks board.json to attribute
each player's rank movement to league-format corrections (structural) versus
everything else (evaluative). The structural part is computed exactly, by
rebuilding the board under published 12-team replacement levels and differencing.

The evaluative part is emitted as **null, deliberately**. The current board
assigns every player at the same positional consensus rank an identical
projection (ADR-017) -- it holds no player-level opinion at all, because no
component-level projection source exists (test-registry #2). There is therefore
nothing to attribute, and inventing a split would be fabricating a number the
board does not contain. `evaluative_adjustment_note` says so in each record.
"""

from __future__ import annotations

import argparse
import csv
import dataclasses
import json
import sqlite3
from collections import defaultdict
from datetime import date, datetime, timezone
from pathlib import Path
from typing import Dict, List, Optional

import numpy as np

import availability as av
import db as dbmod
import draft_sim as ds
import export_history as eh
import freshness as fr
import league_config as lc
import make_board
import roster_status as rst
import standard_scoring
import suspensions as susp
import team_codes as tc
from config import DEFAULT_CONFIG
from scoring import LEAGUE, ReplacementLevels

CONTRACT_VERSION = "1.18.0"
SEASON = 2026
DATA_DIR = Path(__file__).resolve().parent.parent / "data"
EXPORT_DIR = DATA_DIR / "export"

# T4 (interim, thread 057): real, hand-curated, WebSearch-verified suspension
# list -- see the file's own _comment for the research trail and why it is
# currently empty. NOT the synthetic tests/fixtures/suspensions_2026.json
# (that one stays synthetic and exists purely to unit-test the mechanism in
# tests/test_suspensions.py). This is the one the live board actually reads.
SUSPENSIONS_PATH = DATA_DIR / "suspensions_2026.json"

# The 12-team convention public boards implicitly assume: 1QB/2RB/3WR/1TE, no
# flex share -> QB12 / RB24 / WR36 / TE12. Differencing our board against this
# one isolates the replacement-level effect exactly. FIXED regardless of
# which league is being built -- this is a reference point for "how does this
# league's structure compare to the generic public convention", which is a
# meaningful comparison for ANY league, not a per-league parameter.
PUBLISHED_LEVELS = ReplacementLevels(
    teams=12, starters={"QB": 1, "RB": 2, "WR": 3, "TE": 1}, flex_slots=0, flex_split={}
)


def export_dir_for(league_id: str) -> Path:
    """ADR-041: the primary league keeps the unprefixed data/export/ path so
    the front-end session's existing sync is never disrupted. Every other
    league gets its own directory, same filenames, same shape."""
    return EXPORT_DIR if league_id == lc.PRIMARY_LEAGUE_ID else EXPORT_DIR / league_id


def avail_csv_for(league_id: str) -> Path:
    if league_id == lc.PRIMARY_LEAGUE_ID:
        return DATA_DIR / "availability_2026.csv"
    return DATA_DIR / "leagues" / league_id / "availability.csv"


def _canonical_team(code: Optional[str]) -> Optional[str]:
    """T9: resolve a team code to its canonical franchise, failing OPEN (not
    raising) if the code is unrecognized -- an unresolved code should show up
    as a missing bye_week for that team (caught by the T3 positive-coverage
    test), not crash the whole board build. team_codes.py is the source of
    truth for the mapping itself."""
    try:
        return tc.to_canonical(code)
    except KeyError:
        return code


def _bye_weeks(season: int) -> Dict[str, Optional[int]]:
    import nflreadpy as nfl
    import polars as pl
    from nflreadpy.config import update_config

    update_config(cache_mode="filesystem")
    s = nfl.load_schedules(seasons=[season]).filter(pl.col("game_type") == "REG")
    weeks = set(s["week"].to_list())
    teams = sorted(set(s["home_team"].to_list()) | set(s["away_team"].to_list()))
    out: Dict[str, Optional[int]] = {}
    for t in teams:
        played = set(
            s.filter((pl.col("home_team") == t) | (pl.col("away_team") == t))["week"].to_list()
        )
        missing = sorted(weeks - played)
        # T9: schedule team codes are already canonical (nflreadpy's own
        # convention), but canonicalize anyway so this dict's keys always
        # agree with whatever the caller canonicalizes its lookup key to.
        out[_canonical_team(t)] = missing[0] if len(missing) == 1 else None
    return out


def _load_availability_csv(csv_path: Path) -> Dict[str, dict]:
    by_player: Dict[str, Dict[str, Dict[str, float]]] = defaultdict(lambda: defaultdict(dict))
    by_tier: Dict[str, Dict[str, Dict[str, Dict[str, float]]]] = defaultdict(
        lambda: defaultdict(lambda: defaultdict(dict))
    )
    if not csv_path.exists():
        return {"by_player": {}, "by_tier": {}}
    with csv_path.open(encoding="utf-8") as f:
        for row in csv.DictReader(f):
            sig = f"sigma_{int(float(row['sigma']))}"
            if row["record_type"] == "player_available":
                by_player[row["player"]][row["pick"]][sig] = float(row["value"])
            elif row["record_type"] == "tier_available":
                by_tier[row["position"]][row["tier"]][row["pick"]][sig] = float(row["value"])
    return {
        "by_player": {k: dict(v) for k, v in by_player.items()},
        "by_tier": {p: {t: dict(pk) for t, pk in ts.items()} for p, ts in by_tier.items()},
    }


def _load_adp_snapshot(conn: sqlite3.Connection, adp_source: str = "mfl_proxy") -> dict:
    """Real MFL-proxy ADP (ADR-035, `src/ingest_mfl_adp.py`), joined
    gsis -> `player_ids` -> `mfl_id`, for DISPLAY only.

    This is deliberately a separate, additive read from
    `availability.load_mfl_adp_source` -- that function feeds the hazard
    model and stays unwired by design (see its docstring). This one only
    supplies board.json fields for the UI to render; it changes no ranking,
    no VBD, no availability output.

    Per-platform stamping (CLAUDE.md SS4, the module docstring's stated
    rule): every value returned here comes from exactly one `adp_source`.
    Nothing here averages or blends across `adp_source` values, and the
    caller must carry `adp_source` alongside every `adp` value it displays
    -- a bare "ADP" number with no source attached would assert something
    this pull did not derive.

    Returns {"by_gsis": {...}, "as_of_date": str|None, "fcount": int|None,
    "is_ppr": int|None, "total_drafts_in_sample": int|None,
    "match_rate_note": str}. Empty/None values throughout if no
    adp_snapshots rows exist for `adp_source` -- never raises, mirroring
    `load_mfl_adp_source`'s "an ingestion that hasn't run is a normal state"
    stance.
    """
    row = conn.execute(
        "SELECT MAX(retrieved_at) FROM adp_snapshots WHERE adp_source=?", (adp_source,)
    ).fetchone()
    if row is None or row[0] is None:
        return {
            "adp_source": adp_source,
            "by_gsis": {},
            "as_of_date": None,
            "fcount": None,
            "is_ppr": None,
            "total_drafts_in_sample": None,
            "match_rate_note": f"No adp_snapshots rows for adp_source={adp_source!r}.",
        }
    latest = row[0]

    snap_rows = conn.execute(
        "SELECT mfl_id, average_pick, min_pick, max_pick, draft_sel_pct, fcount, is_ppr, "
        "total_drafts_in_sample FROM adp_snapshots WHERE adp_source=? AND retrieved_at=?",
        (adp_source, latest),
    ).fetchall()
    mfl_by_id = {r["mfl_id"]: r for r in snap_rows}
    gsis_to_mfl: Dict[str, str] = {
        r[0]: r[1] for r in conn.execute(
            "SELECT source_id, mfl_id FROM player_ids WHERE source='gsis'"
        ).fetchall()
    }

    fcounts = {r["fcount"] for r in snap_rows}
    is_ppr_vals = {r["is_ppr"] for r in snap_rows}
    drafts = {r["total_drafts_in_sample"] for r in snap_rows}

    by_gsis: Dict[str, dict] = {}
    for gsis_id, mfl_id in gsis_to_mfl.items():
        r = mfl_by_id.get(mfl_id)
        if r is None:
            continue
        by_gsis[gsis_id] = {
            "adp": r["average_pick"],
            "adp_min_pick": r["min_pick"],
            "adp_max_pick": r["max_pick"],
            "adp_selected_pct": r["draft_sel_pct"],
        }

    return {
        "adp_source": adp_source,
        "by_gsis": by_gsis,
        "as_of_date": latest[:10] if latest else None,
        "fcount": next(iter(fcounts)) if len(fcounts) == 1 else None,
        "is_ppr": next(iter(is_ppr_vals)) if len(is_ppr_vals) == 1 else None,
        "total_drafts_in_sample": next(iter(drafts)) if len(drafts) == 1 else None,
        "match_rate_note": f"{len(by_gsis)} of {len(mfl_by_id)} {adp_source} rows resolved "
                            f"a gsis id via player_ids.",
    }


def _ppr_format_description(ppr: float) -> str:
    """Plain-English description of a reception value, for prose that must
    describe WHATEVER league it is building for -- never a hardcoded format
    name. 0 / 0.5 / 1.0 are this project's only in-use values (Westwood's
    scoring.LEAGUE and standard_scoring.py's three presets); anything else
    still gets an honest, non-crashing description rather than a KeyError."""
    if ppr == 0:
        return "standard (0-PPR, no points per reception)"
    if ppr == 0.5:
        return "half-PPR (0.5 points per reception)"
    if ppr == 1.0:
        return "full-PPR (1 point per reception)"
    return f"{ppr}-point-per-reception"


def _adp_source_note(cfg: lc.LeagueConfig, adp_snapshot: dict) -> str:
    """The adp_source_note text, DERIVED from `cfg` -- never hardcoded to any
    one league's ruleset.

    FR-083 (2026-07-30): this note used to assert, verbatim, "this league
    scores half-PPR" for every league board.json is built for, because the
    prose was hand-written once for Westwood and never parameterized.
    Reproduced live against a real STANDARD/0-PPR preset (espn_10_standard),
    which carried the identical false sentence. See
    docs/handoffs/NEW-adp-and-history-not-league-scoring-aware.md.

    This function computes the comparison fresh from cfg.scoring and the
    snapshot's own IS_PPR flag/fcount, so the claim is true for whichever
    league cfg describes -- including the case where MFL's capture happens
    to match this league's format exactly (previously that case was never
    even considered; the note always warned about a half-PPR gap that may
    not exist for this league at all).
    """
    league_ppr = cfg.scoring["offense"]["receptions"]
    league_format = _ppr_format_description(league_ppr)

    mfl_ppr = adp_snapshot["is_ppr"]
    mfl_format = {1: "full-PPR", 0: "standard (non-PPR)"}.get(
        mfl_ppr, "an unrecorded PPR setting"
    )
    format_matches = (mfl_ppr == 1 and league_ppr == 1.0) or (mfl_ppr == 0 and league_ppr == 0)

    fcount = adp_snapshot["fcount"]
    fcount_note = (
        "matching this league's team count"
        if fcount is not None and fcount == cfg.teams
        else f"a {fcount}-team pull, NOT this league's {cfg.teams}-team format"
    )

    format_comparison = (
        "These match, so the reception-value gap this note otherwise warns about does not "
        "apply here -- MFL's capture is a reasonable format proxy for this league."
        if format_matches else
        "MFL's IS_PPR flag is binary and cannot express this league's own reception value "
        f"({league_ppr}), so treat the capture as an approximation, not an exact match: "
        "drafters under a higher PPR value take pass-catchers earlier than drafters under a "
        "lower one, so receiver ADP here may run ahead of or behind where this league would "
        "actually take them, depending on the direction of the mismatch."
    )

    return (
        "adp/adp_min_pick/adp_max_pick/adp_selected_pct on each player row come from "
        f"MyFantasyLeague's public aggregate ADP endpoint (adp_source={adp_snapshot['adp_source']!r}, "
        "ADR-035), NOT this league's own draft history and NOT a blend of platforms -- "
        "adp_source travels with every value and must never be merged with a differently-"
        "sourced ADP number. The population is whoever drafts on MFL (largely dynasty/"
        f"redraft hobbyists), not this league's roster. Captured at FCOUNT={fcount} "
        f"({fcount_note}) and IS_PPR={mfl_ppr} ({mfl_format}), while THIS league "
        f"({cfg.league_id!r}) scores {league_format}. {format_comparison} Sample size is thin "
        f"(total_drafts_in_sample={adp_snapshot['total_drafts_in_sample']}) and MFL only "
        "covers roughly the top ~230 players in a 10-team pull -- most of the board has no "
        "MFL opinion at all, and that is a real null (adp=None), never a fabricated rank. "
        "See adp_match_rate_note for how many of this board's rows actually resolved."
    )


def _not_built_board_json(cfg: lc.LeagueConfig, selection: str, desc: dict) -> dict:
    """FR-2026-07-30: a named source with no implementation returns an
    explicit, honest 'not built' shape -- never a silent fallback to another
    source's board. See make_board.RankingSourceNotBuilt."""
    return {
        "contract_version": CONTRACT_VERSION,
        "generated_utc": datetime.now(timezone.utc).isoformat(),
        "league_id": cfg.league_id,
        "season": SEASON,
        "ranking_source_selection": selection,
        "ranking_source_label": desc["label"],
        "ranking_source_built": False,
        "ranking_source_note": desc["note"],
        "ranking_source_as_of_date": None,
        "ranking_source_row_count": None,
        "players": [],
    }


def build_board_json(
    conn: sqlite3.Connection,
    cfg: lc.LeagueConfig = lc.CURRENT_LEAGUE,
    enforce_freshness: bool = True,
    freshness_today=None,
    suspensions_path: Path = SUSPENSIONS_PATH,
    ranking_source_selection: str = "expert_adjusted",
) -> dict:
    """`ranking_source_selection` (FR-2026-07-30, default "expert_adjusted"
    -- byte-identical to this function's pre-existing behavior when the
    caller does not pass it) picks which of the four founder-facing sources
    drives this board. See make_board.RANKING_SOURCE_SELECTIONS.

    'proprietary' returns an explicit not-built shape (see
    _not_built_board_json) rather than raising or falling back -- the
    caller/CLI decides what a client should see for an unbuilt source, this
    function never silently substitutes a different one under that label."""
    if ranking_source_selection not in make_board.RANKING_SOURCE_SELECTIONS:
        raise ValueError(
            f"unknown ranking_source_selection {ranking_source_selection!r}; "
            f"must be one of {make_board.RANKING_SOURCE_SELECTIONS}"
        )
    if ranking_source_selection == "proprietary":
        return _not_built_board_json(
            cfg, ranking_source_selection,
            make_board.describe_ranking_source(conn, SEASON, ranking_source_selection),
        )

    # T5 (fable-draft-day-premortem-2026-07-27.md finding #2): refuse to
    # build the live board from a snapshot older than
    # cfg.freshness_max_age_days, and always print the age -- even when
    # comfortably fresh -- so staleness is visible before it is a problem,
    # not only once it crosses the line. `enforce_freshness=False` exists
    # only for callers that intentionally want the report without the raise
    # (none currently do; kept for the same reason require_fresh/
    # check_freshness are two functions in freshness.py rather than one with
    # a raise flag).
    #
    # Freshness enforcement is only wired against `rankings`-table sources
    # (expert_adjusted/expert_raw) -- freshness.py has no analogous gate for
    # ffc_adp_snapshots (market_adp) yet. market_adp's own as_of_date/row
    # count is still reported honestly below via describe_ranking_source;
    # it is just not a hard build-time cutoff the way the expert sources are.
    if ranking_source_selection == "market_adp":
        source_desc = make_board.describe_ranking_source(conn, SEASON, ranking_source_selection)
        freshness_check = {
            "as_of_date": source_desc["as_of_date"], "age_days": None,
            "max_age_days": cfg.freshness_max_age_days, "stale": None,
        }
        print(f"[freshness] market_adp as_of={source_desc['as_of_date']} (no enforcement gate)")
    else:
        checker = fr.require_fresh if enforce_freshness else fr.check_freshness
        freshness_check = checker(
            conn, SEASON, make_board.SOURCE, cfg.freshness_max_age_days,
            today=freshness_today,
        )
        print(
            f"[freshness] {make_board.SOURCE} as_of={freshness_check['as_of_date']} "
            f"age={freshness_check['age_days']}d "
            f"(max {freshness_check['max_age_days']}d) stale={freshness_check['stale']}"
        )

    levels, flex_split_measured = ReplacementLevels.from_league_config(cfg)
    ours, curves = make_board.build_board(
        conn, SEASON, levels=levels, n_bootstrap=2000, scoring_cfg=cfg.scoring,
        ranking_source_selection=ranking_source_selection,
    )
    published, _ = make_board.build_board(
        conn, SEASON, levels=PUBLISHED_LEVELS, n_bootstrap=0, scoring_cfg=cfg.scoring,
        ranking_source_selection=ranking_source_selection,
    )
    pub_rank = {r.player: r.overall_rank for r in published}

    # Must match the source `ours`/`published` were built from -- these rows
    # feed team_of/pos_rank (positional_rank, positional_label, team) for the
    # SAME players `ours` ranks. Using a different, stale source here would
    # silently desync team/positional-rank display from the board's actual
    # player set (thread 053/067 rewire finding).
    if ranking_source_selection == "market_adp":
        # ffc_adp_snapshots has no scoring_format column -- unlike the
        # rankings-table sources, never fabricate one here (see
        # board_scoring_format below, left None for this selection).
        latest = conn.execute(
            "SELECT MAX(retrieved_at) FROM ffc_adp_snapshots WHERE adp_source=?",
            (make_board.MARKET_ADP_SOURCE,),
        ).fetchone()[0]
        meta = conn.execute(
            "SELECT player_name, team, position, NULL AS scoring_format "
            "FROM ffc_adp_snapshots WHERE adp_source=? AND retrieved_at=? "
            "AND position IN ('QB','RB','WR','TE')",
            (make_board.MARKET_ADP_SOURCE, latest),
        ).fetchall() if latest else []
        # market_adp's positional order must come from the SAME resolved,
        # ADP-ordered rows the board itself used (average_pick order), not a
        # second independent read of ffc_adp_snapshots -- otherwise an
        # unresolved player could silently reappear in pos_rank/team_of
        # while being absent from `ours`.
        adp_rows, _as_of, _n_resolved, _n_total = make_board._consensus_board_market_adp(
            conn, SEASON
        )
        by_pos_source = adp_rows
    else:
        # as_of_date filter: `rankings` now holds MULTIPLE dated snapshots per source
        # (2026-07-27 and 2026-07-30 as of this writing). Without it every player
        # appears once per snapshot -- 1037 rows for 574 distinct ranks, caught by
        # test_consensus_rank_is_unique_across_players. History stays in the table
        # deliberately; CLAUDE.md §6.1 needs as-of-date-correct reads for backtesting.
        # The *current* board always takes the newest.
        meta = conn.execute(
            "SELECT player_name, team, position, adp_rank, scoring_format FROM rankings "
            "WHERE source=? AND season=? AND as_of_date = "
            "  (SELECT MAX(as_of_date) FROM rankings WHERE source=? AND season=?)",
            (make_board.SOURCE, SEASON, make_board.SOURCE, SEASON),
        ).fetchall()
        by_pos_source = meta
    # scoring_format is a column the old fantasypros_ecr mirror never carried
    # (NULL for every row); the new CSV source has a real value per row
    # (thread 053, ingest_fantasypros_csv.py). Read it from the data rather
    # than hardcoding "half_ppr" here, so a future source/league with a
    # different confirmed format doesn't silently mislabel itself.
    scoring_formats = {r["scoring_format"] for r in meta if r["scoring_format"]}
    board_scoring_format = (
        next(iter(scoring_formats)) if len(scoring_formats) == 1 else None
    )
    team_of = {r["player_name"]: r["team"] for r in meta}
    byes = _bye_weeks(SEASON)

    # positional rank by this SOURCE's own order (by_pos_source, not `meta` --
    # for market_adp `meta` has no adp_rank column at all; by_pos_source is
    # always the rows the board itself was built from).
    by_pos: Dict[str, List] = defaultdict(list)
    for r in sorted(by_pos_source, key=lambda x: x["adp_rank"]):
        by_pos[r["position"]].append(r["player_name"])
    pos_rank = {n: i + 1 for pos, names in by_pos.items() for i, n in enumerate(names)}

    # FR-057 part 1 (contract 1.15.0): the CSV/availability.json now cover
    # EVERY slot's pick numbers, not just cfg.user_draft_slot's -- but
    # board.json is a different, much more frequently loaded artifact and
    # embeds this per player. Un-filtered, that meant board.json inherited
    # the full ~10x growth too (measured: 1,020,368 -> 2,276,988 bytes for
    # the primary league, more than doubling an artifact loaded on every
    # page view for a feature FR-057 never asked board.json to carry).
    # Restrict this embed back to cfg's OWN pick numbers, exactly the slice
    # board.json has always carried -- availability.json is where the
    # multi-slot data belongs; board.json's per-player availability is
    # unchanged in shape and size by this contract bump.
    _own_picks = set(str(p) for p in (
        ds.user_pick_numbers() if cfg.is_primary else ds.DraftEngine(cfg).user_pick_numbers()
    ))
    avail_all_slots = _load_availability_csv(avail_csv_for(cfg.league_id))["by_player"]
    avail = {
        player: {pk: sig for pk, sig in picks.items() if pk in _own_picks}
        for player, picks in avail_all_slots.items()
    }
    adp_snapshot = _load_adp_snapshot(conn)
    adp_by_gsis = adp_snapshot["by_gsis"]

    players = []
    for r in ours:
        pr = pos_rank.get(r.player)
        tier_label = None
        if pr and r.position in av.TIERS:
            tier_label = next(
                (t for t, (lo, hi) in av.TIERS[r.position].items() if lo <= pr <= hi), "T5+"
            )
        tier_int = int(tier_label[1]) if tier_label and tier_label[1].isdigit() else 5
        team = team_of.get(r.player)
        # T9: team_of is FantasyPros' spelling (e.g. JAC/LAR); byes is keyed
        # by nflverse's canonical spelling (JAX/LA). Canonicalize the lookup
        # key -- the export's "team" field itself stays as FantasyPros wrote
        # it, since that's a display value, not a join key.
        bye_lookup_team = _canonical_team(team) if team else None
        structural = (pub_rank.get(r.player, r.overall_rank) - r.overall_rank)
        adp_row = adp_by_gsis.get(r.player_id) if r.player_id else None
        players.append({
            # Stable integer id: the design contract keys availability and the
            # player-profile endpoint on an int, and gsis_id strings are not
            # usable as such. Derived from overall_rank so it is deterministic
            # for a given board generation.
            "id": r.overall_rank,
            # Thread 052: was hardcoded None. rankings.player_id (which
            # BoardRow.player_id now carries through, make_board.py) is a
            # gsis_id -- ingest_rankings.py joins fantasypros_id -> gsis_id
            # and aliases the result as player_id at ingest time -- the same
            # id space player_weekly_stats.player_id uses, which is the join
            # key weekly_finishes.json/season_stats.json expose (thread
            # 017/039, src/export_history.py). Populating this field with
            # that value, rather than inventing a second identifier scheme,
            # is what makes board.json joinable to those two exports.
            "player_id_gsis": r.player_id,
            "overall_rank": r.overall_rank,
            "player": r.player,
            "position": r.position,
            "positional_rank": pr,
            "positional_label": f"{r.position}{pr}" if pr else None,
            "team": team,
            "bye_week": byes.get(bye_lookup_team) if bye_lookup_team else None,
            # T6 (interim, no new ingestion): a PROXY, not a real roster-status
            # feed -- see src/roster_status.py's docstring for exactly what it
            # does and does not catch. "active" / "no_active_contract_on_file"
            # / "unknown_no_contract_data". The UI must not present
            # "no_active_contract_on_file" as a confirmed retirement.
            "roster_status": rst.contract_status(conn, r.player_id),
            "projected_points": r.projected_points,
            "ci_low": None if np.isnan(r.vbd_lo) else r.vbd_lo,
            "ci_high": None if np.isnan(r.vbd_hi) else r.vbd_hi,
            "ci_applies_to": "vbd",
            # The rank->points curve is fitted only within draft-relevant depth
            # (QB20/RB45/WR60/TE20). Past that, projected_points and vbd are
            # EXTRAPOLATIONS and no honest interval exists for them. The design
            # contract says never ship a projection without a CI; we cannot
            # manufacture one, so we flag it and the UI must suppress the number
            # rather than render false precision.
            "projection_within_fitted_range": bool(
                pr is not None and pr <= make_board.RELEVANT_DEPTH.get(r.position, 0)
            ),
            "projection_note": (
                None
                if pr is not None and pr <= make_board.RELEVANT_DEPTH.get(r.position, 0)
                else "Beyond the fitted range of the projection curve. Extrapolated, no "
                     "interval available -- do not display a point projection for this player."
            ),
            "vbd": r.vbd,
            "consensus_rank": r.consensus_rank,
            "delta_vs_consensus": r.delta_vs_consensus,
            "tier": tier_int,
            "tier_label": tier_label,
            "structural_adjustment": r.delta_vs_consensus,
            "structural_breakdown": {
                "replacement_levels": structural,
                "scoring_and_vbd_method": r.delta_vs_consensus - structural,
            },
            # ZERO, not null, so the design contract's additivity check holds:
            #   consensus_rank - structural_adjustment - evaluative_adjustment == overall_rank
            # But zero here is a real measurement, not a placeholder: this board
            # has no player-level opinion to attribute. The companion flag tells
            # the UI to suppress the evaluative row rather than render "+0" for
            # every player, which would make the feature look broken instead of
            # absent.
            "evaluative_adjustment": 0,
            "evaluative_adjustment_available": False,
            "evaluative_adjustment_note": (
                "Zero by construction, not by omission. This board assigns every player at "
                "the same positional consensus rank an identical projection, so it holds no "
                "player-level opinion to attribute. All rank movement is structural. A real "
                "evaluative component requires component-level projections (test-registry #2), "
                "which no accessible source provides. SUPPRESS this row in the UI while "
                "evaluative_adjustment_available is false."
            ),
            "availability": avail.get(r.player, {}),
            # Real MFL-proxy market ADP (ADR-035), for DISPLAY only -- does
            # NOT feed the model (availability.load_mfl_adp_source stays
            # unwired by design, see that function's docstring). Honestly
            # null when this player has no gsis->mfl_id match or MFL itself
            # never covered them (MFL's snapshot only reaches ~230 players
            # in a 10-team pull) -- never a fabricated rank, never zero.
            # `adp_source` MUST travel with `adp` any time the UI displays
            # it: this is one platform's behavioural sample, not this
            # league's ADP, and must never be presented as a blended
            # consensus figure alongside other ADP sources.
            "adp": adp_row["adp"] if adp_row else None,
            "adp_min_pick": adp_row["adp_min_pick"] if adp_row else None,
            "adp_max_pick": adp_row["adp_max_pick"] if adp_row else None,
            "adp_selected_pct": adp_row["adp_selected_pct"] if adp_row else None,
            "adp_source": adp_snapshot["adp_source"] if adp_row else None,
        })

    # T4 (interim, thread 057): deterministic games-adjustment for known
    # suspensions -- see src/suspensions.py's docstring. Deliberately applied
    # to every league's board via this shared path (same reasoning as T5
    # freshness: the mechanism is structural, not league-specific). Reads
    # SUSPENSIONS_PATH by default, which is currently an empty, real,
    # sourced list (see that file's _comment) -- an empty list is a no-op
    # here (every row gets suspension_flag=False), which is the correct,
    # honest behavior, not a bug.
    known_suspensions = susp.load_suspensions(suspensions_path)
    players = susp.apply_suspension_flags(players, known_suspensions)

    # Positions this league rosters as starters but that have no scoring
    # engine (K, DEF -- no kicker or DST stats are ingested, ADR-039/041).
    # Generalizes the old DEF-only hardcode to any such position.
    unsupported = sorted(
        p for p in cfg.starters if p not in ReplacementLevels.SCOREABLE_POSITIONS
    )

    return {
        "contract_version": CONTRACT_VERSION,
        "generated_utc": datetime.now(timezone.utc).isoformat(),
        # T5 (thread 074): the FreshnessResult computed above via
        # fr.require_fresh/check_freshness was being printed to the build
        # console and then discarded -- board.json only carried generated_utc,
        # which is the FILE WRITE time, not the underlying rankings snapshot's
        # as_of_date. Those are different claims (a board built today from a
        # 20-day-old snapshot has a fresh generated_utc and a stale snapshot).
        # Attach the actual FreshnessResult fields so the UI can render real
        # staleness instead of conflating the two.
        "snapshot_as_of_date": freshness_check["as_of_date"],
        "snapshot_age_days": freshness_check["age_days"],
        "snapshot_max_age_days": freshness_check["max_age_days"],
        "snapshot_stale": freshness_check["stale"],
        "snapshot_freshness_note": (
            "as_of_date/age_days/stale describe the rankings snapshot "
            f"({make_board.SOURCE!r}, season {SEASON}) that this board was built from -- "
            "NOT when this board.json file was written (see generated_utc for that). "
            "stale=True means the snapshot exceeded snapshot_max_age_days as of build time; "
            "enforce_freshness=True builds refuse to proceed past that point at all, so a "
            "stale=True board only reaches this file when enforce_freshness was explicitly "
            "disabled."
        ),
        "league_id": cfg.league_id,
        "season": SEASON,
        # FR-2026-07-30 (four selectable ranking sources): which of the four
        # founder-facing sources drove THIS board, and this source's OWN
        # as_of_date/row count -- never a shared or blended one. See
        # make_board.RANKING_SOURCE_SELECTIONS / describe_ranking_source.
        "ranking_source_selection": ranking_source_selection,
        "ranking_source_label": make_board.RANKING_SOURCE_LABELS[ranking_source_selection],
        "ranking_source_built": True,
        "ranking_source_as_of_date": freshness_check["as_of_date"],
        "ranking_source_row_count": len(players),
        "ranking_source_note": (
            "Board order is our VBD curve applied to this source's positional ranks -- our "
            "value judgement, re-scored into this league's structure."
            if ranking_source_selection == "expert_adjusted" else
            "Board order is this source's own unmodified rank, never re-derived from our VBD "
            "curve. projected_points/vbd are still shown (our value curve applied to this "
            "order) for comparison, but never change which player is ranked where "
            "(CLAUDE.md sec4 never-blend)."
        ),
        "board_source": (
            "fantasypros_csv_2026draft re-scored into league positional value structure"
        ),
        # The design contract's example shows "blend:4". We have ONE consensus source.
        # ADR-018 found no market ADP legally obtainable at the time; ADR-035
        # partially superseded that with a real MFL ADP proxy, now shown
        # separately (see adp_source/adp_source_note below) -- but it is a
        # separate, much smaller, display-only field, never blended into this
        # consensus_source. Stated explicitly so the UI does not imply a blend.
        "consensus_source": "fantasypros_csv_2026draft",
        "consensus_source_count": 1,
        "consensus_source_note": (
            "Single source. Expert consensus rank, NOT market average draft position, and not "
            "a blend of several providers. A real (if thin and proxy) market ADP is shown "
            "separately below (adp_source='mfl_proxy', ADR-035) -- see adp_source_note -- but "
            "it is never merged into this consensus figure. "
            "Rewired off the old fantasypros_ecr DynastyProcess mirror (thread 053/067): that "
            "source was rank-only, format-blind, and effectively capped; this is the founder's "
            "own FantasyPros export with a confirmed scoring format (see scoring_format below) "
            "and real tier/bye/sos columns. The historical rank->points curve this board's "
            "projections/VBD are fitted on (curve_fits above) still trains on fantasypros_ecr's "
            "multi-season history (2021-2025) -- fantasypros_csv_2026draft is a single one-off "
            "2026 pull with no season history of its own yet."
        ),
        "scoring_format": board_scoring_format,
        "scoring_format_note": (
            "Read from rankings.scoring_format for this board's source, not hardcoded. Null "
            "if the source rows don't carry a confirmed scoring format (e.g. the old "
            "fantasypros_ecr mirror never populated this column) or carry more than one "
            "distinct value."
        ),
        "consensus_state": "preseason_moving",
        "attribution_is_additive": True,
        "attribution_identity": (
            "consensus_rank - structural_adjustment - evaluative_adjustment == overall_rank"
        ),
        "curve_fits": {
            p: {"r_squared": round(c.r_squared, 4), "residual_sd": round(c.residual_sd, 2),
                "n_obs": c.n_obs}
            for p, c in curves.items()
        },
        "curve_caveat": (
            "projected_points comes from E[our_points | position, consensus positional rank]. "
            "R-squared is 0.16-0.27, so consensus rank explains under a third of the variance "
            "in what a player actually scores. Treat projections as weak."
        ),
        "replacement_levels_used": levels.baselines(),
        "replacement_levels_flex_split_measured": flex_split_measured,
        "replacement_levels_flex_split_note": (
            None if flex_split_measured else
            "This league's flex_split was not supplied, so the primary league's measured "
            "split (ADR-029, 26 seasons under ITS scoring rules) is used as an explicitly "
            "flagged placeholder, not a measurement for this league."
        ),
        "published_levels_compared_against": PUBLISHED_LEVELS.baselines(),
        # DEF splits into two questions that had been collapsed into one flag.
        #
        # The replacement RANK is structural arithmetic -- 10 teams x 1 DEF
        # starter = DEF10, the same derivation that yields QB10 -- and needs no
        # player data at all. It is emitted in league.json, which describes the
        # LEAGUE.
        #
        # The replacement POINTS, and therefore any DEF VBD, projection or board
        # row, need DST scoring data. None is ingested (DST rows carry no
        # gsis_id and are dropped at ingest). So no DEF player appears here, and
        # `replacement_levels_used` deliberately excludes DEF: it lists the
        # levels THIS BOARD was built from, and DEF was not one of them.
        "def_supported": "DEF" in cfg.starters and "DEF" not in unsupported,
        "def_note": (
            "DEF is a starting slot in this league but is permanently excluded from the "
            "model: no DST data is ingested, so there is no DEF replacement level, points "
            "projection, VBD or board row. See league.json:positions_without_replacement_levels. "
            "Render this note where a DEF number would go. Do not compute a DEF value from "
            "these files."
        ) if "DEF" in cfg.starters else None,
        # Generalizes def_supported/def_note (kept above, unchanged shape, for
        # backward compatibility) to ANY starter position with no scoring
        # engine -- a Yahoo-style league also rosters K, which has the exact
        # same problem DEF does: no kicker stats are ingested either.
        "unsupported_positions": unsupported,
        "unsupported_positions_note": (
            None if not unsupported else
            f"{', '.join(unsupported)} {'is' if len(unsupported) == 1 else 'are'} rostered "
            f"starting slot(s) with no scoring data ingested, so no replacement level, "
            f"projection, VBD or board row exists for {'it' if len(unsupported) == 1 else 'them'}. "
            f"See league.json:positions_without_replacement_levels."
        ),
        # Real market ADP (ADR-035, MyFantasyLeague proxy), for DISPLAY only
        # -- per-player fields above. This snapshot-level block is the
        # honest-labeling context the founder's request explicitly asked
        # for: which platform, what population, what format assumption, how
        # old, and how many board rows actually resolved to it.
        "adp_source": adp_snapshot["adp_source"],
        "adp_as_of_date": adp_snapshot["as_of_date"],
        "adp_match_rate_note": adp_snapshot["match_rate_note"],
        "adp_source_note": _adp_source_note(cfg, adp_snapshot),
        "players": players,
    }


def _all_slot_pick_numbers(cfg: lc.LeagueConfig) -> Dict[str, List[int]]:
    """Pick-number sequence for EVERY slot 1..cfg.teams, not just cfg's own.

    FR-057 part 1: the multi-slot sweep in run_availability.py already relies
    on pick_order() being independent of which team is "the user" (see that
    module's docstring), which is exactly what makes this cheap -- no
    simulation needed, just the same snake-order arithmetic the frontend's
    slot selector already performs elsewhere. Shipped here too so the
    frontend has ONE source of truth for "which pick numbers belong to slot
    N" instead of a second, independently-written implementation that could
    drift from this one (see FR-057's "two implementations must agree").
    """
    out: Dict[str, List[int]] = {}
    for slot in range(1, cfg.teams + 1):
        if slot == cfg.user_draft_slot:
            out[str(slot)] = ds.user_pick_numbers() if cfg.is_primary else ds.DraftEngine(cfg).user_pick_numbers()
        else:
            out[str(slot)] = ds.DraftEngine(
                dataclasses.replace(cfg, user_draft_slot=slot)
            ).user_pick_numbers()
    return out


def _load_ffc_skill_adp(
    conn: sqlite3.Connection, season_data: "ds.SeasonData", adp_source: str = "ffc_half_ppr_10team"
) -> Dict[str, object]:
    """FFC ADP (thread 119/FR-131), restricted to QB/RB/WR/TE and joined to the
    SAME player universe `ds.load_season` returned -- so its keys line up with
    `by_player`'s by construction, exactly like the consensus-rank block above.

    NOT the model's input today. `simulate_availability` has not switched to
    ADP (that switch is gated on the M0-M5 pre-registration,
    docs/ranking/availability-opponent-model-precommit.md); this is a
    preparatory export for the reformulated shape thread 119's strategist
    reply asked for (thread 104), read fresh from the DB every call so it
    cannot go stale relative to whatever snapshot is actually live.

    Two things are DELIBERATELY NOT done here, both out of a backend
    engineer's scope and explicitly assigned elsewhere in the precommit doc:
      - No axis recalibration (M4(a)): FFC's `average_pick` counts kickers and
        defenses and its sampled drafts run deeper than this league's 16
        rounds, so raw values are on a different axis than a Westwood pick
        number. The precommit doc calls for an isotonic fit against board.json
        to fix this ("returns to strategist before shipping" if material) --
        not invented here. `axis_note` in the caller states this loudly
        instead.
      - No sigma (M0/M2/M3 gate): FFC's `times_drafted` and
        `total_drafts_in_sample` columns do not reconcile (Bijan Robinson
        times_drafted=90 against total_drafts_in_sample=1254 on every row),
        so no per-player sampling-variance weight is trustworthy yet. Nothing
        resembling a sigma value is exported.

    Returns {"by_gsis": {gsis: {"adp_pick": float, "std_dev": float|None,
    "times_drafted": int|None}}, "as_of_date": str|None,
    "sample_window": str|None, "n_skill_rows": int, "adp_source": str}.
    Empty/None throughout if the source has not been ingested -- never raises.
    """
    row = conn.execute(
        "SELECT MAX(retrieved_at) FROM ffc_adp_snapshots WHERE adp_source=?", (adp_source,)
    ).fetchone()
    latest = row[0] if row else None
    if not latest:
        return {
            "by_gsis": {}, "as_of_date": None, "sample_window": None,
            "n_skill_rows": 0, "adp_source": adp_source,
        }
    rows = conn.execute(
        "SELECT f.player_name, f.average_pick, f.std_dev, f.times_drafted, "
        "f.as_of_date, f.sample_window, p.source_id AS gsis "
        "FROM ffc_adp_snapshots f "
        "LEFT JOIN player_ids p ON p.mfl_id = f.mfl_id AND p.source='gsis' "
        "WHERE f.adp_source=? AND f.retrieved_at=? "
        "AND f.position IN ('QB','RB','WR','TE')",
        (adp_source, latest),
    ).fetchall()
    by_gsis: Dict[str, dict] = {}
    as_of_dates = set()
    windows = set()
    for r in rows:
        if r["gsis"]:
            by_gsis[r["gsis"]] = {
                "adp_pick": float(r["average_pick"]) if r["average_pick"] is not None else None,
                "std_dev": float(r["std_dev"]) if r["std_dev"] is not None else None,
                "times_drafted": r["times_drafted"],
            }
        if r["as_of_date"]:
            as_of_dates.add(r["as_of_date"])
        if r["sample_window"]:
            windows.add(r["sample_window"])
    return {
        "by_gsis": by_gsis,
        "as_of_date": max(as_of_dates) if as_of_dates else None,
        "sample_window": next(iter(windows)) if len(windows) == 1 else None,
        "n_skill_rows": len(rows),
        "adp_source": adp_source,
    }


def build_availability_json(
    conn: sqlite3.Connection, cfg: lc.LeagueConfig = lc.CURRENT_LEAGUE
) -> dict:
    payload = _load_availability_csv(avail_csv_for(cfg.league_id))
    # Thread 104 (FR-066 resolution): the per-player rank simulate_availability
    # actually runs its opponent model AND the user's own strategy_bpa pick
    # against -- read via the SAME call (ds.load_season) the simulation itself
    # uses, so this cannot name a source or as_of_date the simulation didn't
    # actually run on. If thread 119 repoints ds.CONSENSUS_RANK_SOURCE at ADP,
    # this follows with zero edits here -- see draft_sim.py's constant
    # docstring. Keyed by data.names[i], the SAME name list run_availability.py
    # writes into the CSV's "player" column, so this lines up with by_player's
    # existing keys by construction, not by convention.
    season_data = ds.load_season(conn, SEASON)
    consensus_ranks_by_name: Dict[str, float] = {
        season_data.names[i]: float(season_data.consensus_rank[i])
        for i in range(len(season_data.names))
    }
    # Thread 119 reformulated thread 104's ask mid-flight: the raw ECR array
    # above is NOT what a client-side recompute should be built against once
    # the opponent model's central tendency moves to ADP (recommended,
    # pending the M0-M5 pre-registration). adp_by_gsis/adp_by_name below is
    # the `{adp_pick, coverage_flag}` shape strategist asked for -- sigma is
    # withheld, not placeholdered, because M0 (times_drafted/
    # total_drafts_in_sample reconciliation) has not cleared. Every key in
    # by_player gets an entry here, coverage_flag True or False, never a
    # silently-missing key -- see docs/handoffs/104-fr066-availability-ranking-source-export.md.
    ffc_adp = _load_ffc_skill_adp(conn, season_data)
    adp_by_name: Dict[str, dict] = {}
    for i, pid in enumerate(season_data.player_ids):
        hit = ffc_adp["by_gsis"].get(pid)
        adp_by_name[season_data.names[i]] = {
            "adp_pick": hit["adp_pick"] if hit else None,
            "coverage_flag": hit is not None,
        }
    n_covered = sum(1 for v in adp_by_name.values() if v["coverage_flag"])
    is_primary = cfg.is_primary
    engine = None if is_primary else ds.DraftEngine(cfg)
    user_picks = ds.user_pick_numbers() if is_primary else engine.user_pick_numbers()
    need_targets = (
        dict(ds.MECHANICAL_NEED_TARGETS) if is_primary else ds.mechanical_need_targets_for(cfg)
    )
    max_at_pos = (
        {"QB": 3, "RB": 8, "WR": 9, "TE": 3} if is_primary
        else ds.default_max_at_position_for(cfg)
    )
    payload.update({
        "contract_version": CONTRACT_VERSION,
        "generated_utc": datetime.now(timezone.utc).isoformat(),
        "league_id": cfg.league_id,
        "metadata": {
            "season": SEASON,
            "simulations_per_setting": 3000,
            "sigma_values": list(ds.SIGMA_SWEEP),
            "sigma_plain_english": (
                "Sigma is how far the other opposing teams stray from consensus, measured in "
                "draft picks: 5 is a disciplined room, 10 is about one round of slippage (the "
                "default), 20 is chaotic. It is a guess, not fitted to observed drafts, which "
                "is why every number is given at all three settings."
            ),
            "user_draft_slot": cfg.user_draft_slot,
            "user_picks": user_picks,
            "reliability_note": (
                "These probabilities never pass through the projection curve, so they are the "
                "most reliable numbers in the project. They describe draft behaviour, not "
                "football outcomes."
            ),
            "figures_are_unconditional_marginals": True,
            "marginals_note": (
                "by_player and by_tier average over every possible draft (Prep mode) -- they "
                "are NOT conditioned on picks actually made so far. Mid-draft, recompute with "
                "client_simulation_parameters against the real board state instead of reading "
                "these numbers as still current. See data-contract.md."
            ),
            # FR-057 part 1 (contract 1.15.0). run_availability.py now sweeps
            # EVERY draft slot 1..teams, not just user_draft_slot above, and
            # merges the results into by_player/by_tier keyed by OVERALL pick
            # number (1..teams*rounds) rather than nesting a nesting level per
            # slot -- see run_availability.py's module docstring for why a
            # merge is safe (no two slots ever write the same pick number).
            # Practical effect: switching the draft-slot selector to slot N
            # and looking up picks_by_slot["N"] in by_player/by_tier now finds
            # real numbers instead of missing keys. Client-side recomputation
            # conditioned on live picks (FR-057 part 2, the founder's stated
            # preference) is a separate, larger build and is NOT this.
            "multi_slot_coverage": True,
            "multi_slot_note": (
                "by_player and by_tier cover pick numbers for EVERY draft slot in this league, "
                "not only user_draft_slot above -- look up picks_by_slot[str(slot)] for the "
                "pick sequence belonging to whichever slot is currently selected in the UI, "
                "then read those pick numbers out of by_player/by_tier as usual. A pick number "
                "not present in ANY slot's sequence (the auto-filled DEF/K reserved round) has "
                "no entry, same as before this change."
            ),
            "picks_by_slot": _all_slot_pick_numbers(cfg),
        },
        # ADR-034. Enough for a client to re-run the same Monte Carlo model
        # CONDITIONED on live draft state (players already gone, each team's
        # actual roster) instead of reading the unconditional marginals above.
        # league.json already carries teams/rounds/user_draft_slot/roster
        # structure; this block adds only what belongs to the OPPONENT MODEL
        # itself.
        "client_simulation_parameters": {
            # Mirrors av.default_ranking_sources(): single source today. Name
            # and as_of_date are READ from season_data (ds.load_season's own
            # provenance fields, see above), not hardcoded here -- if a second
            # source (MFL ADP, ADR-035) is wired into run_availability.py, or
            # thread 119 repoints ds.CONSENSUS_RANK_SOURCE, this list updates
            # itself; only the weight (still a single source) needs a look.
            "ranking_sources": [{
                "name": season_data.consensus_rank_source,
                "weight": 1.0,
                "as_of_date": season_data.consensus_rank_as_of_date,
            }],
            # FR-066/thread 104: the ECR-sourced rank the opponent model AND
            # the user's own strategy_bpa pick actually run on TODAY (ds.load_
            # season's consensus_rank), keyed by player name to match
            # by_player's existing keys. This is NOT board.json:consensus_rank
            # -- those are two different rankings from two different sources
            # (measured: 73 of the top 80 players differ in order, see thread
            # 104). This is what simulate_availability actually runs on right
            # now -- see adp_central_tendency below for what a FUTURE client
            # recompute should be built against instead, once that switch
            # ships.
            "player_ranks": consensus_ranks_by_name,
            "player_ranks_note": (
                "Keyed by player name (matches by_player's keys). Value is the "
                "same consensus_rank ds.load_season/simulate_availability run "
                "the opponent model and the user's own best-available pick "
                "against today -- read from ranking_sources[0] "
                "(name+as_of_date above), NOT from board.json:consensus_rank, "
                "which is a different ranking from a different source (73 of "
                "the top 80 players differ in order). Superseded as the basis "
                "for a NEW client-side recompute by adp_central_tendency below "
                "(thread 119) -- kept here because it is still what the SHIPPED "
                "model runs on until that switch clears its pre-registration."
            ),
            # Thread 119 (strategist reply to thread 104, 2026-07-30):
            # reformulated ask, {adp_pick, sigma_pick, coverage_flag} per
            # player, on the recommendation that the opponent model's central
            # tendency move to FFC ADP with per-player dispersion, at which
            # point the unconditional Prep-mode marginal becomes closed-form
            # (P(available at p) = 1 - F_i(p)) and a browser needs no Monte
            # Carlo port at all -- only (adp, sigma, coverage) per player. NOT
            # YET the model's input; see status_note.
            "adp_central_tendency": {
                "status": "preparatory_switch_not_yet_shipped",
                "status_note": (
                    "simulate_availability has NOT switched to ADP. It still runs "
                    "entirely on ranking_sources[0] (fantasypros_ecr) above; "
                    "player_ranks is still the accurate description of today's "
                    "shipped model. This block is exported ahead of the switch "
                    "(recommended by strategist, thread 119, pending the M0-M5 "
                    "pre-registration at "
                    "docs/ranking/availability-opponent-model-precommit.md) so a "
                    "client build does not have to be redone once it ships. Do "
                    "not use adp_pick to recompute today's availability.json "
                    "numbers -- they do not reflect it."
                ),
                "adp_source": ffc_adp["adp_source"],
                "as_of_date": ffc_adp["as_of_date"],
                "sample_window": ffc_adp["sample_window"],
                "n_players_covered": n_covered,
                "n_players_total": len(adp_by_name),
                "axis_note": (
                    "adp_pick is FFC's raw average_pick, UNCORRECTED. FFC's pick "
                    "axis counts kickers and defenses (Westwood has no kicker "
                    "slot) and its sampled drafts run deeper than this league's "
                    "16 rounds (FFC low_pick reaches ~18.0), so an FFC pick "
                    "number is not directly comparable to a Westwood pick number "
                    "-- most divergent in the back half of the draft. The M4 "
                    "axis correction (isotonic calibration against board.json) "
                    "has not been run; do not treat adp_pick as a Westwood pick "
                    "number without it."
                ),
                "sigma_pending_note": (
                    "No per-player dispersion (sigma_pick) is exported. It is "
                    "gated on M0: FFC's times_drafted and total_drafts_in_sample "
                    "columns do not reconcile as-is (e.g. Bijan Robinson "
                    "times_drafted=90 against total_drafts_in_sample=1254 on "
                    "every row of the same snapshot), so no per-player sampling-"
                    "variance weight is trustworthy yet. A placeholder sigma is "
                    "deliberately withheld rather than shipped -- see M0 in the "
                    "precommit doc."
                ),
                "coverage_note": (
                    "by_player carries entries for every player in "
                    "adp_central_tendency.by_player, coverage_flag true or "
                    "false -- never a missing key. adp_pick is present (non-"
                    "null) only when coverage_flag is true; a player outside "
                    "the FFC skill-position snapshot gets adp_pick=null, never "
                    "a fabricated value."
                ),
                "by_player": adp_by_name,
            },
            "mechanical_need_targets": need_targets,
            "mechanical_need_targets_note": (
                "Per position: STARTERS[pos] + (FLEX_SLOTS if pos is flex-eligible else 0). "
                "An UPPER BOUND per position, not a partition of the shared flex slots -- a "
                "team could plausibly need up to this many of ANY one eligible position, not "
                "all of them at once. Below this count a team is not penalised for taking the "
                "position again; a team at or past max_at_position never takes another."
            ),
            "max_at_position": max_at_pos,
            "max_at_position_note": (
                "The primary league's values are a hand-set judgement call (how much bench "
                "depth a manager hoards), not a formula. Other leagues use an explicitly "
                "flagged heuristic instead (mechanical_need_targets + bench size) -- see "
                "ADR-041; this has not been measured for any league."
            ),
            "need_penalty_per_surplus": 25.0,
            "room_noise_drawn_once_per_draft": True,
            "room_noise_note": (
                "One Gaussian(0, sigma) draw per player is shared by the whole room for a "
                "single simulated draft, not redrawn per pick or per team -- this models "
                "\"the room collectively valued him a round higher this year\", not nine "
                "independently confused teams."
            ),
            "algorithm_note": (
                "Per simulated draft: (1) sample each opponent team's ranking source from "
                "ranking_sources (fresh draw every draft, never fixed to a team); (2) draw one "
                "shared noise vector for the room; (3) each opponent's effective rank is their "
                "source's rank plus the shared noise; (4) pick order is standard snake over "
                "teams=league.json:teams, rounds=league.json:rounds, "
                "user_slot=league.json:user_draft_slot; (5) each opponent picks the lowest "
                "effective-rank available player, with mechanical_need_targets applied as an "
                "additive rank penalty (need_penalty_per_surplus per player beyond target, "
                "infinite at max_at_position); (6) the user is assumed to draft best-available "
                "off THIS SAME unperturbed consensus rank (player_ranks above / "
                "ranking_sources[0]) -- corrected 2026-07-30 (thread 104): this previously said "
                "board.json, which is wrong and was never wired that way; ds.strategy_bpa reads "
                "data.consensus_rank, the identical array the opponent model's ranking_sources "
                "draws from, not board.json's separately-sourced rank."
            ),
        },
    })
    return payload


def _scoring_for_export(cfg: dict) -> dict:
    """LEAGUE rendered so it survives a real JSON parser.

    The last `points_allowed` tier carries `float("inf")` as its upper bound.
    json.dumps emits that as a bare `Infinity` token -- a valid Python literal
    and NOT valid JSON (RFC 8259). `JSON.parse` and `fetch().json()` both throw
    on it, so no browser could load league.json at all. The scoring engine keeps
    the sentinel (it needs a comparable upper bound); only the export drops it.

    The open-ended tier is emitted with a `null` upper bound. This is the ONE
    place in the contract where null does not mean "not available" -- it means
    "no upper bound" -- so `points_allowed_note` states that inline rather than
    leaving the reader to reconcile it against the cross-cutting convention.
    """
    out = {k: dict(v) if isinstance(v, dict) else v for k, v in cfg.items()}
    tiers = out["defense"]["points_allowed"]
    out["defense"] = dict(out["defense"])
    out["defense"]["points_allowed"] = [
        [None if ceiling == float("inf") else ceiling, bonus] for ceiling, bonus in tiers
    ]
    out["defense"]["points_allowed_note"] = (
        "Tiers are [points_allowed_ceiling, bonus], inclusive upper bound. A null ceiling "
        "means NO UPPER BOUND (the open-ended top tier) -- it does not mean 'not available' "
        "as null does elsewhere in this contract."
    )
    return out


def build_league_json(cfg: lc.LeagueConfig = lc.CURRENT_LEAGUE) -> dict:
    levels, flex_split_measured = ReplacementLevels.from_league_config(cfg)
    is_primary = cfg.is_primary
    unsupported = sorted(
        p for p in cfg.starters if p not in ReplacementLevels.SCOREABLE_POSITIONS
    )
    pick_sequence = ds.user_pick_numbers() if is_primary else ds.DraftEngine(cfg).user_pick_numbers()

    if is_primary:
        # Preserve the exact prose the primary league has always shipped --
        # only a non-primary league gets the generalized, position-list
        # version of these notes.
        replacement_levels_note = (
            "Derived from this league's 10 teams and starter counts, not hardcoded. Public "
            "boards assume a 12-team RB24/WR36 convention; ours is RB30/WR40/TE10/QB10, "
            "measured rather than assumed (ADR-029)."
        )
        positions_without_replacement_levels_note = (
            "DEF is a starting slot (1 per team) with no replacement level, deliberately and "
            "permanently. No DST data is ingested, so no DEF points projection, VBD or board "
            "row exists. Do not derive a DEF value from these files. Render "
            "board.json:def_note where a DEF number would otherwise go."
        )
    else:
        replacement_levels_note = (
            f"Derived from this league's {cfg.teams} teams and starter counts, not hardcoded. "
            f"See replacement_levels_flex_split_note in board.json for whether flex_split was "
            f"measured for this specific league."
        )
        positions_without_replacement_levels_note = (
            None if not unsupported else
            f"{', '.join(unsupported)} {'is a' if len(unsupported) == 1 else 'are'} starting "
            f"slot(s) with no scoring data ingested (no kicker or DST stats exist in this "
            f"project). Do not derive a value for {'it' if len(unsupported) == 1 else 'them'} "
            f"from these files."
        )

    return {
        "contract_version": CONTRACT_VERSION,
        # league.json was the only artifact shipping without this, so consumers
        # keying provenance on it fell back to an "unversioned" run id.
        "generated_utc": datetime.now(timezone.utc).isoformat(),
        "league_id": cfg.league_id,
        "league_name": cfg.name,
        "platform": cfg.platform,
        "teams": cfg.teams,
        "rounds": cfg.rounds,
        "user_draft_slot": cfg.user_draft_slot,
        "draft_type": cfg.draft_type,
        "pick_sequence": pick_sequence,
        "roster": {
            "starters": {**cfg.starters, "FLEX": cfg.flex_slots},
            "flex_eligible": list(cfg.flex_eligible),
            "bench": cfg.bench,
            "ir": cfg.ir,
            "kicker": "K" in cfg.starters,
        },
        "scoring": _scoring_for_export(cfg.scoring),
        "replacement_levels": levels.baselines(),
        # DEF is PERMANENTLY EXCLUDED, by decision (2026-07-25, ADR-039), and
        # this field exists so that reads as a decision rather than an
        # omission. Generalized (ADR-041) to any unscored starter position --
        # a Yahoo-style league also rosters K, which has the identical
        # problem: no kicker stats are ingested either.
        #
        # NOTE FOR A FUTURE SESSION, so this is not relitigated: DEF10/K10-
        # style RANKS *are* derivable without any player data (teams x
        # starters, the same arithmetic that yields QB10). They are left out
        # anyway. A published level invites a downstream VBD, and the POINTS
        # half genuinely does not exist for either position.
        "positions_without_replacement_levels": unsupported,
        "positions_without_replacement_levels_note": positions_without_replacement_levels_note,
        "replacement_levels_note": replacement_levels_note,
        "flex_split_assumption": levels.flex_split,
        "flex_split_measured": flex_split_measured,
        "flex_split_note": (
            "MEASURED, not assumed (ADR-029, 2026-07-25 -- this note previously said the "
            "opposite and was stale). Derived from 26 seasons: rank all flex-eligible players "
            "under this league's exact rules, remove the mandated starters, and count who wins "
            "the 20 flex slots. Season-to-season variance is large (RB flex ranges 5 to 17, "
            "sd 3.0) and the answer moves +/-1 rank by era window, so treat it as a measured "
            "midpoint, not a precise constant. TE is the robust part: zero flex slots in every "
            "window tested."
        ) if is_primary else (
            "NOT measured for this league (flex_split_measured is false): borrowed from the "
            "primary league's ADR-029 measurement as an explicitly flagged placeholder. A real "
            "measurement requires re-running that analysis under this league's own scoring "
            "rules, which has not been done."
        ),
        "playoff": {
            "teams": cfg.playoff_teams, "weeks": list(cfg.playoff_weeks),
            "reseeding": cfg.reseeding,
        },
        "trade_deadline": cfg.trade_deadline,
        "faab_budget": cfg.faab_budget,
        # FR-042 (2026-07-29): only the primary league carries Westwood's
        # verified custom ruleset (scoring.LEAGUE, ADR-052). Every other
        # league (presets and founder-created) uses standard_scoring.
        # STANDARD_LEAGUE -- state that on screen rather than let a preset
        # named "ESPN-default" imply platform-verified scoring it doesn't
        # have. See standard_scoring.SCORING_RULESET_NOTE for what in that
        # ruleset is founder-specified vs. an unverified placeholder.
        # Shared with export_history.py's per-league envelope (FR-083/FR-079)
        # via lc.scoring_ruleset_note_for so the two never disagree.
        "scoring_ruleset_note": lc.scoring_ruleset_note_for(cfg),
    }


def _real_draft_picks(conn: sqlite3.Connection, cfg: lc.LeagueConfig, season: int = SEASON) -> List[sqlite3.Row]:
    """Picks from a REAL (is_mock=0) draft logged for this league and season.

    Deliberately season-scoped: the only is_mock=0 draft on file today is the
    2025 real draft, and 2025 is a locked holdout (CLAUDE.md #6.1/#6.3). This
    query asks for `season` (SEASON = 2026, the current draft's year), which
    that row does not match, so it is excluded by construction -- not by a
    special-cased holdout check. No path in this function can return 2025 pick
    data for a 2026 export.
    """
    conn.row_factory = sqlite3.Row
    return conn.execute(
        "SELECT p.overall_pick, p.round, p.team_slot, p.player_name_raw, p.mfl_id "
        "FROM mock_picks p JOIN mock_drafts d ON p.mock_id = d.mock_id "
        "WHERE d.is_mock = 0 AND d.league_config_id = ? "
        "AND CAST(strftime('%Y', d.drafted_at) AS INTEGER) = ? "
        "ORDER BY p.overall_pick",
        (cfg.league_id, season),
    ).fetchall()


def _position_lookup(conn: sqlite3.Connection, season: int = SEASON) -> Dict[str, str]:
    rows = conn.execute(
        "SELECT player_name, position FROM rankings "
        "WHERE source='fantasypros_ecr' AND season=? AND position IS NOT NULL", (season,)
    ).fetchall()
    return {r["player_name"]: r["position"] for r in rows}


def build_rosters_json(
    conn: sqlite3.Connection, cfg: lc.LeagueConfig = lc.CURRENT_LEAGUE,
) -> dict:
    """Full league rosters: all teams, every slot (starters, flex, bench, IR),
    filled mechanically from actual draft picks on file for THIS season.

    Observable facts only -- see thread 016. Slot assignment is pure
    arithmetic over `roster_slots` and the order picks were made: each pick is
    placed into the first open starter slot at its position, then flex if
    flex-eligible, then bench, in that priority. `needs` is
    required-minus-filled per slot type. Nothing here infers what a team
    WANTS or is LIKELY to draft next -- that was explicitly refused elsewhere
    in this project (docs/handoffs/016) as an indefensible inference about
    latent strategy. IR is never filled by a draft pick (it is a
    post-draft/waiver slot in this league, see league_config.drafted_rounds),
    so ir.filled is always 0 from this data source.

    Before the real 2026 draft happens, `_real_draft_picks` returns no rows
    (see its docstring) and every team comes back with an empty roster and
    full needs -- the correct, honest state right now, not a bug.
    """
    picks = _real_draft_picks(conn, cfg, season=SEASON)
    pos_of = _position_lookup(conn, season=SEASON) if picks else {}

    known_names = {}
    if cfg.is_primary:
        from export_static import KNOWN_OPPONENTS
        known_names = {v["draft_slot_2026"]: k for k, v in KNOWN_OPPONENTS.items()}

    by_team: Dict[int, List[dict]] = defaultdict(list)
    unresolved_positions = 0
    for p in picks:
        slot = p["team_slot"]
        if slot is None:
            continue
        name = p["player_name_raw"]
        pos = pos_of.get(name)
        if pos is None:
            unresolved_positions += 1
        by_team[slot].append({
            "player": name,
            "position": pos,
            "overall_pick": p["overall_pick"],
            "round": p["round"],
            "position_resolved": pos is not None,
        })

    rosters = []
    for slot in range(1, cfg.teams + 1):
        team_picks = sorted(by_team.get(slot, []), key=lambda x: x["overall_pick"])
        starter_filled: Dict[str, List[dict]] = defaultdict(list)
        flex_filled: List[dict] = []
        bench_filled: List[dict] = []
        for pick in team_picks:
            pos = pick["position"]
            if pos in cfg.starters and len(starter_filled[pos]) < cfg.starters[pos]:
                starter_filled[pos].append(pick)
            elif pos in cfg.flex_eligible and len(flex_filled) < cfg.flex_slots:
                flex_filled.append(pick)
            else:
                bench_filled.append(pick)

        starters_block = {
            pos: {
                "required": req,
                "filled": len(starter_filled.get(pos, [])),
                "players": starter_filled.get(pos, []),
            }
            for pos, req in cfg.starters.items()
        }
        needs = {
            pos: max(0, req - len(starter_filled.get(pos, [])))
            for pos, req in cfg.starters.items()
        }
        needs["FLEX"] = max(0, cfg.flex_slots - len(flex_filled))
        needs["BENCH"] = max(0, cfg.bench - len(bench_filled))
        needs["IR"] = cfg.ir  # never filled by a draft pick -- see docstring

        rosters.append({
            "team_slot": slot,
            "is_user": slot == cfg.user_draft_slot,
            "team_name": known_names.get(slot),
            "roster_slots": {
                "starters": starters_block,
                "flex": {
                    "required": cfg.flex_slots, "filled": len(flex_filled),
                    "eligible_positions": list(cfg.flex_eligible), "players": flex_filled,
                },
                "bench": {"required": cfg.bench, "filled": len(bench_filled), "players": bench_filled},
                "ir": {
                    "required": cfg.ir, "filled": 0, "players": [],
                    "note": "IR is filled off-waiver after the draft, never by a draft pick "
                            "(league_config.drafted_rounds excludes it). Always 0 here.",
                },
            },
            "needs": needs,
            "players": team_picks,
        })

    total_picks = sum(len(v) for v in by_team.values())
    if total_picks == 0:
        draft_state = "not_started"
    elif total_picks >= cfg.teams * cfg.drafted_rounds():
        draft_state = "complete"
    else:
        draft_state = "in_progress"

    return {
        "contract_version": CONTRACT_VERSION,
        "generated_utc": datetime.now(timezone.utc).isoformat(),
        "league_id": cfg.league_id,
        "season": SEASON,
        "teams": cfg.teams,
        "draft_state": draft_state,
        "picks_ingested": total_picks,
        "unresolved_position_count": unresolved_positions,
        "data_source_note": (
            "Built from a REAL (is_mock=0) draft logged for this league and season only. No "
            f"such draft is on file for {SEASON} yet, so every roster below is empty and every "
            "need equals the full slot requirement -- this is the honest current state, not a "
            "placeholder. As soon as the real draft is logged pick-by-pick, re-running this "
            "export fills rosters incrementally without any code change."
        ) if total_picks == 0 else (
            f"{total_picks} real pick(s) on file for {SEASON}, resolved against fantasypros_ecr "
            f"positions where available ({unresolved_positions} unresolved)."
        ),
        "inference_scope_note": (
            "This artifact states what each team HAS (drafted, by slot) and what it still NEEDS "
            "(mechanical arithmetic: required minus filled per slot). It does not model, guess, "
            "or rank what a team is likely to draft next -- see docs/handoffs/016. For "
            "behavioural/tendency data on known opponents, see opponents.json instead."
        ),
        "rosters": rosters,
    }


def build_ranking_sources_json(conn: sqlite3.Connection) -> dict:
    """FR-2026-07-30: a catalog of all four founder-facing ranking sources --
    label, whether each is actually built, and its own as_of_date/row count.
    Exists so a client can render the full picker (including the disabled
    'proprietary' option) from ONE file, without probing each board variant
    to discover what exists. Never blends across sources -- see
    make_board.describe_ranking_source's per-source note field."""
    return {
        "contract_version": CONTRACT_VERSION,
        "generated_utc": datetime.now(timezone.utc).isoformat(),
        "season": SEASON,
        "sources": [
            make_board.describe_ranking_source(conn, SEASON, sel)
            for sel in make_board.RANKING_SOURCE_SELECTIONS
        ],
        # Filename each BUILT selection's per-source board.json variant is
        # exported under (write_all). 'expert_adjusted' is board.json itself
        # -- the default/primary artifact every existing consumer already
        # reads, unchanged in name so nothing breaks without a code change.
        "board_files": {
            "expert_adjusted": "board.json",
            "expert_raw": "board.expert_raw.json",
            "market_adp": "board.market_adp.json",
            "proprietary": None,
        },
    }


def write_all(
    out_dir: Path, conn: sqlite3.Connection, strategies: Optional[dict] = None,
    cfg: lc.LeagueConfig = lc.CURRENT_LEAGUE,
) -> List[Path]:
    out_dir.mkdir(parents=True, exist_ok=True)
    written = []
    artifacts = {
        "board.json": build_board_json(conn, cfg),
        "availability.json": build_availability_json(conn, cfg),
        "league.json": build_league_json(cfg),
        "rosters.json": build_rosters_json(conn, cfg),
        # FR-2026-07-30: the other two BUILT sources, as separate,
        # never-blended files -- same shape as board.json, different
        # ranking_source_selection. 'proprietary' is deliberately absent from
        # this dict (no file to write) -- ranking_sources.json is where a
        # client learns it exists and is not built.
        "board.expert_raw.json": build_board_json(conn, cfg, ranking_source_selection="expert_raw"),
        "board.market_adp.json": build_board_json(conn, cfg, ranking_source_selection="market_adp"),
        "ranking_sources.json": build_ranking_sources_json(conn),
    }
    if strategies is not None:
        artifacts["strategies.json"] = strategies
    for name, payload in artifacts.items():
        p = out_dir / name
        # allow_nan=False: refuse to WRITE invalid JSON rather than emit bare
        # Infinity/NaN tokens that no non-Python consumer can parse. Raises
        # ValueError at export time, which is where a human is looking.
        p.write_text(
            json.dumps(payload, indent=2, default=str, allow_nan=False), encoding="utf-8"
        )
        written.append(p)
    # weekly_finishes.json / season_stats.json (FR-079/FR-083, contract
    # 1.16.0): every caller of this write_all -- the single-league CLI AND
    # generate_config_matrix's 24-preset loop -- gets a per-league,
    # league-scoring-aware history export for free, the same way board.json/
    # league.json already are. Previously these two files were built
    # separately (export_history.main(), never called from here or from the
    # matrix loop) and only ever landed unprefixed at the top level,
    # regardless of which league's directory this write_all was asked for.
    written.extend(eh.write_all(out_dir, conn, cfg=cfg))
    return written


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--out", type=Path, default=None)
    ap.add_argument(
        "--league", default=lc.PRIMARY_LEAGUE_ID,
        help="league_id of a saved config under data/leagues/, or 'primary' (default)",
    )
    args = ap.parse_args()
    cfg = (
        lc.CURRENT_LEAGUE if args.league == lc.PRIMARY_LEAGUE_ID else lc.LeagueConfig.load(args.league)
    )
    out_dir = args.out or export_dir_for(cfg.league_id)
    conn = dbmod.connect()
    try:
        written = write_all(out_dir, conn, cfg=cfg)
    finally:
        conn.close()
    for p in written:
        print(f"wrote {p}  ({p.stat().st_size:,} bytes)")


if __name__ == "__main__":
    main()
