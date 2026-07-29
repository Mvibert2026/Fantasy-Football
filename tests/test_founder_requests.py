import importlib.util
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[1]


def _load_module():
    spec = importlib.util.spec_from_file_location(
        "founder_requests_under_test", str(REPO_ROOT / "tools" / "founder_requests.py")
    )
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


@pytest.fixture
def fr(tmp_path, monkeypatch):
    mod = _load_module()
    fr_dir = tmp_path / "founder-requests"
    fr_dir.mkdir()
    archive = tmp_path / "founder-requests.md"
    archive.write_text("## FR-001\n...\n## FR-017\n...\n## FR-015\n(duplicate, as in the real archive)\n", encoding="utf-8")
    monkeypatch.setattr(mod, "FR_DIR", fr_dir)
    monkeypatch.setattr(mod, "INDEX", fr_dir / "INDEX.md")
    monkeypatch.setattr(mod, "ARCHIVE", archive)
    return mod


def test_next_free_id_seeds_past_archive_max(fr):
    assert fr.next_free_id() == 18  # archive tops out at FR-017


def test_next_free_id_scans_filenames_not_frontmatter(fr):
    (fr.FR_DIR / "FR-020-alpha.md").write_text("---\nID: FR-999\nSTATUS: NEW\n---\n\nbody\n", encoding="utf-8")
    assert fr.next_free_id() == 21  # driven by filename (020), not the lying ID: field (999)


def test_new_writes_unallocated_file_then_allocates_via_sync(fr):
    class Args:
        raised_by = "cowork chat"
        subject = "Add a widget"
    fr.cmd_new(Args)
    allocated = list(fr.FR_DIR.glob("FR-*.md"))
    assert len(allocated) == 1
    assert allocated[0].name == "FR-018-add-a-widget.md"
    assert "ID: FR-018" in allocated[0].read_text(encoding="utf-8")
    assert not list(fr.FR_DIR.glob("NEW-*.md"))  # nothing left pending


def test_ingest_refuses_to_overwrite_existing_destination(fr):
    # Forces the exact collision next_free_id() would otherwise avoid naturally -- mirrors
    # tools/handoffs.py's own test for the cross-worktree-race case (thread 076): two
    # worktrees can each compute a locally-valid "next free" number that collides at merge.
    (fr.FR_DIR / "FR-018-taken.md").write_text("---\nID: FR-018\nSTATUS: NEW\n---\n\nbody\n", encoding="utf-8")
    src = fr.FR_DIR / "NEW-taken.md"
    src.write_text("---\nSTATUS: NEW\n---\n\nbody\n", encoding="utf-8")
    with pytest.raises(SystemExit):
        fr._ingest_one(src, nid=18, today="2026-07-28")
    assert src.exists()  # the pending file must survive a refused ingestion


def test_subject_strips_full_fr_nnn_prefix_not_just_first_hyphen(fr):
    p = fr.FR_DIR / "FR-018-test-allocator-seeds-past-archive-max.md"
    p.write_text("---\nID: FR-018\nSTATUS: NEW\n---\n\nbody\n", encoding="utf-8")
    req = fr.Request(p)
    assert req.subject == "Test allocator seeds past archive max"


def test_next_free_id_widens_past_local_tree_via_refs(fr, monkeypatch):
    """FR-020 double-allocated on two branches, 2026-07-29 -- a number claimed only on
    a branch this tree hasn't checked out must not be reused."""
    monkeypatch.setattr(fr, "_git_ref_names", lambda: ["origin/other-branch"])
    monkeypatch.setattr(
        fr, "_git_tree_filenames",
        lambda ref, subdir: ["FR-025-claimed-elsewhere.md"] if ref == "origin/other-branch" else [],
    )
    assert fr.next_free_id() == 26  # not 18 -- FR-025 on the other branch must be respected


def test_find_fr_collisions_flags_conflicting_slugs(fr, monkeypatch):
    (fr.FR_DIR / "FR-020-stop-asking-permission.md").write_text(
        "---\nID: FR-020\nSTATUS: NEW\n---\n\nbody\n", encoding="utf-8"
    )
    monkeypatch.setattr(fr, "_git_ref_names", lambda: ["origin/other-branch"])
    monkeypatch.setattr(
        fr, "_git_tree_filenames",
        lambda ref, subdir: ["FR-020-completely-different-ask.md"] if ref == "origin/other-branch" else [],
    )
    problems = fr.find_fr_collisions()
    assert any("FR-020" in p for p in problems)


def test_find_fr_collisions_silent_when_no_conflict(fr, monkeypatch):
    (fr.FR_DIR / "FR-020-same-ask.md").write_text(
        "---\nID: FR-020\nSTATUS: NEW\n---\n\nbody\n", encoding="utf-8"
    )
    monkeypatch.setattr(fr, "_git_ref_names", lambda: ["origin/other-branch"])
    monkeypatch.setattr(
        fr, "_git_tree_filenames",
        lambda ref, subdir: ["FR-020-same-ask.md"] if ref == "origin/other-branch" else [],
    )
    assert fr.find_fr_collisions() == []


def test_sync_groups_by_status(fr):
    (fr.FR_DIR / "FR-018-a.md").write_text("---\nID: FR-018\nSTATUS: NEW\n---\n\nbody\n", encoding="utf-8")
    (fr.FR_DIR / "FR-019-b.md").write_text("---\nID: FR-019\nSTATUS: SHIPPED\n---\n\nbody\n", encoding="utf-8")
    fr.cmd_sync(None)
    text = fr.INDEX.read_text(encoding="utf-8")
    assert "## NEW — 1" in text
    assert "## SHIPPED — 1" in text
    assert "FR-018-a.md" in text
    assert "FR-019-b.md" in text
