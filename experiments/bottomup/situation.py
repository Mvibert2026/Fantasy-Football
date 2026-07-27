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
from typing import Dict, List, Optional, Tuple

from .data import canon_team


@dataclass(frozen=True)
class SituationFeatures:
    changed_team: float
    vac_rec_share: float
    vac_carry_share: float
    vac_att_share: float
    arr_rec_share: float
    arr_carry_share: float
    # V7 (registration: FABLE-EXT3-2026-07-27.md): rookie-arrival draft
    # capital (rook_cap_same, rook_top64_same, rook_cap_x_vac). None when
    # the variant is not enabled, so V3/V5 vectors keep their length.
    rookie: Optional[Tuple[float, float, float]] = None

    def as_list(self) -> List[float]:
        base = [self.changed_team, self.vac_rec_share, self.vac_carry_share,
                self.vac_att_share, self.arr_rec_share, self.arr_carry_share]
        return base + (list(self.rookie) if self.rookie is not None else [])


N_FEATURES = 6
N_ROOKIE_FEATURES = 3
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

    def __init__(self, store, target_season: int, usage_arm: bool,
                 exclude_self: bool = False, rookies: bool = False):
        """exclude_self (V5, registered in the FABLE-EXT2 amendment): remove
        the player's own contribution from the vacated numerators of HIS OWN
        features. Self-inclusion arises only in the no-early-appearance case
        (a departed player's production vacates his OLD franchise while his
        features read his NEW one), and it encodes 'not playing early in
        season t' — an availability leak. V3 keeps it (upper-bound
        reference); V5/V6 exclude it and are the only carry candidates.

        rookies (V7, registered in FABLE-EXT3 BEFORE this code existed):
        append same-position rookie-arrival draft capital — the registered
        blind spot of V3/V5, whose arrival shares need t-1 production and so
        cannot see a drafted rookie. Draft capital is April information:
        no new look-ahead enters (the weeks-1-4 franchise assignment's
        registered disclosure is the only one, unchanged)."""
        prior = store.player_seasons(target_season - 1,
                                     for_target=target_season)
        early: Dict[str, str] = store.early_rosters(target_season)
        self._early = early
        self._exclude_self = exclude_self
        self._rook: Optional[Dict[Tuple[str, str], List[int]]] = (
            store.rookie_draft_capital(target_season) if rookies else None)
        self._own_vols: Dict[str, Tuple[float, float, float]] = {}
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
                if cur is None:
                    # the only self-inclusion case; remembered for V5
                    self._own_vols[pid] = (rec, car, att)
            if cur is not None and cur != f_prev:
                arr[cur].append((pid, rec, car))
        self._tot, self._vac, self._arr = tot, vac, arr

    def features_for(self, pid: str,
                     position: Optional[str] = None) -> SituationFeatures:
        """`position` is required for the V7 rookie features (same-position
        competition and the position-relevant vacated share); ignored when
        the variant is off, so V3/V5 call sites are unchanged."""
        f_prev = self._prior_team.get(pid)
        cur = self._early.get(pid)
        f_cur = cur if cur is not None else f_prev
        if not f_cur:
            return self._finish(_ZERO, None, position)
        changed = 1.0 if (cur is not None and f_prev and cur != f_prev) else 0.0
        tot = self._tot.get(f_cur)
        if not tot:
            # current franchise had no t-1 production (expansion team):
            # shares are 0 by the registered zero-denominator rule. Rookie
            # capital is production-independent and still applies (V7).
            return self._finish(
                SituationFeatures(changed, 0.0, 0.0, 0.0, 0.0, 0.0),
                f_cur, position)
        vac = list(self._vac.get(f_cur, (0.0, 0.0, 0.0)))
        if self._exclude_self and pid in self._own_vols:
            own = self._own_vols[pid]
            vac = [max(0.0, v - o) for v, o in zip(vac, own)]

        def share(num: float, den: float) -> float:
            return num / den if den > 0 else 0.0

        # arrivals exclude the player himself (registered: no self-competition)
        arr_rec = sum(r for q, r, _c in self._arr.get(f_cur, ()) if q != pid)
        arr_car = sum(c for q, _r, c in self._arr.get(f_cur, ()) if q != pid)
        return self._finish(SituationFeatures(
            changed,
            share(vac[0], tot[0]), share(vac[1], tot[1]), share(vac[2], tot[2]),
            share(arr_rec, tot[0]), share(arr_car, tot[1]),
        ), f_cur, position)

    def _finish(self, base: SituationFeatures, f_cur: Optional[str],
                position: Optional[str]) -> SituationFeatures:
        """Append the V7 rookie triple when the variant is on (else pass
        through). rook_cap_same = sum of 1/sqrt(overall pick) over rookies
        drafted by the current franchise at the player's position;
        rook_top64_same = any such pick <= 64; rook_cap_x_vac = capital x
        the position-relevant SELF-EXCLUDED vacated share (att for QB,
        carries for RB, rec for WR/TE) — the registered mechanism term."""
        if self._rook is None:
            return base
        cap = top64 = 0.0
        if f_cur and position:
            picks = self._rook.get((f_cur, position), ())
            cap = sum(pk ** -0.5 for pk in picks)
            top64 = 1.0 if any(pk <= 64 for pk in picks) else 0.0
        vshare = {"QB": base.vac_att_share, "RB": base.vac_carry_share,
                  "WR": base.vac_rec_share, "TE": base.vac_rec_share
                  }.get(position or "", 0.0)
        return SituationFeatures(
            base.changed_team, base.vac_rec_share, base.vac_carry_share,
            base.vac_att_share, base.arr_rec_share, base.arr_carry_share,
            rookie=(cap, top64, cap * vshare))
