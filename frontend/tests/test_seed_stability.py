"""Guards against the ADR-028 class of bug: unstable seed derivation.

Python salts str hashing per process, so anything built from `hash(str)` gives a
different seed on every run. That silently broke reproducibility across the
strategy simulator and the backtest CIs, and produced two different "measured"
values for the same arm with no code change between them.
"""
import pathlib
import re
import subprocess
import sys

import pytest

from config import stable_offset

SRC = pathlib.Path(__file__).resolve().parent.parent / "src"


def test_stable_offset_is_deterministic_within_a_process():
    assert stable_offset("elite_te_early") == stable_offset("elite_te_early")


def test_stable_offset_is_deterministic_ACROSS_processes():
    """The property that actually failed. A same-process check would have passed
    while the bug was live."""
    code = (
        "import sys; sys.path.insert(0, r'%s');"
        "from config import stable_offset; print(stable_offset('elite_te_early'))" % SRC
    )
    outs = {
        subprocess.run([sys.executable, "-c", code], capture_output=True, text=True).stdout.strip()
        for _ in range(3)
    }
    assert len(outs) == 1, f"seed offset varied across processes: {outs}"


def test_stable_offset_matches_a_pinned_value():
    """Pinned so a change of hashing algorithm is a deliberate, visible act --
    it would silently invalidate every previously reported simulation number."""
    assert stable_offset("elite_te_early") == 601
    assert stable_offset("bpa_consensus") == 318


def test_no_source_file_derives_a_seed_from_builtin_hash():
    """Static guard. `hash()` is fine for dict keys; it is never acceptable in a
    seed expression."""
    offenders = []
    for path in SRC.glob("*.py"):
        for i, line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
            if re.search(r"seed\s*=.*\bhash\s*\(", line) or re.search(r"\bhash\s*\(.*\)\s*%", line):
                stripped = line.strip()
                # skip comments, docstring prose, and the fixed helper itself
                if ("stable_offset" in line or stripped.startswith("#")
                        or "`" in line or stripped.startswith('"')):
                    continue
                offenders.append(f"{path.name}:{i}: {line.strip()}")
    assert not offenders, "seed derived from unstable builtin hash():\n" + "\n".join(offenders)
