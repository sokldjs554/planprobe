from __future__ import annotations

from pathlib import Path

from planprobe.engine.pipeline import PlanProbePipeline
from planprobe.models import (
    Assumption,
    EvidenceRef,
    ImplementationPlan,
    PlanStep,
    ProbeResult,
)
from planprobe.store import RunStore


def _plan(*, evidence_ids: list[str] | None = None, assumptions: list[Assumption] | None = None) -> ImplementationPlan:
    return ImplementationPlan(
        version=1,
        summary="plan",
        steps=[PlanStep(id="P1", title="step", detail="detail")],
        assumptions=assumptions or [],
        evidence_ids=evidence_ids or [],
    )


def test_unknown_load_bearing_premise_stays_fail_closed(tmp_path: Path) -> None:
    pipeline = PlanProbePipeline(tmp_path, RunStore(tmp_path / "runs.db"))
    assumption = Assumption(
        id="A1",
        claim="fact",
        why_it_matters="load bearing",
        plan_step_ids=["P1"],
    )
    initial = _plan(assumptions=[assumption])
    result = ProbeResult(
        probe_id="PR1",
        assumption_id="A1",
        verdict="unknown",
        observed="no evidence",
        expected="fact",
        evidence=[],
        duration_ms=0.1,
    )
    assert pipeline._unknown_load_bearing(initial, [result]) == ["A1"]


def test_replan_cannot_invent_evidence_ids(tmp_path: Path) -> None:
    pipeline = PlanProbePipeline(tmp_path, RunStore(tmp_path / "runs.db"))
    assumption = Assumption(
        id="A1",
        claim="fact",
        why_it_matters="load bearing",
        plan_step_ids=["P1"],
    )
    initial = _plan(assumptions=[assumption])
    result = ProbeResult(
        probe_id="PR1",
        assumption_id="A1",
        verdict="contradicted",
        observed="false",
        expected="true",
        evidence=[EvidenceRef(id="EV1", path="app.py", line_start=1, line_end=1, snippet="x = 1")],
        duration_ms=0.1,
    )
    revised = _plan(evidence_ids=["EV-NOT-RUN"])
    error = pipeline._validate_replan(initial, revised, [result])
    assert error is not None
    assert "실행되지 않은 근거" in error


def test_replan_must_carry_contradiction_evidence_and_no_new_load_bearing_premises(tmp_path: Path) -> None:
    pipeline = PlanProbePipeline(tmp_path, RunStore(tmp_path / "runs.db"))
    assumption = Assumption(
        id="A1",
        claim="fact",
        why_it_matters="load bearing",
        plan_step_ids=["P1"],
    )
    initial = _plan(assumptions=[assumption])
    result = ProbeResult(
        probe_id="PR1",
        assumption_id="A1",
        verdict="contradicted",
        observed="false",
        expected="true",
        evidence=[EvidenceRef(id="EV1", path="app.py", line_start=1, line_end=1, snippet="x = 1")],
        duration_ms=0.1,
    )
    missing = _plan(evidence_ids=[])
    assert "반증 근거" in (pipeline._validate_replan(initial, missing, [result]) or "")

    new_assumption = Assumption(
        id="A2",
        claim="new unverified fact",
        why_it_matters="load bearing",
        plan_step_ids=["P1"],
    )
    unsafe = _plan(evidence_ids=["EV1"], assumptions=[new_assumption])
    assert "새로운 미검증 핵심 전제" in (pipeline._validate_replan(initial, unsafe, [result]) or "")

    safe = _plan(evidence_ids=["EV1"])
    assert pipeline._validate_replan(initial, safe, [result]) is None
