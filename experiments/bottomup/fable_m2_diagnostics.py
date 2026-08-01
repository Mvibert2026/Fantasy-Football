"""Fable M2 diagnostics D0/D1/D2 on the frozen v1 panel. Pre-registered in
docs/fable/M2-findings.md + docs/ranking/factor-campaign-manifest/batch-M2.md
(commit 3af33cd) BEFORE this ran. Read-only over committed CSVs; no refit; 2025 absent."""
import numpy as np, pandas as pd

R = "/home/user/Fantasy-Football/experiments/bottomup/results"
P = pd.read_csv(f"{R}/ranking_v1_v1_players.csv")
SM = pd.read_csv(f"{R}/ranking_v1_v1_season_metrics.csv")
SEED, REPS = 20260801, 4000

def spearman(a, b):
    ar = pd.Series(a).rank().to_numpy(); br = pd.Series(b).rank().to_numpy()
    ar = (ar - ar.mean()) / ar.std(); br = (br - br.mean()) / br.std()
    return float(np.mean(ar * br))

def v1_slots(d, rank_col, proj_col="proj_points"):
    """Exact replica of ranking_v1.v1_scores, parameterised by projection column.
    Returns slot (lower=better) aligned to d's rows."""
    r = d[rank_col].to_numpy(dtype=float)
    order = np.argsort(r, kind="stable")
    is_rookie = (d["entry"].to_numpy() == "rookie")[order]
    proj = d[proj_col].to_numpy(dtype=float)[order]
    slots = np.arange(len(order), dtype=float)
    out_slot = np.empty(len(order), dtype=float)
    out_slot[is_rookie] = slots[is_rookie]
    vet_slots = slots[~is_rookie]
    vet_idx = np.argsort(-np.nan_to_num(proj[~is_rookie], nan=-1e18), kind="stable")
    filled = np.empty(int((~is_rookie).sum()), dtype=float)
    filled[vet_idx] = vet_slots
    out_slot[~is_rookie] = filled
    slot = np.empty(len(d), dtype=float)
    slot[order] = out_slot
    return slot

PANELS = [("M", "ffc_pos_rank", (2018, 2024), "rho_b1_market_adp"),
          ("E", "ecr_pos_rank", (2021, 2024), "rho_b2_expert_ecr")]
POS = ["QB", "RB", "WR", "TE"]

# oracle-games projection (D1)
P["oracle_pts"] = P["proj_points"] * P["games"] / np.maximum(P["proj_games"], 1.0)

print("=" * 100)
print("D0 -- reproduce published rho_v1 per cell from the per-player panel")
print("=" * 100)
max_err = 0.0
blocks = {}   # (panel,pos,season) -> block df with slots attached
for panel, rank_col, span, crowd_rho in PANELS:
    for pos in POS:
        sub = P[(P.position == pos) & P[rank_col].notna()
                & P.season.between(span[0], span[1])]
        for season, g in sub.groupby("season"):
            if len(g) < 10:
                continue
            g = g.copy()
            g["v1_slot"] = v1_slots(g, rank_col)
            g["og_slot"] = v1_slots(g, rank_col, "oracle_pts")
            act = g["points"].to_numpy(dtype=float)
            rho_mine = spearman(-g["v1_slot"].to_numpy(), act)
            pub = SM[(SM.panel == panel) & (SM.position == pos) & (SM.season == season)]
            rho_pub = float(pub["rho_v1"].iloc[0])
            max_err = max(max_err, abs(rho_mine - rho_pub))
            blocks[(panel, pos, int(season))] = g
print(f"max |rho_mine - rho_published| over all cells: {max_err:.2e}")
assert max_err <= 0.005, "REPRODUCTION FAILED -- stop, this is the finding"

print()
print("=" * 100)
print("D0b -- batch 5/7 'full-universe improvement degrades the board' sign check")
print("=" * 100)
for b in (5, 7):
    d = pd.read_csv(f"{R}/factor_batch{b}_results.csv")
    cols = [c for c in d.columns]
    e1a = [c for c in cols if "e1a" in c.lower()]
    e1b = [c for c in cols if "e1b" in c.lower()]
    print(f"batch {b}: cols e1a-like={e1a[:3]} e1b-like={e1b[:3]} n={len(d)}")
    if e1a and e1b:
        a, bb = d[e1a[0]], d[e1b[0]]
        imp = d[(a < 0)]
        print(f"  arms improving full universe (E1a<0): {len(imp)}; "
              f"of those, E1b>0 (board worse): {(imp[e1b[0]] > 0).sum()}")

def boot_rate(per_season, reps=REPS, seed=SEED):
    """per_season: list of (wins, pairs). Season-block bootstrap of pooled rate."""
    rng = np.random.default_rng(seed)
    arr = np.array(per_season, dtype=float)
    n = len(arr)
    tot_w, tot_p = arr[:, 0].sum(), arr[:, 1].sum()
    if tot_p == 0:
        return np.nan, np.nan, np.nan, np.nan, 0
    rates = []
    for _ in range(reps):
        pick = arr[rng.integers(0, n, size=n)]
        w, p = pick[:, 0].sum(), pick[:, 1].sum()
        rates.append(w / p if p > 0 else np.nan)
    rates = np.array(rates)
    rates = rates[np.isfinite(rates)]
    pv = 2.0 * min(float((rates <= 0.5).mean()), float((rates >= 0.5).mean()))
    return (tot_w / tot_p, float(np.percentile(rates, 2.5)),
            float(np.percentile(rates, 97.5)), min(1.0, max(pv, 1.0 / reps)), int(tot_p))

def pair_stats(g, slot_col, crowd_col, vets_only, min_gap=0):
    """wins, pairs for v1 vs crowd inversions in one block."""
    if vets_only:
        g = g[g.entry != "rookie"]
    v = g[slot_col].to_numpy(); c = g[crowd_col].to_numpy(dtype=float)
    pts = g["points"].to_numpy(dtype=float)
    n = len(g)
    wins = pairs = 0
    for i in range(n):
        for j in range(i + 1, n):
            dv, dc = v[i] - v[j], c[i] - c[j]
            if dv == 0 or dc == 0 or np.sign(dv) == np.sign(dc):
                continue
            if abs(dv) < min_gap:
                continue
            pref, other = (i, j) if dv < 0 else (j, i)   # lower slot = better
            if pts[pref] == pts[other]:
                continue
            pairs += 1
            wins += int(pts[pref] > pts[other])
    return wins, pairs

print()
print("=" * 100)
print("D1 -- availability channel: v1 with ORACLE GAMES (rates fixed, games = realised)")
print("=" * 100)
d1_rows = []
for panel, rank_col, span, crowd_rho in PANELS:
    for pos in POS:
        cells = [(s, g) for (pn, ps, s), g in blocks.items() if pn == panel and ps == pos]
        deltas, deltas_og = [], []
        for season, g in sorted(cells):
            act = g["points"].to_numpy(dtype=float)
            rho_v1 = spearman(-g["v1_slot"].to_numpy(), act)
            rho_og = spearman(-g["og_slot"].to_numpy(), act)
            pub = SM[(SM.panel == panel) & (SM.position == pos) & (SM.season == season)]
            rho_crowd = float(pub[crowd_rho].iloc[0])
            deltas.append(rho_v1 - rho_crowd)
            deltas_og.append(rho_og - rho_crowd)
        d, dog = float(np.mean(deltas)), float(np.mean(deltas_og))
        closed = (dog - d) / (-d) if d < 0 else np.nan
        d1_rows.append((panel, pos, d, dog, closed))
        print(f"  {panel} {pos:3s}  drho v1: {d:+.4f}   drho oracle-games: {dog:+.4f}"
              f"   deficit closed: {closed if np.isfinite(closed) else float('nan'):+.0%}"
              if d < 0 else
              f"  {panel} {pos:3s}  drho v1: {d:+.4f}   drho oracle-games: {dog:+.4f}   (no deficit)")

print()
print("D1b -- player-level d^2 attribution of the v1-vs-crowd rank-error excess")
print("(share of the excess Sum d^2_v1 - Sum d^2_crowd from players with missed_wks_1 >= 4)")
for panel, rank_col, span, crowd_rho in PANELS:
    for pos in POS:
        cells = [(s, g) for (pn, ps, s), g in blocks.items() if pn == panel and ps == pos]
        exc_missed = exc_full = 0.0
        n_missed = n_full = 0
        for season, g in sorted(cells):
            act_rank = pd.Series(-g["points"].to_numpy()).rank().to_numpy()
            v1_rank = pd.Series(g["v1_slot"].to_numpy()).rank().to_numpy()
            cr_rank = pd.Series(g[rank_col].to_numpy(dtype=float)).rank().to_numpy()
            d2_v1 = (v1_rank - act_rank) ** 2
            d2_cr = (cr_rank - act_rank) ** 2
            excess = d2_v1 - d2_cr
            missed = (g["missed_wks_1"].fillna(99).to_numpy() >= 4)
            exc_missed += excess[missed].sum(); exc_full += excess[~missed].sum()
            n_missed += missed.sum(); n_full += (~missed).sum()
        tot = exc_missed + exc_full
        share = exc_missed / tot if tot > 0 else np.nan
        print(f"  {panel} {pos:3s}  excess d2 total {tot:+12.0f}  from missed-time "
              f"players: {share if np.isfinite(share) else float('nan'):+.0%} "
              f"(they are {n_missed/(n_missed+n_full):.0%} of rows)")

print()
print("=" * 100)
print("D2 -- disagreement-conditional win rate (PRIMARY: veteran-only pairs), 8 graded cells")
print("=" * 100)
d2 = []
for panel, rank_col, span, crowd_rho in PANELS:
    for pos in POS:
        cells = [(s, g) for (pn, ps, s), g in blocks.items() if pn == panel and ps == pos]
        per_season = [pair_stats(g, "v1_slot", rank_col, vets_only=True)
                      for _, g in sorted(cells)]
        rate, lo, hi, pv, npairs = boot_rate(per_season)
        d2.append(dict(panel=panel, pos=pos, rate=rate, lo=lo, hi=hi, p=pv, pairs=npairs))
        print(f"  {panel} {pos:3s}  vet-pair win rate {rate:.3f} [{lo:.3f}, {hi:.3f}] "
              f"p={pv:.4f}  pairs={npairs}")
print("\nD2 sensitivity: all pairs (rookie-involved included)")
for panel, rank_col, span, crowd_rho in PANELS:
    for pos in POS:
        cells = [(s, g) for (pn, ps, s), g in blocks.items() if pn == panel and ps == pos]
        per_season = [pair_stats(g, "v1_slot", rank_col, vets_only=False)
                      for _, g in sorted(cells)]
        rate, lo, hi, pv, npairs = boot_rate(per_season)
        print(f"  {panel} {pos:3s}  all-pair win rate {rate:.3f} [{lo:.3f}, {hi:.3f}] "
              f"p={pv:.4f}  pairs={npairs}")
print("\nD2 descriptive: veteran-pair win rate by v1 conviction (v1 slot gap)")
for gap in (3, 5, 10):
    row = []
    for panel, rank_col, span, crowd_rho in PANELS:
        for pos in POS:
            cells = [(s, g) for (pn, ps, s), g in blocks.items() if pn == panel and ps == pos]
            per_season = [pair_stats(g, "v1_slot", rank_col, True, min_gap=gap)
                          for _, g in sorted(cells)]
            arr = np.array(per_season, dtype=float)
            w, p = arr[:, 0].sum(), arr[:, 1].sum()
            row.append(f"{panel}-{pos}: {w/p if p>0 else float('nan'):.3f}/{int(p)}")
    print(f"  gap>={gap:2d}  " + "  ".join(row))

print()
print("D2 oracle-games variant (does fixing availability fix the disagreements?)")
for panel, rank_col, span, crowd_rho in PANELS:
    for pos in POS:
        cells = [(s, g) for (pn, ps, s), g in blocks.items() if pn == panel and ps == pos]
        per_season = [pair_stats(g, "og_slot", rank_col, vets_only=True)
                      for _, g in sorted(cells)]
        rate, lo, hi, pv, npairs = boot_rate(per_season)
        print(f"  {panel} {pos:3s}  oracle-games vet-pair win rate {rate:.3f} "
              f"[{lo:.3f}, {hi:.3f}] p={pv:.4f}  pairs={npairs}")
