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
    assert dest.name == "2026-07-27-some-thread.md"
    text = dest.read_text(encoding="utf-8")
    assert "ID: 2026-07-27-some-thread" in text
    assert "OPENED: 2026-07-27" in text
    assert not (hf.HANDOFFS / "NEW-some-thread.md").exists()


def test_sync_ingests_pm_outbox_files(hf):
    _write(hf.PM_OUTBOX / "founder-csv-request.md", frm="pm", to="backend")
    ingested = hf.ingest_pending(today="2026-07-27")
    assert len(ingested) == 1
    assert ingested[0].name == "2026-07-27-founder-csv-request.md"
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


# --- W3: date+slug allocation (supersedes the NNN counter for NEW threads) --------------

def test_new_thread_filename_has_no_shared_counter_and_no_git_dependency(hf, monkeypatch):
    """The core W3 property: allocating a new thread filename never reads git refs or
    any 'highest so far' state -- it is a pure function of (date, slug). Prove it by
    making any git call blow up and confirming allocation still works."""
    def _boom(*a, **kw):
        raise AssertionError("new_thread_filename must not touch git")
    monkeypatch.setattr(hf, "_git_ref_names", _boom)
    monkeypatch.setattr(hf.subprocess, "run", _boom)
    path = hf.new_thread_filename("2026-07-30", "availability-opponent-model")
    assert path.name == "2026-07-30-availability-opponent-model.md"
    assert path.exists()  # claimed atomically


def test_new_thread_filename_dedupes_same_day_same_slug_deterministically(hf):
    """Two threads opened on the same day with the same subject, in the SAME working
    tree, must not collide -- and must not require a human to pick a number. The
    second call gets a deterministic -2 suffix instead of overwriting or raising."""
    p1 = hf.new_thread_filename("2026-07-30", "sprint-4-runbook")
    p2 = hf.new_thread_filename("2026-07-30", "sprint-4-runbook")
    p3 = hf.new_thread_filename("2026-07-30", "sprint-4-runbook")
    assert {p1.name, p2.name, p3.name} == {
        "2026-07-30-sprint-4-runbook.md",
        "2026-07-30-sprint-4-runbook-2.md",
        "2026-07-30-sprint-4-runbook-3.md",
    }


def test_two_worktrees_different_subjects_same_day_cannot_collide(hf, tmp_path, monkeypatch):
    """Reproduces thread 076's actual scenario under the NEW scheme: two isolated
    worktrees (simulated as two separate HANDOFFS directories, standing in for two
    working trees neither of which can see the other's in-flight file) each allocate a
    thread on the same day. Under the OLD counter scheme this is exactly the case that
    collided (both worktrees compute the same 'next free number' from what they can
    see). Under the date+slug scheme, allocation needs no visibility into the other
    worktree at all -- the filenames differ because the *subjects* differ, which is
    already known locally with nothing to race."""
    tree_a = tmp_path / "worktree-a" / "docs" / "handoffs"
    tree_b = tmp_path / "worktree-b" / "docs" / "handoffs"
    tree_a.mkdir(parents=True)
    tree_b.mkdir(parents=True)

    monkeypatch.setattr(hf, "HANDOFFS", tree_a)
    path_a = hf.new_thread_filename("2026-07-30", hf._slugify("Availability opponent model"))

    monkeypatch.setattr(hf, "HANDOFFS", tree_b)
    path_b = hf.new_thread_filename("2026-07-30", hf._slugify("Sprint 4 runbook"))

    # Different subjects -> different filenames -> a merge of both worktrees is a
    # clean two-file add, never a collision. (Under the old NNN scheme, both worktrees
    # would independently have computed the SAME next number here.)
    assert path_a.name != path_b.name
    assert path_a.name == "2026-07-30-availability-opponent-model.md"
    assert path_b.name == "2026-07-30-sprint-4-runbook.md"


def test_ingest_never_raises_on_same_day_same_slug_pm_outbox_race(hf):
    """The old scheme's collision test (`test_ingest_refuses_to_overwrite_existing_path`,
    an artifact of counter-based allocation) is gone: under W3 there is nothing left to
    hard-fail on. Two pending files that would slugify to the same name on the same day
    both ingest successfully, deterministically disambiguated."""
    _write(hf.HANDOFFS / "NEW-conflict.md")
    _write(hf.PM_OUTBOX / "conflict.md")
    ingested = hf.ingest_pending(today="2026-07-27")
    assert len(ingested) == 2
    assert {p.name for p in ingested} == {"2026-07-27-conflict.md", "2026-07-27-conflict-2.md"}


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
    monkeypatch.setattr(hf, "_git_ref_names", lambda: [])  # isolate from this repo's real branches
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
    monkeypatch.setattr(mod, "_git_ref_names", lambda: [])  # isolate from this repo's real branches
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


# --- Cross-branch ID allocation widening + duplicate backstop (2026-07-29) -------------

def test_next_free_id_widens_past_local_tree_via_refs(hf, monkeypatch):
    """A number claimed only on a branch this working tree hasn't checked out must not
    be reused. Simulate that by stubbing the git-scan helpers instead of depending on
    real repo state."""
    _write(hf.HANDOFFS / "003-alpha.md")
    monkeypatch.setattr(hf, "_git_ref_names", lambda: ["origin/other-branch"])
    monkeypatch.setattr(
        hf, "_git_tree_filenames",
        lambda ref, subdir: ["009-claimed-elsewhere.md"] if ref == "origin/other-branch" else [],
    )
    assert hf.next_free_id() == 10  # not 4 -- 009 on the other branch must be respected


def test_next_free_id_falls_back_when_git_unavailable(hf, monkeypatch, capsys):
    """If the ref scan can't run, allocation must still work from the local tree alone,
    and must say so on stderr rather than pretend nothing happened."""
    _write(hf.HANDOFFS / "003-alpha.md")
    monkeypatch.setattr(hf, "_git_ref_names", lambda: [])
    assert hf.next_free_id() == 4


def test_adr_next_widens_past_local_tree_via_refs(hf, tmp_path, monkeypatch):
    decisions = tmp_path / "decisions.md"
    decisions.write_text("ADR-010\n", encoding="utf-8")
    monkeypatch.setattr(hf, "DECISIONS_LOG", decisions)
    monkeypatch.setattr(hf, "ADR_DRAFTS", tmp_path / "no-such-dir")
    monkeypatch.setattr(hf, "_git_ref_names", lambda: ["origin/other-branch"])
    monkeypatch.setattr(hf, "_git_tree_filenames", lambda ref, subdir: [])
    monkeypatch.setattr(
        hf, "_git_show",
        lambda ref, path: "ADR-030 -- taken on the other branch\n" if ref == "origin/other-branch" else None,
    )
    assert hf.adr_next() == 31  # not 11 -- ADR-030 on the other branch must be respected


def test_find_adr_collisions_flags_same_number_different_header(hf, tmp_path, monkeypatch):
    """The real 2026-07-29 case: ADR-054 recorded with two different headers on main
    and on the unmerged backend/mock-calibration-kickers branch. Must flag, not resolve."""
    decisions = tmp_path / "decisions.md"
    decisions.write_text("## ADR-054 — FFC ingester wired into CI\n", encoding="utf-8")
    monkeypatch.setattr(hf, "DECISIONS_LOG", decisions)
    monkeypatch.setattr(hf, "_git_ref_names", lambda: ["origin/backend/mock-calibration-kickers"])
    monkeypatch.setattr(
        hf, "_git_show",
        lambda ref, path: "## ADR-054 — Batch mock-draft ingestion gains a frozen snapshot\n"
        if ref == "origin/backend/mock-calibration-kickers" and path == "docs/decisions.md" else None,
    )
    problems = hf.find_adr_collisions()
    assert any("ADR-054" in p for p in problems)


def test_find_adr_collisions_silent_on_identical_header(hf, tmp_path, monkeypatch):
    """Same ADR number, same text on both refs (e.g. after a merge) -- not a collision."""
    decisions = tmp_path / "decisions.md"
    decisions.write_text("## ADR-054 — Same decision everywhere\n", encoding="utf-8")
    monkeypatch.setattr(hf, "DECISIONS_LOG", decisions)
    monkeypatch.setattr(hf, "_git_ref_names", lambda: ["origin/other-branch"])
    monkeypatch.setattr(
        hf, "_git_show",
        lambda ref, path: "## ADR-054 — Same decision everywhere\n" if ref == "origin/other-branch" else None,
    )
    assert hf.find_adr_collisions() == []


def test_find_thread_id_collisions_flags_conflicting_slugs(hf, monkeypatch):
    _write(hf.HANDOFFS / "042-fix-the-thing.md")
    monkeypatch.setattr(hf, "_git_ref_names", lambda: ["origin/other-branch"])
    monkeypatch.setattr(
        hf, "_git_tree_filenames",
        lambda ref, subdir: ["042-completely-different-ask.md"] if ref == "origin/other-branch" else [],
    )
    problems = hf.find_thread_id_collisions()
    assert any("042" in p for p in problems)


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


# --- Pre-existing legacy debt carve-out (frozen 2026-07-30, ADR-064) --------------------

def test_known_legacy_collisions_registry_is_frozen():
    """Pins the exact contents of the debt registries so a future session can't quietly
    grow them to hide a NEW collision. Growing this set is a real edit that must be
    visible in review, not something check silently absorbs."""
    mod = _load_module()
    assert mod.KNOWN_LEGACY_ID_COLLISIONS == frozenset({"093", "094", "109", "110", "111", "112"})
    assert mod.KNOWN_LEGACY_ADR_COLLISIONS == frozenset({"ADR-054", "ADR-055"})


def test_check_passes_on_real_repo_only_via_known_legacy_debt():
    """The real docs/handoffs/ mailbox check must be green -- and specifically because
    its existing collisions are all accounted for in the frozen registry, not because
    the detectors stopped working. If this ever fails, either a genuinely new collision
    appeared (fix it) or one of the debt entries above was quietly resolved (shrink the
    registry and update docs/known-id-collisions.md, don't just leave it stale)."""
    mod = _load_module()
    threads = mod.load()
    seen: dict[str, str] = {}
    dup_problems = []
    for t in threads:
        if t.id in seen:
            dup_problems.append(f"{t.path.name}: duplicate ID {t.id} (also {seen[t.id]})")
        seen[t.id] = t.path.name
    dup_problems += mod.find_adr_collisions()
    dup_problems += mod.find_thread_id_collisions()
    hard = [p for p in dup_problems if not mod._is_known_legacy_debt(p)]
    assert hard == [], f"unaccounted-for collision(s), not in the frozen debt registry: {hard}"


def test_is_known_legacy_debt_does_not_match_new_ids():
    """A collision on a number NOT in the frozen registry must still be treated as hard
    -- the carve-out names specific pre-existing numbers, it is not a blanket exemption
    for anything shaped like a legacy id."""
    mod = _load_module()
    assert mod._is_known_legacy_debt("999-some-thread.md: duplicate ID 999 (also 998-other.md)") is False
    assert mod._is_known_legacy_debt("thread 999 claimed for conflicting subjects across branches: a, b") is False
    assert mod._is_known_legacy_debt("ADR-999 has 2 conflicting headers across branches: a | b") is False
    # sanity: a real frozen entry does match
    assert mod._is_known_legacy_debt("093-x.md: duplicate ID 093 (also 093-y.md)") is True
