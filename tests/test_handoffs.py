import subprocess
import pytest
from pathlib import Path


def test_mailbox_health():
    """Verify the handoff mailbox is healthy and all threads are properly addressed."""
    repo_root = Path(__file__).resolve().parents[1]
    result = subprocess.run(
        ["py", str(repo_root / "tools" / "handoffs.py"), "check"],
        cwd=repo_root,
        capture_output=True,
        text=True
    )
    assert result.returncode == 0, f"Mailbox check failed:\n{result.stdout}\n{result.stderr}"
