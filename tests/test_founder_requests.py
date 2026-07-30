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
    today = fr.datetime.date.today().isoformat()
    assert allocated[0].name == f"FR-{today}-add-a-widget.md"
    assert f"ID: FR-{today}-add-a-widget" in allocated[0].read_text(encoding="utf-8")
    assert not list(fr.FR_DIR.glob("NEW-*.md"))  # nothing left pending


def test_ingest_never_raises_on_same_day_same_slug(fr):
    """W3: the old counter-collision test is gone -- new_request_filename() cannot
    return an already-taken path, so there is nothing left for _ingest_one to
    hard-fail on. Two pending files that slugify identically on the same day both
    ingest, deterministically disambiguated."""
    (fr.FR_DIR / f"FR-2026-07-28-taken.md").write_text(
        "---\nID: FR-2026-07-28-taken\nSTATUS: NEW\n---\n\nbody\n", encoding="utf-8"
    )
    src = fr.FR_DIR / "NEW-taken.md"
    src.write_text("---\nSTATUS: NEW\n---\n\nbody\n", encoding="utf-8")
    dest = fr._ingest_one(src, today="2026-07-28")
    assert dest.name == "FR-2026-07-28-taken-2.md"
    assert not src.exists()


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


def test_known_legacy_fr_collisions_registry_is_frozen():
    mod = _load_module()
    assert mod.KNOWN_LEGACY_FR_COLLISIONS == frozenset({"FR-029", "FR-030"})


def test_check_passes_on_real_repo_only_via_known_legacy_debt():
    """Mirrors tools/handoffs.py's equivalent: the real docs/founder-requests/ mailbox
    must be green, and specifically because its pre-existing collisions are named in
    the frozen registry -- not because detection stopped working."""
    mod = _load_module()
    problems = mod.find_fr_collisions()
    hard = [p for p in problems if not any(p.startswith(f"{fid} ") for fid in mod.KNOWN_LEGACY_FR_COLLISIONS)]
    assert hard == [], f"unaccounted-for FR collision(s), not in the frozen debt registry: {hard}"


def test_sync_groups_by_status(fr):
    (fr.FR_DIR / "FR-018-a.md").write_text("---\nID: FR-018\nSTATUS: NEW\n---\n\nbody\n", encoding="utf-8")
    (fr.FR_DIR / "FR-019-b.md").write_text("---\nID: FR-019\nSTATUS: SHIPPED\n---\n\nbody\n", encoding="utf-8")
    fr.cmd_sync(None)
    text = fr.INDEX.read_text(encoding="utf-8")
    assert "## NEW — 1" in text
    assert "## SHIPPED — 1" in text
    assert "FR-018-a.md" in text
    assert "FR-019-b.md" in text
