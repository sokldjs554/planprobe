from __future__ import annotations

from planprobe.models import GateDecision, ImplementationPlan, ProbeResult


def decide_gate(plan: ImplementationPlan, results: list[ProbeResult]) -> GateDecision:
    blocked: list[str] = []
    for assumption in plan.assumptions:
        if not assumption.load_bearing:
            continue
        matches = [result for result in results if result.assumption_id == assumption.id]
        if not matches or any(result.verdict != "verified" for result in matches):
            blocked.append(assumption.id)
    if blocked:
        return GateDecision(
            status="block",
            blocked_assumptions=blocked,
            reason="검증되지 않았거나 실제 저장소와 모순되는 핵심 전제가 있어 코드 생성을 허용하지 않습니다.",
            source_edits_before_gate=0,
        )
    return GateDecision(
        status="pass",
        blocked_assumptions=[],
        reason="모든 핵심 전제가 저장소 증거로 검증되었습니다.",
        source_edits_before_gate=0,
    )
