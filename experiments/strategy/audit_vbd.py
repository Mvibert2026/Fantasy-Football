"""FR-109 audit of the FR-085 VBD arm.

The founder challenged `docs/ranking/fr085-zero-rb.md` §1(6): plain VBD takes its
first RB in round 6.3. This module dumps the arm's ACTUAL behaviour rather than
arguing about it -- the top-10 available by the simulator's own VBD at a sequence
of picks in a single seeded draft, plus a reconciliation of the simulator's VBD
against the ADR-016 / test-registry #46 slot values (RB 168.5 > WR 153.2 >
QB 114.1 > TE 73.1).

Nothing here changes the simulator. It only reads it.

    .venv/bin/python -m experiments.strategy.audit_vbd
"""
from __future__ import annotations

import argparse
import sqlite3
import sys
from collections import defaultdict
from pathlib import Path
from typing import Dict, List

import numpy as np

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO))
sys.path.insert(0, str(REPO / "src"))

import db  # noqa: E402
from experiments.strategy import board as boardmod  # noqa: E402
from experiments.strategy import sim as simmod  # noqa: E402

DB_PATH = REPO / "data" / "nfl.db"
DUMP_PICKS = (1, 5, 10, 20, 40, 60, 76)


def _conn() -> sqlite3.Connection:
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute(db._CREATE_SCORING_VIEW_SQL)
    return conn


# --------------------------------------------------------------- 1. the dump
def dump_draft(conn, season: int, source: str, user_slot: int, sim_index: int,
               rounds_total: int = simmod.N_ROUNDS_FULL) -> None:
    """Replay one seeded draft, printing the top-10 available by the simulator's
    own VBD at each pick in DUMP_PICKS. The user runs `strategy_vbd`."""
    min_players = simmod.N_TEAMS * (rounds_total - 1)
    b = boardmod.build_board(conn, season, source, min_players)
    n = len(b.pos_idx)

    rng = np.random.default_rng(20260730 + season * 1000)
    zs = rng.standard_normal((sim_index + 1, n))
    slots = rng.integers(0, simmod.N_TEAMS, size=sim_index + 1)
    sd = np.where(np.isnan(b.pick_sd), np.nanmedian(b.pick_sd), b.pick_sd)
    noise = zs[sim_index] * sd
    if user_slot is None:
        user_slot = int(slots[sim_index])

    print(f"\n{'='*100}")
    print(f"DRAFT DUMP  season={season} source={source} user_slot={user_slot+1} "
          f"(0-indexed {user_slot})  sigma=ffc measured  board n={n}")
    print(f"{'='*100}")

    effective = b.consensus_rank + noise
    available = np.ones(n, dtype=bool)
    order = simmod._pick_order(rounds_total)
    rosters: List[List[int]] = [[] for _ in range(simmod.N_TEAMS)]
    counts = [{p: 0 for p in simmod.POSITIONS} for _ in range(simmod.N_TEAMS)]
    user_picks = []

    for pick_i, team in enumerate(order):
        rnd = pick_i // simmod.N_TEAMS
        if rnd == rounds_total - 1:
            continue
        overall = pick_i + 1

        if overall in DUMP_PICKS:
            _print_top10(b, available, counts[user_slot], rnd, overall,
                         is_user=(team == user_slot), rounds_total=rounds_total)

        if team == user_slot:
            st = simmod.State(rnd, counts[team])
            mask = simmod._legal_mask(st, b, rounds_total)
            choice = simmod.strategy_vbd(st, available, b, mask, b.consensus_rank)
            user_picks.append((rnd + 1, overall, choice))
        else:
            choice = simmod._opponent_pick(effective, available, counts[team], b)
        if not available[choice]:
            continue
        available[choice] = False
        rosters[team].append(choice)
        counts[team][simmod.POSITIONS[b.pos_idx[choice]]] += 1

    print(f"\n--- what the VBD arm actually drafted (slot {user_slot+1}) ---")
    print(f"{'rd':>3s} {'ovr':>4s}  {'pos':3s} {'VBD':>8s} {'VBDrk':>6s} {'cons':>5s}  name")
    for rnd1, overall, idx in user_picks:
        print(f"{rnd1:3d} {overall:4d}  {simmod.POSITIONS[b.pos_idx[idx]]:3s} "
              f"{b.vbd[idx]:8.1f} {b.vbd_rank[idx]:6.0f} {b.consensus_rank[idx]:5.0f}  "
              f"{b.names[idx]}")
    firsts = [r for r, _, i in user_picks if simmod.POSITIONS[b.pos_idx[i]] == "RB"]
    print(f"  first RB round = {firsts[0] if firsts else 'never'}")


def _print_top10(b, available, user_counts, rnd, overall, is_user, rounds_total):
    pen = simmod.need_penalty_vector(user_counts, b)
    st = simmod.State(rnd, user_counts)
    mask = simmod._legal_mask(st, b, rounds_total)
    score = b.vbd_rank + pen
    s = np.where(available & mask, score, np.inf)
    top = np.argsort(s, kind="stable")[:10]
    who = "USER ON THE CLOCK" if is_user else "board state (user not on the clock)"
    have = {k: v for k, v in user_counts.items() if v}
    print(f"\n-- overall pick {overall} (round {rnd+1}) -- {who}; user roster so far: "
          f"{have or 'empty'}")
    print(f"   {'#':>2s} {'pos':3s} {'raw VBD':>9s} {'VBDrank':>8s} {'need pen':>9s} "
          f"{'score':>8s} {'consensus':>9s}  name")
    for j, i in enumerate(top, 1):
        if not np.isfinite(s[i]):
            break
        print(f"   {j:2d} {simmod.POSITIONS[b.pos_idx[i]]:3s} {b.vbd[i]:9.1f} "
              f"{b.vbd_rank[i]:8.0f} {pen[i]:9.1f} {s[i]:8.1f} "
              f"{b.consensus_rank[i]:9.0f}  {b.names[i]}")
    # where is the best available RB, if it is not in the top 10?
    rb = simmod.POSITIONS.index("RB")
    rb_avail = available & mask & (b.pos_idx == rb)
    if rb_avail.any() and not any(b.pos_idx[i] == rb for i in top):
        i = int(np.argmin(np.where(rb_avail, score, np.inf)))
        rank_among = int((s < s[i]).sum()) + 1
        print(f"   ... best available RB is #{rank_among} on this list: "
              f"{simmod.POSITIONS[b.pos_idx[i]]} {b.names[i]} raw VBD {b.vbd[i]:.1f} "
              f"(VBD rank {b.vbd_rank[i]:.0f}, consensus {b.consensus_rank[i]:.0f})")


# ------------------------------------------------- 2. curve reconciliation
def reconcile(conn, seasons=(2021, 2022, 2023, 2024)) -> None:
    """The simulator's VBD of the rank-1 slot, per position, per season, next to
    the ADR-016 / registry #46 numbers it is supposed to agree with."""
    print(f"\n{'='*100}")
    print("RECONCILIATION -- simulator VBD of the positional rank-1 slot")
    print(f"{'='*100}")
    print(f"{'season':>7s} " + " ".join(f"{p:>28s}" for p in boardmod.POSITIONS))
    print(f"{'':>7s} " + " ".join(f"{'r1pts  replpts   VBD':>28s}"
                                  for _ in boardmod.POSITIONS))
    acc = defaultdict(list)
    for s in seasons:
        c = boardmod.ValueCurves(conn, s)
        cells = []
        for p in boardmod.POSITIONS:
            base = boardmod.BASELINES[p]
            r1 = c.expected_points(p, 1)
            rp = c.expected_points(p, base)
            v = c.vbd(p, 1)
            acc[p].append(v)
            cells.append(f"{r1:8.1f} {rp:8.1f} {v:8.1f}")
        print(f"{s:7d} " + " ".join(f"{x:>28s}" for x in cells))
    print(f"{'mean':>7s} " + " ".join(
        f"{'':17s}{np.mean(acc[p]):8.1f}" for p in boardmod.POSITIONS))
    print("\nADR-016 / test-registry #46 (log-linear on CONSENSUS rank, 2021-2025):")
    print("        RB 168.5   WR 153.2   QB 114.1   TE  73.1")

    curves = {s: boardmod.ValueCurves(conn, s) for s in seasons}
    ranks = (1, 2, 3, 5, 8, 10, 12, 15, 20, 24, 30, 36, 40, 50)
    print("\nSimulator curve = descending FINISH-rank season totals. VBD at each "
          "positional rank, mean over the seasons above:")
    print("  " + f"{'pos':>4s} " + " ".join(f"{'r'+str(k):>7s}" for k in ranks))
    for p in boardmod.POSITIONS:
        vals = [np.mean([curves[s].vbd(p, k) for s in seasons]) for k in ranks]
        print("  " + f"{p:>4s} " + " ".join(f"{v:7.1f}" for v in vals))
    print("\n  ... and the raw expected points behind it:")
    for p in boardmod.POSITIONS:
        vals = [np.mean([curves[s].expected_points(p, k) for s in seasons]) for k in ranks]
        print("  " + f"{p:>4s} " + " ".join(f"{v:7.1f}" for v in vals))

    # The comparison ADR-016 actually settled: E[points | CONSENSUS rank], not
    # points | finish rank. Fit the same log-linear form on the same board.
    print("\nCONSENSUS-rank curve (ADR-016's form: pts ~ a + b*ln(consensus pos rank), "
          "fitted per season on seasons < target, same 5-season lookback):")
    print("  " + f"{'pos':>4s} " + " ".join(f"{'r'+str(k):>7s}" for k in ranks))
    cons = {p: _consensus_vbd_curve(conn, p, seasons, ranks) for p in boardmod.POSITIONS}
    for p in boardmod.POSITIONS:
        print("  " + f"{p:>4s} " + " ".join(f"{v:7.1f}" for v in cons[p]))
    print("\n  ratio finish-curve VBD / consensus-curve VBD "
          "(>1 = simulator overstates the value of that slot):")
    print("  " + f"{'pos':>4s} " + " ".join(f"{'r'+str(k):>7s}" for k in ranks))
    for p in boardmod.POSITIONS:
        fin = [np.mean([curves[s].vbd(p, k) for s in seasons]) for k in ranks]
        print("  " + f"{p:>4s} " + " ".join(
            f"{(f/c if abs(c) > 1e-6 else float('nan')):7.2f}" for f, c in zip(fin, cons[p])))


DEPTH = {"QB": 20, "RB": 45, "WR": 60, "TE": 20}   # ADR-016 draft-relevant depth


def _consensus_vbd_curve(conn, pos: str, seasons, ranks):
    """VBD from E[points | CONSENSUS positional rank], the quantity ADR-016 adopted.

    For each target season, fit pts ~ a + b*ln(consensus positional rank) on the
    same 5 prior seasons the simulator uses, on the FFC board's own consensus
    ordering, then take the fitted value at rank k minus the fitted value at the
    position's replacement level. Averaged over target seasons."""
    out = np.zeros(len(ranks))
    base = boardmod.BASELINES[pos]
    m2g = boardmod._mfl_to_gsis(conn)
    for tgt in seasons:
        xs, ys = [], []
        for s in range(tgt - boardmod.CURVE_LOOKBACK, tgt):
            rows = conn.execute(
                "SELECT mfl_id, rank FROM ffc_adp_snapshots WHERE "
                "adp_source='ffc_half_ppr_12team' AND period=? AND position=? ORDER BY rank",
                (s, pos)).fetchall()
            tot: Dict[str, float] = defaultdict(float)
            for r in conn.execute(
                    f"SELECT * FROM {db.SCORING_VIEW} WHERE season=? AND season_type='REG'", (s,)):
                from scoring import score_offensive_game
                tot[r["player_id"]] += score_offensive_game(
                    {c: r[c] for c in db.SCORING_STAT_COLUMNS})
            scale = boardmod.scheduled_games(tgt) / boardmod.scheduled_games(s)
            pr = 0
            for mfl, _rank in rows:
                if mfl is None:
                    continue
                pr += 1
                if pr > DEPTH[pos]:
                    break
                g = m2g.get(str(mfl))
                xs.append(np.log(pr))
                ys.append(tot.get(g, 0.0) * scale if g else 0.0)
        if len(xs) < 10:
            continue
        b, a = np.polyfit(np.array(xs), np.array(ys), 1)
        f = lambda k: a + b * np.log(k)          # noqa: E731
        out += np.array([f(k) - f(base) for k in ranks])
    return out / len(seasons)


# -------------------------------------------- 3. first-RB round distribution
def first_rb_distribution(conn, source: str, seasons, sims: int,
                          rounds_total: int = simmod.N_ROUNDS_FULL) -> Dict:
    """Full distribution of the VBD arm's first-RB round, overall and BY SLOT.
    The reported 6.33 is a mean; this shows whether it is bimodal."""
    min_players = simmod.N_TEAMS * (rounds_total - 1)
    boards = {s: boardmod.build_board(conn, s, source, min_players) for s in seasons}
    by_slot: Dict[int, List[int]] = defaultdict(list)
    allv: List[int] = []
    for season in seasons:
        b = boards[season]
        n = len(b.pos_idx)
        sd = np.where(np.isnan(b.pick_sd), np.nanmedian(b.pick_sd), b.pick_sd)
        rng = np.random.default_rng(20260730 + season * 1000)
        zs = rng.standard_normal((sims, n))
        slots = rng.integers(0, simmod.N_TEAMS, size=sims)
        for i in range(sims):
            noise = zs[i] * sd
            slot = int(slots[i])
            rosters, legal = simmod.simulate_draft(
                b, simmod.strategy_vbd, slot, noise, rounds_total)
            if not legal:
                continue
            ur = list(rosters[slot])
            rbs = [k for k, p in enumerate(ur)
                   if simmod.POSITIONS[b.pos_idx[p]] == "RB"]
            first = (rbs[0] + 1) if rbs else 99
            by_slot[slot].append(first)
            allv.append(first)
    print(f"\n{'='*100}")
    print(f"FIRST-RB ROUND DISTRIBUTION -- VBD arm, {source}, seasons {list(seasons)}, "
          f"{sims} sims/season")
    print(f"{'='*100}")
    _hist("ALL SLOTS POOLED", allv)
    for slot in sorted(by_slot):
        _hist(f"slot {slot+1}", by_slot[slot])
    return {"all": allv, "by_slot": dict(by_slot)}


def _hist(label: str, vals: List[int]) -> None:
    if not vals:
        print(f"  {label:16s}  (no legal drafts)")
        return
    a = np.array(vals, dtype=float)
    counts = np.bincount(np.array(vals), minlength=17)[1:17]
    bars = " ".join(f"r{k+1}:{c}" for k, c in enumerate(counts) if c)
    print(f"  {label:16s} n={len(vals):5d} mean={a.mean():5.2f} median={np.median(a):5.1f} "
          f"p10={np.percentile(a,10):4.1f} p90={np.percentile(a,90):4.1f} "
          f"min={a.min():.0f} max={a.max():.0f}")
    print(f"  {'':16s} {bars}")


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--season", type=int, default=2022)
    ap.add_argument("--source", default="ffc")
    ap.add_argument("--slot", type=int, default=0, help="0-indexed draft slot")
    ap.add_argument("--sim", type=int, default=0)
    ap.add_argument("--sims", type=int, default=100)
    ap.add_argument("--skip-dist", action="store_true")
    a = ap.parse_args()
    conn = _conn()
    dump_draft(conn, a.season, a.source, a.slot, a.sim)
    reconcile(conn)
    if not a.skip_dist:
        first_rb_distribution(conn, a.source, (2018, 2019, 2020, 2021, 2022, 2023, 2024),
                              a.sims)


if __name__ == "__main__":
    main()
