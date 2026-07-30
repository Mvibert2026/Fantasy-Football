"""FR-109: classify WHY the VBD arm takes its first RB when it does.

Three mutually exclusive causes, decided at the pick itself:

  VALUE   the RB had the highest RAW VBD of every available legal player --
          the arm took him because he was the best player left.
  PENALTY the RB did NOT have the highest raw VBD, but won once the positional
          need penalty (25 rank units per surplus, the amendment described in
          `sim.need_penalty_vector`) was added. The arm took him because other
          positions were penalised, not because he was the best value.
  FORCED  the legality mask had already removed every non-RB option -- the arm
          had no choice.

"VBD waits until round 6.3" means something completely different depending on
which of these dominates.

    .venv/bin/python -m experiments.strategy.why_first_rb --sims 200
"""
from __future__ import annotations

import argparse
import sys
from collections import defaultdict
from pathlib import Path
from typing import Dict, List

import numpy as np

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO))
sys.path.insert(0, str(REPO / "src"))

from experiments.strategy import audit_vbd as auditmod  # noqa: E402
from experiments.strategy import board as boardmod  # noqa: E402
from experiments.strategy import sim as simmod  # noqa: E402
from experiments.strategy.run_strategies import FFC_SEASONS, RNG_SEED  # noqa: E402

RB = simmod.POSITIONS.index("RB")


def classify_draft(b, user_slot: int, noise: np.ndarray, rounds_total: int):
    """Replay one VBD draft.

    Returns (round, cause, taken_before, qb_rounds) for the first RB, where
    `taken_before` counts the user's QB/WR/TE picks made before it -- the
    crowd-out question -- and `qb_rounds` are the rounds those QBs went in."""
    n = len(b.pos_idx)
    effective = b.consensus_rank + noise
    available = np.ones(n, dtype=bool)
    order = simmod._pick_order(rounds_total)
    counts = [{p: 0 for p in simmod.POSITIONS} for _ in range(simmod.N_TEAMS)]
    before = {"QB": 0, "WR": 0, "TE": 0}
    qb_rounds: List[int] = []
    for pick_i, team in enumerate(order):
        rnd = pick_i // simmod.N_TEAMS
        if rnd == rounds_total - 1:
            continue
        if team == user_slot:
            st = simmod.State(rnd, counts[team])
            mask = simmod._legal_mask(st, b, rounds_total)
            pen = simmod.need_penalty_vector(counts[team], b)
            choice = simmod._argmin_masked(b.vbd_rank + pen, available, mask)
            if b.pos_idx[choice] == RB:
                legal_avail = available & mask
                non_rb = legal_avail & (b.pos_idx != RB)
                if not non_rb.any():
                    cause = "FORCED"
                else:
                    best_raw = int(np.argmax(np.where(legal_avail, b.vbd, -np.inf)))
                    cause = "VALUE" if b.pos_idx[best_raw] == RB else "PENALTY"
                return rnd + 1, cause, dict(before), list(qb_rounds)
            pname = simmod.POSITIONS[b.pos_idx[choice]]
            before[pname] = before.get(pname, 0) + 1
            if pname == "QB":
                qb_rounds.append(rnd + 1)
        else:
            choice = simmod._opponent_pick(effective, available, counts[team], b)
        if not available[choice]:
            continue
        available[choice] = False
        counts[team][simmod.POSITIONS[b.pos_idx[choice]]] += 1
    return None


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--sims", type=int, default=200)
    ap.add_argument("--source", default="ffc")
    ap.add_argument("--rounds", type=int, default=simmod.N_ROUNDS_FULL)
    a = ap.parse_args()

    conn = auditmod._conn()
    min_players = simmod.N_TEAMS * (a.rounds - 1)
    tally: Dict[int, Dict[str, int]] = defaultdict(lambda: defaultdict(int))
    by_round: Dict[int, Dict[str, int]] = defaultdict(lambda: defaultdict(int))
    crowd: Dict[int, Dict[str, List[int]]] = defaultdict(lambda: defaultdict(list))
    qb_first_rounds: List[int] = []
    qb_rank_of_qb1: List[float] = []
    for season in FFC_SEASONS:
        b = boardmod.build_board(conn, season, a.source, min_players)
        n = len(b.pos_idx)
        # Where does THIS board put QB1 overall by its own VBD?
        qb = simmod.POSITIONS.index("QB")
        qb1 = int(np.argmax(np.where(b.pos_idx == qb, b.vbd, -np.inf)))
        qb_rank_of_qb1.append(b.vbd_rank[qb1])
        print(f"[{season}] simulator board: best QB by VBD is {b.names[qb1]} "
              f"VBD {b.vbd[qb1]:.1f}, overall VBD rank {b.vbd_rank[qb1]:.0f}, "
              f"consensus {b.consensus_rank[qb1]:.0f}")
        sd = np.where(np.isnan(b.pick_sd), np.nanmedian(b.pick_sd), b.pick_sd)
        rng = np.random.default_rng(RNG_SEED + season * 1000)
        zs = rng.standard_normal((a.sims, n))
        for i in range(a.sims):
            noise = zs[i] * sd
            for slot in range(simmod.N_TEAMS):
                got = classify_draft(b, slot, noise, a.rounds)
                if got is None:
                    tally[slot]["NEVER"] += 1
                    continue
                rnd, cause, before, qbr = got
                tally[slot][cause] += 1
                by_round[rnd][cause] += 1
                for k, v in before.items():
                    crowd[slot][k].append(v)
                qb_first_rounds.extend(qbr)

    print(f"\n{'='*88}")
    print(f"WHY THE VBD ARM TAKES ITS FIRST RB -- {a.source}, primary sigma, "
          f"{a.sims} sims x {len(FFC_SEASONS)} seasons x 10 slots")
    print(f"{'='*88}")
    causes = ("VALUE", "PENALTY", "FORCED", "NEVER")
    print(f"{'slot':>5s} " + " ".join(f"{c:>10s}" for c in causes) + "     share VALUE")
    tot: Dict[str, int] = defaultdict(int)
    for slot in sorted(tally):
        row = tally[slot]
        n = sum(row.values())
        for c in causes:
            tot[c] += row[c]
        print(f"{slot+1:5d} " + " ".join(f"{row[c]:10d}" for c in causes) +
              f"     {row['VALUE']/max(n,1):.3f}")
    n = sum(tot.values())
    print(f"{'ALL':>5s} " + " ".join(f"{tot[c]:10d}" for c in causes) +
          f"     {tot['VALUE']/max(n,1):.3f}")

    print(f"\n{'first-RB round x cause':^88s}")
    print(f"{'round':>6s} " + " ".join(f"{c:>10s}" for c in causes[:3]) + f" {'total':>10s}")
    for rnd in sorted(by_round):
        r = by_round[rnd]
        print(f"{rnd:6d} " + " ".join(f"{r[c]:10d}" for c in causes[:3]) +
              f" {sum(r.values()):10d}")

    print(f"\n{'='*88}")
    print("CROWD-OUT: how many QB / WR / TE the VBD arm takes BEFORE its first RB")
    print(f"{'='*88}")
    print(f"{'slot':>5s} {'mean QB':>9s} {'mean WR':>9s} {'mean TE':>9s} "
          f"{'P(>=1 QB first)':>16s} {'P(>=2 QB first)':>16s}")
    for slot in sorted(crowd):
        c = crowd[slot]
        q = np.array(c["QB"])
        print(f"{slot+1:5d} {np.mean(q):9.2f} {np.mean(c['WR']):9.2f} "
              f"{np.mean(c['TE']):9.2f} {np.mean(q >= 1):16.3f} {np.mean(q >= 2):16.3f}")
    allq = np.concatenate([np.array(crowd[s]["QB"]) for s in crowd])
    allw = np.concatenate([np.array(crowd[s]["WR"]) for s in crowd])
    allt = np.concatenate([np.array(crowd[s]["TE"]) for s in crowd])
    print(f"{'ALL':>5s} {np.mean(allq):9.2f} {np.mean(allw):9.2f} {np.mean(allt):9.2f} "
          f"{np.mean(allq >= 1):16.3f} {np.mean(allq >= 2):16.3f}")
    if qb_first_rounds:
        qr = np.array(qb_first_rounds)
        print(f"\n  rounds those pre-first-RB QBs went in: mean {qr.mean():.2f}, "
              f"median {np.median(qr):.0f}, "
              f"share in rounds 1-4 = {np.mean(qr <= 4):.3f}, "
              f"share in round 1 = {np.mean(qr == 1):.3f}")
    print(f"\n  simulator board's overall VBD rank of its own best QB, by season: "
          f"{[int(x) for x in qb_rank_of_qb1]}")


if __name__ == "__main__":
    main()
