from __future__ import annotations

from planprobe.models import GateDecision, ImplementationPlan, ProbeResult


def decide_gate(plan: ImplementationPlan, results: list[ProbeResult]) -> GateDecision:
    by_assumption = {result.assumption_id: result for result in results}
    blocked: list[str] = []
    for assumption in plan.assumptions:
        if not assumption.load_bearing:
            continue
        result = by_assumption.get(assumption.id)
        if result is None or result.verdict in {"contradicted", "unknown"}:
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
