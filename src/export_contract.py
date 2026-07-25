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

CONTRACT_VERSION = "1.0.0"
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
        tier = None
        if pr and r.position in av.TIERS:
            tier = next((t for t, (lo, hi) in av.TIERS[r.position].items() if lo <= pr <= hi),
                        "T5+")
        team = team_of.get(r.player)
        structural = (pub_rank.get(r.player, r.overall_rank) - r.overall_rank)
        players.append({
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
            "vbd": r.vbd,
            "consensus_rank": r.consensus_rank,
            "delta_vs_consensus": r.delta_vs_consensus,
            "tier": tier,
            "structural_adjustment": r.delta_vs_consensus,
            "structural_breakdown": {
                "replacement_levels": structural,
                "scoring_and_vbd_method": r.delta_vs_consensus - structural,
            },
            "evaluative_adjustment": None,
            "evaluative_adjustment_note": (
                "Null by construction, not by omission. This board assigns every player at "
                "the same positional consensus rank an identical projection, so it holds no "
                "player-level opinion to attribute. All rank movement is structural. A real "
                "evaluative component requires component-level projections (test-registry #2), "
                "which no accessible source provides."
            ),
            "availability": avail.get(r.player, {}),
        })

    return {
        "contract_version": CONTRACT_VERSION,
        "generated_utc": datetime.now(timezone.utc).isoformat(),
        "season": SEASON,
        "board_source": "fantasypros_ecr re-scored into league positional value structure",
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
        "scoring": LEAGUE,
        "replacement_levels": levels.baselines(),
        "replacement_levels_note": (
            "Derived from this league's 10 teams and starter counts, not hardcoded. Public "
            "boards assume a 12-team RB24/WR36 convention; ours is RB28/WR41/TE11/QB10."
        ),
        "flex_split_assumption": levels.flex_split,
        "flex_split_note": (
            "How flex slots get filled league-wide is not knowable in advance. This is an "
            "explicit tunable assumption, not a measurement."
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
        p.write_text(json.dumps(payload, indent=2, default=str), encoding="utf-8")
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
