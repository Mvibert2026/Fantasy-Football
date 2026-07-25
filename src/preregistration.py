"""
Pre-registration, the persistent test counter, and FDR correction (Task 7).

THE PROBLEM THIS SOLVES. statistical-guardrails.md §3 requires that the
multiple-comparisons correction apply across every test actually run, not
across whichever subset looked interesting afterwards. That is unenforceable by
memory: the tests that get forgotten are exactly the ones that failed, and
forgetting them is what turns a 1-in-20 fluke into a "finding".

So three mechanisms:

1. PRE-REGISTRATION FILES. One markdown file per factor test in
   docs/preregistration/, stating the hypothesis, the exact metric, and the
   threshold that would count as confirmation -- written BEFORE the test runs.
   `require_preregistration()` refuses to execute a test with no file.
   The point is to make "we predicted this" checkable rather than remembered.

2. A PERSISTENT, APPEND-ONLY RUN LOG. Every executed test appends to
   docs/preregistration/test_run_log.jsonl. That file is tracked in git
   deliberately: the count must survive a database rebuild, because a counter
   living in a gitignored .db would silently reset and the FDR denominator
   would quietly shrink to whatever was run most recently. Which is precisely
   the failure mode being defended against.

3. BENJAMINI-HOCHBERG over the true total.

`preregistration_id` is the join key across all three.
"""

from __future__ import annotations

import datetime as dt
import json
import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, List, Optional, Sequence, Tuple

import numpy as np

PREREG_DIR = Path(__file__).resolve().parent.parent / "docs" / "preregistration"
RUN_LOG_PATH = PREREG_DIR / "test_run_log.jsonl"

REQUIRED_FIELDS = ("id", "title", "hypothesis", "metric", "confirmation_threshold", "status")


class PreRegistrationMissing(Exception):
    """Raised when a test tries to run without a pre-registration file."""


class PreRegistrationInvalid(Exception):
    """Raised when a pre-registration file is missing required fields."""


@dataclass(frozen=True)
class PreRegistration:
    id: str
    title: str
    hypothesis: str
    metric: str
    confirmation_threshold: str
    status: str
    path: Path
    fields: Dict[str, str] = field(default_factory=dict)


def _parse_frontmatter(text: str) -> Tuple[Dict[str, str], str]:
    """Parse a leading `---` delimited key: value block.

    Hand-rolled rather than pulling in a YAML dependency: the format is a flat
    key/value map and the values are prose.
    """
    if not text.startswith("---"):
        return {}, text
    end = text.find("\n---", 3)
    if end == -1:
        return {}, text
    block = text[3:end].strip("\n")
    body = text[end + 4 :]
    fields: Dict[str, str] = {}
    current_key: Optional[str] = None
    for line in block.splitlines():
        if not line.strip():
            continue
        m = re.match(r"^([A-Za-z_][A-Za-z0-9_]*):\s*(.*)$", line)
        if m:
            current_key = m.group(1)
            fields[current_key] = m.group(2).strip()
        elif current_key:  # continuation line
            fields[current_key] = (fields[current_key] + " " + line.strip()).strip()
    return fields, body


def load_preregistration(test_id: str, directory: Path = PREREG_DIR) -> PreRegistration:
    """Load and validate the pre-registration for `test_id`.

    Raises rather than returning None: a missing pre-registration must stop the
    test, not degrade to a warning that gets scrolled past.
    """
    if not directory.exists():
        raise PreRegistrationMissing(
            f"no pre-registration directory at {directory}; create it and add {test_id}.md "
            "before running any factor test"
        )
    matches = sorted(directory.glob(f"{test_id}*.md"))
    if not matches:
        raise PreRegistrationMissing(
            f"no pre-registration file for test id {test_id!r} in {directory}. "
            "Write the hypothesis, metric and confirmation threshold BEFORE running the "
            "test (statistical-guardrails.md §3.4)."
        )
    path = matches[0]
    fields, _ = _parse_frontmatter(path.read_text(encoding="utf-8"))
    missing = [f for f in REQUIRED_FIELDS if not fields.get(f)]
    if missing:
        raise PreRegistrationInvalid(
            f"pre-registration {path.name} is missing required field(s): {missing}"
        )
    return PreRegistration(
        id=fields["id"],
        title=fields["title"],
        hypothesis=fields["hypothesis"],
        metric=fields["metric"],
        confirmation_threshold=fields["confirmation_threshold"],
        status=fields["status"],
        path=path,
        fields=fields,
    )


def require_preregistration(test_id: str, directory: Path = PREREG_DIR) -> PreRegistration:
    """Guard to call at the top of any factor test."""
    return load_preregistration(test_id, directory)


# ------------------------------------------------------------------ run log


def record_test_run(
    test_id: str,
    metric: str,
    p_value: Optional[float],
    effect_size: Optional[float],
    seasons_used: Sequence[int],
    notes: str = "",
    log_path: Path = RUN_LOG_PATH,
) -> dict:
    """Append one executed test to the permanent run log.

    Call this for EVERY run, including ones that produced nothing. A test that
    is run and not recorded shrinks the FDR denominator and inflates every
    surviving result.
    """
    log_path.parent.mkdir(parents=True, exist_ok=True)
    entry = {
        "timestamp_utc": dt.datetime.now(dt.timezone.utc).isoformat(),
        "test_id": test_id,
        "metric": metric,
        "p_value": p_value,
        "effect_size": effect_size,
        "seasons_used": list(seasons_used),
        "notes": notes,
    }
    with log_path.open("a", encoding="utf-8") as f:
        f.write(json.dumps(entry) + "\n")
    return entry


def all_test_runs(log_path: Path = RUN_LOG_PATH) -> List[dict]:
    if not log_path.exists():
        return []
    with log_path.open(encoding="utf-8") as f:
        return [json.loads(line) for line in f if line.strip()]


def total_tests_run(log_path: Path = RUN_LOG_PATH) -> int:
    return len(all_test_runs(log_path))


# ------------------------------------------------------------------ FDR


@dataclass(frozen=True)
class FDRResult:
    p_values: List[float]
    adjusted: List[float]
    rejected: List[bool]
    alpha: float
    n_tested: int
    n_total_considered: int
    note: str


def benjamini_hochberg(
    p_values: Sequence[float],
    alpha: float = 0.05,
    n_total: Optional[int] = None,
) -> FDRResult:
    """Benjamini-Hochberg FDR correction.

    `n_total` lets the correction apply across the TRUE number of tests run
    (from the persistent log) even when only a subset is being reported here.
    Passing the reported subset alone is the error this argument exists to
    prevent: correcting 5 hand-picked p-values as though 5 tests were run, when
    30 were, understates the false-discovery rate roughly six-fold.
    """
    p = np.asarray(list(p_values), dtype=float)
    m_reported = len(p)
    if m_reported == 0:
        return FDRResult([], [], [], alpha, 0, n_total or 0, "no p-values supplied")
    m = int(n_total) if n_total is not None else m_reported
    if m < m_reported:
        raise ValueError(
            f"n_total ({m}) is smaller than the number of p-values supplied ({m_reported})"
        )

    order = np.argsort(p)
    ranked = p[order]
    ranks = np.arange(1, m_reported + 1)
    adj_sorted = np.minimum.accumulate((ranked * m / ranks)[::-1])[::-1]
    adj_sorted = np.clip(adj_sorted, 0.0, 1.0)

    adjusted = np.empty_like(adj_sorted)
    adjusted[order] = adj_sorted
    rejected = adjusted <= alpha

    note = ""
    if n_total is not None and n_total > m_reported:
        note = (
            f"corrected across the full run log ({m} tests), not just the "
            f"{m_reported} reported here"
        )
    return FDRResult(
        p_values=[float(x) for x in p],
        adjusted=[float(x) for x in adjusted],
        rejected=[bool(x) for x in rejected],
        alpha=alpha,
        n_tested=m_reported,
        n_total_considered=m,
        note=note,
    )


def correct_against_full_log(
    p_values: Sequence[float], alpha: float = 0.05, log_path: Path = RUN_LOG_PATH
) -> FDRResult:
    """BH correction whose denominator is the persistent run-log total."""
    total = max(total_tests_run(log_path), len(p_values))
    return benjamini_hochberg(p_values, alpha=alpha, n_total=total)
