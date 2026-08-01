"""
Discovery pass 1, section 2 — systematic screening: correlate every candidate column against
the residual, on the discovery sample (2018-2021) only. Rank by |effect size|, not p-value.
Denominator is printed and written to disk. Negative control (seeded noise) is screened
identically and its rank/percentile is what "noise looks like in this screen."
"""
import numpy as np
import pandas as pd
from scipy import stats

from experiments.bottomup.discovery_pass1 import CANDIDATE_COLS

DISC_CSV = "experiments/bottomup/results/discovery_pass1_discovery_sample.csv"


def spearman_safe(x, y):
    mask = x.notna() & y.notna()
    n = mask.sum()
    if n < 20:
        return np.nan, np.nan, n
    rho, p = stats.spearmanr(x[mask], y[mask])
    return rho, p, n


def screen(disc, target_col, screen_cols):
    rows = []
    for col in screen_cols:
        rho, p, n = spearman_safe(disc[col], disc[target_col])
        rows.append({"column": col, "target": target_col, "n": n, "spearman_rho": rho, "p_raw": p})
    out = pd.DataFrame(rows)
    out["abs_rho"] = out["spearman_rho"].abs()
    out = out.sort_values("abs_rho", ascending=False).reset_index(drop=True)
    out["rank"] = np.arange(1, len(out) + 1)
    return out


def screen_by_position(disc, target_col, screen_cols):
    frames = []
    for pos, g in disc.groupby("position"):
        r = screen(g, target_col, screen_cols)
        r["position"] = pos
        frames.append(r)
    return pd.concat(frames, ignore_index=True)


def main():
    disc = pd.read_csv(DISC_CSV)
    screen_cols = CANDIDATE_COLS + ["NOISE_CONTROL"]

    all_signed = screen(disc, "signed_resid", screen_cols)
    all_abs = screen(disc, "abs_resid", screen_cols)
    pos_signed = screen_by_position(disc, "signed_resid", screen_cols)
    pos_abs = screen_by_position(disc, "abs_resid", screen_cols)

    all_signed.to_csv("experiments/bottomup/results/discovery_pass1_screen_signed_all.csv", index=False)
    all_abs.to_csv("experiments/bottomup/results/discovery_pass1_screen_abs_all.csv", index=False)
    pos_signed.to_csv("experiments/bottomup/results/discovery_pass1_screen_signed_bypos.csv", index=False)
    pos_abs.to_csv("experiments/bottomup/results/discovery_pass1_screen_abs_bypos.csv", index=False)

    n_targets = 2  # signed_resid, abs_resid
    n_slices = 1 + disc["position"].nunique()  # pooled + per-position
    total_tests = len(screen_cols) * n_targets * n_slices
    print(f"Candidate columns: {len(screen_cols)} (incl. 1 noise control)")
    print(f"Targets screened: {n_targets} (signed_resid, abs_resid)")
    print(f"Slices: pooled + {disc['position'].nunique()} positions = {n_slices}")
    print(f"TOTAL SCREENING DENOMINATOR THIS SECTION: {total_tests}")

    print("\n=== Pooled, signed_resid, top 15 by |rho| ===")
    print(all_signed.head(15).to_string(index=False))
    noise_rank_signed = all_signed.loc[all_signed["column"] == "NOISE_CONTROL", "rank"].iloc[0]
    print(f"\nNOISE_CONTROL rank (pooled, signed_resid): {noise_rank_signed} of {len(all_signed)}, "
          f"rho={all_signed.loc[all_signed['column']=='NOISE_CONTROL','spearman_rho'].iloc[0]:.4f}")

    print("\n=== Pooled, abs_resid, top 15 by |rho| ===")
    print(all_abs.head(15).to_string(index=False))
    noise_rank_abs = all_abs.loc[all_abs["column"] == "NOISE_CONTROL", "rank"].iloc[0]
    print(f"\nNOISE_CONTROL rank (pooled, abs_resid): {noise_rank_abs} of {len(all_abs)}, "
          f"rho={all_abs.loc[all_abs['column']=='NOISE_CONTROL','spearman_rho'].iloc[0]:.4f}")

    with open("experiments/bottomup/results/discovery_pass1_screen_denominator.txt", "w") as f:
        f.write(f"Section 2 systematic screening denominator\n")
        f.write(f"Candidate columns (incl. noise control): {len(screen_cols)}\n")
        f.write(f"Targets: {n_targets}\n")
        f.write(f"Slices (pooled + per-position): {n_slices}\n")
        f.write(f"TOTAL: {total_tests}\n")
        f.write(f"\nNoise control rank, pooled signed_resid: {noise_rank_signed} of {len(all_signed)}\n")
        f.write(f"Noise control rank, pooled abs_resid: {noise_rank_abs} of {len(all_abs)}\n")


if __name__ == "__main__":
    main()
