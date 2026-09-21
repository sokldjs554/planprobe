from __future__ import annotations

import json
import shutil
import time
import uuid
from pathlib import Path
from typing import Literal

from planprobe.agent.factory import build_provider
from planprobe.engine.gate import decide_gate
from planprobe.engine.patching import apply_patch
from planprobe.engine.probes import run_probe_fail_closed
from planprobe.engine.verification import run_checks
from planprobe.engine.workspace import create_workspace
from planprobe.models import (
    GateDecision,
    ImplementationPlan,
    ProbeResult,
    ProbeSpec,
    RunPacket,
    RunStage,
)
from planprobe.store import RunStore


class PlanProbePipeline:
    def __init__(self, project_root: Path, store: RunStore) -> None:
        self.project_root = project_root
        self.store = store
        self.runs_root = project_root / ".planprobe" / "runs"
        self.runs_root.mkdir(parents=True, exist_ok=True)

    def start(self, request_text: str, provider: str = "deterministic-demo") -> str:
        run_id = uuid.uuid4().hex[:12]
        self.store.create(run_id, request_text, provider)
        return run_id

    def execute(self, run_id: str) -> RunPacket:
        record = self.store.get(run_id)
        provider = build_provider(record.provider)
        run_root = self.runs_root / run_id
        started = time.perf_counter()
        try:
            workspace = create_workspace(self.project_root, run_root)
            self._event(run_id, RunStage.PLANNING, "AI가 구현 계획을 만들고 있습니다.")
            initial_plan = provider.plan(record.request_text, workspace)
            self._write(run_root / "initial-plan.json", initial_plan.model_dump())

            self._event(run_id, RunStage.EXTRACTING, "계획이 암묵적으로 의존하는 핵심 전제를 추출했습니다.")
            probes = provider.compile_probes(initial_plan, workspace)
            self._write(run_root / "probes.json", [probe.model_dump() for probe in probes])

            self._event(run_id, RunStage.PROBING, "코드를 쓰기 전에 저장소 증거로 전제를 반증하고 있습니다.")
            results = [run_probe_fail_closed(workspace, probe) for probe in probes]
            self._write(run_root / "probe-results.json", [result.model_dump() for result in results])
            gate = decide_gate(initial_plan, results)
            if gate.status == "block":
                self._event(
                    run_id,
                    RunStage.BLOCKED,
                    f"잘못되거나 확인되지 않은 핵심 전제 {len(gate.blocked_assumptions)}개를 발견해 코드 생성을 차단했습니다.",
                )

            unknown_blocked = self._unknown_load_bearing(initial_plan, results)
            if unknown_blocked:
                packet = self._blocked_packet(
                    run_id=run_id,
                    request_text=record.request_text,
                    provider_name=provider.name,
                    initial_plan=initial_plan,
                    probes=probes,
                    results=results,
                    gate=gate,
                    revised=None,
                    provider_metrics=provider.metrics(),
                    started=started,
                    reason=(
                        "확인 불가 상태의 핵심 전제가 남아 있습니다. v0.1은 증거 없이 추측해 재계획하거나 코드를 생성하지 않습니다: "
                        + ", ".join(unknown_blocked)
                    ),
                )
                self._finish_blocked(run_id, packet)
                return packet

            self._event(run_id, RunStage.REPLANNING, "실제 저장소 근거를 반영해 구현 계획을 다시 작성합니다.")
            revised = provider.replan(initial_plan, results)
            self._write(run_root / "revised-plan.json", revised.model_dump())
            replan_error = self._validate_replan(initial_plan, revised, results)
            if replan_error is not None:
                packet = self._blocked_packet(
                    run_id=run_id,
                    request_text=record.request_text,
                    provider_name=provider.name,
                    initial_plan=initial_plan,
                    probes=probes,
                    results=results,
                    gate=gate,
                    revised=revised,
                    provider_metrics=provider.metrics(),
                    started=started,
                    reason=replan_error,
                )
                self._finish_blocked(run_id, packet)
                return packet

            self._event(run_id, RunStage.CODING, "검증된 계획으로만 source patch를 생성합니다.")
            patch = provider.generate_patch(revised, workspace)
            changed = apply_patch(workspace, patch)
            self._write(run_root / "patch.json", patch.model_dump())

            self._event(run_id, RunStage.VERIFYING, "기존 계약과 신규 기능 검증을 함께 실행합니다.")
            checks = run_checks(workspace)
            passed = all(check.status == "pass" for check in checks)
            verdict: Literal["ready_with_evidence", "blocked"] = (
                "ready_with_evidence" if passed else "blocked"
            )
            packet = RunPacket(
                run_id=run_id,
                request_text=record.request_text,
                provider=provider.name,
                initial_plan=initial_plan,
                probes=probes,
                probe_results=results,
                first_gate=gate,
                revised_plan=revised,
                patch=patch,
                checks=checks,
                verdict=verdict,
                metrics={
                    "initial_assumptions": len(initial_plan.assumptions),
                    "contradicted_assumptions": sum(r.verdict == "contradicted" for r in results),
                    "unknown_assumptions": sum(r.verdict == "unknown" for r in results),
                    "source_edits_before_gate": gate.source_edits_before_gate,
                    "changed_files": len(changed),
                    "checks_passed": sum(c.status == "pass" for c in checks),
                    "checks_total": len(checks),
                    "pipeline_ms": int((time.perf_counter() - started) * 1000),
                    **provider.metrics(),
                },
                limitations=self._limitations(),
            )
            self._write(run_root / "packet.json", packet.model_dump())
            final_workspace = run_root / "final-workspace"
            if final_workspace.exists():
                shutil.rmtree(final_workspace)
            shutil.copytree(workspace, final_workspace)
            self.store.update(
                run_id,
                stage=RunStage.COMPLETE,
                status_message="검증된 계획으로 구현과 회귀 검증까지 완료했습니다." if passed else "최종 검증이 실패해 차단했습니다.",
                packet=packet,
                event={"stage": "complete", "message": f"Verdict: {verdict}"},
            )
            return packet
        except Exception as exc:
            self.store.update(
                run_id,
                stage=RunStage.FAILED,
                status_message=f"실패: {exc}",
                event={"stage": "failed", "message": str(exc)},
            )
            raise

    @staticmethod
    def _unknown_load_bearing(plan: ImplementationPlan, results: list[ProbeResult]) -> list[str]:
        by_assumption = {item.assumption_id: item for item in results}
        blocked: list[str] = []
        for assumption in plan.assumptions:
            if not assumption.load_bearing:
                continue
            result = by_assumption.get(assumption.id)
            if result is None or result.verdict == "unknown":
                blocked.append(assumption.id)
        return blocked

    @staticmethod
    def _validate_replan(
        initial: ImplementationPlan, revised: ImplementationPlan, results: list[ProbeResult]
    ) -> str | None:
        actual_evidence = {ref.id for result in results for ref in result.evidence}
        contradicted_ids = {
            result.assumption_id for result in results if result.verdict == "contradicted"
        }
        load_bearing_contradicted = {
            assumption.id
            for assumption in initial.assumptions
            if assumption.load_bearing and assumption.id in contradicted_ids
        }
        required_evidence = {
            ref.id
            for result in results
            if result.assumption_id in load_bearing_contradicted
            for ref in result.evidence
        }
        revised_evidence = set(revised.evidence_ids)
        if not revised_evidence.issubset(actual_evidence):
            invented = sorted(revised_evidence - actual_evidence)
            return "재계획이 실행되지 않은 근거 ID를 참조해 코드 생성을 차단했습니다: " + ", ".join(invented)
        if not required_evidence.issubset(revised_evidence):
            missing = sorted(required_evidence - revised_evidence)
            return "재계획이 반증 근거를 모두 연결하지 않아 코드 생성을 차단했습니다: " + ", ".join(missing)
        if any(assumption.load_bearing for assumption in revised.assumptions):
            return "재계획이 새로운 미검증 핵심 전제를 도입해 코드 생성을 차단했습니다."
        return None

    def _blocked_packet(
        self,
        *,
        run_id: str,
        request_text: str,
        provider_name: str,
        initial_plan: ImplementationPlan,
        probes: list[ProbeSpec],
        results: list[ProbeResult],
        gate: GateDecision,
        revised: ImplementationPlan | None,
        provider_metrics: dict[str, int | float | str],
        started: float,
        reason: str,
    ) -> RunPacket:
        return RunPacket(
            run_id=run_id,
            request_text=request_text,
            provider=provider_name,
            initial_plan=initial_plan,
            probes=probes,
            probe_results=results,
            first_gate=gate,
            revised_plan=revised,
            patch=None,
            checks=[],
            verdict="blocked",
            metrics={
                "initial_assumptions": len(initial_plan.assumptions),
                "contradicted_assumptions": sum(r.verdict == "contradicted" for r in results),
                "unknown_assumptions": sum(r.verdict == "unknown" for r in results),
                "source_edits_before_gate": gate.source_edits_before_gate,
                "changed_files": 0,
                "checks_passed": 0,
                "checks_total": 0,
                "pipeline_ms": int((time.perf_counter() - started) * 1000),
                "block_reason": reason,
                **provider_metrics,
            },
            limitations=self._limitations(),
        )

    def _finish_blocked(self, run_id: str, packet: RunPacket) -> None:
        run_root = self.runs_root / run_id
        self._write(run_root / "packet.json", packet.model_dump())
        reason = str(packet.metrics.get("block_reason", "검증 근거가 부족합니다."))
        self.store.update(
            run_id,
            stage=RunStage.COMPLETE,
            status_message=reason,
            packet=packet,
            event={"stage": "complete", "message": "Verdict: blocked before code"},
        )

    @staticmethod
    def _limitations() -> list[str]:
        return [
            "기본 데모 provider는 파이프라인 재현용 deterministic route이며 LLM 품질 벤치마크가 아니다.",
            "합성 LiveOps 저장소는 포트폴리오용이며 게임스프링 내부 구조나 실제 데이터를 추정하지 않는다.",
            "v0.1 probe DSL은 Python AST·정적 설정·기존 pytest 계약에 한정된다.",
            "실제 로컬 Qwen/hosted model 비교 수치는 별도 실행 artifact가 생기기 전까지 주장하지 않는다.",
        ]

    def _event(self, run_id: str, stage: RunStage, message: str) -> None:
        self.store.update(
            run_id,
            stage=stage,
            status_message=message,
            event={"stage": stage.value, "message": message},
        )

    @staticmethod
    def _write(path: Path, data: object) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(data, ensure_ascii=False, indent=2, default=str), encoding="utf-8")
