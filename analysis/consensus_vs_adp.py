"""
FR-099: is expert consensus (ECR) or market ADP the better predictor of realized
fantasy outcomes -- and what should a drafter do when they disagree?

WHAT THIS IS. A head-to-head measurement of two EXTERNAL baselines against each
other. Neither is our model; no parameter here is fit to anything. That is why
this is safe to run at full available coverage rather than being development
work subject to the factor-selection holdout rule (CLAUDE.md 6.1/6.3,
src/holdout.py) -- see COVERAGE NOTE below for why the point turns out to be
moot anyway.

COVERAGE NOTE -- the founder-request dispatch's stated premise is corrected
here, not silently worked around. The dispatch says "Five completed seasons
(2021-2025) have both [ECR and ADP] plus realised outcomes." That is not what
the data contains. `ffc_adp_snapshots` (adp_source='ffc_half_ppr_12team') has
ONLY seasons 2018-2024 (docs/handoffs/055-ffc-adp-history-harvest.md: "No 2025
archive exists in any of the three formats", reconfirmed here by direct query).
There is no other pre-draft, this-format-aware ADP source with 2025 coverage in
this database. So the ECR x ADP overlap is **2021-2024, n=4 seasons, not 5**.

This means 2025 -- the locked holdout -- is never read by this script, not
because of holdout discipline but because the ADP side of the comparison does
not exist for that season. holdout.DEFAULT_LOCK.guard() is still called
explicitly below on every season read, so if that ever changes (a 2025 ADP
source lands) this script fails loud rather than silently expanding scope.

Run: python3 analysis/consensus_vs_adp.py
Requires data/nfl.db with `rankings` (source='fantasypros_ecr') and
`ffc_adp_snapshots` (adp_source='ffc_half_ppr_12team') populated.
Output: console summary + data/qa/consensus-vs-adp-2026-07-30.json
"""

from __future__ import annotations

import json
import math
import random
import sqlite3
import sys
from dataclasses import dataclass, asdict
from pathlib import Path
from typing import Dict, List, Optional, Sequence, Tuple

REPO = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO / "src"))

import db  # noqa: E402
import holdout as holdout_mod  # noqa: E402
from scoring import ReplacementLevels  # noqa: E402
from backtest import _season_actuals  # noqa: E402
from scipy.stats import kendalltau  # noqa: E402

DB_PATH = REPO / "data" / "nfl.db"
OUT_PATH = REPO / "data" / "qa" / "consensus-vs-adp-2026-07-30.json"

ECR_SOURCE = "fantasypros_ecr"
ADP_SOURCE = "ffc_half_ppr_12team"
POSITIONS = ("QB", "RB", "WR", "TE")
SEASONS = (2021, 2022, 2023, 2024)  # measured overlap; see module docstring

# Disagreement threshold: one full round in a 12-team draft, applied to each
# player's ORDINAL rank within the matched (ECR ∩ ADP) universe for that
# season -- not raw ECR rank (a ~450-player board) vs raw ADP pick (a
# ~150-player board), which are not on a comparable scale. Ordinal rank within
# the shared, drafted-in-both-systems subset makes "one round apart" mean the
# same thing on both sides. Justified in the report, §1.
ROUND_SIZE = 12
DISAGREEMENT_THRESHOLD = ROUND_SIZE  # > 12 ordinal positions apart
EARLY_LATE_SPLIT = 5 * ROUND_SIZE  # ordinal rank 60 = end of round 5

Z95 = 1.96


def wilson_interval(successes: int, n: int, z: float = Z95) -> Tuple[float, float, float]:
    if n == 0:
        return (0.0, 0.0, 0.0)
    phat = successes / n
    denom = 1 + z * z / n
    center = (phat + z * z / (2 * n)) / denom
    margin = (z * math.sqrt(phat * (1 - phat) / n + z * z / (4 * n * n))) / denom
    return (phat, max(0.0, center - margin), min(1.0, center + margin))


# --------------------------------------------------------------------------
# Data loading
# --------------------------------------------------------------------------


def load_mfl_to_gsis(conn: sqlite3.Connection) -> Dict[str, str]:
    rows = conn.execute(
        "SELECT mfl_id, gsis_id FROM ff_playerids "
        "WHERE mfl_id IS NOT NULL AND gsis_id IS NOT NULL"
    ).fetchall()
    return {str(mfl): gsis for mfl, gsis in rows}


def load_ecr(conn: sqlite3.Connection, season: int) -> Dict[str, Tuple[int, str]]:
    """{player_id (gsis): (adp_rank, position)}"""
    rows = conn.execute(
        "SELECT player_id, adp_rank, position FROM rankings "
        "WHERE source=? AND season=? AND position IN (?,?,?,?) AND adp_rank IS NOT NULL",
        (ECR_SOURCE, season, *POSITIONS),
    ).fetchall()
    return {pid: (rank, pos) for pid, rank, pos in rows}


def load_adp(
    conn: sqlite3.Connection, season: int, mfl_to_gsis: Dict[str, str]
) -> Dict[str, Tuple[float, str]]:
    """{player_id (gsis): (average_pick, position)}. Drops unmatched mfl_ids."""
    rows = conn.execute(
        "SELECT mfl_id, average_pick, position FROM ffc_adp_snapshots "
        "WHERE adp_source=? AND period=? AND position IN (?,?,?,?) "
        "AND average_pick IS NOT NULL",
        (ADP_SOURCE, season, *POSITIONS),
    ).fetchall()
    out: Dict[str, Tuple[float, str]] = {}
    unmatched = 0
    for mfl_id, pick, pos in rows:
        gsis = mfl_to_gsis.get(str(mfl_id))
        if gsis is None:
            unmatched += 1
            continue
        out[gsis] = (pick, pos)
    return out, unmatched


def ordinal_ranks(scored: Dict[str, float]) -> Dict[str, int]:
    """1 = best (lowest raw value for ranks; caller passes the right sign)."""
    ordered = sorted(scored.items(), key=lambda kv: (kv[1], kv[0]))
    return {pid: i + 1 for i, (pid, _) in enumerate(ordered)}


def season_actual_vbd(
    conn: sqlite3.Connection, season: int, universe_positions: Dict[str, str],
    levels: ReplacementLevels,
) -> Dict[str, float]:
    """Actual VBD points for every player in `universe_positions`, floored at
    0 raw points (not dropped) for anyone absent from the stats table --
    CLAUDE.md 6.2 survivorship: a bust must stay in with actual_points=0, not
    fall out of the sample for lacking a row.

    Replacement level is computed from the FULL season universe (every player
    with any weekly stats row that season), matching adp_vs_production.py's
    convention -- the floor itself must not be distorted by which players
    happen to appear in the (much smaller) matched ECR-x-ADP subset.
    """
    actuals = _season_actuals(conn, season)  # {pid: (points, position)} -- has-a-row only
    by_pos_full: Dict[str, List[Tuple[str, float]]] = {}
    for pid, (pts, pos) in actuals.items():
        if pos in POSITIONS:
            by_pos_full.setdefault(pos, []).append((pid, pts))

    baselines = levels.baselines()
    replacement_pts: Dict[str, float] = {}
    for pos, entries in by_pos_full.items():
        ranked = sorted(entries, key=lambda kv: -kv[1])
        idx = min(baselines.get(pos, len(ranked)) - 1, len(ranked) - 1)
        replacement_pts[pos] = ranked[idx][1] if ranked else 0.0

    points_lookup = {pid: pts for pid, (pts, _pos) in actuals.items()}
    out: Dict[str, float] = {}
    for pid, pos in universe_positions.items():
        raw = points_lookup.get(pid, 0.0)  # bust floor: 0, never dropped
        repl = replacement_pts.get(pos, 0.0)
        out[pid] = raw - repl
    return out


# --------------------------------------------------------------------------
# Per-season build
# --------------------------------------------------------------------------


@dataclass
class SeasonRecord:
    season: int
    n_matched: int
    n_ecr_universe: int
    n_adp_universe: int
    n_adp_unmatched_mfl: int
    tau: float
    n_disagreement: int
    disagreement_threshold: int


@dataclass
class PlayerPair:
    season: int
    player_id: str
    position: str
    ecr_ordinal: int
    adp_ordinal: int
    actual_ordinal: int
    actual_vbd: float
    ecr_expected_vbd: float
    adp_expected_vbd: float
    winner: str  # "ECR" | "ADP" | "TIE"
    effect_pts: float  # positive = ECR closer (more accurate), in VBD points


def build_season(
    conn: sqlite3.Connection, season: int, mfl_to_gsis: Dict[str, str],
    levels: ReplacementLevels,
) -> Tuple[SeasonRecord, List[PlayerPair]]:
    ecr = load_ecr(conn, season)
    adp, unmatched = load_adp(conn, season, mfl_to_gsis)

    matched_ids = sorted(set(ecr) & set(adp))
    ecr_ordinal = ordinal_ranks({pid: ecr[pid][0] for pid in matched_ids})
    adp_ordinal = ordinal_ranks({pid: adp[pid][0] for pid in matched_ids})

    # Position: prefer ECR's label; both sources should agree in the huge
    # majority of cases (both describe primary offensive role).
    universe_positions = {pid: ecr[pid][1] for pid in matched_ids}

    actual_vbd = season_actual_vbd(conn, season, universe_positions, levels)
    actual_ordinal = ordinal_ranks({pid: -actual_vbd[pid] for pid in matched_ids})

    value_curve = [actual_vbd[pid] for pid, _ in
                   sorted(actual_ordinal.items(), key=lambda kv: kv[1])]

    tau, _p = kendalltau(
        [ecr_ordinal[pid] for pid in matched_ids],
        [adp_ordinal[pid] for pid in matched_ids],
    )

    pairs: List[PlayerPair] = []
    for pid in matched_ids:
        eo, ao, ro = ecr_ordinal[pid], adp_ordinal[pid], actual_ordinal[pid]
        if abs(eo - ao) <= DISAGREEMENT_THRESHOLD:
            continue
        exp_ecr = value_curve[eo - 1]
        exp_adp = value_curve[ao - 1]
        err_ecr = abs(actual_vbd[pid] - exp_ecr)
        err_adp = abs(actual_vbd[pid] - exp_adp)
        dist_ecr = abs(eo - ro)
        dist_adp = abs(ao - ro)
        if dist_ecr < dist_adp:
            winner = "ECR"
        elif dist_adp < dist_ecr:
            winner = "ADP"
        else:
            winner = "TIE"
        pairs.append(PlayerPair(
            season=season, player_id=pid, position=universe_positions[pid],
            ecr_ordinal=eo, adp_ordinal=ao, actual_ordinal=ro,
            actual_vbd=actual_vbd[pid], ecr_expected_vbd=exp_ecr,
            adp_expected_vbd=exp_adp, winner=winner,
            effect_pts=err_adp - err_ecr,
        ))

    rec = SeasonRecord(
        season=season, n_matched=len(matched_ids), n_ecr_universe=len(ecr),
        n_adp_universe=len(adp), n_adp_unmatched_mfl=unmatched,
        tau=float(tau) if tau is not None and not math.isnan(tau) else float("nan"),
        n_disagreement=len(pairs), disagreement_threshold=DISAGREEMENT_THRESHOLD,
    )
    return rec, pairs


# --------------------------------------------------------------------------
# Aggregation
# --------------------------------------------------------------------------


def win_stats(pairs: Sequence[PlayerPair]) -> Dict:
    decided = [p for p in pairs if p.winner != "TIE"]
    ecr_wins = sum(1 for p in decided if p.winner == "ECR")
    phat, lo, hi = wilson_interval(ecr_wins, len(decided))
    return {
        "n_pairs": len(pairs), "n_decided": len(decided),
        "n_ties": len(pairs) - len(decided),
        "ecr_wins": ecr_wins, "adp_wins": len(decided) - ecr_wins,
        "ecr_win_rate": phat, "wilson_lo": lo, "wilson_hi": hi,
        "mean_effect_pts_ecr_minus_adp": (
            sum(p.effect_pts for p in pairs) / len(pairs) if pairs else float("nan")
        ),
    }


def season_clustered_bootstrap_ci(
    per_season_values: Sequence[float], n_draws: int = 2000, seed: int = 20260730,
) -> Tuple[Optional[float], Optional[float], bool, str]:
    """Resample SEASONS, not player-pairs (ADR-021 convention). n=4 seasons
    is below MIN_SEASONS_FOR_STABLE_CI (8) -- flagged as degenerate, reported
    anyway per guardrails, not hidden."""
    vals = [v for v in per_season_values if v is not None and not math.isnan(v)]
    n = len(vals)
    if n == 0:
        return None, None, True, "no seasons with data"
    if n < 8:
        note = (
            f"degenerate: only {n} season(s), season-level bootstrap CI is "
            "poorly estimated below 8 seasons (ADR-021 MIN_SEASONS_FOR_STABLE_CI)"
        )
    else:
        note = ""
    rng = random.Random(seed)
    means = []
    for _ in range(n_draws):
        draw = [vals[rng.randrange(n)] for _ in range(n)]
        means.append(sum(draw) / n)
    means.sort()
    lo = means[int(0.025 * n_draws)]
    hi = means[int(0.975 * n_draws)]
    return lo, hi, n < 8, note


def main() -> None:
    conn = sqlite3.connect(str(DB_PATH))
    conn.row_factory = sqlite3.Row
    levels = ReplacementLevels()

    # Structural guard: explicit, logged, and would fail loud the day a 2025
    # ADP source lands and someone widens SEASONS without re-checking scope.
    holdout_mod.DEFAULT_LOCK.guard(SEASONS, purpose="FR-099 consensus-vs-adp: ECR x ADP overlap")

    mfl_to_gsis = load_mfl_to_gsis(conn)

    season_records: List[SeasonRecord] = []
    all_pairs: List[PlayerPair] = []
    for season in SEASONS:
        rec, pairs = build_season(conn, season, mfl_to_gsis, levels)
        season_records.append(rec)
        all_pairs.extend(pairs)

    # ---- 1. overall correlation, reported FIRST ----
    print("=== Overall ECR-vs-ADP rank correlation (matched universe, per season) ===")
    for rec in season_records:
        print(f"  {rec.season}: n_matched={rec.n_matched:4d}  tau_b={rec.tau:+.3f}  "
              f"ecr_universe={rec.n_ecr_universe} adp_universe={rec.n_adp_universe} "
              f"adp_unmatched_mfl={rec.n_adp_unmatched_mfl}")
    taus = [r.tau for r in season_records]
    print(f"  mean tau_b across {len(taus)} seasons: {sum(taus)/len(taus):+.3f}")

    # ---- 2. disagreement subset, pooled ----
    print(f"\n=== Disagreement subset (|ordinal diff| > {DISAGREEMENT_THRESHOLD}), pooled ===")
    pooled = win_stats(all_pairs)
    print(f"  n_pairs={pooled['n_pairs']} n_decided={pooled['n_decided']} "
          f"n_ties={pooled['n_ties']}")
    print(f"  ECR win rate: {pooled['ecr_win_rate']:.3f} "
          f"[{pooled['wilson_lo']:.3f}, {pooled['wilson_hi']:.3f}] "
          f"({pooled['ecr_wins']}/{pooled['n_decided']})")
    print(f"  mean effect (VBD pts, +=ECR more accurate): "
          f"{pooled['mean_effect_pts_ecr_minus_adp']:+.2f}")

    # ---- 3. per-season stability ----
    print("\n=== Per-season disagreement win rate (stability check) ===")
    per_season_stats = {}
    for season in SEASONS:
        sp = [p for p in all_pairs if p.season == season]
        st = win_stats(sp)
        per_season_stats[season] = st
        print(f"  {season}: n={st['n_pairs']:3d} decided={st['n_decided']:3d} "
              f"ECR win rate {st['ecr_win_rate']:.3f} "
              f"[{st['wilson_lo']:.3f}, {st['wilson_hi']:.3f}]  "
              f"mean effect {st['mean_effect_pts_ecr_minus_adp']:+.2f} pts")

    season_lo, season_hi, degenerate, note = season_clustered_bootstrap_ci(
        [per_season_stats[s]["ecr_win_rate"] for s in SEASONS]
    )
    print(f"\n  season-clustered bootstrap CI on ECR win rate (mean of season means): "
          f"[{season_lo:.3f}, {season_hi:.3f}]  degenerate={degenerate}  {note}")

    # ---- 4. by position ----
    print("\n=== By position ===")
    by_position = {}
    for pos in POSITIONS:
        sp = [p for p in all_pairs if p.position == pos]
        st = win_stats(sp)
        by_position[pos] = st
        print(f"  {pos}: n={st['n_pairs']:3d} decided={st['n_decided']:3d} "
              f"ECR win rate {st['ecr_win_rate']:.3f} "
              f"[{st['wilson_lo']:.3f}, {st['wilson_hi']:.3f}]  "
              f"mean effect {st['mean_effect_pts_ecr_minus_adp']:+.2f} pts")

    # ---- 5. by ADP range (early vs late) ----
    print(f"\n=== By ADP range (ordinal <= {EARLY_LATE_SPLIT} = early, else late) ===")
    by_range = {}
    for label, cond in [
        ("early", lambda p: min(p.ecr_ordinal, p.adp_ordinal) <= EARLY_LATE_SPLIT),
        ("late", lambda p: min(p.ecr_ordinal, p.adp_ordinal) > EARLY_LATE_SPLIT),
    ]:
        sp = [p for p in all_pairs if cond(p)]
        st = win_stats(sp)
        by_range[label] = st
        print(f"  {label}: n={st['n_pairs']:3d} decided={st['n_decided']:3d} "
              f"ECR win rate {st['ecr_win_rate']:.3f} "
              f"[{st['wilson_lo']:.3f}, {st['wilson_hi']:.3f}]  "
              f"mean effect {st['mean_effect_pts_ecr_minus_adp']:+.2f} pts")

    # ---- 6. position x range cross-tab (diagnostic, matches adp_vs_production
    #      precedent of checking whether a headline pattern is round-conditional) ----
    print("\n=== Position x ADP range cross-tab ===")
    by_pos_range = {}
    for pos in POSITIONS:
        by_pos_range[pos] = {}
        for label, cond in [
            ("early", lambda p: min(p.ecr_ordinal, p.adp_ordinal) <= EARLY_LATE_SPLIT),
            ("late", lambda p: min(p.ecr_ordinal, p.adp_ordinal) > EARLY_LATE_SPLIT),
        ]:
            sp = [p for p in all_pairs if p.position == pos and cond(p)]
            st = win_stats(sp)
            by_pos_range[pos][label] = st
            print(f"  {pos}/{label}: n={st['n_pairs']:3d} "
                  f"ECR win rate {st['ecr_win_rate']:.3f} "
                  f"[{st['wilson_lo']:.3f}, {st['wilson_hi']:.3f}]")

    out = {
        "season_records": [asdict(r) for r in season_records],
        "pooled": pooled,
        "per_season": per_season_stats,
        "season_clustered_bootstrap": {
            "lo": season_lo, "hi": season_hi, "degenerate": degenerate, "note": note,
        },
        "by_position": by_position,
        "by_adp_range": by_range,
        "by_position_and_range": by_pos_range,
        "disagreement_threshold": DISAGREEMENT_THRESHOLD,
        "early_late_split": EARLY_LATE_SPLIT,
        "seasons": list(SEASONS),
        "all_pairs": [asdict(p) for p in all_pairs],
    }
    OUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    OUT_PATH.write_text(json.dumps(out, indent=2), encoding="utf-8")
    print(f"\nWrote {OUT_PATH}")


if __name__ == "__main__":
    main()
