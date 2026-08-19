"""Two workers pushing sweep results to one branch must lose nothing.

This guards `tools/sweep070_push.py`, which resolves a push conflict by
resetting hard to the remote and rebuilding from a union. A reset that got the
union wrong would silently delete hours of another machine's compute, and the
symptom -- a cell that is merely *shorter* than it should be -- is invisible
without a test like this one, because a truncated draws file is still a valid
prefix and the sweep happily resumes from it.

Runs against a synthetic repo, not the project's own, so it is a real CI test
rather than a with-data one. `sweep070_archive.py` and `sweep070_push.py` are
both standalone (stdlib plus pandas), which is what makes that possible.
"""
from __future__ import annotations

import shutil
import subprocess
import sys
from pathlib import Path

import pandas as pd
import pytest

ROOT = Path(__file__).resolve().parents[1]
TOOLS = ["sweep070_push.py", "sweep070_archive.py"]
REL = "experiments/bottomup/results/sweep070"
BRANCH = "work"
#: must exceed sweep070_archive.GROWTH_ROWS so the archive actually rewrites
BIG = 25_000


def _git(cwd: Path, *args: str) -> subprocess.CompletedProcess:
    return subprocess.run(["git", "-C", str(cwd), *args],
                          capture_output=True, text=True, check=True)


def _draws(clone: Path, cell: str, rows: int) -> None:
    p = clone / REL / "draws" / f"{cell}.csv"
    p.parent.mkdir(parents=True, exist_ok=True)
    body = "".join(f"{k},2020,{k * 0.5}\n" for k in range(rows))
    p.write_text("k,season,delta\n" + body)


def _cells(clone: Path, name: str, runs: list[str]) -> None:
    p = clone / REL / "cells" / f"{name}.csv"
    p.parent.mkdir(parents=True, exist_ok=True)
    pd.DataFrame([
        {"batch": "CTRL", "run": r, "position": "QB", "season": 2020, "k": 0, "v": 1.0}
        for r in runs
    ]).to_csv(p, index=False)


def _archive(clone: Path) -> None:
    subprocess.run([sys.executable, str(clone / "tools/sweep070_archive.py"), "archive"],
                   cwd=clone, check=True, capture_output=True)


def _make_clone(bare: Path, path: Path, name: str) -> Path:
    subprocess.run(["git", "clone", "-q", str(bare), str(path)], check=True)
    _git(path, "config", "user.email", f"{name}@test")
    _git(path, "config", "user.name", name)
    return path


@pytest.fixture()
def repos(tmp_path: Path):
    bare = tmp_path / "bare.git"
    subprocess.run(["git", "init", "-q", "--bare", "-b", BRANCH, str(bare)], check=True)

    seed = tmp_path / "seed"
    subprocess.run(["git", "clone", "-q", str(bare), str(seed)], check=True)
    _git(seed, "config", "user.email", "seed@test")
    _git(seed, "config", "user.name", "seed")
    (seed / ".gitignore").write_text(f"{REL}/draws/\n")
    # The tools ship tracked in the real repo, so track them here too -- an
    # untracked tools/ makes the reconcile guard fire on a test artifact.
    (seed / "tools").mkdir()
    for t in TOOLS:
        shutil.copy2(ROOT / "tools" / t, seed / "tools" / t)
    (seed / REL / "cells").mkdir(parents=True)
    (seed / REL / "draws_archive").mkdir(parents=True)
    (seed / REL / "cells" / ".keep").write_text("")
    (seed / REL / "draws_archive" / ".keep").write_text("")
    _git(seed, "add", "-A")
    _git(seed, "commit", "-q", "-m", "seed")
    _git(seed, "push", "-q", "origin", BRANCH)

    a = _make_clone(bare, tmp_path / "a", "a")
    b = _make_clone(bare, tmp_path / "b", "b")
    return bare, a, b


def test_conflicting_workers_union_rather_than_clobber(repos):
    _, a, b = repos

    # Worker A finishes first and pushes: shared cell X at 30k draws, plus its
    # own rows in the shared control shard.
    _draws(a, "CTRL__T2P__QB", 30_000)
    _draws(a, "A_ONLY__ARM__QB", BIG)
    _cells(a, "CTRL-T2P", ["ctrlA1", "ctrlA2"])
    _archive(a)
    _git(a, "add", "-A", REL)
    _git(a, "commit", "-q", "-m", "worker A")
    _git(a, "push", "-q", "origin", f"HEAD:{BRANCH}")

    # Worker B computed the same shared cell further (50k), has a cell A never
    # touched, and wrote different rows into the same control shard. It has not
    # seen A's push, so its rebase will conflict on the binary archive.
    _draws(b, "CTRL__T2P__QB", 50_000)
    _draws(b, "B_ONLY__ARM__QB", BIG)
    _cells(b, "CTRL-T2P", ["ctrlB1"])
    _archive(b)

    out = subprocess.run(
        [sys.executable, str(b / "tools/sweep070_push.py"),
         "--branch", BRANCH, "--message", "worker B", "--paths", REL],
        cwd=b, capture_output=True, text=True,
    )
    assert out.returncode == 0, f"push failed:\n{out.stdout}\n{out.stderr}"

    # 1. B kept its own further-along compute on the shared cell.
    shared = b / REL / "draws" / "CTRL__T2P__QB.csv"
    assert sum(1 for _ in shared.open()) == 50_001, "B's longer cell was truncated"

    # 2. A's exclusive cell survived into B's tree via the archive restore.
    assert (b / REL / "draws" / "A_ONLY__ARM__QB.csv").exists(), \
        "worker A's cell was destroyed by the reconcile"

    # 3. Both workers' rows are in the shared control shard.
    runs = set(pd.read_csv(b / REL / "cells" / "CTRL-T2P.csv")["run"])
    assert {"ctrlA1", "ctrlA2", "ctrlB1"} <= runs, f"lost control rows: {runs}"

    # 4. The remote carries both sides' archives, so a third worker inherits
    #    the union rather than either half.
    verify = b.parent / "verify"
    subprocess.run(["git", "clone", "-q", "-b", BRANCH, str(repos[0]), str(verify)], check=True)
    names = {p.name for p in (verify / REL / "draws_archive").glob("*.gz")}
    assert {"CTRL__T2P__QB.csv.gz", "A_ONLY__ARM__QB.csv.gz",
            "B_ONLY__ARM__QB.csv.gz"} <= names, f"remote missing archives: {names}"


def test_reconcile_refuses_when_unrelated_work_would_be_lost(repos):
    """The reset is destructive; it must refuse rather than eat a code edit."""
    _, a, b = repos

    _draws(a, "CTRL__T2P__QB", 30_000)
    _archive(a)
    _git(a, "add", "-A", REL)
    _git(a, "commit", "-q", "-m", "worker A")
    _git(a, "push", "-q", "origin", f"HEAD:{BRANCH}")

    _draws(b, "CTRL__T2P__QB", 50_000)
    _archive(b)
    # An unrelated, uncommitted edit that a `reset --hard` would silently erase.
    (b / "important_local_edit.py").write_text("# hours of work\n")

    out = subprocess.run(
        [sys.executable, str(b / "tools/sweep070_push.py"),
         "--branch", BRANCH, "--message", "worker B", "--paths", REL, "--attempts", "1"],
        cwd=b, capture_output=True, text=True,
    )
    assert out.returncode != 0
    assert "refusing to reconcile" in (out.stdout + out.stderr)
    assert (b / "important_local_edit.py").exists(), "the guard did not protect the edit"
