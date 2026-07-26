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
import make_board
from config import DEFAULT_CONFIG
from scoring import LEAGUE, ReplacementLevels

CONTRACT_VERSION = "1.5.0"
SEASON = 2026
EXPORT_DIR = Path(__file__).resolve().parent.parent / "data" / "export"
AVAIL_CSV = Path(__file__).resolve().parent.parent / "data" / "availability_2026.csv"

# The 12-team convention public boards implicitly assume: 1QB/2RB/3WR/1TE, no
# flex share -> QB12 / RB24 / WR36 / TE12. Differencing our board against this
# one isolates the replacement-level effect exactly.
PUBLISHED_LEVELS = ReplacementLevels(
    teams=12, starters={"QB": 1, "RB": 2, "WR": 3, "TE": 1}, flex_slots=0, flex_split={}
)


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
        out[t] = missing[0] if len(missing) == 1 else None
    return out


def _load_availability_csv() -> Dict[str, dict]:
    by_player: Dict[str, Dict[str, Dict[str, float]]] = defaultdict(lambda: defaultdict(dict))
    by_tier: Dict[str, Dict[str, Dict[str, Dict[str, float]]]] = defaultdict(
        lambda: defaultdict(lambda: defaultdict(dict))
    )
    te_scen: List[dict] = []
    if not AVAIL_CSV.exists():
        return {"by_player": {}, "by_tier": {}, "te_scenarios": []}
    with AVAIL_CSV.open(encoding="utf-8") as f:
        for row in csv.DictReader(f):
            sig = f"sigma_{int(float(row['sigma']))}"
            if row["record_type"] == "player_available":
                by_player[row["player"]][row["pick"]][sig] = float(row["value"])
            elif row["record_type"] == "tier_available":
                by_tier[row["position"]][row["tier"]][row["pick"]][sig] = float(row["value"])
            elif row["record_type"] == "te_scenario":
                te_scen.append({
                    "tier": row["tier"], "pick": int(row["pick"]),
                    "probability_available": float(row["value"]), "note": row["note"],
                })
    return {
        "by_player": {k: dict(v) for k, v in by_player.items()},
        "by_tier": {p: {t: dict(pk) for t, pk in ts.items()} for p, ts in by_tier.items()},
        "te_scenarios": te_scen,
    }


def build_board_json(conn: sqlite3.Connection) -> dict:
    ours, curves = make_board.build_board(conn, SEASON, n_bootstrap=2000)
    published, _ = make_board.build_board(
        conn, SEASON, levels=PUBLISHED_LEVELS, n_bootstrap=0
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

    avail = _load_availability_csv()["by_player"]

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
        structural = (pub_rank.get(r.player, r.overall_rank) - r.overall_rank)
        players.append({
            # Stable integer id: the design contract keys availability and the
            # player-profile endpoint on an int, and gsis_id strings are not
            # usable as such. Derived from overall_rank so it is deterministic
            # for a given board generation.
            "id": r.overall_rank,
            "player_id_gsis": None,
            "overall_rank": r.overall_rank,
            "player": r.player,
            "position": r.position,
            "positional_rank": pr,
            "positional_label": f"{r.position}{pr}" if pr else None,
            "team": team,
            "bye_week": byes.get(team) if team else None,
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

    return {
        "contract_version": CONTRACT_VERSION,
        "generated_utc": datetime.now(timezone.utc).isoformat(),
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
        "replacement_levels_used": ReplacementLevels().baselines(),
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
        "def_supported": False,
        "def_note": (
            "DEF is a starting slot in this league (1 per team) but is permanently excluded "
            "from the model: no DST data is ingested, so there is no DEF replacement level, "
            "points projection, VBD or board row. See "
            "league.json:positions_without_replacement_levels. Render this note where a DEF "
            "number would go. Do not compute a DEF value from these files."
        ),
        "players": players,
    }


def build_availability_json() -> dict:
    payload = _load_availability_csv()
    payload.update({
        "contract_version": CONTRACT_VERSION,
        "generated_utc": datetime.now(timezone.utc).isoformat(),
        "metadata": {
            "season": SEASON,
            "simulations_per_setting": 3000,
            "sigma_values": list(ds.SIGMA_SWEEP),
            "sigma_plain_english": (
                "Sigma is how far the other nine teams stray from consensus, measured in draft "
                "picks: 5 is a disciplined room, 10 is about one round of slippage (the "
                "default), 20 is chaotic. It is a guess, not fitted to observed drafts, which "
                "is why every number is given at all three settings."
            ),
            "user_draft_slot": ds.USER_SLOT,
            "user_picks": ds.user_pick_numbers(),
            "reliability_note": (
                "These probabilities never pass through the projection curve, so they are the "
                "most reliable numbers in the project. They describe draft behaviour, not "
                "football outcomes."
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


def build_league_json() -> dict:
    levels = ReplacementLevels()
    return {
        "contract_version": CONTRACT_VERSION,
        "teams": ds.N_TEAMS,
        "rounds": ds.N_ROUNDS,
        "user_draft_slot": ds.USER_SLOT,
        "pick_sequence": ds.user_pick_numbers(),
        "roster": {
            "starters": {**ds.STARTERS, "FLEX": ds.FLEX_SLOTS, "DEF": 1},
            "flex_eligible": list(ds.FLEX_ELIGIBLE),
            "bench": 6,
            "ir": 1,
            "kicker": False,
        },
        "scoring": _scoring_for_export(LEAGUE),
        "replacement_levels": levels.baselines(),
        # DEF is PERMANENTLY EXCLUDED, by decision (2026-07-25), and this field
        # exists so that reads as a decision rather than an omission -- which is
        # how the front end reasonably read it when roster.starters declared
        # DEF:1 against a replacement_levels with no DEF key.
        #
        # NOTE FOR A FUTURE SESSION, so this is not relitigated: DEF10 *is*
        # derivable without any player data (10 teams x 1 DEF starter, the same
        # arithmetic that yields QB10). It is left out anyway. A published level
        # invites a downstream VBD, and the POINTS half genuinely does not exist
        # -- no DST data is ingested. Publishing the rank alone would put a
        # number in reach of a consumer who cannot see that distinction.
        "positions_without_replacement_levels": ["DEF"],
        "positions_without_replacement_levels_note": (
            "DEF is a starting slot (1 per team) with no replacement level, deliberately and "
            "permanently. No DST data is ingested, so no DEF points projection, VBD or board "
            "row exists. Do not derive a DEF value from these files. Render "
            "board.json:def_note where a DEF number would otherwise go."
        ),
        "replacement_levels_note": (
            "Derived from this league's 10 teams and starter counts, not hardcoded. Public "
            "boards assume a 12-team RB24/WR36 convention; ours is RB30/WR40/TE10/QB10, "
            "measured rather than assumed (ADR-029)."
        ),
        "flex_split_assumption": levels.flex_split,
        "flex_split_note": (
            "MEASURED, not assumed (ADR-029, 2026-07-25 -- this note previously said the "
            "opposite and was stale). Derived from 26 seasons: rank all flex-eligible players "
            "under this league's exact rules, remove the mandated starters, and count who wins "
            "the 20 flex slots. Season-to-season variance is large (RB flex ranges 5 to 17, "
            "sd 3.0) and the answer moves +/-1 rank by era window, so treat it as a measured "
            "midpoint, not a precise constant. TE is the robust part: zero flex slots in every "
            "window tested."
        ),
        "playoff": {"teams": 4, "weeks": [16, 17], "reseeding": False},
        "trade_deadline": "2026-11-28",
        "faab_budget": 100,
    }


def write_all(out_dir: Path, conn: sqlite3.Connection, strategies: Optional[dict] = None) -> List[Path]:
    out_dir.mkdir(parents=True, exist_ok=True)
    written = []
    artifacts = {
        "board.json": build_board_json(conn),
        "availability.json": build_availability_json(),
        "league.json": build_league_json(),
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
    ap.add_argument("--out", type=Path, default=EXPORT_DIR)
    args = ap.parse_args()
    conn = dbmod.connect()
    try:
        written = write_all(args.out, conn)
    finally:
        conn.close()
    for p in written:
        print(f"wrote {p}  ({p.stat().st_size:,} bytes)")


if __name__ == "__main__":
    main()
