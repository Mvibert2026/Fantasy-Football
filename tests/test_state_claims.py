"""The document-claim detector, and its planted-fault proof.

Read `tools/state_claims.py`'s module docstring for the design. This file is the acceptance
evidence `docs/pm/CHARTER.md` demands before the detector is trusted: every one of the false
claims found on 2026-07-29 is planted as a fixture and must be caught, and every corrected
version must pass clean. Both directions. A detector that only ever fires is not a detector.

This test is **not** `tests/test_handoffs.py::test_mailbox_health`, which is red by design over
a real ADR numbering collision on an unmerged branch. A failure here means a document in
`docs/state-claims.toml`'s `live_docs` list asserts something the repository contradicts; the
message names the document, the line, and both values. Fix the document (or the registry, if
the registry is the thing that went stale) — do not add a suppression to make it quiet.
"""
from __future__ import annotations

import json
import re
import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT / "tools"))

import state_claims  # noqa: E402

FIXTURES = REPO_ROOT / "tests" / "fixtures" / "state_claims"


@pytest.fixture(scope="module")
def registry() -> dict:
    return state_claims.load_registry()


def _render(name: str) -> str:
    """Load a fixture, substituting live repository values.

    A fixture that hardcodes today's contract version would silently become a *false* document
    the next time the contract bumps, and the "corrected version passes clean" test would start
    failing for a reason that has nothing to do with the detector.
    """
    text = (FIXTURES / name).read_text(encoding="utf-8")
    contract = re.search(
        r'CONTRACT_VERSION\s*=\s*"([^"]+)"',
        (REPO_ROOT / "src" / "export_contract.py").read_text(encoding="utf-8"),
    ).group(1)
    text = text.replace("{{CONTRACT_VERSION}}", contract)
    board = REPO_ROOT / "data" / "export" / "board.json"
    if "{{BOARD_PLAYERS}}" in text:
        if not board.exists():
            pytest.skip("data/export/board.json absent (gitignored data dir, fresh clone)")
        n = len(json.loads(board.read_text(encoding="utf-8"))["players"])
        text = text.replace("{{BOARD_PLAYERS}}", str(n))
    return text


def _scan(registry: dict, docs: dict[str, str]) -> list[state_claims.Violation]:
    """Run the real registry over fixture text, with file checks against the real tree."""
    found = state_claims.check(registry, REPO_ROOT, docs)
    return [v for v in found if v.doc in docs]


# ---------------------------------------------------------------------------------------
# The planted faults. Each row is a real false claim from 2026-07-29.
# ---------------------------------------------------------------------------------------

PLANTED = [
    pytest.param(
        "f1-ffc-source-status", "status", "ffc-access",
        id="F1-source-status-ffc-blocked-by-robots-txt",
    ),
    pytest.param(
        "f2-predictions-existence", "artifact", "predictions-view",
        id="F2-existence-predictions-tab-absent",
    ),
    pytest.param(
        "f3-design-capability", "status", "design-repo-read-access",
        id="F3-capability-design-cannot-read-this-repo",
    ),
    pytest.param(
        "f4-contract-version", "constant", "contract-version",
        id="F4-version-contract-quoted-in-prose-drifted",
    ),
    pytest.param(
        "f5-board-count", "count", "board-players",
        id="F5-count-board-player-count-stale",
    ),
    pytest.param(
        "f6-rankings-history", "status", "rankings-history-recoverability",
        id="F6-existence-rankings-history-unrecoverable",
    ),
]


@pytest.mark.parametrize("stem,kind,claim_id", PLANTED)
def test_planted_fault_is_caught(registry, stem, kind, claim_id):
    doc = f"{stem}.bad.md"
    found = _scan(registry, {doc: _render(doc)})
    matching = [v for v in found if v.kind == kind and v.claim_id == claim_id]
    assert matching, (
        f"{doc} plants a known-false claim and the checker did not catch it. "
        f"Expected a {kind}/{claim_id} violation; got: "
        f"{[(v.kind, v.claim_id) for v in found] or 'nothing'}"
    )


@pytest.mark.parametrize("stem,kind,claim_id", PLANTED)
def test_corrected_document_is_clean(registry, stem, kind, claim_id):
    doc = f"{stem}.good.md"
    found = _scan(registry, {doc: _render(doc)})
    assert not found, (
        f"{doc} states the corrected version and must not fire. A checker that flags correct "
        f"documents gets switched off within a week. Got:\n"
        + "\n".join(v.render() for v in found)
    )


def test_cross_document_contradiction_is_caught_without_ground_truth(registry):
    """Class 5, and the honest form of the one failure this tool cannot verify directly.

    Neither document is checkable on its own — whether a GitHub Actions *schedule* has fired is
    not readable from a checkout. The violation is that the two disagree.
    """
    docs = {
        "f7-crossdoc-a.md": _render("f7-crossdoc-a.md"),
        "f7-crossdoc-b.md": _render("f7-crossdoc-b.md"),
    }
    found = _scan(registry, docs)
    matching = [v for v in found if v.claim_id == "adp-cloud-capture-schedule"]
    assert matching, (
        "Two live documents assert opposite polarities about the scheduled ADP capture and the "
        "checker stayed silent."
    )
    assert "f7-crossdoc-a.md" in matching[0].message or "f7-crossdoc-b.md" in matching[0].message


def test_each_document_alone_does_not_fire_on_the_contested_claim(registry):
    """The stated gap, asserted rather than described.

    A single document asserting "the capture runs unattended" passes — there is nothing on disk
    to contradict it. This test exists so the limitation is a measured property of the tool and
    not a paragraph in a report that nobody rereads.
    """
    for doc in ("f7-crossdoc-a.md", "f7-crossdoc-b.md"):
        found = _scan(registry, {doc: _render(doc)})
        assert not [v for v in found if v.claim_id == "adp-cloud-capture-schedule"], (
            f"{doc} alone fired; the contested-claim check is supposed to need two documents."
        )


# ---------------------------------------------------------------------------------------
# The live gate
# ---------------------------------------------------------------------------------------


def test_live_documents_contain_no_contradicted_claims(registry):
    violations = state_claims.check(registry, REPO_ROOT)
    assert not violations, (
        f"{len(violations)} document claim(s) the repository contradicts. This is not the "
        f"mailbox-health test; fix the document, not the checker.\n\n"
        + "\n\n".join(v.render() for v in violations)
    )


# ---------------------------------------------------------------------------------------
# Anti-rot: keep the registry from decaying into a rubber stamp
# ---------------------------------------------------------------------------------------


def test_append_only_logs_are_out_of_scope(registry):
    """Scanning history logs is the fastest way to turn this into noise nobody reads.

    `docs/status.md`, `docs/status/`, `docs/decisions.md` and the numbered handoff threads are
    records of what was believed at the time. Flagging them would be flagging a document for
    doing its job.
    """
    banned_prefixes = (
        "docs/status", "docs/decisions.md", "docs/founder-requests",
        "docs/SNAPSHOT-", "docs/RUN-",
    )
    for doc in state_claims.live_doc_names(registry):
        assert not doc.startswith(banned_prefixes), (
            f"{doc} is an append-only or frozen document and must not be in live_docs."
        )
        assert not re.match(r"docs/handoffs/\d", doc), (
            f"{doc} is a handoff thread — history, not current state."
        )


def test_every_live_document_exists(registry):
    missing = [d for d in state_claims.live_doc_names(registry) if not (REPO_ROOT / d).exists()]
    assert not missing, f"live_docs names documents that do not exist: {missing}"


def test_every_registered_claim_has_an_id(registry):
    for section in ("artifact", "constant", "status", "count"):
        for entry in registry.get(section, []):
            assert entry.get("id"), f"a [[{section}]] entry has no id"


def test_suppressions_and_allowances_carry_a_reason(registry):
    """A suppression without a stated reason is indistinguishable from hiding a fault."""
    for entry in registry.get("ignore", []):
        assert entry.get("reason"), f"suppression {entry.get('id')} has no reason"
    for entry in registry.get("paths", {}).get("allow", []):
        assert entry.get("reason"), f"path allowance {entry.get('path')} has no reason"


def test_retraction_masking_is_bounded():
    """An unbalanced `~~` must not blank out the rest of a document and hide real claims."""
    text = "~~struck~~ FFC is blocked ~~ dangling"
    assert "FFC is blocked" in state_claims.prepare(text)
    assert "struck" not in state_claims.prepare(text)


def test_hard_wrapped_claims_are_still_matched():
    """The real CURRENT-STATE.md fault straddled a line break; a line-by-line scan missed it."""
    flow = state_claims.prepare("... and FFC remains\n   blocked (ToS unretrievable) ...")
    assert state_claims._phrase_re(["remains blocked"]).search(flow)
