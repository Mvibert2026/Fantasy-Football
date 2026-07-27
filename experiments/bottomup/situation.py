"""Vacated/arrived-opportunity features (V3, work order R1).

Registration: docs/reviews/FABLE-EXT2-2026-07-27.md (V3), frozen and committed
BEFORE this module existed. Definitions here implement that text exactly.

Look-ahead discipline: the only target-season read is
`SeasonStore.early_rosters(t)` — weeks 1-4 (player_id, team) membership, never
a production column. That read is the REGISTERED mild look-ahead the R1 spec
blesses, and every V3 report carries the flag. Rookies are invisible to
arrival shares (registered blind spot: t-1 production is the only visibility).
"""

from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass
from typing import Dict, List, Tuple

from .data import canon_team


@dataclass(frozen=True)
class SituationFeatures:
    changed_team: float
    vac_rec_share: float
    vac_carry_share: float
    vac_att_share: float
    arr_rec_share: float
    arr_carry_share: float

    def as_list(self) -> List[float]:
        return [self.changed_team, self.vac_rec_share, self.vac_carry_share,
                self.vac_att_share, self.arr_rec_share, self.arr_carry_share]


N_FEATURES = 6
_ZERO = SituationFeatures(0.0, 0.0, 0.0, 0.0, 0.0, 0.0)


class Situation:
    """Vacated/arrived shares for one target season, canonical franchises.

    A t-1 producer is RETAINED by his franchise iff his weeks-1-4 modal
    franchise in t equals his t-1 modal franchise. Departed and
    no-early-appearance players both count as vacated for the franchise
    they produced for (their production is not walking back onto the field
    early in t); a no-early-appearance player is nevertheless assigned to
    his old franchise for his OWN features, with changed_team=0 — the two
    questions differ, per the registration.
    """

    def __init__(self, store, target_season: int, usage_arm: bool):
        prior = store.player_seasons(target_season - 1,
                                     for_target=target_season)
        early: Dict[str, str] = store.early_rosters(target_season)
        self._early = early
        self._prior_team: Dict[str, str] = {}
        # franchise -> [rec_vol, carries, attempts]; rec_vol = targets (usage
        # arm) or receptions (long arm) — same availability rule as rec_vol.
        tot: Dict[str, List[float]] = defaultdict(lambda: [0.0, 0.0, 0.0])
        vac: Dict[str, List[float]] = defaultdict(lambda: [0.0, 0.0, 0.0])
        arr: Dict[str, List[Tuple[str, float, float]]] = defaultdict(list)
        for pid, ps in prior.items():
            f_prev = canon_team(ps.team)
            if not f_prev:
                continue
            rec = float(ps.targets if usage_arm else ps.receptions)
            car, att = float(ps.carries), float(ps.attempts)
            self._prior_team[pid] = f_prev
            t = tot[f_prev]
            t[0] += rec
            t[1] += car
            t[2] += att
            cur = early.get(pid)
            if cur != f_prev:  # departed OR no early appearance
                v = vac[f_prev]
                v[0] += rec
                v[1] += car
                v[2] += att
            if cur is not None and cur != f_prev:
                arr[cur].append((pid, rec, car))
        self._tot, self._vac, self._arr = tot, vac, arr

    def features_for(self, pid: str) -> SituationFeatures:
        f_prev = self._prior_team.get(pid)
        cur = self._early.get(pid)
        f_cur = cur if cur is not None else f_prev
        if not f_cur:
            return _ZERO
        changed = 1.0 if (cur is not None and f_prev and cur != f_prev) else 0.0
        tot = self._tot.get(f_cur)
        if not tot:
            # current franchise had no t-1 production (expansion team):
            # shares are 0 by the registered zero-denominator rule.
            return SituationFeatures(changed, 0.0, 0.0, 0.0, 0.0, 0.0)
        vac = self._vac.get(f_cur, [0.0, 0.0, 0.0])

        def share(num: float, den: float) -> float:
            return num / den if den > 0 else 0.0

        # arrivals exclude the player himself (registered: no self-competition)
        arr_rec = sum(r for q, r, _c in self._arr.get(f_cur, ()) if q != pid)
        arr_car = sum(c for q, _r, c in self._arr.get(f_cur, ()) if q != pid)
        return SituationFeatures(
            changed,
            share(vac[0], tot[0]), share(vac[1], tot[1]), share(vac[2], tot[2]),
            share(arr_rec, tot[0]), share(arr_car, tot[1]),
        )
