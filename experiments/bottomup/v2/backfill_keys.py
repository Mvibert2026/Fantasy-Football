#!/usr/bin/env python
"""§4.8 rule 5 — backfill provenance keys onto published B1/C1/C2 CSVs.

    .venv/bin/python -m experiments.bottomup.v2.backfill_keys

LABELLING ONLY. No metric column is touched, no number re-derived; the four
key columns (`universe`, `targets`, `S`, `first_feature_season`) are appended
per row from the batches' own REGISTERED control windows (`run_c1.CONTROLS`,
`run_c2.CONTROLS`, batch-B1's single window). Idempotent: rows already keyed
are left alone.

Every published B1/C1/C2 number is on the half-PPR 12-team board. Windows:
  C1  CTRL-A/B: targets 2018-2024 (S=7), ff 2012/2015; CTRL-C: 2019-2024
      (S=6), ff 2017
  C2  CTRL-A2 as CTRL-A; CTRL-D: 2021-2024 (S=4), ff 2018
  B1  all cells 2018-2024 (S=7), ff 2012
  placebo replication: CTRL-A (the registered placebo window)
"""

from __future__ import annotations

import sys
from pathlib import Path
from typing import Dict, Tuple

import pandas as pd

_REPO = Path(__file__).resolve().parents[3]
if str(_REPO) not in sys.path:
    sys.path.insert(0, str(_REPO))

from experiments.bottomup.v2.run_c1 import ARMS as C1_ARMS, CONTROLS as C1_CTRL
from experiments.bottomup.v2.run_c2 import ARMS as C2_ARMS, CONTROLS as C2_CTRL

RESULTS = _REPO / "experiments" / "bottomup" / "results"
UNIVERSE = "m_panel_halfppr12"
KEYS = ["universe", "targets", "S", "first_feature_season"]


def _key(ff: int, ft: int, lt: int) -> Dict:
    return {"universe": UNIVERSE, "targets": f"{ft}-{lt}", "S": lt - ft + 1,
            "first_feature_season": ff}


def _window_of(run: str, arms: Dict, ctrls: Dict) -> Tuple[int, int, int]:
    if run in ctrls:
        return ctrls[run]
    if run in arms:
        return ctrls[arms[run][0]]
    raise KeyError(f"unknown run {run!r}")


def _backfill(path: Path, run_col: str, arms: Dict, ctrls: Dict) -> None:
    df = pd.read_csv(path, keep_default_na=False, na_values=[""])
    if all(k in df.columns for k in KEYS):
        print(f"  {path.name}: already keyed")
        return
    keyed = df[run_col].map(
        lambda r: _key(*_window_of(str(r), arms, ctrls)))
    for k in KEYS:
        df[k] = [d[k] for d in keyed]
    df.to_csv(path, index=False)
    print(f"  {path.name}: keyed {len(df)} rows")


def _backfill_fixed(path: Path, ff: int, ft: int, lt: int) -> None:
    df = pd.read_csv(path, keep_default_na=False, na_values=[""])
    if all(k in df.columns for k in KEYS):
        print(f"  {path.name}: already keyed")
        return
    for k, v in _key(ff, ft, lt).items():
        df[k] = v
    df.to_csv(path, index=False)
    print(f"  {path.name}: keyed {len(df)} rows")


def main() -> None:
    print("C1 (registered windows from run_c1):")
    _backfill(RESULTS / "factor_c1_cells.csv", "run", C1_ARMS, C1_CTRL)
    _backfill(RESULTS / "factor_c1_contrasts.csv", "factor", C1_ARMS, C1_CTRL)
    _backfill_fixed(RESULTS / "factor_c1_placebo_replication.csv",
                    *C1_CTRL["CTRL-A"])
    print("C2 (registered windows from run_c2):")
    _backfill(RESULTS / "factor_c2_cells.csv", "run", C2_ARMS, C2_CTRL)
    _backfill(RESULTS / "factor_c2_contrasts.csv", "factor", C2_ARMS, C2_CTRL)
    print("B1 (single registered window, ff 2012, targets 2018-2024):")
    for name in ("ranking_v2_contrasts.csv", "ranking_v2_G1_cells.csv",
                 "ranking_v2_G1a_cells.csv", "ranking_v2_G2a_cells.csv"):
        p = RESULTS / name
        if p.exists():
            _backfill_fixed(p, 2012, 2018, 2024)


if __name__ == "__main__":
    main()
