"""H1 + H4 (session-1 overfitting review; built under the extended mandate).

H1 — audit the audit trail. The holdout access log was write-only: nothing
read it, so it deterred nobody. These tests convert it into a tripwire.

FINDING RECORDED AT BUILD TIME (2026-07-27): the log's only recorded cycle
(2026-07-25 21:48 UTC) READ THE SEALED 2025 HOLDOUT via the self-service
`final_evaluation` path, citing no registration id — its reason says the
holdout "was already consumed for this metric" (+84.6 board-vs-consensus),
i.e. an EARLIER, unlogged consumption predates the log itself. UNSEAL_LOG.md
(which ADR-C requires for any 2025 read) has never existed. Session 1's
"never been unsealed" clean bill is therefore true only formally: the
holdout has been read at least twice (once before logging existed, once
logged). Those three historical entries are pinned below as REVIEWED —
accepted as history, not as precedent. Any NEW event fails this test until
a human moves it into the reviewed set with a registration id.

H4 — structural read guard, cheap version: new `sqlite3.connect` callsites
in src/ outside the ingestion allowlist fail, forcing analysis code through
db.connect / CutoffEnforcedStore.
"""

import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PREREG_DIR = ROOT / "docs" / "preregistration"
ACCESS_LOG = PREREG_DIR / "holdout_access_log.jsonl"
UNSEAL_LOG = PREREG_DIR / "UNSEAL_LOG.md"

# Historical entries reviewed 2026-07-27 (Fable extended-mandate session 2).
# Keyed by timestamp_utc. Do not add to this set without a registration id
# in the entry's reason and a note in docs/decisions.md.
REVIEWED_TIMESTAMPS = {
    "2026-07-25T21:48:28.622372+00:00",  # FINAL_EVALUATION_OPENED (no prereg id)
    "2026-07-25T21:48:28.623402+00:00",  # ALLOWED (same cycle)
    "2026-07-25T21:48:33.520512+00:00",  # FINAL_EVALUATION_CLOSED (same cycle)
}

AUDITED_EVENTS = {
    "FINAL_EVALUATION_OPENED", "FINAL_FIT_OPENED", "ALLOWED", "DENIED",
}


def _log_entries():
    if not ACCESS_LOG.exists():
        return []
    with ACCESS_LOG.open(encoding="utf-8") as f:
        return [json.loads(line) for line in f if line.strip()]


def _registration_ids():
    return {p.stem.split("-")[0] + "-" + p.stem.split("-")[1]
            for p in PREREG_DIR.glob("PR-*.md")}


def test_unseal_log_does_not_exist_until_sanctioned():
    """ADR-C requires a signed UNSEAL_LOG.md for any sanctioned 2025 unseal.
    Until the first sanctioned unseal, its very existence is an alarm; after
    one, replace this assertion with a pinned expected-entry count."""
    assert not UNSEAL_LOG.exists(), (
        "UNSEAL_LOG.md exists. Either a sanctioned unseal happened (then pin "
        "its entry count here and record it in docs/decisions.md) or "
        "something forged it."
    )


def test_no_unreviewed_holdout_access_events():
    ids = _registration_ids()
    offenders = []
    for e in _log_entries():
        if e.get("event") not in AUDITED_EVENTS:
            continue
        if e.get("timestamp_utc") in REVIEWED_TIMESTAMPS:
            continue
        reason = e.get("reason", "")
        if not any(rid in reason for rid in ids):
            offenders.append(e)
    assert not offenders, (
        "Holdout access log contains unreviewed events that cite no "
        "registration id. A DENIED means someone TRIED; an ALLOWED/OPENED "
        "means the holdout was read. Review each, then either add its "
        f"timestamp to REVIEWED_TIMESTAMPS with justification: {offenders}"
    )


def test_reviewed_set_matches_log():
    """The reviewed set must stay a subset of the real log — a rewritten or
    truncated log that orphans reviewed timestamps is itself suspicious."""
    present = {e.get("timestamp_utc") for e in _log_entries()}
    missing = REVIEWED_TIMESTAMPS - present
    assert not missing, (
        f"Reviewed timestamps missing from the access log (log truncated or "
        f"rewritten?): {missing}"
    )


# ---------------------------------------------------------------------- H4
# Modules that legitimately open raw connections (ingestion + the DAL).
CONNECT_ALLOWLIST = {
    "db.py",
    "ingest_fantasypros_csv.py",
    "ingest_coordinators_wikipedia.py",
    "ingest_ffc_adp.py",
    "ingest_mfl_adp.py",
    "ingest_mock_drafts.py",
    "ingest_play_callers.py",
    "ingest_rankings.py",
    "ingest_reference.py",
    "ingest_weekly_stats.py",
}


def test_no_new_direct_sqlite_connections_in_src():
    pattern = re.compile(r"sqlite3\.connect")
    offenders = []
    for path in sorted((ROOT / "src").glob("*.py")):
        if path.name in CONNECT_ALLOWLIST:
            continue
        if pattern.search(path.read_text(encoding="utf-8", errors="replace")):
            offenders.append(path.name)
    assert not offenders, (
        f"New direct sqlite3.connect in src/ outside the ingestion allowlist: "
        f"{offenders}. Analysis code must go through db.connect / "
        f"CutoffEnforcedStore so the cutoff guard can see it (guardrails "
        f"'structural, not procedural')."
    )
