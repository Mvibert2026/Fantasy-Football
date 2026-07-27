"""Staleness guard for docs/CURRENT-STATE.md.

CURRENT-STATE.md declares itself canonical and forbids drifting silently from the working tree.
This test makes that enforceable instead of aspirational:

- The commit hash recorded in the file must be HEAD or an ancestor of HEAD (never a hash that
  isn't in this repo's history at all, and never something from a detached, unrelated line).
- The "Last verified" date must not be older than a threshold, so the file cannot rot silently
  for weeks with nobody noticing.
"""
import re
import subprocess
import sys
from datetime import date, timedelta
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[1]
CURRENT_STATE = REPO_ROOT / "docs" / "CURRENT-STATE.md"
STALENESS_THRESHOLD_DAYS = 14


def _read_current_state() -> str:
    return CURRENT_STATE.read_text(encoding="utf-8")


def _git(*args: str) -> str:
    result = subprocess.run(
        ["git", *args],
        cwd=REPO_ROOT,
        capture_output=True,
        text=True,
    )
    if result.returncode != 0:
        pytest.fail(f"git {' '.join(args)} failed: {result.stderr}")
    return result.stdout.strip()


def test_current_state_file_exists():
    assert CURRENT_STATE.exists(), "docs/CURRENT-STATE.md is missing"


def test_recorded_commit_is_head_or_ancestor():
    text = _read_current_state()
    match = re.search(r"`([0-9a-f]{7,40})`", text)
    assert match, (
        "No commit hash found in CURRENT-STATE.md's 'Build state' table — "
        "the file must record a real commit hash in backticks."
    )
    recorded_commit = match.group(1)

    # The recorded hash must exist in this repo and be reachable from HEAD.
    result = subprocess.run(
        ["git", "merge-base", "--is-ancestor", recorded_commit, "HEAD"],
        cwd=REPO_ROOT,
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0, (
        f"CURRENT-STATE.md records commit {recorded_commit!r}, which is not HEAD or an ancestor "
        f"of HEAD. The file has drifted from the repository and must be re-verified."
    )


def test_last_verified_date_is_recent():
    text = _read_current_state()
    match = re.search(r"\*\*Last verified:\*\*\s*(\d{4}-\d{2}-\d{2})", text)
    assert match, "No '**Last verified:** YYYY-MM-DD' line found in CURRENT-STATE.md"
    verified_date = date.fromisoformat(match.group(1))

    # Use the latest commit date as "now" rather than the wall clock, so this test is
    # deterministic regardless of when it happens to run relative to the last commit.
    latest_commit_date_str = _git("log", "-1", "--format=%cs")
    latest_commit_date = date.fromisoformat(latest_commit_date_str)

    age = latest_commit_date - verified_date
    assert age <= timedelta(days=STALENESS_THRESHOLD_DAYS), (
        f"CURRENT-STATE.md was last verified {verified_date} but the latest commit is dated "
        f"{latest_commit_date} ({age.days} days later, threshold is "
        f"{STALENESS_THRESHOLD_DAYS}). Re-verify the file against the working tree."
    )


def test_no_second_current_state_section():
    """The file's own header rule: edit in place, never append a duplicate section."""
    text = _read_current_state()
    header_count = text.count("# CURRENT STATE")
    assert header_count == 1, (
        f"Found {header_count} top-level '# CURRENT STATE' headers — the file's own rule is "
        "in-place editing, not appending a second canonical section."
    )
