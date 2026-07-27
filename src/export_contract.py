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
import freshness as fr
import league_config as lc
import make_board
import roster_status as rst
import team_codes as tc
from config import DEFAULT_CONFIG
from scoring import LEAGUE, ReplacementLevels

CONTRACT_VERSION = "1.10.0"
SEASON = 2026
DATA_DIR = Path(__file__).resolve().parent.parent / "data"
EXPORT_DIR = DATA_DIR / "export"

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


def build_board_json(
    conn: sqlite3.Connection,
    cfg: lc.LeagueConfig = lc.CURRENT_LEAGUE,
    enforce_freshness: bool = True,
    freshness_today=None,
) -> dict:
    # T5 (fable-draft-day-premortem-2026-07-27.md finding #2): refuse to
    # build the live board from a snapshot older than
    # cfg.freshness_max_age_days, and always print the age -- even when
    # comfortably fresh -- so staleness is visible before it is a problem,
    # not only once it crosses the line. `enforce_freshness=False` exists
    # only for callers that intentionally want the report without the raise
    # (none currently do; kept for the same reason require_fresh/
    # check_freshness are two functions in freshness.py rather than one with
    # a raise flag).
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
        conn, SEASON, levels=levels, n_bootstrap=2000, scoring_cfg=cfg.scoring
    )
    published, _ = make_board.build_board(
        conn, SEASON, levels=PUBLISHED_LEVELS, n_bootstrap=0, scoring_cfg=cfg.scoring
    )
    pub_rank = {r.player: r.overall_rank for r in published}

    meta = conn.execute(
        "SELECT player_name, team, position, adp_rank FROM rankings "
        "WHERE source='fantasypros_ecr' AND season=?", (SEASON,)
    ).fetchall()
    team_of = {r["player_name"]: r["team"] for r in meta}
    byes = _bye_weeks(SEASON)

    # positional rank by consensus order
    by_pos: Dict[str, List] = defaultdict(list)
    for r in sorted(meta, key=lambda x: x["adp_rank"]):
        by_pos[r["position"]].append(r["player_name"])
    pos_rank = {n: i + 1 for pos, names in by_pos.items() for i, n in enumerate(names)}

    avail = _load_availability_csv(avail_csv_for(cfg.league_id))["by_player"]

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
        })

    # Positions this league rosters as starters but that have no scoring
    # engine (K, DEF -- no kicker or DST stats are ingested, ADR-039/041).
    # Generalizes the old DEF-only hardcode to any such position.
    unsupported = sorted(
        p for p in cfg.starters if p not in ReplacementLevels.SCOREABLE_POSITIONS
    )

    return {
        "contract_version": CONTRACT_VERSION,
        "generated_utc": datetime.now(timezone.utc).isoformat(),
        "league_id": cfg.league_id,
        "season": SEASON,
        "board_source": "fantasypros_ecr re-scored into league positional value structure",
        # The design contract's example shows "blend:4". We have ONE source.
        # ADR-018: no market ADP is obtainable within CLAUDE.md §10, so there is
        # nothing to blend. Stated explicitly so the UI does not imply a blend.
        "consensus_source": "fantasypros_ecr",
        "consensus_source_count": 1,
        "consensus_source_note": (
            "Single source. Expert consensus rank, NOT market average draft position, and not "
            "a blend of several providers. No ADP source is legally obtainable (ADR-018)."
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
        "players": players,
    }


def build_availability_json(cfg: lc.LeagueConfig = lc.CURRENT_LEAGUE) -> dict:
    payload = _load_availability_csv(avail_csv_for(cfg.league_id))
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
        },
        # ADR-034. Enough for a client to re-run the same Monte Carlo model
        # CONDITIONED on live draft state (players already gone, each team's
        # actual roster) instead of reading the unconditional marginals above.
        # league.json already carries teams/rounds/user_draft_slot/roster
        # structure; this block adds only what belongs to the OPPONENT MODEL
        # itself.
        "client_simulation_parameters": {
            # Mirrors av.default_ranking_sources(): single source today. Not
            # computed from a live SeasonData here (this function only reads the
            # CSV) -- if a second source (MFL ADP, ADR-035) is wired into
            # run_availability.py, update this list in the same commit.
            "ranking_sources": [{"name": "fantasypros_ecr", "weight": 1.0}],
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
                "off the TRUE consensus board (unperturbed) -- see board.json."
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


def write_all(
    out_dir: Path, conn: sqlite3.Connection, strategies: Optional[dict] = None,
    cfg: lc.LeagueConfig = lc.CURRENT_LEAGUE,
) -> List[Path]:
    out_dir.mkdir(parents=True, exist_ok=True)
    written = []
    artifacts = {
        "board.json": build_board_json(conn, cfg),
        "availability.json": build_availability_json(cfg),
        "league.json": build_league_json(cfg),
        "rosters.json": build_rosters_json(conn, cfg),
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
