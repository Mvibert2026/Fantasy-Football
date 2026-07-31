#!/usr/bin/env python
"""Ranking **v1**, applied forward to the **2026** season. Display only.

    .venv/bin/python -m experiments.bottomup.ranking_v1_board_2026

WHAT THIS IS. One run of the frozen config in
`experiments/bottomup/ranking_versions/v1.json` pointed at a season that has not
been played. Nothing is tuned, no variant is selected, and there is **no
accuracy number anywhere in the output** -- not for 2026, which has not happened,
and not for 2025, which is sealed.

WHAT IT IS NOT. It is not evidence. v1 was measured on 2018-2024 in
`docs/ranking/ranking-v1-results.md` and it **beat neither crowd at any
position**; it lost to expert consensus at QB, RB and WR with BH-significant
intervals. That context travels with this artifact.

------------------------------------------------------------------ THE HOLDOUT

The one thing this run has to get right.

`WalkForward.run()` trains on every pair whose OUTCOME season is strictly before
the target. Pointed at 2026 it would train on **2025 outcomes** -- the sealed
holdout -- and burn it permanently.

So the fit is frozen at outcome seasons <= 2024, and 2025 is read as a FEATURE
year only, which is what `CLAUDE.md` §6.1 both permits and requires ("inputs for
season N may use data through the end of season N-1"). Three independent
enforcements, none of them a comment:

  1. `build_panel(feature_gate=2026, outcome_gate=2025)` -- the panel's own
     accessor refuses to serve any outcome at 2025 or later. A training pair
     carrying a 2025 outcome cannot be constructed.
  2. `WalkForward.project_target(target, train_outcome_max)` requires the fit
     bound as an argument and raises `RuntimeError` if any training pair, or the
     access audit, carries an outcome season past it.
  3. This module re-asserts both after the fact, per position, and refuses to
     write any artifact unless all four positions pass.

There is no `outcome_components(panel, u, 2026)` call and no scoring step. The
absence of an evaluation is structural, not a matter of restraint.

------------------------------------------------------------------- THE PANEL

The 2026 consensus board is `rankings` @ `source='fantasypros_csv_2026draft'`,
`as_of_date` = the latest snapshot, positions QB/RB/WR/TE -- exactly the 527
rows already in `data/export/rankings_comparison_2026.json`, whose `consensus`
column is this same board. Pre-kickoff is asserted against the measured 2026
Week 1 gameday from `schedules`, not assumed.

Rookies -- `entry == 'rookie'`, i.e. no prior NFL season anywhere in the panel --
are **pinned to their consensus positional slot and labelled**, exactly as v1
does elsewhere. On those rows v1 *is* the crowd. They carry no projected points,
because the number the model would emit for them is not the number that placed
them.

CROSS-POSITIONAL ORDER IS CONSENSUS'S, NOT v1'S. v1's config declares a VBD
revaluation channel and its own precommit says that channel is
`measured_by_this_design: false` and "must not be claimed as tested". So the
overall board keeps consensus's cross-positional structure and substitutes v1's
occupant into each positional slot: the overall rank of a player is the overall
rank consensus gave to whoever consensus put at that positional slot. Every
overall movement you see is a within-position movement, which is the only content
v1 has ever been measured on.

DEF is blank with a note. `nfl.db` has zero DEF coverage; no fabricated number.
"""

from __future__ import annotations

import datetime as _dt
import hashlib
import json
import sqlite3
import subprocess
import sys
import warnings
from pathlib import Path
from typing import Dict, List

import numpy as np
import pandas as pd

warnings.filterwarnings("ignore")

_REPO = Path(__file__).resolve().parents[2]
if str(_REPO) not in sys.path:
    sys.path.insert(0, str(_REPO))

from experiments.bottomup.components import pos_data as PD          # noqa: E402
from experiments.bottomup.components import pos_eval as E           # noqa: E402
from experiments.bottomup.ranking_v1 import v1_scores               # noqa: E402

CONFIG_PATH = _REPO / "experiments" / "bottomup" / "ranking_versions" / "v1.json"
DB = _REPO / "data" / "nfl.db"
EXPORT = _REPO / "data" / "export"
RESULTS = _REPO / "experiments" / "bottomup" / "results"
HOLDOUT_LOG = _REPO / "docs" / "preregistration" / "holdout_access_log.jsonl"

TARGET_SEASON = 2026
#: The fit is frozen HERE. 2025 outcomes are the sealed holdout and never enter.
TRAIN_OUTCOME_MAX = 2024
#: 2025 is legal as an INPUT year and is the whole reason the two gates differ.
FEATURE_GATE = 2026
OUTCOME_GATE = 2025

CONSENSUS_SOURCE = "fantasypros_csv_2026draft"
BOARD_POSITIONS = ("QB", "RB", "WR", "TE")


# --------------------------------------------------------------- the 2026 board
def week1_gameday(season: int) -> pd.Timestamp:
    """Measured, not assumed. A pre-kickoff claim gets checked against the
    schedule the league published, or it is not a claim."""
    conn = sqlite3.connect(f"file:{DB}?mode=ro", uri=True)
    try:
        row = conn.execute(
            "SELECT MIN(gameday) FROM schedules WHERE season=? AND game_type='REG' "
            "AND week=1", (season,)).fetchone()
    finally:
        conn.close()
    if not row or not row[0]:
        raise RuntimeError(f"no {season} Week 1 gameday in schedules; refusing to "
                           f"assume one")
    return pd.Timestamp(row[0])


def load_consensus_board() -> pd.DataFrame:
    """The 2026 pre-draft consensus board. Latest snapshot, K dropped, DEF absent."""
    conn = sqlite3.connect(f"file:{DB}?mode=ro", uri=True)
    try:
        df = pd.read_sql_query(
            "SELECT player_id, player_name, position, team, adp_rank, bye_week, "
            "as_of_date FROM rankings WHERE source=? AND season=?",
            conn, params=(CONSENSUS_SOURCE, TARGET_SEASON))
    finally:
        conn.close()
    if not len(df):
        raise RuntimeError(f"no {CONSENSUS_SOURCE} rows for {TARGET_SEASON}")
    latest = df["as_of_date"].max()
    df = df[df["as_of_date"] == latest].copy()

    kickoff = week1_gameday(TARGET_SEASON)
    ts = pd.to_datetime(df["as_of_date"], errors="coerce")
    if ts.isna().any() or (ts >= kickoff).any():
        raise RuntimeError(
            f"{CONSENSUS_SOURCE} rows are not strictly pre-kickoff "
            f"({kickoff.date()}); refusing to use them")

    df = df[df["position"].isin(BOARD_POSITIONS)]
    df = df[df["player_id"].notna() & (df["player_id"] != "")]
    df["adp_rank"] = df["adp_rank"].astype(float)
    df = df.drop_duplicates("player_id").sort_values("adp_rank").reset_index(drop=True)
    # dense overall consensus slot over the drafted-positions board
    df["consensus_overall_slot"] = np.arange(1, len(df) + 1, dtype=int)
    df["consensus_pos_rank"] = df.groupby("position")["adp_rank"].rank(method="first")
    return df, str(latest), kickoff


# ------------------------------------------------------------------- the run
def project_positions(cfg: Dict, board: pd.DataFrame):
    """One frozen-fit v1 projection per position. No outcome at or after 2025."""
    eng = cfg["engine"]
    panel = PD.build_panel(feature_gate=FEATURE_GATE, outcome_gate=OUTCOME_GATE)
    if panel.outcome_gate > PD.HOLDOUT_SEASON:
        raise RuntimeError("outcome gate above the holdout")

    frames, audits = [], []
    for pos in BOARD_POSITIONS:
        wf = E.WalkForward(panel=panel, position=pos,
                           first_target=TARGET_SEASON, last_target=TARGET_SEASON,
                           min_train_seasons=eng["min_train_seasons"],
                           avail_arm=eng["avail_arm"],
                           calibrate_bonus=eng["calibrate_bonus"])
        ids = board.loc[board["position"] == pos, "player_id"].tolist()
        proj, aud = wf.project_target(TARGET_SEASON, TRAIN_OUTCOME_MAX,
                                      extra_ids=ids)

        # ------ the assertion this deliverable exists to carry, re-checked here
        if aud["observed_max_outcome_season"] > TRAIN_OUTCOME_MAX:
            raise RuntimeError(
                f"{pos}: training outcome season {aud['observed_max_outcome_season']} "
                f"> {TRAIN_OUTCOME_MAX} -- this would burn the holdout")
        if aud["max_outcome_season"] > TRAIN_OUTCOME_MAX:
            raise RuntimeError(f"{pos}: audit outcome read past the frozen fit bound")
        if aud["max_feature_cutoff"] > TARGET_SEASON - 1:
            raise RuntimeError(f"{pos}: feature read at or past the target season")
        if aud["n_outcome_reads_at_target"]:
            raise RuntimeError(f"{pos}: an outcome was read at the target season")
        audits.append(aud)
        frames.append(proj)
    return pd.concat(frames, ignore_index=True), pd.DataFrame(audits), panel


def assemble(board: pd.DataFrame, proj: pd.DataFrame) -> pd.DataFrame:
    """Rank-space assembly, identical to `ranking_v1.v1_scores`, per position."""
    d = board.merge(
        proj[["player_id", "position", "entry", "proj_points", "proj_games"]],
        on=["player_id", "position"], how="left")
    if d["entry"].isna().any():
        missing = d.loc[d["entry"].isna(), "player_name"].tolist()
        raise RuntimeError(f"{len(missing)} board players never reached the model "
                           f"universe: {missing[:10]}")

    out = []
    for pos, g in d.groupby("position"):
        g = g.copy()
        # v1_scores returns -slot (0-based), higher = better. Reuse it verbatim
        # rather than re-implementing the assembly the evaluation was run on.
        g["_score"] = v1_scores(g.rename(columns={"consensus_pos_rank": "cpr"}),
                                "cpr")
        g["v1_pos_rank"] = (-g["_score"]).astype(int) + 1
        # slot substitution: v1's occupant of positional slot j inherits the
        # overall slot consensus gave to ITS occupant of positional slot j.
        slot_to_overall = (g.sort_values("consensus_pos_rank")
                            ["consensus_overall_slot"].to_numpy())
        g["v1_overall_key"] = slot_to_overall[g["v1_pos_rank"].to_numpy() - 1]
        out.append(g.drop(columns=["_score"]))
    d = pd.concat(out, ignore_index=True)
    d["v1_overall_rank"] = d["v1_overall_key"].rank(method="first").astype(int)
    d["is_rookie_pinned"] = (d["entry"] == "rookie")
    # a pinned row is consensus's opinion, not v1's. It carries no v1 points.
    d["v1_projected_points"] = np.where(d["is_rookie_pinned"], np.nan,
                                        d["proj_points"])
    return d.sort_values("v1_overall_rank").reset_index(drop=True)


# ------------------------------------------------------------------- artifacts
def git_head() -> str:
    try:
        return subprocess.run(["git", "rev-parse", "HEAD"], cwd=_REPO,
                              capture_output=True, text=True,
                              check=True).stdout.strip()
    except Exception:
        return "unknown"


def write_board_json(d: pd.DataFrame, cfg: Dict, consensus_as_of: str,
                     kickoff: pd.Timestamp, audits: pd.DataFrame) -> Path:
    players = []
    for r in d.itertuples():
        pts = None if not np.isfinite(r.v1_projected_points) \
            else round(float(r.v1_projected_points), 2)
        players.append({
            "name": r.player_name,
            "pos": r.position,
            "team": None if pd.isna(r.team) else str(r.team),
            "bye": None if pd.isna(r.bye_week) else int(r.bye_week),
            "v1_overall_rank": int(r.v1_overall_rank),
            "v1_pos_rank": int(r.v1_pos_rank),
            "v1_projected_points": pts,
            "source": "consensus_pinned" if r.is_rookie_pinned else "model",
            "consensus_overall_rank": int(r.consensus_overall_slot),
            "consensus_pos_rank": int(r.consensus_pos_rank),
        })
    n_rookie = int(d["is_rookie_pinned"].sum())
    doc = {
        "generated_for": TARGET_SEASON,
        "generated_at": _dt.datetime.now(_dt.timezone.utc).isoformat(),
        "generated_by": "ranker",
        "git_commit": git_head(),
        "ranking_version": cfg["version_id"],
        "config_sha256": cfg["_sha256"],
        "status": "DISPLAY ONLY -- UNVALIDATED",
        "what_this_is": (
            "One run of the frozen v1 config projected forward to an unplayed "
            "season. No tuning, no variant selection, no evaluation."),
        "validation": (
            "v1 was measured on 2018-2024 (docs/ranking/ranking-v1-results.md). "
            "It beat NEITHER crowd at ANY position; it lost to expert consensus "
            "at QB, RB and WR with BH-significant intervals, and reached parity "
            "-- not edge -- at WR only. Nothing in this file has been measured "
            "against anything."),
        "holdout": {
            "season": 2025,
            "spent": False,
            "fit_frozen_at_outcome_season": TRAIN_OUTCOME_MAX,
            "2025_role": "input features only (CLAUDE.md 6.1); never a training "
                         "outcome, never an evaluation target",
            "enforcement": "SeasonPanel.outcome_gate=2025 refuses to serve any "
                           "outcome at or after 2025; "
                           "WalkForward.project_target raises RuntimeError if a "
                           "training pair or the access audit carries an outcome "
                           "season past 2024",
        },
        "cross_positional_note": (
            "Overall order is CONSENSUS'S cross-positional structure with v1's "
            "occupant substituted into each positional slot. v1's own VBD "
            "revaluation channel is declared measured_by_this_design=false in "
            "v1.json and is not applied here. Every overall movement below is a "
            "within-position movement."),
        "rookie_note": (
            f"{n_rookie} of {len(d)} rows are players with no prior NFL season. "
            f"They are PINNED to their consensus positional slot and carry no "
            f"projected points: on those rows v1 is the crowd, by design."),
        "def_note": (
            "DEF is a starting slot in this league and is ABSENT from this board. "
            "nfl.db has zero DEF coverage and v1 emits no DEF ranking. Blank with "
            "a note rather than a fabricated number."),
        "consensus_source": CONSENSUS_SOURCE,
        "consensus_as_of": consensus_as_of,
        "week1_kickoff_measured": str(kickoff.date()),
        "counts": {
            "players": len(d),
            "rookies_pinned_to_consensus": n_rookie,
            "model_ranked": int(len(d) - n_rookie),
            **{f"n_{p}": int((d["position"] == p).sum()) for p in BOARD_POSITIONS},
        },
        "audit": json.loads(audits.to_json(orient="records")),
        "players": players,
    }
    path = EXPORT / "ranking_v1_2026.json"
    path.write_text(json.dumps(doc, indent=2) + "\n")
    return path


def patch_comparison(d: pd.DataFrame) -> Path:
    path = EXPORT / "rankings_comparison_2026.json"
    doc = json.loads(path.read_text())
    key = {(r.player_name, r.position): r for r in d.itertuples()}
    hits = 0
    for row in doc["players"]:
        r = key.get((row["name"], row["pos"]))
        if r is None:
            row["v1"] = None
            row["v1_source"] = "not on v1 board"
            continue
        hits += 1
        row["v1"] = int(r.v1_overall_rank)
        row["v1_pos_rank"] = int(r.v1_pos_rank)
        row["v1_source"] = "consensus_pinned" if r.is_rookie_pinned else "model"
        row["v1_projected_points"] = (
            None if not np.isfinite(r.v1_projected_points)
            else round(float(r.v1_projected_points), 2))
    n_rookie = int(d["is_rookie_pinned"].sum())
    doc["v1_status"] = (
        f"PRODUCED 2026-07-31 -- DISPLAY ONLY, UNVALIDATED. One run of the frozen "
        f"bottom-up-v1 config, fit frozen at outcome seasons <= {TRAIN_OUTCOME_MAX}; "
        f"2025 read as input features only and the 2025 holdout remains UNSPENT. "
        f"No accuracy was measured for this board. v1's only measured record "
        f"(2018-2024) is that it beat NEITHER crowd at ANY position. "
        f"{n_rookie} of {len(doc['players'])} rows are rookies pinned to consensus. "
        f"DEF absent -- no coverage in nfl.db. Overall order keeps consensus's "
        f"cross-positional structure; movement is within-position only. "
        f"Source: data/export/ranking_v1_2026.json")
    doc["v1_source"] = "data/export/ranking_v1_2026.json"
    path.write_text(json.dumps(doc, indent=2) + "\n")
    print(f"  patched {hits}/{len(doc['players'])} comparison rows with v1")
    return path


def log_feature_read(audits: pd.DataFrame) -> None:
    """Every access is logged, including the permitted ones."""
    entry = {
        "timestamp_utc": _dt.datetime.now(_dt.timezone.utc).isoformat(),
        "event": "FEATURES_ONLY_READ",
        "holdout_season": 2025,
        "seasons_requested": [2025],
        "holdout_spent": False,
        "access_kind": "input features only",
        "fit_frozen_at_outcome_season": TRAIN_OUTCOME_MAX,
        "target_season": TARGET_SEASON,
        "reason": (
            "ranker: produce ranking v1's 2026 board for display. 2025 box-score "
            "stats were read as INPUT FEATURES for a 2026 projection, which "
            "CLAUDE.md 6.1 permits and requires. THE FIT IS FROZEN AT OUTCOME "
            "SEASONS <= 2024: no 2025 outcome entered training, evaluation, or "
            "any sanity check, and no accuracy number was computed for 2025 or "
            "2026. THIS IS NOT A HOLDOUT SPEND. Enforced structurally by "
            "SeasonPanel.outcome_gate=2025 (the accessor refuses to serve a 2025 "
            "outcome) and by WalkForward.project_target's RuntimeError on any "
            "training pair past the frozen bound."),
        "enforcement": {
            "panel_feature_gate": FEATURE_GATE,
            "panel_outcome_gate": OUTCOME_GATE,
            "max_training_outcome_season_observed":
                int(audits["observed_max_outcome_season"].max()),
            "max_feature_cutoff_observed": int(audits["max_feature_cutoff"].max()),
            "outcome_reads_at_target": int(audits["n_outcome_reads_at_target"].sum()),
        },
        "artifacts": ["data/export/ranking_v1_2026.json",
                      "data/export/rankings_comparison_2026.json"],
        "git_commit": git_head(),
    }
    with HOLDOUT_LOG.open("a") as fh:
        fh.write(json.dumps(entry) + "\n")


# ------------------------------------------------------------------------ main
def main() -> None:
    raw = CONFIG_PATH.read_bytes()
    cfg = json.loads(raw)
    cfg["_sha256"] = hashlib.sha256(raw).hexdigest()
    print(f"config {CONFIG_PATH.relative_to(_REPO)}  sha256={cfg['_sha256'][:16]}")
    print(f"target {TARGET_SEASON}  |  fit FROZEN at outcome season "
          f"<= {TRAIN_OUTCOME_MAX}  |  2025 = features only")

    board, as_of, kickoff = load_consensus_board()
    print(f"consensus board {CONSENSUS_SOURCE} as_of {as_of}  n={len(board)}  "
          f"(2026 Week 1 measured {kickoff.date()})")

    proj, audits, panel = project_positions(cfg, board)
    print("\nLOOK-AHEAD / HOLDOUT AUDIT (one row per position)")
    cols = ["season", "train_outcome_max", "observed_max_outcome_season",
            "train_outcome_seasons", "max_feature_cutoff", "max_outcome_season",
            "n_outcome_reads_at_target", "n_preseason_proxy_reads"]
    print(audits[cols].to_string(index=False))
    assert (audits["observed_max_outcome_season"] <= TRAIN_OUTCOME_MAX).all()
    assert (audits["max_outcome_season"] <= TRAIN_OUTCOME_MAX).all()
    assert (audits["max_feature_cutoff"] <= TARGET_SEASON - 1).all()
    assert (audits["n_outcome_reads_at_target"] == 0).all()
    print("PASS -- no training pair carries an outcome season after "
          f"{TRAIN_OUTCOME_MAX}; 2025 outcomes were never served")

    d = assemble(board, proj)
    RESULTS.mkdir(parents=True, exist_ok=True)
    d.to_csv(RESULTS / "ranking_v1_2026_board.csv", index=False)

    n_rookie = int(d["is_rookie_pinned"].sum())
    nan_vet = int((~d["is_rookie_pinned"] & ~np.isfinite(d["proj_points"])).sum())
    print(f"\nboard {len(d)} players | {n_rookie} rookies pinned to consensus | "
          f"{len(d) - n_rookie} model-ranked | {nan_vet} veterans with no "
          f"projectable history (sunk to the bottom of their position)")
    print(d.groupby("position")["is_rookie_pinned"].agg(["size", "sum"]).to_string())

    print("\nTOP 30 -- v1 2026, display only, unvalidated")
    top = d.head(30)[["v1_overall_rank", "player_name", "position", "v1_pos_rank",
                      "v1_projected_points", "consensus_overall_slot",
                      "consensus_pos_rank", "is_rookie_pinned"]]
    print(top.to_string(index=False))

    p1 = write_board_json(d, cfg, as_of, kickoff, audits)
    p2 = patch_comparison(d)
    log_feature_read(audits)
    print(f"\nwrote {p1.relative_to(_REPO)}")
    print(f"wrote {p2.relative_to(_REPO)}")
    print(f"logged the 2025 features-only read to "
          f"{HOLDOUT_LOG.relative_to(_REPO)}")
    print("\nHOLDOUT 2025: UNSPENT. This run measured v1's accuracy at NOTHING.")


if __name__ == "__main__":
    main()
