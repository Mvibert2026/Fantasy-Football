"""
Discovery pass 1, section 3 — flexible model as a hypothesis GENERATOR ONLY.

Fits a RandomForestRegressor (a flexible model) on signed_resid using the discovery sample
(2018-2021) only, and reads feature importances. This is NOT a model decision -- CLAUDE.md
Section 6.3's "start with weighted/regression approaches, not ML" governs what gets shipped.
Here the forest is used purely as an instrument to point at candidates for later testing in
the simple registered framework, exactly as the dispatch specifies.

Two variants are fit and reported:
  (a) full candidate set -- dominated by proj_* columns, which are mechanically close to the
      residual's own definition (signed_resid = z_actual - z_proj) and mostly re-discover
      regression-to-the-mean, already established in section 1/2.
  (b) candidate set EXCLUDING proj_* (except proj_games, kept as the single usage-level
      control) -- surfaces secondary structure not explained by "how big was the projection."
A seeded-noise feature is included in both variants as the negative control for what an
importance score looks like for a column that provably carries no signal.
"""
import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestRegressor
from sklearn.inspection import permutation_importance

from experiments.bottomup.discovery_pass1 import CANDIDATE_COLS

DISC_CSV = "experiments/bottomup/results/discovery_pass1_discovery_sample.csv"
RNG_SEED = 20260801


def fit_and_report(disc, features, label, target="signed_resid"):
    d = disc[features + [target]].copy()
    d = d.fillna(d.median(numeric_only=True))
    X = d[features].values
    y = d[target].values

    rf = RandomForestRegressor(
        n_estimators=200, max_depth=5, min_samples_leaf=20,
        random_state=RNG_SEED, n_jobs=1,
    )
    rf.fit(X, y)

    imp = permutation_importance(
        rf, X, y, n_repeats=10, random_state=RNG_SEED, n_jobs=1
    )
    out = pd.DataFrame({
        "feature": features,
        "importance_mean": imp.importances_mean,
        "importance_std": imp.importances_std,
        "gini_importance": rf.feature_importances_,
    }).sort_values("importance_mean", ascending=False).reset_index(drop=True)
    out["rank"] = np.arange(1, len(out) + 1)

    print(f"\n=== {label} (n_features={len(features)}, n={len(d)}) ===")
    print(out.head(15).to_string(index=False))
    noise_row = out[out["feature"] == "NOISE_CONTROL"]
    if len(noise_row):
        print(f"NOISE_CONTROL rank: {noise_row['rank'].iloc[0]} of {len(out)}, "
              f"importance_mean={noise_row['importance_mean'].iloc[0]:.5f}")
    return out


def main():
    disc = pd.read_csv(DISC_CSV)
    # DISC_CSV already carries a NOISE_CONTROL column written by discovery_pass1.py (section 2's
    # negative control draw); reuse it here rather than creating a duplicate-named column.
    assert "NOISE_CONTROL" in disc.columns

    full_features = list(CANDIDATE_COLS) + ["NOISE_CONTROL"]
    reduced_features = [c for c in CANDIDATE_COLS if not c.startswith("proj_") or c == "proj_games"]
    reduced_features = reduced_features + ["NOISE_CONTROL"]

    pooled_full = fit_and_report(disc, full_features, "POOLED, full candidate set")
    pooled_reduced = fit_and_report(disc, reduced_features, "POOLED, proj_* excluded (except proj_games)")

    pooled_full.to_csv("experiments/bottomup/results/discovery_pass1_gbm_pooled_full.csv", index=False)
    pooled_reduced.to_csv("experiments/bottomup/results/discovery_pass1_gbm_pooled_reduced.csv", index=False)

    for pos in ["QB", "RB", "WR", "TE"]:
        sub = disc[disc["position"] == pos]
        r = fit_and_report(sub, reduced_features, f"{pos}, proj_* excluded (except proj_games)")
        r.to_csv(f"experiments/bottomup/results/discovery_pass1_gbm_{pos}_reduced.csv", index=False)

    print(f"\nGBM section feature-set sizes: full={len(full_features)}, reduced={len(reduced_features)}")
    print(f"Models fit (pooled x2 + 4 positions x reduced) = 6; each screens its full feature "
          f"set (denominator already counted at the column level in section 2).")


if __name__ == "__main__":
    main()
