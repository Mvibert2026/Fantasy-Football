"""Persist the ADR-070 permutation draws into git, and restore them after a
container rollback.

WHY THIS EXISTS. On 2026-08-04 the session container's disk rolled back roughly
eight hours. `experiments/bottomup/results/sweep070/draws/` was gitignored as
"regenerable compute, not results", which is true in principle and useless in
practice: regenerating it costs hours per cell, and three completed cells
(D1A1/Q0 at RB, WR and TE, each 8,999 draws) evaporated along with 2,500 draws
of a fourth. Git is the only durable store this environment has. Anything not
committed is not saved.

The raw CSVs are too big and too churny to track directly -- ~5.5 MB for a full
8,999-draw cell, appended to continuously. So this keeps a gzipped mirror
(~1.5 MB per full cell, ~4x smaller) and only rewrites it when a cell has grown
by a meaningful amount, which bounds how many blobs enter history.

    archive   gzip each draws CSV into draws_archive/ (new, or grown by
              >= GROWTH_ROWS since the archived copy)
    restore   gunzip back any cell whose live CSV is missing or SHORTER than
              the archive -- i.e. exactly the rollback case

Restore never truncates: a live file longer than its archive is left alone,
because the live one is ahead. Draw order is the registered order and draws are
append-only, so a prefix is always valid and the sweep resumes from the next k.

Worst case loss between archives is GROWTH_ROWS/seasons draws, tens of minutes
rather than the eight hours that motivated this.
"""
from __future__ import annotations

import argparse
import gzip
import shutil
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DRAWS = ROOT / "experiments/bottomup/results/sweep070/draws"
ARCHIVE = ROOT / "experiments/bottomup/results/sweep070/draws_archive"

#: Rows, not draws -- a cell writes one row per graded season per draw, so this
#: is roughly 2,000 draws at 10 seasons. Small enough that a rollback costs
#: minutes; large enough that a full cell contributes ~5 blobs, not ~450.
GROWTH_ROWS = 20_000


def _rows(p: Path, opener=open) -> int:
    if not p.exists():
        return 0
    with opener(p, "rt") as fh:
        return sum(1 for _ in fh)


def archive() -> int:
    ARCHIVE.mkdir(parents=True, exist_ok=True)
    n = 0
    for src in sorted(DRAWS.glob("*.csv")):
        dst = ARCHIVE / (src.name + ".gz")
        live, kept = _rows(src), _rows(dst, gzip.open)
        if live == 0 or (dst.exists() and live < kept + GROWTH_ROWS):
            continue
        tmp = dst.with_suffix(".gz.tmp")
        with src.open("rb") as fi, gzip.open(tmp, "wb", compresslevel=6) as fo:
            shutil.copyfileobj(fi, fo)
        tmp.replace(dst)          # atomic: a kill mid-gzip cannot corrupt it
        print(f"archived {src.name}: {live} rows (was {kept})")
        n += 1
    return n


def restore() -> int:
    if not ARCHIVE.exists():
        return 0
    DRAWS.mkdir(parents=True, exist_ok=True)
    n = 0
    for src in sorted(ARCHIVE.glob("*.csv.gz")):
        dst = DRAWS / src.name[:-3]
        live, kept = _rows(dst), _rows(src, gzip.open)
        if live >= kept:
            continue              # live is ahead of (or equal to) the archive
        tmp = dst.with_suffix(".csv.tmp")
        with gzip.open(src, "rb") as fi, tmp.open("wb") as fo:
            shutil.copyfileobj(fi, fo)
        tmp.replace(dst)
        print(f"RESTORED {dst.name}: {live} -> {kept} rows")
        n += 1
    return n


if __name__ == "__main__":
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("mode", choices=("archive", "restore"))
    a = ap.parse_args()
    changed = archive() if a.mode == "archive" else restore()
    print(f"{a.mode}: {changed} cell(s) changed")
    sys.exit(0)
