"""D3: v2-flatgames, registered in batch-M2.md Amendment 1 (commit fb68505) before this ran."""
import numpy as np, pandas as pd

R = "/home/user/Fantasy-Football/experiments/bottomup/results"
P = pd.read_csv(f"{R}/ranking_v1_v1_players.csv")
SM = pd.read_csv(f"{R}/ranking_v1_v1_season_metrics.csv")
SEED, REPS = 20260801, 4000

def spearman(a, b):
    ar = pd.Series(a).rank().to_numpy(); br = pd.Series(b).rank().to_numpy()
    ar = (ar - ar.mean()) / ar.std(); br = (br - br.mean()) / br.std()
    return float(np.mean(ar * br))

def v1_slots(d, rank_col, proj_col):
    r = d[rank_col].to_numpy(dtype=float)
    order = np.argsort(r, kind="stable")
    is_rookie = (d["entry"].to_numpy() == "rookie")[order]
    proj = d[proj_col].to_numpy(dtype=float)[order]
    slots = np.arange(len(order), dtype=float)
    out = np.empty(len(order), dtype=float)
    out[is_rookie] = slots[is_rookie]
    vs = slots[~is_rookie]
    vi = np.argsort(-np.nan_to_num(proj[~is_rookie], nan=-1e18), kind="stable")
    filled = np.empty(int((~is_rookie).sum()), dtype=float)
    filled[vi] = vs
    out[~is_rookie] = filled
    s = np.empty(len(d), dtype=float)
    s[order] = out
    return s

P["ppg_proj"] = P["proj_points"] / np.maximum(P["proj_games"], 1.0)          # v2-flatgames
P["shrunk"]   = P["proj_points"] * 0 # placeholder, set per block (needs pos mean games)

PANELS = [("M", "ffc_pos_rank", (2018, 2024), "rho_b1_market_adp"),
          ("E", "ecr_pos_rank", (2021, 2024), "rho_b2_expert_ecr")]
POS = ["QB", "RB", "WR", "TE"]

def pair_stats(g, slot_col, crowd_col):
    g = g[g.entry != "rookie"]
    v = g[slot_col].to_numpy(); c = g[crowd_col].to_numpy(dtype=float)
    pts = g["points"].to_numpy(dtype=float)
    n = len(g); wins = pairs = 0
    for i in range(n):
        for j in range(i + 1, n):
            dv, dc = v[i] - v[j], c[i] - c[j]
            if dv == 0 or dc == 0 or np.sign(dv) == np.sign(dc): continue
            pref, other = (i, j) if dv < 0 else (j, i)
            if pts[pref] == pts[other]: continue
            pairs += 1; wins += int(pts[pref] > pts[other])
    return wins, pairs

print("D3 -- v2-flatgames (veterans by projected per-game points), 8 graded cells")
print(f"{'cell':8s} {'d_v1':>8s} {'d_v2':>8s} {'v2-v1':>8s} {'95% CI':>20s} {'p':>7s}  verdict")
rng_master = np.random.default_rng(SEED)
for panel, rank_col, span, crowd_rho in PANELS:
    for pos in POS:
        sub = P[(P.position == pos) & P[rank_col].notna() & P.season.between(*span)]
        dd = []   # per-season (delta_v2 - delta_v1)
        d1l, d2l = [], []
        ws_v2 = []
        for season, g in sub.groupby("season"):
            if len(g) < 10: continue
            g = g.copy()
            g["s1"] = v1_slots(g, rank_col, "proj_points")
            g["s2"] = v1_slots(g, rank_col, "ppg_proj")
            act = g["points"].to_numpy(dtype=float)
            pub = SM[(SM.panel == panel) & (SM.position == pos) & (SM.season == season)]
            rho_crowd = float(pub[crowd_rho].iloc[0])
            r1 = spearman(-g["s1"].to_numpy(), act) - rho_crowd
            r2 = spearman(-g["s2"].to_numpy(), act) - rho_crowd
            d1l.append(r1); d2l.append(r2); dd.append(r2 - r1)
            ws_v2.append(pair_stats(g, "s2", rank_col))
        dd = np.array(dd); n = len(dd)
        rng = np.random.default_rng(SEED)
        boot = np.array([np.mean(rng.choice(dd, size=n, replace=True)) for _ in range(REPS)])
        lo, hi = np.percentile(boot, [2.5, 97.5])
        p = 2.0 * min(float((boot <= 0).mean()), float((boot >= 0).mean()))
        p = min(1.0, max(p, 1.0 / REPS))
        verdict = "WIN" if lo > 0 else ("HARM" if hi < 0 else "NULL")
        arr = np.array(ws_v2, dtype=float); w, pr = arr[:, 0].sum(), arr[:, 1].sum()
        print(f"{panel}-{pos:3s} {np.mean(d1l):+8.4f} {np.mean(d2l):+8.4f} {np.mean(dd):+8.4f} "
              f"[{lo:+8.4f},{hi:+8.4f}] {p:7.4f}  {verdict}   "
              f"(v2 vet-pair win rate {w/pr if pr>0 else float('nan'):.3f}/{int(pr)})")

print()
print("Descriptive sensitivity only (NOT a candidate): 0.5-shrink of games toward block mean")
for panel, rank_col, span, crowd_rho in PANELS:
    row = []
    for pos in POS:
        sub = P[(P.position == pos) & P[rank_col].notna() & P.season.between(*span)]
        deltas = []
        for season, g in sub.groupby("season"):
            if len(g) < 10: continue
            g = g.copy()
            vets = g.entry != "rookie"
            mg = g.loc[vets, "proj_games"].mean()
            g["gsh"] = g["ppg_proj"] * (0.5 * np.maximum(g["proj_games"], 1.0) + 0.5 * mg)
            g["s3"] = v1_slots(g, rank_col, "gsh")
            act = g["points"].to_numpy(dtype=float)
            pub = SM[(SM.panel == panel) & (SM.position == pos) & (SM.season == season)]
            deltas.append(spearman(-g["s3"].to_numpy(), act) - float(pub[crowd_rho].iloc[0]))
        row.append(f"{pos}: {np.mean(deltas):+.4f}")
    print(f"  {panel}  " + "   ".join(row))

print()
print("Context: how good is proj_games at all? (veterans, pooled, both panels' union)")
vets = P[(P.entry != "rookie") & P["ffc_pos_rank"].notna()]
for pos in POS:
    g = vets[vets.position == pos]
    c_proj = np.corrcoef(g["proj_games"], g["games"])[0, 1]
    c_naive = np.corrcoef(g["games_1"].fillna(0), g["games"])[0, 1]
    mae_p = np.mean(np.abs(g["proj_games"] - g["games"]))
    mae_n = np.mean(np.abs(g["games_1"].fillna(0) - g["games"]))
    print(f"  {pos}: corr(proj_games, games)={c_proj:+.3f} vs corr(games_1, games)={c_naive:+.3f}; "
          f"MAE {mae_p:.2f} vs naive {mae_n:.2f}  (n={len(g)})")
