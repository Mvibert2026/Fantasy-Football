"""
Discovery pass 1, section 1 — residual slice analysis (the core of the method).

Builds a fixed set of slice variables from pre-Week-1-constructible information, computes the
mean signed_resid within each slice cell (discovery sample only, 2018-2021), and reports the
cells where the residual is most systematically non-zero. Also slices the seeded-noise
residual identically as the negative control for "what does an empty slice look like here."
"""
import numpy as np
import pandas as pd
from scipy import stats

DISC_CSV = "experiments/bottomup/results/discovery_pass1_discovery_sample.csv"


def bucket(series, edges, labels):
    return pd.cut(series, bins=edges, labels=labels, right=False)


def build_slices(disc):
    d = disc.copy()
    d["age_bucket"] = bucket(d["age"], [0, 24, 27, 30, 99], ["<24", "24-26", "27-29", "30+"])
    d["prior_games_bucket"] = bucket(
        d["games_1"].fillna(-1), [-1, 0, 5, 10, 14, 18], ["rookie/no N-1", "0-4", "5-9", "10-13", "14-17"]
    )
    d["workload_tier"] = d.groupby("position")["pts_1"].transform(
        lambda s: pd.qcut(s.rank(method="first"), 4, labels=["Q1 low", "Q2", "Q3", "Q4 high"])
    )
    d["depth_role"] = np.where(d["depth_chart_starter_wk1"] == 1, "wk1 starter", "wk1 non-starter/unlisted")
    d["prior_injury_tier"] = bucket(
        d["inj_missed_share_1"].fillna(-0.01), [-0.02, 0.0, 0.1, 0.3, 1.01],
        ["none", "light (0-10%)", "moderate (10-30%)", "heavy (30%+)"]
    )
    d["unexpected_absence_tier"] = bucket(
        d["unexp_missed_share_1"].fillna(-0.01), [-0.02, 0.0, 0.1, 0.3, 1.01],
        ["none", "light", "moderate", "heavy"]
    )
    d["evidence_tier"] = bucket(d["evidence"].fillna(0), [0, 1, 3, 5, 99], ["0", "1-2", "3-4", "5+"])
    d["wk1_injury_report"] = np.where(d["wk1_injury_report_flag"] == 1, "flagged", "clear")
    return d


SLICE_VARS = [
    "position", "entry", "age_bucket", "prior_games_bucket", "workload_tier",
    "depth_role", "prior_injury_tier", "unexpected_absence_tier", "evidence_tier",
    "wk1_injury_report",
]


def slice_report(d, resid_col, min_n=15):
    rows = []
    for var in SLICE_VARS:
        for level, g in d.groupby(var, observed=True):
            n = g[resid_col].notna().sum()
            if n < min_n:
                continue
            vals = g[resid_col].dropna()
            mean = vals.mean()
            se = vals.std(ddof=1) / np.sqrt(n)
            t = mean / se if se > 0 else np.nan
            rows.append({
                "slice_var": var, "level": str(level), "n": n,
                "mean_resid": mean, "se": se, "t_stat": t,
            })
    out = pd.DataFrame(rows)
    out["abs_t"] = out["t_stat"].abs()
    return out.sort_values("abs_t", ascending=False).reset_index(drop=True)


def main():
    disc = pd.read_csv(DISC_CSV)
    d = build_slices(disc)

    # negative control: seeded noise residual, sliced identically
    np.random.seed(20260801 + 1)
    d["NOISE_RESID"] = np.random.normal(size=len(d))

    real = slice_report(d, "signed_resid")
    noise = slice_report(d, "NOISE_RESID")

    n_cells_real = len(real)
    n_cells_noise = len(noise)
    print(f"Real slice cells examined (n>=15): {n_cells_real}")
    print(f"Noise slice cells examined (n>=15): {n_cells_noise}")
    print(f"Total slice denominator (real + noise): {n_cells_real + n_cells_noise}")

    print("\n=== Top 20 real slices by |t| (signed_resid, mean_resid: + = beats proj, - = overprojected) ===")
    print(real.head(20).to_string(index=False))

    print("\n=== Top 10 NOISE slices by |t| (negative control -- what a spurious slice looks like) ===")
    print(noise.head(10).to_string(index=False))

    real.to_csv("experiments/bottomup/results/discovery_pass1_slices_real.csv", index=False)
    noise.to_csv("experiments/bottomup/results/discovery_pass1_slices_noise.csv", index=False)

    with open("experiments/bottomup/results/discovery_pass1_slices_denominator.txt", "w") as f:
        f.write(f"Section 1 slice denominator\n")
        f.write(f"Slice variables: {len(SLICE_VARS)} ({SLICE_VARS})\n")
        f.write(f"Real slice cells with n>=15: {n_cells_real}\n")
        f.write(f"Noise slice cells with n>=15 (negative control): {n_cells_noise}\n")
        f.write(f"Noise slice max |t|: {noise['abs_t'].max():.3f} "
                f"({noise.iloc[0]['slice_var']}={noise.iloc[0]['level']})\n")
        f.write(f"Noise slice cells with |t| > 2: {(noise['abs_t'] > 2).sum()} of {n_cells_noise}\n")
        f.write(f"Real slice cells with |t| > 2: {(real['abs_t'] > 2).sum()} of {n_cells_real}\n")


if __name__ == "__main__":
    main()
