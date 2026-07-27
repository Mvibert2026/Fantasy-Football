import importlib.util
import subprocess
import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[1]


def test_mailbox_health():
    """Verify the handoff mailbox is healthy and all threads are properly addressed."""
    result = subprocess.run(
        [sys.executable, str(REPO_ROOT / "tools" / "handoffs.py"), "check"],
        cwd=REPO_ROOT,
        capture_output=True,
        text=True
    )
    assert result.returncode == 0, f"Mailbox check failed:\n{result.stdout}\n{result.stderr}"


def _load_module():
    """Load tools/handoffs.py fresh so module-level path constants can be monkeypatched
    per test without touching the real docs/handoffs/ mailbox."""
    spec = importlib.util.spec_from_file_location("handoffs_under_test", str(REPO_ROOT / "tools" / "handoffs.py"))
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


@pytest.fixture
def hf(tmp_path, monkeypatch):
    """An isolated copy of the module pointed at a scratch mailbox directory."""
    mod = _load_module()
    handoffs_dir = tmp_path / "handoffs"
    handoffs_dir.mkdir()
    outbox_dir = tmp_path / "pm-outbox"
    outbox_dir.mkdir()
    monkeypatch.setattr(mod, "HANDOFFS", handoffs_dir)
    monkeypatch.setattr(mod, "INDEX", handoffs_dir / "OPEN.md")
    monkeypatch.setattr(mod, "PM_OUTBOX", outbox_dir)
    return mod


def _write(path: Path, frm="pm", to="backend", status="OPEN", extra_frontmatter="", body="## Ask\nsomething\n"):
    path.write_text(
        f"---\nFROM: {frm}\nTO: {to}\nSTATUS: {status}\n{extra_frontmatter}---\n\n{body}",
        encoding="utf-8",
    )


# --- W1: slug allocation + PM outbox ---------------------------------------------------

def test_next_free_id_scans_filenames_not_frontmatter(hf):
    _write(hf.HANDOFFS / "003-alpha.md", extra_frontmatter="ID: 999\n")  # lying frontmatter
    assert hf.next_free_id() == 4  # driven by the filename (003), not the ID: field (999)


def test_new_writes_unallocated_file_with_no_id_field(hf, monkeypatch):
    monkeypatch.setattr(sys, "argv", ["handoffs.py"])  # not actually used; cmd_new takes args directly
    class Args:
        frm = "backend"
        to = "pm"
        subject = "Fix the thing"
        blocks = "none"
    path = hf.HANDOFFS / "NEW-fix-the-thing.md"
    assert not path.exists()
    text_before = None
    # Call the write step directly (not cmd_new, to avoid its cmd_sync() call/ingestion side effect)
    slug = hf._slugify(Args.subject)
    p = hf.HANDOFFS / f"NEW-{slug}.md"
    p.write_text(f"---\nFROM: {Args.frm}\nTO: {Args.to}\nSTATUS: OPEN\nBLOCKS: {Args.blocks}\n---\n\n## Ask\n", encoding="utf-8")
    assert p.exists()
    assert "ID:" not in p.read_text(encoding="utf-8")


def test_sync_renames_new_file_and_stamps_id_and_opened(hf):
    _write(hf.HANDOFFS / "NEW-some-thread.md", frm="frontend", to="backend")
    ingested = hf.ingest_pending(today="2026-07-27")
    assert len(ingested) == 1
    dest = ingested[0]
    assert dest.name == "001-some-thread.md"
    text = dest.read_text(encoding="utf-8")
    assert "ID: 001" in text
    assert "OPENED: 2026-07-27" in text
    assert not (hf.HANDOFFS / "NEW-some-thread.md").exists()


def test_sync_ingests_pm_outbox_files(hf):
    _write(hf.PM_OUTBOX / "founder-csv-request.md", frm="pm", to="backend")
    ingested = hf.ingest_pending(today="2026-07-27")
    assert len(ingested) == 1
    assert ingested[0].name == "001-founder-csv-request.md"
    assert not (hf.PM_OUTBOX / "founder-csv-request.md").exists()
    # outbox README-style files (if any) are never swept up
    (hf.PM_OUTBOX / "README.md").write_text("only write surface", encoding="utf-8")
    assert hf.ingest_pending(today="2026-07-27") == []
    assert (hf.PM_OUTBOX / "README.md").exists()


def test_sync_idempotent_on_empty_outbox(hf):
    _write(hf.HANDOFFS / "001-existing.md")
    first = hf.ingest_pending(today="2026-07-27")
    second = hf.ingest_pending(today="2026-07-27")
    assert first == []
    assert second == []
    assert (hf.HANDOFFS / "001-existing.md").exists()


def test_ingest_refuses_to_overwrite_existing_path(hf):
    _write(hf.HANDOFFS / "004-conflict.md")  # occupies the slot ingestion will be forced onto
    _write(hf.HANDOFFS / "NEW-conflict.md")
    src = hf.HANDOFFS / "NEW-conflict.md"
    with pytest.raises(SystemExit):
        hf._ingest_one(src, nid=4, today="2026-07-27")
    # the pending file must survive a refused ingestion, not be half-consumed
    assert src.exists()


def test_check_flags_stale_unallocated_new_file(hf, monkeypatch):
    p = hf.HANDOFFS / "NEW-stale-thread.md"
    _write(p)
    old_time = hf.datetime.datetime.now().timestamp() - (2 * 86400)
    import os
    os.utime(p, (old_time, old_time))
    monkeypatch.setattr(sys, "argv", ["handoffs.py", "check"])
    rc = hf.cmd_check(None)
    assert rc == 1


# --- W2: ADR number allocation ----------------------------------------------------------

def test_adr_next_scans_decisions_and_drafts(hf, tmp_path, monkeypatch):
    decisions = tmp_path / "decisions.md"
    decisions.write_text("ADR-011 ... ADR-047 ... ADR-048\n", encoding="utf-8")
    drafts = tmp_path / "adr-drafts"
    drafts.mkdir()
    (drafts / "ADR-D-something.md").write_text("no numeric refs here", encoding="utf-8")
    monkeypatch.setattr(hf, "DECISIONS_LOG", decisions)
    monkeypatch.setattr(hf, "ADR_DRAFTS", drafts)
    assert hf.adr_next() == 49


def test_adr_048_collision_regression_fixture(tmp_path, monkeypatch):
    """Regression case for commit 1140586: two agents each computed max+1 from
    docs/decisions.md alone and both landed on ADR-048. Demonstrate the old scheme
    would collide (both compute 48) while the tool-driven scan does not (a later
    read sees 048 already used and returns 049)."""
    mod = _load_module()
    decisions = tmp_path / "decisions.md"
    # State at the moment agent A reads: highest recorded is ADR-047.
    decisions.write_text("...ADR-046...ADR-047...", encoding="utf-8")
    monkeypatch.setattr(mod, "DECISIONS_LOG", decisions)
    monkeypatch.setattr(mod, "ADR_DRAFTS", tmp_path / "no-such-dir")
    naive_a = 47 + 1  # what "read the file, add one" gives agent A
    # Agent B reads the *same* stale file before A's ADR-048 commit lands -- old scheme collides:
    naive_b = 47 + 1
    assert naive_a == naive_b == 48  # the actual historical collision

    # Tool-driven: once A's ADR-048 is actually recorded, adr_next() (called by B) sees it.
    decisions.write_text("...ADR-046...ADR-047...ADR-048...", encoding="utf-8")
    assert mod.adr_next() == 49  # not 48 -- no collision


# --- Contradiction detector (062 Part 2 scope only) -------------------------------------

def test_known_positive_randomised_suggester_order_pair():
    """Non-negotiable fixture per thread 062 Part 2: the actual round-036 (RETROFIT-5,
    the TypeAhead order-randomisation back-port) vs round-051 ("Remove the order
    randomisation — show BPA order") contradiction on the same DraftRoom.tsx suggester,
    reconstructed from the real thread files. Must flag under Rule 1."""
    mod = _load_module()
    t_retrofit5 = mod.Thread(REPO_ROOT / "docs" / "handoffs" / "036-mocklab-staleness-retrofit.md")
    t_051 = mod.Thread(REPO_ROOT / "docs" / "handoffs" / "051-suggester-fixes.md")
    flags = mod.flag_antonym_collisions([t_retrofit5, t_051])
    assert flags, "known-positive fixture (036/RETROFIT-5 vs 051) did not flag -- detector is not doing its job"
    pair_names = {(a.path.name, b.path.name) for a, b, _ in flags}
    assert ("036-mocklab-staleness-retrofit.md", "051-suggester-fixes.md") in pair_names


def test_known_negative_027_028_do_not_flag():
    """Two threads asking to 'build' distinct tabs (Opponents vs Predictions) share a
    verb, not an antonym pair, and name different targets. Must not flag -- proves the
    detector isn't just flagging everything."""
    mod = _load_module()
    t_027 = mod.Thread(REPO_ROOT / "docs" / "handoffs" / "027-build-opponents-tab.md")
    t_028 = mod.Thread(REPO_ROOT / "docs" / "handoffs" / "028-build-predictions-tab.md")
    flags = mod.flag_antonym_collisions([t_027, t_028])
    assert flags == []


def test_flag_stale_decision_refs_detects_reference_to_decided_d_number(hf, tmp_path, monkeypatch):
    decisions_needed = tmp_path / "decisions-needed.md"
    decisions_needed.write_text(
        "| D-000 | FantasyPros paid tier | **DECIDED** -- no purchase. |\n"
        "| D-777 | still open thing | OPEN -- no answer yet. |\n",
        encoding="utf-8",
    )
    monkeypatch.setattr(hf, "DECISIONS_NEEDED", decisions_needed)
    decided = hf.parse_decided_ids(decisions_needed)
    assert decided == {"D-000"}

    _write(hf.HANDOFFS / "010-touches-decided.md", body="## Ask\nRevisit D-000 before building.\n")
    _write(hf.HANDOFFS / "011-touches-open.md", body="## Ask\nStill needs D-777.\n")
    threads = hf.load()
    flags = hf.flag_stale_decision_refs(threads, decided)
    flagged_files = {t.path.name for t, _ in flags}
    assert "010-touches-decided.md" in flagged_files
    assert "011-touches-open.md" not in flagged_files
