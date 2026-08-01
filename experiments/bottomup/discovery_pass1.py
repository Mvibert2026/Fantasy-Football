"""
Discovery pass 1 — reverse-identification hypothesis generation on ranking v2 residuals.

FR-2026-07-31-reverse-discovery. This script is a SEARCH INSTRUMENT, not a model and not a
test. Everything it prints is a candidate for later registered confirmation, never a finding.

Discipline enforced structurally in this file:
  - Discovery is run ONLY on seasons 2018-2021. Seasons 2022-2024 are loaded for bookkeeping
    (counts, coverage) but no correlation, slice mean, or importance score is ever computed
    on them here. 2025 does not exist in this CSV at all (holdout, untouched).
  - Every candidate predictor column screened is counted. The counter is printed and written
    into the output artifacts so the report's stated denominator is reproducible, not asserted.
  - A seeded-noise column is screened identically to every real candidate (negative control).
  - Only pre-Week-1-constructible columns are screened as candidates (proj_*, lag-1 actuals,
    age/evidence/adp/entry, and two DB-joined preseason indicators). Target-season actual
    columns (games, points, targets, ...) are used ONLY to build the residual/outcome, never
    as candidate predictors of themselves.
"""
import sqlite3
import numpy as np
import pandas as pd
from scipy import stats

RNG_SEED = 20260801
DISCOVERY_SEASONS = [2018, 2019, 2020, 2021]
CONFIRMATION_SEASONS = [2022, 2023, 2024]  # loaded for bookkeeping only, never analyzed here

CSV_PATH = "experiments/bottomup/results/ranking_v2_G0_players.csv"
DB_PATH = "data/nfl.db"


def load_base():
    df = pd.read_csv(CSV_PATH)
    assert (df["arm"] == "G0").all(), "expected pinned G0 arm only"
    return df


def add_db_joined_features(df):
    """Join two additional pre-Week-1-constructible features from unused DB tables.

    depth_chart_starter_wk1: was this player listed at pos_rank 1 (starter) at their position
        on their team's Week 1 (regular-season) depth chart of the TARGET season. Depth charts
        are set before kickoff, so this is available before Week 1 games are played.
    preseason_injury_flag: did this player appear on an injury report during the PRESEASON
        (game_type == 'PRE') of the target season, at any practice/report status. Preseason
        injury reports are, by construction, pre-Week-1.
    Both are counted in the screening denominator (see NOTE_DB_JOINED below).
    """
    con = sqlite3.connect(DB_PATH)

    depth = pd.read_sql(
        """
        SELECT DISTINCT gsis_id AS player_id, season, pos_rank
        FROM depth_charts_weekly
        WHERE game_type = 'REG' AND week = 1 AND gsis_id IS NOT NULL
        """,
        con,
    )
    depth["pos_rank_num"] = pd.to_numeric(depth["pos_rank"], errors="coerce")
    depth = depth.sort_values("pos_rank_num").drop_duplicates(["player_id", "season"], keep="first")
    depth["depth_chart_starter_wk1"] = (depth["pos_rank_num"] == 1).astype(float)
    depth = depth[["player_id", "season", "depth_chart_starter_wk1"]]

    inj = pd.read_sql(
        """
        SELECT DISTINCT gsis_id AS player_id, season
        FROM injuries
        WHERE game_type = 'PRE' AND gsis_id IS NOT NULL
        """,
        con,
    )
    inj["preseason_injury_flag"] = 1.0
    inj = inj[["player_id", "season", "preseason_injury_flag"]]

    con.close()

    df = df.merge(depth, on=["player_id", "season"], how="left")
    df = df.merge(inj, on=["player_id", "season"], how="left")
    df["depth_chart_starter_wk1"] = df["depth_chart_starter_wk1"].fillna(0.0)
    df["preseason_injury_flag"] = df["preseason_injury_flag"].fillna(0.0)
    return df


# Candidate predictor columns — must be constructible before Week 1 of the target season.
CANDIDATE_COLS = [
    # projection-side (v2's own pre-season stat-line projection)
    "proj_games", "proj_apg", "proj_attempts", "proj_pass_yards", "proj_pass_tds",
    "proj_interceptions", "proj_carries", "proj_rush_yards", "proj_rush_tds",
    "proj_fumbles_lost", "proj_ypa", "proj_td_per_att", "proj_bonus_points",
    "proj_points_base", "proj_points", "proj_cpg", "proj_tpg", "proj_targets",
    "proj_receptions", "proj_rec_yards", "proj_rec_tds", "proj_ypc", "proj_catch_rate",
    "proj_ypr", "proj_td_per_target",
    # prior-season (N-1) lag actuals — known before Week 1 of N
    "pts_1", "ppg_w", "gshare_w", "gshare_1", "age", "evidence", "present_1",
    "gshare_max3", "inj_missed_share_1", "unexp_missed_share_1", "rostered_absent_share_1",
    "offroster_share_1", "depth_first_share_1", "inj_out_wks_1", "missed_wks_1",
    "games_1", "tgt_1", "rec_1", "recyds_1", "rectd_1", "carries_1", "rushyds_1",
    "rushtd_1", "att_1", "passyds_1", "passtd_1", "ints_1", "late4_share_1",
    "endgap_share_1", "played_thru_1", "chronic_missed_share", "miss1_x_endgap",
    "miss1_x_resolved",
    # meta / market
    "average_pick", "n_train_seasons",
    # DB-joined preseason indicators
    "depth_chart_starter_wk1", "preseason_injury_flag",
]

# columns that are NOT candidates: target-season actuals (games, points, targets, rec_yards,
# ..., g100/r100/p300 etc, entry_act, position_act) — these define the residual, not predict it.


def compute_residuals(df):
    """Signed and absolute residual, standardized within season x position on realised points
    vs v2's projected points. Positive signed_resid = v2 under-projected (player beat proj);
    negative = v2 over-projected (bust relative to proj)."""
    df = df.copy()
    grp = df.groupby(["season", "position"])
    df["z_actual"] = grp["points"].transform(lambda s: (s - s.mean()) / s.std(ddof=0) if s.std(ddof=0) > 0 else 0.0)
    df["z_proj"] = grp["proj_points"].transform(lambda s: (s - s.mean()) / s.std(ddof=0) if s.std(ddof=0) > 0 else 0.0)
    df["signed_resid"] = df["z_actual"] - df["z_proj"]
    df["abs_resid"] = df["signed_resid"].abs()
    # rank-based residual (rank of actual minus rank of proj, within season-position; positive =
    # finished better than projected rank)
    df["rank_actual"] = grp["points"].rank(ascending=False)
    df["rank_proj"] = grp["proj_points"].rank(ascending=False)
    df["rank_resid"] = df["rank_proj"] - df["rank_actual"]  # positive = beat projection
    return df


def main():
    np.random.seed(RNG_SEED)
    df = load_base()
    df = add_db_joined_features(df)
    df = compute_residuals(df)

    df["sample"] = np.where(df["season"].isin(DISCOVERY_SEASONS), "discovery",
                    np.where(df["season"].isin(CONFIRMATION_SEASONS), "confirmation", "other"))

    print("=== Sample sizes ===")
    print(df["sample"].value_counts())
    print(df.groupby(["sample"])["season"].unique())

    disc = df[df["sample"] == "discovery"].copy()
    print(f"\nDiscovery n = {len(disc)} (seasons {DISCOVERY_SEASONS})")
    print("Confirmation set loaded but NOT analyzed in this pass "
          f"(n = {(df['sample']=='confirmation').sum()}, seasons {CONFIRMATION_SEASONS}).")

    # Negative control column: seeded noise, screened identically to real candidates.
    disc["NOISE_CONTROL"] = np.random.normal(size=len(disc))
    screen_cols = CANDIDATE_COLS + ["NOISE_CONTROL"]

    disc.to_csv("experiments/bottomup/results/discovery_pass1_discovery_sample.csv", index=False)
    df.to_csv("experiments/bottomup/results/discovery_pass1_full_with_residuals.csv", index=False)

    print(f"\nCandidate columns screened (incl. noise control): {len(screen_cols)}")
    with open("experiments/bottomup/results/discovery_pass1_denominator.txt", "w") as f:
        f.write(f"Discovery-sample screening denominator (Section 2, systematic screening)\n")
        f.write(f"Real candidate columns: {len(CANDIDATE_COLS)}\n")
        f.write(f"Plus 1 seeded-noise negative control column.\n")
        f.write(f"Total columns screened against signed_resid AND abs_resid (2 targets): "
                f"{len(screen_cols)} x 2 = {len(screen_cols)*2}\n\n")
        f.write("Candidate columns:\n")
        for c in CANDIDATE_COLS:
            f.write(f"  {c}\n")


if __name__ == "__main__":
    main()
