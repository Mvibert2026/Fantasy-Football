import importlib.util
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[1]


def _load_module():
    spec = importlib.util.spec_from_file_location("status_log_under_test", str(REPO_ROOT / "tools" / "status_log.py"))
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


@pytest.fixture
def sl(tmp_path, monkeypatch):
    mod = _load_module()
    status_dir = tmp_path / "status"
    monkeypatch.setattr(mod, "STATUS_DIR", status_dir)
    monkeypatch.setattr(mod, "INDEX", status_dir / "INDEX.md")
    return mod


def test_new_creates_dated_file_with_role_and_slug(sl):
    class Args:
        role = "backend"
        slug = "my session"
    sl.cmd_new(Args)
    files = list(sl.STATUS_DIR.glob("*.md"))
    assert len(files) == 1
    assert files[0].name.endswith("-backend-my-session.md")


def test_new_refuses_to_overwrite_existing_file(sl):
    class Args:
        role = "backend"
        slug = "dup"
    sl.cmd_new(Args)
    with pytest.raises(SystemExit):
        sl.cmd_new(Args)


def test_session_files_excludes_readme_and_index(sl):
    sl.STATUS_DIR.mkdir(parents=True)
    (sl.STATUS_DIR / "README.md").write_text("protocol", encoding="utf-8")
    (sl.STATUS_DIR / "INDEX.md").write_text("generated", encoding="utf-8")
    (sl.STATUS_DIR / "2026-07-28-backend-real-session.md").write_text("# real\n", encoding="utf-8")
    files = sl.session_files()
    assert [f.name for f in files] == ["2026-07-28-backend-real-session.md"]


def test_sync_concatenates_sessions_in_chronological_filename_order(sl):
    sl.STATUS_DIR.mkdir(parents=True)
    (sl.STATUS_DIR / "2026-07-27-backend-first.md").write_text("# first session\n", encoding="utf-8")
    (sl.STATUS_DIR / "2026-07-28-frontend-second.md").write_text("# second session\n", encoding="utf-8")
    sl.cmd_sync(None)
    text = sl.INDEX.read_text(encoding="utf-8")
    assert text.index("first session") < text.index("second session")
    assert "2 sessions recorded" in text


def test_sync_is_idempotent_with_no_sessions(sl):
    sl.cmd_sync(None)
    first = sl.INDEX.read_text(encoding="utf-8")
    sl.cmd_sync(None)
    second = sl.INDEX.read_text(encoding="utf-8")
    assert "0 sessions recorded" in first
    assert "0 sessions recorded" in second
