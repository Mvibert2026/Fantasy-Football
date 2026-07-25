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
    assert p.status == "REGISTERED"
    assert "carry" in p.title.lower()
    assert p.confirmation_threshold


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
