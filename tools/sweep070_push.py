#!/usr/bin/env python3
"""Push sweep070 results to the working branch, reconciling concurrent writers.

WHY THIS EXISTS. Four matrix jobs (and, when one is rented, a CPU box) all
compute sweep cells and all push to the same branch. Most of the output is
already namespaced per batch -- `cells/<batch>.csv`, `state_<batch>.json`,
`sweep_<batch>.log`, `graded_<batch>.csv` -- and those never collide. Two
things are genuinely shared and do collide:

  * `draws_archive/*.gz` for CONTROL cells. Control families are shared across
    batches (T2P is defined in the C3 adapter and used by C4), so two batches
    running the same family write the same archive blob.
  * `cells/CTRL-<family>.csv`, for the same reason.

The old retry loop was `git pull --rebase && git push`, five times. That cannot
work: a conflict on a binary `.gz` stops the rebase and leaves the repository
*in* a rebase, so every later attempt fails on "cannot pull during a rebase"
regardless of contention having cleared. One conflict poisoned all five
retries, and the job then exited having computed for hours and saved nothing.

WHY UNION IS THE CORRECT RESOLUTION, not a heuristic. Draws are generated
sequentially k=0,1,2,... and are pure functions of (cell, k) -- draw 400 of a
cell is the same value whoever computed it. So for a single cell "longer wins"
IS the union, and `sweep070_archive.py restore` already implements exactly that
(it only ever lengthens a live draws file, never truncates one). The archive is
in turn a pure function of the live draws. Therefore:

    take their archives -> restore (unions into our live draws) -> re-archive

yields the union of both sides' compute, with no possibility of losing a draw
either side had. Cells are unioned on their natural key instead, since they are
rows rather than sequences.

Deliberately NOT a force push. A force push here would "resolve" the conflict
by deleting the other worker's hours of compute, which is the exact failure
this is written to prevent.

    python tools/sweep070_push.py --branch <branch> --message "<commit msg>"
"""
from __future__ import annotations

import argparse
import json
import shutil
import subprocess
import sys
import tempfile
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
RESULTS = ROOT / "experiments/bottomup/results/sweep070"
CELLS_DIR = RESULTS / "cells"
#: must match grade070._CELL_KEY -- the natural key of an observation row
CELL_KEY = ["batch", "run", "position", "season", "k"]


def git(*args: str, check: bool = True) -> subprocess.CompletedProcess:
    return subprocess.run(
        ["git", "-C", str(ROOT), *args],
        capture_output=True, text=True, check=check,
    )


def _log(msg: str) -> None:
    print(f"[push] {msg}", flush=True)


def _abort_any_rebase() -> None:
    """Leave the repository in a clean, non-rebasing state.

    This is the step whose absence broke the old loop. `git rebase --abort`
    fails loudly when no rebase is in progress, which is the common case, so
    both of these are best-effort by design.
    """
    for cmd in (("rebase", "--abort"), ("merge", "--abort")):
        git(*cmd, check=False)


def _union_cells(theirs: Path, ours: Path) -> None:
    """Union two cell shards on the observation key, preferring our rows.

    `keep="last"` with ours concatenated second means a row we recomputed wins
    over the same row from the remote. That matters only when both sides ran
    the same (batch, run, position, season, k), in which case the values are
    equal anyway -- so the choice is arbitrary and stated here so it is not
    mistaken for a substantive rule.
    """
    import pandas as pd

    frames = [pd.read_csv(p) for p in (theirs, ours) if p.exists() and p.stat().st_size > 0]
    if not frames:
        return
    df = pd.concat(frames, ignore_index=True)
    key = [c for c in CELL_KEY if c in df.columns]
    if key:
        df = df.drop_duplicates(subset=key, keep="last")
    df.to_csv(ours, index=False)


def _assert_only_results_are_dirty(paths: list[str]) -> None:
    """Refuse to reconcile if anything outside the results tree would be lost.

    `_reconcile` runs `git reset --hard`, which discards local work. In CI and
    on a rented box the checkout is clean and only results are ever touched, so
    that is safe. In a development checkout it would silently delete edits in
    progress. This turns that into a loud refusal instead.
    """
    dirty = [
        ln[3:].strip()
        for ln in git("status", "--porcelain", check=False).stdout.splitlines()
        if ln.strip()
    ]
    stray = [p for p in dirty if not any(p.startswith(a) for a in paths)]
    if stray:
        raise SystemExit(
            "[push] refusing to reconcile: uncommitted changes outside the results "
            "tree would be destroyed by the reset:\n  " + "\n  ".join(stray[:20])
        )


def _reconcile(branch: str, paths: list[str]) -> None:
    """Rebuild our results on top of the remote, losing nothing from either."""
    _log("conflict — reconciling against the remote by union")
    _abort_any_rebase()
    _assert_only_results_are_dirty(paths)
    git("fetch", "origin", branch)

    # Snapshot our committed results before resetting them away. Live draws are
    # gitignored, so `reset --hard` does not touch them -- that is what makes
    # the restore/re-archive round-trip below a union rather than a takeover.
    tmp = Path(tempfile.mkdtemp(prefix="sweep070-push-"))
    saved = tmp / "results"
    shutil.copytree(RESULTS, saved, ignore=shutil.ignore_patterns("draws"))

    git("reset", "--hard", f"origin/{branch}")

    # Per-batch artifacts have exactly one writer, so ours is authoritative
    # wherever we have one. Shared cell shards are unioned instead.
    for src in sorted(saved.rglob("*")):
        if src.is_dir():
            continue
        rel = src.relative_to(saved)
        dst = RESULTS / rel
        dst.parent.mkdir(parents=True, exist_ok=True)
        if dst.parent == CELLS_DIR and dst.suffix == ".csv" and dst.exists():
            _union_cells(dst, src)
            shutil.copy2(src, dst)
        elif rel.parts[0] == "draws_archive":
            # Never copied back directly: archives are regenerated below from
            # the unioned live draws, which is strictly more complete.
            continue
        else:
            shutil.copy2(src, dst)

    shutil.rmtree(tmp, ignore_errors=True)

    # Their archives are now on disk; fold them into our live draws (restore
    # only ever lengthens), then rewrite the archives from the union.
    subprocess.run([sys.executable, str(ROOT / "tools/sweep070_archive.py"), "restore"],
                   cwd=ROOT, check=False)
    subprocess.run([sys.executable, str(ROOT / "tools/sweep070_archive.py"), "archive"],
                   cwd=ROOT, check=False)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--branch", required=True)
    ap.add_argument("--message", required=True)
    ap.add_argument("--attempts", type=int, default=6)
    ap.add_argument("--paths", nargs="*",
                    default=["experiments/bottomup/results/sweep070/"])
    args = ap.parse_args()

    for attempt in range(1, args.attempts + 1):
        git("add", "-A", *args.paths, check=False)
        if git("diff", "--cached", "--quiet", check=False).returncode != 0:
            git("commit", "-m", args.message, check=False)

        if git("rev-list", "--count", f"origin/{args.branch}..HEAD",
               check=False).stdout.strip() in ("", "0"):
            _log("nothing to push")
            return 0

        git("fetch", "origin", args.branch, check=False)
        if git("rebase", f"origin/{args.branch}", check=False).returncode == 0:
            if git("push", "origin", f"HEAD:{args.branch}", check=False).returncode == 0:
                _log(f"pushed on attempt {attempt}")
                return 0
            _log(f"attempt {attempt}: push rejected (raced); retrying")
            _abort_any_rebase()
        else:
            _reconcile(args.branch, args.paths)

        # Jittered by attempt number so four jobs that finished together do not
        # keep colliding in lockstep.
        time.sleep(min(60, attempt * 7))

    _log("ERROR: could not push after all attempts — compute is NOT saved")
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
