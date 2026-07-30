#!/usr/bin/env python
"""Factor batch 5 -- run every arm declared in the pre-commitment.

    .venv/bin/python -m experiments.bottomup.factors.run_factors5

Design: `docs/ranking/factor-batch-5-precommit.md`, content committed `c857c67`
BEFORE any arm was fitted. 17 registered tests in one family, plus one
descriptive family that carries no BH claim.

  F1  17 model arms.  E1a = full-universe `targets` MAE, arm - primary.
      E1b = the same MAE on the ADP board (a REQUIRED DIRECTION CHECK, not the
      significance test).  E2 = ADP-board Spearman, the bar, NOT in the family.

  F3  the Heath-0.79 vs Hoopes-0.68 contradiction. Descriptive, no refit, no BH.

MULTIPLICITY IS CORRECTED AT THE CAMPAIGN LEVEL, NOT INSIDE THIS BATCH. Four
factor batches were dispatched simultaneously against the same panel and the
same harness; four BH corrections at m ~ 20 each is one uncontrolled ~80-test
screen wearing four hats. The denominator is read from
`docs/ranking/factor-campaign-manifest/` at grading time, floored at 80.

THREE OF THE SEVENTEEN ARMS ARE CONTROLS, ON PURPOSE. `routes_known` enters the
model ALONE at each position, so batch 2's defect -- a coverage flag turning out
to be 95-97% of an apparently large treatment effect -- is measured in advance
instead of discovered afterwards. The VOID rule at 50% is in the pre-commitment
and is applied here mechanically.

Results are written after EVERY arm, not at the end. Two agents died mid-run on
2026-07-30 and everything uncommitted went with them.
"""

from __future__ import annotations

import re
import sys
import time
import warnings
from dataclasses import dataclass, field
from functools import partial
from pathlib import Path
from typing import Dict, List, Optional, Tuple

import numpy as np
import pandas as pd

warnings.filterwarnings("ignore")

_REPO = Path(__file__).resolve().parents[3]
if str(_REPO) not in sys.path:
    sys.path.insert(0, str(_REPO))

from experiments.bottomup.components import pos_eval as E                 # noqa: E402
from experiments.bottomup.components import pos_model as M                # noqa: E402
from experiments.bottomup.components.pos_data import (                    # noqa: E402
    DEFAULT_DB, HOLDOUT_SEASON, build_panel, season_length, universe_for,
)
from experiments.bottomup.factors.factor_features5 import (               # noqa: E402
    build_factor5_features, gate,
)
from experiments.bottomup.factors.run_factors import (                    # noqa: E402
    benjamini_hochberg, paired,
)

OUT = _REPO / "experiments" / "bottomup" / "results"
MANIFEST = _REPO / "docs" / "ranking" / "factor-campaign-manifest"

FIRST, LAST = 2014, 2024
ROUTE_FIRST = 2018          # precommit §4: fixed before fitting, same rule as batch 3's NGS
BATCH_M = 17                # this batch's registered count
CAMPAIGN_FLOOR = 80         # manifest README: the floor, fixed in advance
VOID_RATIO = 0.50           # precommit §7
TOO_GOOD_PCT = 2.0          # batch 2's escape hatch, re-armed unchanged

GATES = {"routes": 0.80, "firstdown": 0.95}
_GATE_COL = {"routes": "routes_known", "firstdown": "fd_known"}

FEAT = partial(build_factor5_features)                            # primaries
FEAT_R = partial(build_factor5_features, blocks=("routes",))
FEAT_D = partial(build_factor5_features, blocks=("firstdown",))

REC_V = list(M._RECEIVER_VOLUME)
RB_T = list(M._RB_TARGET_VOLUME)


def _add(cols, *names):
    return list(cols) + [n for n in names if n not in cols]


@dataclass
class Arm:
    idx: int
    factor: str
    arm: str
    position: str
    kwargs: Dict = field(default_factory=dict)
    feat: str = "routes"
    first: int = FIRST
    block: str = "routes"
    role: str = "treatment"
    pair: Optional[int] = None

    e1: str = "targets"

    @property
    def gate_key(self):
        return (self.block, self.position, _GATE_COL[self.block])


def _vol(position: str, *cols) -> Dict:
    base = RB_T if position == "RB" else REC_V
    return {"model_kwargs": {"volume_cols": {"tpg": _add(base, *cols)}}}


ARMS: List[Arm] = [
    # ---- R: routes (sweep N3 / registry #16-#17, re-tagged off FTN onto
    #      `participation` -- ten seasons of source, seven target seasons)
    Arm(1, "N3 targets per route run", "R1 TPRR", "WR",
        _vol("WR", "tprr_w"), "routes", ROUTE_FIRST),
    Arm(2, "N3 targets per route run", "R1 TPRR", "TE",
        _vol("TE", "tprr_w"), "routes", ROUTE_FIRST),
    Arm(3, "N3 targets per route run", "R1 TPRR", "RB",
        _vol("RB", "tprr_w"), "routes", ROUTE_FIRST),
    Arm(4, "N3 route VOLUME", "R2 routes per game", "WR",
        _vol("WR", "rpg_w"), "routes", ROUTE_FIRST),
    Arm(5, "N3 route VOLUME", "R2 routes per game", "TE",
        _vol("TE", "rpg_w"), "routes", ROUTE_FIRST),
    Arm(6, "N3 route VOLUME", "R2 routes per game", "RB",
        _vol("RB", "rpg_w"), "routes", ROUTE_FIRST),
    Arm(7, "N4 first downs per route run", "R3 1D/RR", "WR",
        _vol("WR", "fdrr_w"), "routes", ROUTE_FIRST),
    Arm(8, "N4 first downs per route run", "R3 1D/RR", "TE",
        _vol("TE", "fdrr_w"), "routes", ROUTE_FIRST),
    Arm(9, "N3 targets per route run", "R1c CONTROL routes_known", "WR",
        _vol("WR", "routes_known"), "routes", ROUTE_FIRST, role="control", pair=1),
    Arm(10, "N3 targets per route run", "R1c CONTROL routes_known", "TE",
        _vol("TE", "routes_known"), "routes", ROUTE_FIRST, role="control", pair=2),
    Arm(11, "N3 targets per route run", "R1c CONTROL routes_known", "RB",
        _vol("RB", "routes_known"), "routes", ROUTE_FIRST, role="control", pair=3),
    # ---- D: receiving first downs (sweep N4). 11 target seasons -- NOT
    #      comparable to the route arms without saying so, precommit §1(4).
    Arm(12, "N4 receiving first downs", "D1 1D per game", "WR",
        _vol("WR", "fd_pg_w"), "firstdown", FIRST, block="firstdown"),
    Arm(13, "N4 receiving first downs", "D1 1D per game", "TE",
        _vol("TE", "fd_pg_w"), "firstdown", FIRST, block="firstdown"),
    Arm(14, "N4 receiving first downs", "D1 1D per game", "RB",
        _vol("RB", "fd_pg_w"), "firstdown", FIRST, block="firstdown"),
    Arm(15, "N4 receiving first downs", "D2 1D per target", "WR",
        _vol("WR", "fdpt_w"), "firstdown", FIRST, block="firstdown"),
    Arm(16, "N4 receiving first downs", "D2 1D per target", "TE",
        _vol("TE", "fdpt_w"), "firstdown", FIRST, block="firstdown"),
    Arm(17, "N4 receiving first downs", "D2 1D per target", "RB",
        _vol("RB", "fdpt_w"), "firstdown", FIRST, block="firstdown"),
]

_FEATS = {"routes": FEAT_R, "firstdown": FEAT_D}


# ------------------------------------------------------- campaign denominator
def campaign_m() -> Tuple[int, Dict[str, int]]:
    """`max(sum of every batch's registered m over the shared manifest, FLOOR)`.

    Read at grading time rather than hardcoded, because the other three batches
    are running concurrently and may register after this one did. The floor is
    what protects the campaign if they never do.
    """
    found: Dict[str, int] = {}
    if MANIFEST.exists():
        for p in sorted(MANIFEST.glob("batch-*.md")):
            txt = p.read_text(encoding="utf-8")
            hit = re.search(r"m_\d+\s*=\s*\*{0,2}(\d+)", txt)
            if hit:
                found[p.stem] = int(hit.group(1))
    return max(sum(found.values()), CAMPAIGN_FLOOR), found


# ------------------------------------------------------------------- driver
def main() -> None:
    t0 = time.time()
    panel = build_panel()
    g = gate(DEFAULT_DB)
    print(f"panel: {len(panel.seasons)} seasons {panel.seasons[0]}-"
          f"{panel.seasons[-1]} ({HOLDOUT_SEASON} sealed)  [{time.time()-t0:.0f}s]")
    print(f"  route rows (player-season) {len(g._routes)}"
          + (f"  {int(g._routes['season'].min())}-{int(g._routes['season'].max())}"
             if len(g._routes) else ""))
    print(f"  first-down rows            {len(g._fd)}"
          + (f"  {int(g._fd['season'].min())}-{int(g._fd['season'].max())}"
             if len(g._fd) else ""))
    m_campaign, found = campaign_m()
    print(f"  campaign manifest: {found or 'no batch files found'} "
          f"-> M_campaign = {m_campaign} (floor {CAMPAIGN_FLOOR})")

    OUT.mkdir(parents=True, exist_ok=True)
    rows: List[Dict] = []

    # ---- primaries, one per position, on the SAME builder as the arms
    prim: Dict[str, pd.DataFrame] = {}
    for pos in ("WR", "TE", "RB"):
        t = time.time()
        wf = E.WalkForward(panel=panel, position=pos, first_target=FIRST,
                           last_target=LAST, avail_arm="A", feature_fn=FEAT)
        pl, m = wf.run()
        prim[pos] = m
        px = sum(a["n_preseason_proxy_reads"] for a in wf.audit)
        print(f"primary {pos}: {len(pl)} player-seasons, {len(m)} seasons, "
              f"proxy reads {px}  [{time.time()-t:.0f}s]")
        if px:
            raise RuntimeError(f"primary {pos} touched a season-N proxy read")

    # ---- coverage gates, evaluated on the ADP board BEFORE any arm's result
    cov: Dict[Tuple, float] = {}
    for a in ARMS:
        if a.gate_key in cov:
            continue
        col, vals = a.gate_key[2], []
        for s in range(a.first, LAST + 1):
            board = E.adp.load_adp(s, position=a.position)
            extra = (board.loc[~board["unmatched"], "player_id"].tolist()
                     if len(board) else None)
            if not extra:
                continue
            u = universe_for(panel, s, a.position, extra_ids=extra)
            f = _FEATS[a.feat](panel, u, s)
            if col not in f.columns:
                continue
            on_board = f["player_id"].isin(extra)
            if on_board.any():
                vals.append(float(f.loc[on_board, col].mean()))
        cov[a.gate_key] = float(np.mean(vals)) if vals else float("nan")
    print("\ncoverage on the ADP board (gate applied BEFORE results are read):")
    for (b, p, c), v in sorted(cov.items()):
        print(f"  {b:9s} {p:3s} {c:13s} {v:.3f}   gate {GATES[b]:.2f}   "
              f"{'PASS' if v >= GATES[b] else 'NO DATA'}")

    # ---- F1
    for a in ARMS:
        c = cov.get(a.gate_key, float("nan"))
        if not (c >= GATES[a.block]):
            rows.append(dict(family="F1", idx=a.idx, factor=a.factor, arm=a.arm,
                             position=a.position, e1_comp=a.e1, role=a.role,
                             pair=a.pair, coverage=c, block=a.block,
                             n_target_seasons=LAST - a.first + 1, grade="NO DATA"))
            print(f"[{a.idx:2d}/17] {a.position:3s} {a.arm:28s} NO DATA "
                  f"(coverage {c:.3f} < {GATES[a.block]})")
            _flush(rows)
            continue
        t = time.time()
        wf = E.WalkForward(panel=panel, position=a.position, first_target=a.first,
                           last_target=LAST, avail_arm="A",
                           feature_fn=_FEATS[a.feat],
                           allow_preseason_proxy=False, **a.kwargs)
        pl, m = wf.run()
        px = sum(x["n_preseason_proxy_reads"] for x in wf.audit)
        e1a = paired(m, prim[a.position], f"mae_{a.e1}")
        e1b = paired(m, prim[a.position], f"adpsub_mae_{a.e1}")
        e2 = paired(m, prim[a.position], "adpsub_rho_model")
        sub = prim[a.position][prim[a.position]["season"] >= a.first]
        base = float(sub[f"mae_{a.e1}"].mean())
        base_b = float(sub[f"adpsub_mae_{a.e1}"].mean())
        rows.append(dict(
            family="F1", idx=a.idx, factor=a.factor, arm=a.arm,
            position=a.position, e1_comp=a.e1, role=a.role, pair=a.pair,
            coverage=c, block=a.block, n_target_seasons=len(m), p=e1a[3],
            d=e1a[0], lo=e1a[1], hi=e1a[2], n=e1a[4],
            pct=100.0 * e1a[0] / base if base else np.nan,
            e1b_d=e1b[0], e1b_n=e1b[4],
            e1b_pct=100.0 * e1b[0] / base_b if base_b else np.nan,
            e2_d=e2[0], e2_lo=e2[1], e2_hi=e2[2], e2_n=e2[4],
            proxy_reads=px, n_players=len(pl), primary_err=base,
            primary_adpsub_err=base_b))
        print(f"[{a.idx:2d}/17] {a.position:3s} {a.arm:28s} "
              f"E1a {e1a[0]:+8.4f} ({rows[-1]['pct']:+5.2f}%) "
              f"[{e1a[1]:+7.4f},{e1a[2]:+7.4f}] p={e1a[3]:.4f} n={e1a[4]}  "
              f"E1b {e1b[0]:+8.4f}  E2 {e2[0]:+.4f}  proxy={px}  "
              f"[{time.time()-t:.0f}s]")
        _flush(rows)

    res = _grade(pd.DataFrame(rows), m_campaign, found)

    # ---- F3, descriptive, outside the family
    try:
        f3(panel)
    except Exception as exc:                      # never lose F1 to an F3 bug
        print(f"\n!! F3 failed: {type(exc).__name__}: {exc}")
    print(f"\ntotal {time.time()-t0:.0f}s")


def _flush(rows: List[Dict]) -> None:
    pd.DataFrame(rows).to_csv(OUT / "factor_batch5_results.csv", index=False)


def _grade(res: pd.DataFrame, m_campaign: int, found: Dict[str, int]) -> pd.DataFrame:
    res = res.copy()
    if "grade" not in res.columns:
        res["grade"] = np.nan
    computable = res["grade"].isna()
    pv = res.loc[computable, "p"].fillna(1.0).tolist()

    for label, m in (("campaign", m_campaign), ("batch", BATCH_M)):
        padded = pv + [1.0] * max(0, m - len(pv))
        for q in (0.10, 0.05):
            keep = benjamini_hochberg(padded, q)[:int(computable.sum())]
            col = f"bh_{label}_{int(q*100):02d}"
            res[col] = False
            res.loc[computable, col] = keep

    # VOID rule: a control arm reaching 50% of a treatment's effect at the same
    # position voids the treatment's INTERPRETATION (numbers stand, meaning does
    # not). R1c is the control for R1, R2 and R3 at its position.
    void: set = set()
    for r in res.itertuples():
        if r.role != "control" or not np.isfinite(getattr(r, "d", np.nan)):
            continue
        for t in res.itertuples():
            if (t.role == "treatment" and t.position == r.position
                    and t.block == r.block and np.isfinite(getattr(t, "d", np.nan))
                    and abs(t.d) > 0 and abs(r.d) >= VOID_RATIO * abs(t.d)):
                void.add(int(t.idx))

    def grade(r) -> str:
        if isinstance(getattr(r, "grade", None), str):
            return r.grade
        if not np.isfinite(getattr(r, "d", np.nan)):
            return "NO DATA"
        sig = bool(r.bh_campaign_10)
        better = r.d < 0
        if sig and better:
            if int(r.idx) in void:
                return "VOID - COVERAGE ARTIFACT"
            if not (np.isfinite(r.e1b_d) and r.e1b_d < 0):
                return "BOARD-NEUTRAL"
            return "SURVIVES" if (np.isfinite(r.e2_d) and r.e2_d > 0) \
                else "PROJECTION-ONLY"
        if sig and not better:
            return "HARMFUL"
        if np.isfinite(r.lo) and np.isfinite(r.hi):
            if r.lo < 0 and r.hi < 0:
                return "MARGINAL"
            if r.lo > 0 and r.hi > 0:
                return "MARGINAL-HARMFUL"
        return "NULL"

    res["grade"] = [grade(r) for r in res.itertuples()]
    res["void_interpretation"] = res["idx"].isin(void)
    res["too_good"] = res.get("pct", pd.Series(np.nan, index=res.index)).abs() > TOO_GOOD_PCT
    res["m_campaign"] = m_campaign
    res["m_batch"] = BATCH_M

    print("\n" + "=" * 112)
    print(f"RESULTS -- campaign BH m={m_campaign} at q=0.10 (manifest {found or 'floor only'}); "
          f"batch-local m={BATCH_M} shown as a SECONDARY only.")
    print("E1a = `targets` component MAE, arm - primary. NEGATIVE = better. "
          "Season counts differ by block and are printed.")
    print("=" * 112)
    for f_, grp in res.groupby("factor", sort=False):
        print(f"\n{f_}")
        for r in grp.itertuples():
            if r.grade == "NO DATA":
                print(f"  {r.position:3s} {r.arm:28s} NO DATA")
                continue
            print(f"  {r.position:3s} {r.arm:28s} n_seas={int(r.n):2d} "
                  f"{r.d:+8.4f} [{r.lo:+8.4f},{r.hi:+8.4f}] p={r.p:.4f} "
                  f"bh_camp={'Y' if r.bh_campaign_10 else 'n'} "
                  f"bh_batch={'Y' if r.bh_batch_10 else 'n'}  {r.grade}")
    print("\ngrade counts:")
    print(res["grade"].value_counts().to_string())
    if res["too_good"].any():
        print("\n!! TOO-GOOD TRIGGER FIRED (>2% of primary error) -- escalate "
              "before write-up, per CLAUDE.md §8:")
        print(res.loc[res["too_good"], ["idx", "position", "arm", "pct"]]
              .to_string(index=False))
    res.to_csv(OUT / "factor_batch5_results.csv", index=False)
    print(f"\nwrote {OUT/'factor_batch5_results.csv'}")
    return res


# =====================================================================  F3
# The Heath-0.79 vs Hoopes-0.68 contradiction. DESCRIPTIVE. No refit, no BH,
# no promotion path. Design: precommit §6, fixed before any number existed.
FTN_CACHE = OUT / "factor_batch5_ftn_cache.csv"
FTN_SEASONS = (2022, 2023, 2024)          # 2025 is sealed and is NOT fetched


def _ftn() -> pd.DataFrame:
    """FTN charting, cached. NOT in `nfl.db` -- see the data-ops thread
    `2026-07-30-ftn-charting-is-not-in-nfl-db-batch-5-fetched-it`. Fetched for
    2022-2024 only; the sealed season is never requested."""
    if FTN_CACHE.exists():
        return pd.read_csv(FTN_CACHE)
    import nflreadpy as nfl
    import polars as pl
    cols = ["season", "nflverse_game_id", "nflverse_play_id", "read_thrown",
            "is_catchable_ball"]
    parts = [nfl.load_ftn_charting(seasons=[s]).select(cols) for s in FTN_SEASONS]
    FTN_CACHE.parent.mkdir(parents=True, exist_ok=True)
    pl.concat(parts).write_csv(FTN_CACHE)
    return pd.read_csv(FTN_CACHE)


def _ftn_shares() -> pd.DataFrame:
    """Per (player, season): first-read target share, catchable target share and
    catchable rate. BOTH SHARES ARE PROXIES for paid charted definitions and are
    labelled so everywhere they appear."""
    import sqlite3
    ftn = _ftn()
    if "read_thrown" in ftn.columns:
        ftn["read_thrown"] = ftn["read_thrown"].astype(str).str.strip()
    conn = sqlite3.connect(f"file:{DEFAULT_DB}?mode=ro", uri=True)
    try:
        pbp = pd.read_sql_query(
            "SELECT season, game_id, play_id, posteam, receiver_player_id "
            "FROM pbp WHERE pass = 1 AND season IN "
            f"({','.join(str(s) for s in FTN_SEASONS)}) AND season < {HOLDOUT_SEASON}",
            conn)
    finally:
        conn.close()
    pbp = pbp[pbp["receiver_player_id"].notna() & (pbp["receiver_player_id"] != "")]
    j = pbp.merge(ftn, left_on=["season", "game_id", "play_id"],
                  right_on=["season", "nflverse_game_id", "nflverse_play_id"],
                  how="inner")
    j["first_read"] = (j["read_thrown"] == "1").astype(float)
    j["catchable"] = j["is_catchable_ball"].astype(str).str.lower().isin(
        ["true", "1", "1.0"]).astype(float)
    pl_ = j.groupby(["season", "posteam", "receiver_player_id"], as_index=False).agg(
        tgt_ftn=("first_read", "size"), fr=("first_read", "sum"),
        cat=("catchable", "sum"))
    tm = pl_.groupby(["season", "posteam"], as_index=False).agg(
        tm_fr=("fr", "sum"), tm_cat=("cat", "sum"))
    pl_ = pl_.merge(tm, on=["season", "posteam"], how="left")
    # a player who changed clubs mid-season is summed across his clubs, with the
    # share taken against the club where he took the most targets. Stated, not
    # hidden: it affects a handful of players a season.
    pl_ = pl_.sort_values("tgt_ftn").drop_duplicates(
        ["season", "receiver_player_id"], keep="last")
    pl_["first_read_share"] = pl_["fr"] / pl_["tm_fr"].replace(0, np.nan)
    pl_["catchable_share"] = pl_["cat"] / pl_["tm_cat"].replace(0, np.nan)
    pl_["catchable_rate"] = pl_["cat"] / pl_["tgt_ftn"].replace(0, np.nan)
    return pl_.rename(columns={"receiver_player_id": "player_id"})[
        ["season", "player_id", "tgt_ftn", "first_read_share",
         "catchable_share", "catchable_rate"]]


def _season_table(panel) -> pd.DataFrame:
    """Every predictor, per player-season, from sources already gated."""
    hist = panel.before(HOLDOUT_SEASON - 1)
    team = panel.team_before(HOLDOUT_SEASON - 1)
    d = hist.merge(team, on=["team", "season"], how="left")
    g = gate(DEFAULT_DB)
    r = g.routes_before(panel, HOLDOUT_SEASON - 1)
    fd = g.fd_before(panel, HOLDOUT_SEASON - 1)
    d = d.merge(r, on=["season", "player_id"], how="left")
    d = d.merge(fd, on=["season", "player_id"], how="left")
    d = d.merge(_ftn_shares(), on=["season", "player_id"], how="left")

    gm = d["games"].replace(0, np.nan)
    rt = d["routes"].replace(0, np.nan)
    tg = d["targets"].replace(0, np.nan)
    d["fpg"] = (d["points"] / gm).fillna(0.0)
    d["fp_per_sched"] = d["points"] / d["season"].map(season_length)
    d["tshare"] = (d["targets"] / d["team_targets"].replace(0, np.nan)).fillna(0.0)
    d["tpg"] = (d["targets"] / gm).fillna(0.0)
    d["tprr"] = d["targets"] / rt
    d["yprr"] = d["rec_yards"] / rt
    d["fdrr"] = d["rec_fd"] / rt
    d["fd_pg"] = (d["rec_fd"] / gm).fillna(0.0)
    d["fdpt"] = d["rec_fd"] / tg
    return d


#: predictor -> (label, needs-routes?, is-a-proxy?)
_PREDICTORS = [
    ("fpg", "prior FPG  [THE INCUMBENT -- Hoopes 0.68]", False, False),
    ("tshare", "target share", False, False),
    ("tpg", "targets per game", False, False),
    ("first_read_share", "first-read target share  [PROXY]", False, True),
    ("catchable_share", "catchable target share  [PROXY]", False, True),
    ("catchable_rate", "catchable rate  [PROXY]", False, True),
    ("tprr", "TPRR  [PROXY routes]", True, True),
    ("yprr", "YPRR  [PROXY routes]", True, True),
    ("fdrr", "1D per route run  [PROXY routes]", True, True),
    ("fd_pg", "1D per game", False, False),
    ("fdpt", "1D per target", False, False),
]

MIN_TGT = 30            # Heath's stated target-share filter, per the sweep
MIN_ROUTES = 235        # Hoopes's stated filter, per the sweep


def f3(panel) -> pd.DataFrame:
    print("\n" + "=" * 112)
    print("F3 -- Heath 0.79 vs Hoopes 0.68, both sides on ONE population. "
          "DESCRIPTIVE, outside the FDR family, no BH claim.")
    print("=" * 112)
    d = _season_table(panel)
    rows: List[Dict] = []
    for position in ("WR", "TE", "RB"):
        pos_d = d[d["position"] == position]
        for key, label, needs_routes, is_proxy in _PREDICTORS:
            for pop in ("S", "U"):
                per = _f3_pairs(panel, pos_d, d, position, key, needs_routes, pop)
                # A season pair where the predictor is constant across the whole
                # population has no correlation to report -- that is what the
                # 2003-2008 targets hole and the pre-2006 ff_opportunity floor
                # produce. Dropped, and the surviving pair count is what gets
                # printed, so a thin cell cannot pass for a thick one.
                per = [p for p in per
                       if np.isfinite(p["r_s"]) and np.isfinite(p["base_s"])]
                if not per:
                    continue
                arr = np.array([p["r_s"] for p in per], dtype=float)
                base = np.array([p["base_s"] for p in per], dtype=float)
                delta = arr - base
                row = dict(position=position, predictor=key, label=label,
                           population=pop, proxy=is_proxy, n_pairs=len(per),
                           seasons=",".join(str(p["y"]) for p in per),
                           r_spearman=float(np.mean(arr)),
                           r_pearson=float(np.mean([p["r_p"] for p in per])),
                           base_spearman=float(np.mean(base)),
                           delta_vs_prior_fpg=float(np.mean(delta)),
                           n_players_mean=float(np.mean([p["n"] for p in per])))
                if len(per) >= 5:
                    rng = np.random.default_rng(20260730)
                    boot = np.array([np.mean(rng.choice(delta, len(delta), replace=True))
                                     for _ in range(4000)])
                    row["delta_lo"] = float(np.percentile(boot, 2.5))
                    row["delta_hi"] = float(np.percentile(boot, 97.5))
                else:
                    row["delta_lo"] = np.nan
                    row["delta_hi"] = np.nan
                    row["per_season"] = " | ".join(
                        f"{p['y']}->{p['y']+1} r={p['r_s']:+.3f} "
                        f"(prior FPG {p['base_s']:+.3f}, n={p['n']})" for p in per)
                rows.append(row)
    out = pd.DataFrame(rows)
    out.to_csv(OUT / "factor_batch5_f3_contradiction.csv", index=False)

    for position in ("WR", "TE", "RB"):
        for pop, popname in (("S", "SURVIVOR-FILTERED (the shops' population)"),
                             ("U", "OUR FROZEN UNIVERSE, busts retained")):
            sub = out[(out["position"] == position) & (out["population"] == pop)]
            if not len(sub):
                continue
            print(f"\n{position} -- {popname}")
            print(f"  {'predictor':42s} {'pairs':>5s} {'rho':>7s} {'r':>7s} "
                  f"{'vs prior FPG':>13s} {'95% CI':>20s}")
            for r in sub.itertuples():
                ci = (f"[{r.delta_lo:+.3f},{r.delta_hi:+.3f}]"
                      if np.isfinite(r.delta_lo) else "  n<5, none quoted")
                print(f"  {r.label:42s} {r.n_pairs:5d} {r.r_spearman:+7.3f} "
                      f"{r.r_pearson:+7.3f} {r.delta_vs_prior_fpg:+13.3f} {ci:>20s}")
            for r in sub.itertuples():
                if isinstance(getattr(r, "per_season", None), str):
                    print(f"    {r.predictor}: {r.per_season}")
    print(f"\nwrote {OUT/'factor_batch5_f3_contradiction.csv'}")
    return out


def _f3_pairs(panel, pos_d: pd.DataFrame, all_d: pd.DataFrame, position: str,
              key: str, needs_routes: bool, pop: str) -> List[Dict]:
    """One (Y -> Y+1) correlation per season pair, for `key` and for the
    incumbent `fpg` on exactly the same rows."""
    from experiments.bottomup.components.pos_eval import spearman
    have = pos_d[pos_d[key].notna()]["season"].unique()
    out: List[Dict] = []
    for y in sorted(int(s) for s in have):
        if y + 1 > HOLDOUT_SEASON - 1:
            continue
        cur = pos_d[pos_d["season"] == y]
        if pop == "S":
            nxt = pos_d[pos_d["season"] == y + 1]
            j = cur.merge(nxt[["player_id", "fpg", "targets", "routes"]],
                          on="player_id", suffixes=("", "_n"))
            ok = (j["targets"] >= MIN_TGT) & (j["targets_n"] >= MIN_TGT)
            if needs_routes:
                ok &= (j["routes"].fillna(0) >= MIN_ROUTES) & \
                      (j["routes_n"].fillna(0) >= MIN_ROUTES)
            j = j[ok & j[key].notna()]
            y_col = "fpg_n"
        else:
            u = universe_for(panel, y + 1, position)
            nxt = (all_d[all_d["season"] == y + 1][["player_id", "fp_per_sched"]]
                   .rename(columns={"fp_per_sched": "outcome"}))
            j = (u[["player_id"]]
                 .merge(cur.drop(columns=["fp_per_sched"]), on="player_id", how="left")
                 .merge(nxt, on="player_id", how="left"))
            j["outcome"] = j["outcome"].fillna(0.0)             # busts retained
            j[key] = j[key].fillna(0.0)
            j["fpg"] = j["fpg"].fillna(0.0)
            y_col = "outcome"
        if len(j) < 25:
            continue
        x = j[key].to_numpy(dtype=float)
        b = j["fpg"].to_numpy(dtype=float)
        yv = j[y_col].to_numpy(dtype=float)
        with np.errstate(invalid="ignore"):
            rp = float(np.corrcoef(x, yv)[0, 1]) if np.std(x) > 0 else np.nan
        out.append(dict(y=y, n=len(j), r_s=spearman(x, yv), r_p=rp,
                        base_s=spearman(b, yv)))
    return out


if __name__ == "__main__":
    if "--f3-only" in sys.argv:
        # F3 refits nothing and grades nothing. Re-running it alone cannot
        # change an F1 number, which is why it is allowed a separate entry
        # point; F1 itself is run ONCE, per the pre-commitment's stopping rule.
        f3(build_panel())
    else:
        main()
