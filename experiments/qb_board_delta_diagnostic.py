"""Why do QBs rank high on our board in a 4-pt-passing-TD league?

Diagnostic for the founder's challenge (2026-07-29): the shipped board moves
Josh Allen +20 and Lamar Jackson +19 vs consensus, putting Allen 6th overall,
in a league whose passing-TD scoring is at the STINGY end. CLAUDE.md §8 says a
result that looks too good is usually leakage; this treats it as a suspected
defect first.

Run:  python experiments/qb_board_delta_diagnostic.py
"""

from __future__ import annotations

import copy
import sys
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "src"))

import db as dbmod  # noqa: E402
import make_board as mb  # noqa: E402
from scoring import LEAGUE, ReplacementLevels, score_offensive_game  # noqa: E402

SEASON = 2026


# ------------------------------------------------------------- scoring variants
def variant(**mutations) -> dict:
    cfg = copy.deepcopy(LEAGUE)
    off = cfg["offense"]
    for key, val in mutations.items():
        if key.endswith("_bonuses"):
            off[key[: -len("_bonuses")] + "_yards"]["bonuses"] = val
        else:
            off[key] = val
    return cfg


VARIANTS = {
    "FULL (shipped rules)": LEAGUE,
    "no PASSING bonuses": variant(passing_bonuses=[]),
    "no RUSHING bonuses": variant(rushing_bonuses=[]),
    "no RECEIVING bonuses": variant(receiving_bonuses=[]),
    "no bonuses at all": variant(passing_bonuses=[], rushing_bonuses=[], receiving_bonuses=[]),
    "passing TD = 6 (generous)": variant(passing_td=6),
    "passing TD = 2 (brutal)": variant(passing_td=2),
}


def board_for(conn, cfg):
    board, curves = mb.build_board(conn, SEASON, n_bootstrap=0, scoring_cfg=cfg)
    return board, curves


def find(board, name):
    for r in board:
        if name.lower() in r.player.lower():
            return r
    return None


# --------------------------------------------------- exact component decomposition
COMPONENTS = {
    "pass yds (base)": lambda s: (s.get("passing_yards") or 0) / 25.0,
    "pass yd BONUSES": lambda s: sum(
        b for t, b in LEAGUE["offense"]["passing_yards"]["bonuses"]
        if (s.get("passing_yards") or 0) >= t
    ),
    "pass TD @4": lambda s: (s.get("passing_tds") or 0) * 4,
    "interceptions": lambda s: (s.get("interceptions") or 0) * -2,
    "rush yds (base)": lambda s: (s.get("rushing_yards") or 0) / 10.0,
    "rush yd BONUSES": lambda s: sum(
        b for t, b in LEAGUE["offense"]["rushing_yards"]["bonuses"]
        if (s.get("rushing_yards") or 0) >= t
    ),
    "rush TD @6": lambda s: (s.get("rushing_tds") or 0) * 6,
    "receiving (all)": lambda s: (s.get("receptions") or 0) * 0.5
    + (s.get("receiving_yards") or 0) / 10.0
    + sum(b for t, b in LEAGUE["offense"]["receiving_yards"]["bonuses"]
          if (s.get("receiving_yards") or 0) >= t)
    + (s.get("receiving_tds") or 0) * 6,
    "misc (2pt/fum/ret)": lambda s: (s.get("return_tds") or 0) * 6
    + (s.get("two_point_conversions") or 0) * 2
    + (s.get("fumbles_lost") or 0) * -2
    + (s.get("offensive_fumble_return_tds") or 0) * 6,
}


def component_totals(conn, seasons):
    """{season: {component: {player_id: season_points_from_that_component}}}"""
    out = {}
    for season in seasons:
        per_comp = {c: {} for c in COMPONENTS}
        for row in dbmod.actual_season_outcomes(conn, season):
            stats = {c: row[c] for c in dbmod.SCORING_STAT_COLUMNS}
            pid = row["player_id"]
            for cname, fn in COMPONENTS.items():
                per_comp[cname][pid] = per_comp[cname].get(pid, 0.0) + fn(stats)
        out[season] = per_comp
    return out


def decompose_qb_vbd(conn, seasons, pos="QB", base_rank=10):
    """Exact additive split of VBD@rank1 by scoring component.

    Licensed by tests/test_qb_board_delta.py::
    test_slope_decomposes_exactly_across_additive_components -- OLS slope is a
    fixed linear functional of y, so components sum exactly.
    """
    comps = component_totals(conn, seasons)
    depth = mb.RELEVANT_DEPTH[pos]
    pooled = {c: [] for c in COMPONENTS}
    pooled_total = []
    for season in seasons:
        rows = mb._positional_ranks(
            mb._consensus_board(conn, season, source=mb.TRAINING_SOURCE)
        ).get(pos, [])
        for i, r in enumerate(rows, start=1):
            if i > depth:
                break
            pid = r["player_id"]
            tot = 0.0
            for c in COMPONENTS:
                v = comps[season][c].get(pid, 0.0)
                pooled[c].append((i, v))
                tot += v
            pooled_total.append((i, tot))

    ln_ratio = np.log(1.0) - np.log(base_rank)  # VBD@rank1 multiplier
    results = {}
    for c, pairs in pooled.items():
        f = mb._fit_one(pos, pairs)
        results[c] = f.slope_log_rank * ln_ratio
    ftot = mb._fit_one(pos, pooled_total)
    return results, ftot.slope_log_rank * ln_ratio, ftot


def main():
    conn = dbmod.connect(dbmod.DB_PATH)
    levels = ReplacementLevels()
    print("Replacement baselines:", levels.baselines())
    train = mb.resolve_training_seasons(conn, SEASON)
    print("Training seasons for the rank->points curve:", train)
    print()

    # ---- 1. hand-check the engine on real QB seasons (per-game vs per-season)
    print("=" * 78)
    print("1. BONUS ARITHMETIC ON REAL QB SEASONS (per game vs season total)")
    print("=" * 78)
    rows = list(dbmod.actual_season_outcomes(conn, 2024))
    byqb = {}
    for r in rows:
        if r["position"] != "QB":
            continue
        byqb.setdefault((r["player_id"], r["player_name"]), []).append(r)
    ranked = sorted(
        byqb.items(),
        key=lambda kv: -sum(
            score_offensive_game({c: g[c] for c in dbmod.SCORING_STAT_COLUMNS}) for g in kv[1]
        ),
    )
    print(f"{'QB (2024)':<22} {'G':>3} {'pts':>7} {'passBonus':>10} {'rushBonus':>10} "
          f"{'g>=300':>7} {'g>=100ru':>9} {'seasonPY':>9}")
    for (pid, name), games in ranked[:6]:
        pts = pb = rb = 0.0
        n300 = n100 = 0
        season_py = 0.0
        for g in games:
            s = {c: g[c] for c in dbmod.SCORING_STAT_COLUMNS}
            pts += score_offensive_game(s)
            py = s.get("passing_yards") or 0
            ry = s.get("rushing_yards") or 0
            season_py += py
            pb += sum(b for t, b in LEAGUE["offense"]["passing_yards"]["bonuses"] if py >= t)
            rb += sum(b for t, b in LEAGUE["offense"]["rushing_yards"]["bonuses"] if ry >= t)
            n300 += py >= 300
            n100 += ry >= 100
        print(f"{(name or pid)[:22]:<22} {len(games):>3} {pts:>7.1f} {pb:>10.1f} "
              f"{rb:>10.1f} {n300:>7} {n100:>9} {season_py:>9.0f}")
    print("  -> if bonuses were computed off the SEASON total, passBonus would be a")
    print("     flat 4.5 for every QB above (4.5 = 1.0+1.5+2.0). It is not.")
    print()

    # ---- 2. board under each scoring variant
    print("=" * 78)
    print("2. BOARD UNDER SCORING VARIANTS -- the decisive test")
    print("=" * 78)
    base_board = None
    for label, cfg in VARIANTS.items():
        board, curves = board_for(conn, cfg)
        if base_board is None:
            base_board = board
        allen = find(board, "Allen")
        lamar = find(board, "Lamar")
        qbs_top12 = sum(1 for r in board[:12] if r.position == "QB")
        slopes = " ".join(
            f"{p}:{curves[p].slope_log_rank:+7.1f}" for p in ("QB", "RB", "WR", "TE")
            if p in curves
        )
        print(f"\n{label}")
        print(f"   slopes  {slopes}")
        if allen:
            print(f"   Allen  overall #{allen.overall_rank:<3} vbd {allen.vbd:7.1f}  "
                  f"delta {allen.delta_vs_consensus:+d}")
        if lamar:
            print(f"   Lamar  overall #{lamar.overall_rank:<3} vbd {lamar.vbd:7.1f}  "
                  f"delta {lamar.delta_vs_consensus:+d}")
        print(f"   QBs in top 12: {qbs_top12}")
        print("   VBD@pos-rank1: " + " ".join(
            f"{p}={curves[p].slope_log_rank * (0 - np.log(levels.baselines()[p])):6.1f}"
            for p in ("QB", "RB", "WR", "TE") if p in curves
        ))
    print()

    # ---- 3. exact decomposition of QB1 VBD
    print("=" * 78)
    print("3. EXACT COMPONENT DECOMPOSITION OF VBD AT POSITIONAL RANK 1")
    print("=" * 78)
    for pos, base in (("QB", 10), ("RB", 30), ("WR", 40)):
        parts, total, fit = decompose_qb_vbd(conn, train, pos=pos, base_rank=base)
        print(f"\n{pos} (replacement {pos}{base}, curve R2={fit.r_squared:.3f}, n={fit.n_obs})")
        print(f"   {'component':<22} {'VBD@rank1':>10} {'share':>8}")
        for c, v in sorted(parts.items(), key=lambda kv: -kv[1]):
            print(f"   {c:<22} {v:>10.1f} {v / total * 100:>7.1f}%")
        print(f"   {'TOTAL':<22} {total:>10.1f}   (sum of parts "
              f"{sum(parts.values()):.1f} -- must match exactly)")

    conn.close()


if __name__ == "__main__":
    main()
