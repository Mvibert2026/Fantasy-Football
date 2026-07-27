import json

import numpy as np
import pytest

import preregistration as prereg


VALID = """---
id: PR-999
title: A test
hypothesis: Something is true
metric: incremental adjusted R2
confirmation_threshold: adjusted p <= 0.05 and delta R2 >= 0.01
status: REGISTERED
---

Body prose.
"""


@pytest.fixture
def prereg_dir(tmp_path):
    d = tmp_path / "preregistration"
    d.mkdir()
    return d


# ------------------------------- loading -------------------------------


def test_missing_preregistration_raises_not_warns(prereg_dir):
    with pytest.raises(prereg.PreRegistrationMissing):
        prereg.require_preregistration("PR-404", directory=prereg_dir)


def test_missing_directory_raises(tmp_path):
    with pytest.raises(prereg.PreRegistrationMissing):
        prereg.require_preregistration("PR-001", directory=tmp_path / "nope")


def test_valid_preregistration_loads_all_required_fields(prereg_dir):
    (prereg_dir / "PR-999-a-test.md").write_text(VALID, encoding="utf-8")
    p = prereg.require_preregistration("PR-999", directory=prereg_dir)
    assert p.id == "PR-999"
    assert p.metric == "incremental adjusted R2"
    assert p.status == "REGISTERED"


def test_incomplete_preregistration_is_rejected(prereg_dir):
    incomplete = "---\nid: PR-998\ntitle: Missing things\nstatus: REGISTERED\n---\n"
    (prereg_dir / "PR-998-x.md").write_text(incomplete, encoding="utf-8")
    with pytest.raises(prereg.PreRegistrationInvalid, match="missing required field"):
        prereg.require_preregistration("PR-998", directory=prereg_dir)


def test_multiline_frontmatter_values_are_joined(prereg_dir):
    text = VALID.replace(
        "hypothesis: Something is true",
        "hypothesis: Something is true\n  and continues here",
    )
    (prereg_dir / "PR-999-a-test.md").write_text(text, encoding="utf-8")
    p = prereg.require_preregistration("PR-999", directory=prereg_dir)
    assert "continues here" in p.hypothesis


def test_the_real_pr001_file_is_valid():
    """The shipped pre-registration must actually parse."""
    p = prereg.require_preregistration("PR-001")
    assert "carry" in p.title.lower()
    assert p.confirmation_threshold


def test_pr001_stays_frozen_while_the_alpha_track_is_closed():
    """PR-001 is an ALPHA-track test and the alpha track is structurally closed
    for 2026 (ADR-026): with 4 development seasons the exact sign test floors at
    p=0.125, so no factor can reach significance regardless of merit.

    This guards against a future session quietly flipping it back to REGISTERED
    and running it. Reopening is legitimate only when development coverage
    reaches n>=6 seasons -- at which point this test should be updated
    deliberately, not deleted to make a red bar go away."""
    p = prereg.require_preregistration("PR-001")
    assert p.status == "FROZEN-FOR-FUTURE"
    assert p.fields.get("frozen_reason")


def test_run_preregistrations_record_their_result():
    """PR-002 and PR-003 were executed; both must carry a result line so a
    reader cannot mistake a run test for a pending one."""
    for pid in ("PR-002", "PR-003"):
        p = prereg.require_preregistration(pid)
        assert p.status == "RUN"
        assert p.fields.get("result"), f"{pid} is RUN but records no result"


# ------------------------------- run log -------------------------------


def test_recording_a_run_appends_to_the_log(tmp_path):
    log = tmp_path / "runs.jsonl"
    prereg.record_test_run("PR-001", "delta_r2", 0.04, 0.02, [2022, 2023], log_path=log)
    prereg.record_test_run("PR-002", "delta_r2", 0.60, 0.00, [2022, 2023], log_path=log)
    assert prereg.total_tests_run(log) == 2
    entries = prereg.all_test_runs(log)
    assert entries[0]["test_id"] == "PR-001"
    assert entries[1]["p_value"] == 0.60


def test_run_log_records_null_results_too(tmp_path):
    """A test run and not recorded shrinks the FDR denominator."""
    log = tmp_path / "runs.jsonl"
    prereg.record_test_run("PR-003", "delta_r2", None, None, [2022], notes="no result", log_path=log)
    assert prereg.total_tests_run(log) == 1
    assert prereg.all_test_runs(log)[0]["p_value"] is None


def test_empty_log_counts_zero(tmp_path):
    assert prereg.total_tests_run(tmp_path / "absent.jsonl") == 0


# ------------------------------- BH -------------------------------


def test_bh_leaves_a_single_small_p_significant():
    r = prereg.benjamini_hochberg([0.001], alpha=0.05)
    assert r.rejected == [True]
    assert r.adjusted[0] == pytest.approx(0.001)


def test_bh_is_less_strict_than_bonferroni():
    ps = [0.01, 0.02, 0.03, 0.04, 0.05]
    r = prereg.benjamini_hochberg(ps, alpha=0.05)
    # Bonferroni would reject none of these at 0.05/5 = 0.01 except the first
    assert sum(r.rejected) > 1


def test_bh_adjusted_values_are_monotone_in_p():
    ps = [0.001, 0.01, 0.2, 0.5, 0.9]
    r = prereg.benjamini_hochberg(ps, alpha=0.05)
    ordered = [a for _, a in sorted(zip(ps, r.adjusted))]
    assert ordered == sorted(ordered)


def test_bh_adjusted_values_never_exceed_one():
    r = prereg.benjamini_hochberg([0.6, 0.7, 0.8, 0.99], alpha=0.05)
    assert all(a <= 1.0 for a in r.adjusted)


def test_bh_preserves_input_order():
    ps = [0.5, 0.001, 0.2]
    r = prereg.benjamini_hochberg(ps, alpha=0.05)
    assert r.p_values == ps
    assert r.adjusted[1] < r.adjusted[0]


def test_correcting_across_the_true_total_is_stricter_than_the_subset():
    """The core anti-p-hacking property: reporting 3 of 30 tests must not be
    corrected as though only 3 were run."""
    ps = [0.01, 0.02, 0.03]
    subset = prereg.benjamini_hochberg(ps, alpha=0.05)
    full = prereg.benjamini_hochberg(ps, alpha=0.05, n_total=30)
    assert all(f >= s for f, s in zip(full.adjusted, subset.adjusted))
    assert sum(full.rejected) < sum(subset.rejected)
    assert "full run log" in full.note


def test_n_total_smaller_than_supplied_p_values_is_rejected():
    with pytest.raises(ValueError):
        prereg.benjamini_hochberg([0.01, 0.02, 0.03], n_total=2)


def test_correct_against_full_log_uses_the_persistent_count(tmp_path):
    log = tmp_path / "runs.jsonl"
    for i in range(20):
        prereg.record_test_run(f"PR-{i:03d}", "m", 0.5, 0.0, [2022], log_path=log)
    r = prereg.correct_against_full_log([0.01, 0.02], alpha=0.05, log_path=log)
    assert r.n_total_considered == 20


def test_empty_p_value_list_is_handled():
    r = prereg.benjamini_hochberg([], alpha=0.05)
    assert r.rejected == []
    assert "no p-values" in r.note


# =========================== ADR-C: registration format (PR-004+) ===========================

CONFIRMATORY_TEXT = """---
id: PR-900
test_registry_id: T-900
family: F-TEST
mode: confirmatory
question: >
  Does the widget move the needle?
metric: flip_rate_top1
threshold: "adopt iff flip_rate(10) < 0.02"
data_scope: {seasons: [2021, 2022, 2023, 2024], holdout_unsealed: false}
frozen: {at: 2026-07-26T14:02:00Z, code_sha: abc123, seed: 42, content_hash: sha256:PLACEHOLDER}
---

Body prose.
"""

EXPLORATORY_TEXT = """---
id: PR-901
mode: exploratory
question: Poking at whether X correlates with Y at all.
frozen: {at: 2026-07-26T09:00:00Z, code_sha: abc123, seed: 1, content_hash: sha256:PLACEHOLDER}
---

Body prose.
"""


@pytest.fixture
def v2_dir(tmp_path):
    d = tmp_path / "preregistration"
    d.mkdir()
    return d


def test_confirmatory_registration_loads_all_nine_fields(v2_dir):
    (v2_dir / "PR-900-widget.md").write_text(CONFIRMATORY_TEXT, encoding="utf-8")
    reg = prereg.load_registration("PR-900", directory=v2_dir)
    assert reg.id == "PR-900"
    assert reg.test_registry_id == "T-900"
    assert reg.family == "F-TEST"
    assert reg.mode == "confirmatory"
    assert "needle" in reg.question
    assert reg.metric == "flip_rate_top1"
    assert reg.data_scope == {"seasons": [2021, 2022, 2023, 2024], "holdout_unsealed": False}
    assert reg.frozen["code_sha"] == "abc123"
    assert reg.resampling_unit == "season"  # confirmatory default
    assert reg.is_confirmatory


def test_exploratory_registration_is_nearly_free(v2_dir):
    (v2_dir / "PR-901-poke.md").write_text(EXPLORATORY_TEXT, encoding="utf-8")
    reg = prereg.load_registration("PR-901", directory=v2_dir)
    assert reg.mode == "exploratory"
    assert not reg.is_confirmatory


def test_confirmatory_missing_a_required_field_is_rejected(v2_dir):
    text = CONFIRMATORY_TEXT.replace("metric: flip_rate_top1\n", "")
    (v2_dir / "PR-900-widget.md").write_text(text, encoding="utf-8")
    with pytest.raises(prereg.RegistrationInvalid, match="missing required field"):
        prereg.load_registration("PR-900", directory=v2_dir)


def test_missing_registration_raises(v2_dir):
    with pytest.raises(prereg.RegistrationMissing):
        prereg.load_registration("PR-404", directory=v2_dir)


def test_non_season_resampling_unit_requires_power_note(v2_dir):
    text = CONFIRMATORY_TEXT.replace(
        "frozen: {at:",
        "resampling_unit: draft\nfrozen: {at:",
    )
    (v2_dir / "PR-900-widget.md").write_text(text, encoding="utf-8")
    with pytest.raises(prereg.RegistrationInvalid, match="power_note"):
        prereg.load_registration("PR-900", directory=v2_dir)

    text2 = text.replace(
        "resampling_unit: draft\n", "resampling_unit: draft\npower_note: justified in writing\n"
    )
    (v2_dir / "PR-900-widget.md").write_text(text2, encoding="utf-8")
    reg = prereg.load_registration("PR-900", directory=v2_dir)
    assert reg.resampling_unit == "draft"


def test_require_confirmatory_gates_a_declared_exploratory_registration(v2_dir):
    (v2_dir / "PR-901-poke.md").write_text(EXPLORATORY_TEXT, encoding="utf-8")
    with pytest.raises(prereg.RegistrationInvalid):
        prereg.require_confirmatory("PR-901", directory=v2_dir)


def test_require_confirmatory_passes_a_valid_confirmatory_registration(v2_dir):
    (v2_dir / "PR-900-widget.md").write_text(CONFIRMATORY_TEXT, encoding="utf-8")
    reg = prereg.require_confirmatory("PR-900", directory=v2_dir)
    assert reg.id == "PR-900"


# =========================== ADR-C: exploratory artifact guard ===========================


def test_exploratory_artifact_may_not_carry_a_p_value():
    with pytest.raises(prereg.RegistrationInvalid):
        prereg.validate_exploratory_artifact("exploratory", {"p_value": 0.02})


def test_exploratory_artifact_may_carry_a_point_estimate():
    prereg.validate_exploratory_artifact("exploratory", {"point_estimate": 1.23})


def test_confirmatory_artifact_is_not_checked():
    # the guard is scoped to exploratory mode; confirmatory results may
    # legitimately carry a p-value.
    prereg.validate_exploratory_artifact("confirmatory", {"p_value": 0.02})


# =========================== ADR-C: content hash ===========================


def test_content_hash_is_stable_across_reads(v2_dir):
    path = v2_dir / "PR-900-widget.md"
    path.write_text(CONFIRMATORY_TEXT, encoding="utf-8")
    h1 = prereg.compute_content_hash(path)
    h2 = prereg.compute_content_hash(path)
    assert h1 == h2
    assert h1.startswith("sha256:")


def test_content_hash_changes_when_body_changes(v2_dir):
    path = v2_dir / "PR-900-widget.md"
    path.write_text(CONFIRMATORY_TEXT, encoding="utf-8")
    h1 = prereg.compute_content_hash(path)
    path.write_text(CONFIRMATORY_TEXT + "\nMore prose.\n", encoding="utf-8")
    h2 = prereg.compute_content_hash(path)
    assert h1 != h2


# =========================== ADR-C: amendments (the rule with teeth) ===========================


def test_amendment_without_data_seen_keeps_mode_confirmatory(v2_dir):
    path = v2_dir / "PR-900-widget.md"
    path.write_text(CONFIRMATORY_TEXT, encoding="utf-8")
    reg = prereg.record_amendment(
        "PR-900",
        fields_changed=["threshold"],
        reason="grid step made 0.05 non-discriminating, changed before any run",
        data_seen=False,
        directory=v2_dir,
    )
    assert reg.mode == "confirmatory"
    assert reg.is_confirmatory
    assert len(reg.amendments) == 1
    assert reg.amendments[0]["data_seen"] is False


def test_amendment_with_data_seen_irreversibly_demotes_to_exploratory(v2_dir):
    path = v2_dir / "PR-900-widget.md"
    path.write_text(CONFIRMATORY_TEXT, encoding="utf-8")
    reg = prereg.record_amendment(
        "PR-900",
        fields_changed=["threshold"],
        reason="changed after peeking at an interim result",
        data_seen=True,
        directory=v2_dir,
    )
    assert reg.mode == "exploratory"
    assert reg.effective_mode == "exploratory"
    assert not reg.is_confirmatory
    # and it stays that way on a fresh reload from disk -- not just an
    # in-memory computed property.
    reloaded = prereg.load_registration("PR-900", directory=v2_dir)
    assert reloaded.mode == "exploratory"


def test_amendment_updates_the_content_hash_so_check_stays_clean(v2_dir):
    path = v2_dir / "PR-900-widget.md"
    path.write_text(CONFIRMATORY_TEXT, encoding="utf-8")
    prereg.record_amendment(
        "PR-900", fields_changed=["threshold"], reason="pre-run fix", data_seen=False,
        directory=v2_dir,
    )
    assert prereg.check_registration("PR-900", directory=v2_dir) == []


def test_silent_edit_without_an_amendment_fails_check(v2_dir):
    path = v2_dir / "PR-900-widget.md"
    path.write_text(CONFIRMATORY_TEXT, encoding="utf-8")
    reg = prereg.load_registration("PR-900", directory=v2_dir)
    # simulate a silent edit: file mutated with no matching amendments entry
    path.write_text(CONFIRMATORY_TEXT.replace("flip_rate_top1", "some_other_metric"), encoding="utf-8")
    violations = prereg.check_registration("PR-900", directory=v2_dir)
    assert any("content hash mismatch" in v for v in violations)


def test_record_amendment_requires_a_reason(v2_dir):
    path = v2_dir / "PR-900-widget.md"
    path.write_text(CONFIRMATORY_TEXT, encoding="utf-8")
    with pytest.raises(ValueError):
        prereg.record_amendment(
            "PR-900", fields_changed=["threshold"], reason="  ", data_seen=False,
            directory=v2_dir,
        )


# =========================== ADR-C: family manifests (BH denominator) ===========================


@pytest.fixture
def families_dir(tmp_path):
    d = tmp_path / "families"
    return d


def test_open_family_declares_m_before_any_test_runs(families_dir):
    fam = prereg.open_family("F-TEST", m=3, directory=families_dir)
    assert fam.m == 3
    assert fam.status == "open"


def test_register_confirmatory_test_increments_m(families_dir):
    prereg.open_family("F-TEST", m=3, directory=families_dir)
    fam = prereg.register_confirmatory_test("F-TEST", directory=families_dir)
    assert fam.m == 4
    assert fam.status == "open"


def test_register_confirmatory_test_reopens_a_closed_family(families_dir):
    prereg.open_family("F-TEST", m=3, directory=families_dir)
    path = families_dir / "F-TEST.yaml"
    path.write_text("id: F-TEST\nm: 3\nstatus: closed\n", encoding="utf-8")
    fam = prereg.register_confirmatory_test("F-TEST", directory=families_dir)
    assert fam.status == "open"
    assert fam.m == 4


def test_closed_unsealed_family_never_reopens(families_dir):
    prereg.open_family("F-TEST", m=3, directory=families_dir)
    prereg.close_family_after_unseal("F-TEST", directory=families_dir)
    with pytest.raises(prereg.FamilyClosed):
        prereg.register_confirmatory_test("F-TEST", directory=families_dir)


def test_missing_family_raises(families_dir):
    with pytest.raises(prereg.FamilyMissing):
        prereg.load_family("F-NOPE", directory=families_dir)


# =========================== ADR-C: unseal log ===========================


def test_unseal_is_logged_false_when_no_log_exists(tmp_path):
    assert prereg.unseal_is_logged("PR-900", log_path=tmp_path / "UNSEAL_LOG.md") is False


def test_append_unseal_log_then_is_logged(tmp_path):
    log = tmp_path / "UNSEAL_LOG.md"
    prereg.append_unseal_log("PR-900", family="F-TEST", reason="pre-registered final look",
                              approver="founder", log_path=log)
    assert prereg.unseal_is_logged("PR-900", log_path=log) is True
    assert prereg.unseal_is_logged("PR-999", log_path=log) is False


def test_append_unseal_log_requires_reason_and_approver(tmp_path):
    log = tmp_path / "UNSEAL_LOG.md"
    with pytest.raises(ValueError):
        prereg.append_unseal_log("PR-900", family="F-TEST", reason="", approver="founder", log_path=log)
    with pytest.raises(ValueError):
        prereg.append_unseal_log("PR-900", family="F-TEST", reason="ok", approver="", log_path=log)
