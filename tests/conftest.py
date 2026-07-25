import sys
from pathlib import Path

import pytest

SRC_DIR = Path(__file__).resolve().parent.parent / "src"
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))


@pytest.fixture(autouse=True, scope="session")
def _isolate_holdout_audit_log(tmp_path_factory):
    """Point the holdout audit log at a temp file for the whole test session.

    docs/preregistration/holdout_access_log.jsonl is tracked in git as evidence
    of when the locked season was actually read. Letting the test suite append
    to it on every run would bury the handful of real accesses under hundreds of
    synthetic ones and destroy the audit trail's value.
    """
    import holdout

    original = holdout.DEFAULT_LOCK.log_path
    holdout.DEFAULT_LOCK.log_path = tmp_path_factory.mktemp("holdout") / "access.jsonl"
    yield
    holdout.DEFAULT_LOCK.log_path = original
