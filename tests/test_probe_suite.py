from __future__ import annotations

from planprobe.eval.probe_suite import build_probe_cases, run_probe_suite


def test_frozen_probe_suite_has_six_classes_and_twenty_four_cases() -> None:
    cases = build_probe_cases()
    assert len(cases) == 24
    assert len({case.premise_class for case in cases}) == 6
    counts = {name: sum(case.premise_class == name for case in cases) for name in {case.premise_class for case in cases}}
    assert set(counts.values()) == {4}


def test_frozen_probe_suite_matches_expected_repository_facts() -> None:
    result = run_probe_suite()
    summary = result["summary"]
    assert summary["cases"] == 24
    assert summary["verdict_correct"] == 24
    assert summary["gate_correct"] == 24
    assert summary["source_unchanged"] == 24
    assert summary["false_blocks"] == 0
    assert summary["missed_blocks"] == 0
    assert summary["unknown_results"] == 6
