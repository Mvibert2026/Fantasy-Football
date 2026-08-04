"""`grade070.draw_delta_bars` incremental cache must not change a single bar.

The sweep driver calls `draw_delta_bars` between every chunk of draws to run
the Besag-Clifford sequential test, and the function is O(n) in draws. With the
cache it folds in only the rows added since the last call. These bars decide
INCLUDE/HARM/NULL verdicts, so the bar for equivalence is exact equality, not
tolerance.

Skips when no draws file is on disk -- `data/` and the draws cache are
gitignored, so this is a with-data test, not a CI test.
"""
from __future__ import annotations

import shutil
import tempfile
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

from experiments.bottomup.v2 import ensemble070 as ens
from experiments.bottomup.v2 import grade070 as gr


def _first_cell_with_draws():
    """Any (arm, position) that has draws banked, so the test follows whatever
    the sweep happens to have run rather than hardcoding a cell."""
    if not gr.DRAWS.exists():
        return None
    for p in sorted(gr.DRAWS.glob("*.csv")):
        if p.stat().st_size < 1024:
            continue
        for (batch, arm), a in ens.ARMS070.items():
            for pos in a.positions:
                if p.name == f"{gr.cell_id(batch, arm, pos)}.csv":
                    return a, pos, p
    return None


def test_incremental_cache_is_byte_identical():
    found = _first_cell_with_draws()
    if found is None:
        pytest.skip("no banked draws on disk")
    a, pos, real = found

    cells = gr.load_cells()
    _, ctl_c = gr.obs_frames(cells, a, pos)
    if ctl_c is None:
        pytest.skip("no control cells for this arm")

    df = pd.read_csv(real)
    ks = sorted(df["k"].unique())
    if len(ks) < 24:
        pytest.skip("too few draws banked to exercise the fold-in")

    tmp = Path(tempfile.mkdtemp())
    orig = gr.DRAWS
    gr.DRAWS = tmp
    dest = tmp / real.name
    try:
        # prefixes mimicking the driver's adaptive chunk schedule
        cuts = [k for k in (12, 24, 48, 96, 150, 250, 400, 650, 1000)
                if k <= ks[-1]] + [ks[-1]]
        for cut in cuts:
            df[df["k"] <= cut].to_csv(dest, index=False)

            # warm: folds onto the cache built at the previous, smaller prefix
            bars_inc, mat_inc, seas_inc = gr.draw_delta_bars(a, pos, ctl_c)

            # cold: identical bytes on disk, no cache. Leaves the cache in the
            # correct state for this prefix, so the next loop is genuinely
            # incremental.
            gr._BARS_CACHE.clear()
            bars_cold, mat_cold, seas_cold = gr.draw_delta_bars(a, pos, ctl_c)

            assert seas_inc == seas_cold
            assert bars_inc.shape == bars_cold.shape, f"k<={cut}"
            assert mat_inc.shape == mat_cold.shape, f"k<={cut}"
            assert np.array_equal(bars_inc, bars_cold, equal_nan=True), \
                f"bars diverged at k<={cut}"
            assert np.array_equal(mat_inc, mat_cold, equal_nan=True), \
                f"delta matrix diverged at k<={cut}"
    finally:
        gr.DRAWS = orig
        gr._BARS_CACHE.clear()
        shutil.rmtree(tmp, ignore_errors=True)
