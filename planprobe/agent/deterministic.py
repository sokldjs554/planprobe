from __future__ import annotations

from pathlib import Path

from planprobe.agent.base import AgentProvider
from planprobe.models import (
    Assumption,
    ImplementationPlan,
    PatchEdit,
    PatchSet,
    PlanStep,
    ProbeResult,
    ProbeSpec,
)


class DeterministicDemoProvider(AgentProvider):
    name = "deterministic-demo"

    def plan(self, request_text: str, workspace: Path) -> ImplementationPlan:
        _ = workspace
        return ImplementationPlan(
            version=1,
            summary="연속 접속 보너스를 추가하되 기존 재시도 안전성과 이벤트 시간 판정을 유지한다.",
            steps=[
                PlanStep(
                    id="P1",
                    title="요청 정규화",
                    detail="단일 region과 UTC 일정 기준으로 보상 가능 여부를 계산한다.",
                    target_files=["synthetic_app/liveops_service/rewards.py"],
                ),
                PlanStep(
                    id="P2",
                    title="연속 접속 보너스 계산",
                    detail="streak_days를 사용해 보너스를 계산하고 기존 coins 응답을 유지한다.",
                    target_files=[
                        "synthetic_app/liveops_service/models.py",
                        "synthetic_app/liveops_service/rewards.py",
                    ],
                ),
                PlanStep(
                    id="P3",
                    title="기존 재시도 계약 보존",
                    detail="동일 idempotency_key는 기존 receipt를 재사용하고 ledger 중복 기록을 만들지 않는다.",
                    target_files=["synthetic_app/liveops_service/rewards.py"],
                ),
            ],
            assumptions=[
                Assumption(
                    id="A-UTC",
                    claim="모든 이벤트 일정은 UTC 기준으로 저장되고 판정된다.",
                    why_it_matters="이 전제가 틀리면 지역별 이벤트 노출 시간이 바뀔 수 있다.",
                    plan_step_ids=["P1"],
                ),
                Assumption(
                    id="A-REGION",
                    claim="보상 요청 하나에는 region이 하나만 존재한다.",
                    why_it_matters="이 전제가 틀리면 일부 지역이 누락되거나 잘못된 이벤트 판정이 발생한다.",
                    plan_step_ids=["P1"],
                ),
                Assumption(
                    id="A-IDEMPOTENCY",
                    claim="동일 idempotency_key 재시도는 기존 receipt를 반환하고 ledger를 추가하지 않는다.",
                    why_it_matters="보상이 중복 지급될 수 있으므로 반드시 보존해야 한다.",
                    plan_step_ids=["P3"],
                ),
                Assumption(
                    id="A-ORDER",
                    claim="보상 receipt가 계산된 뒤에만 ledger write가 수행된다.",
                    why_it_matters="부분 실패나 잘못된 금액 기록을 막기 위한 순서 계약이다.",
                    plan_step_ids=["P2", "P3"],
                ),
            ],
        )

    def compile_probes(self, plan: ImplementationPlan, workspace: Path) -> list[ProbeSpec]:
        _ = plan, workspace
        return [
            ProbeSpec(
                id="PR-UTC",
                assumption_id="A-UTC",
                kind="mapping_all_equal",
                target_path="synthetic_app/liveops_service/config.py",
                params={"symbol": "REGION_TIMEZONES", "expected_value": "UTC"},
                rationale="시간 정책을 추측하지 않고 실제 region→timezone mapping을 검사한다.",
            ),
            ProbeSpec(
                id="PR-REGION",
                assumption_id="A-REGION",
                kind="field_shape",
                target_path="synthetic_app/liveops_service/models.py",
                params={"class": "RewardRequest", "field": "regions", "expected_shape": "scalar"},
                rationale="요청 스키마의 타입 구조를 AST로 읽어 단일/복수 지역 여부를 판정한다.",
            ),
            ProbeSpec(
                id="PR-IDEMPOTENCY",
                assumption_id="A-IDEMPOTENCY",
                kind="pytest_node",
                target_path="synthetic_app/liveops_service/tests/test_rewards.py",
                params={
                    "node": "synthetic_app/liveops_service/tests/test_rewards.py::test_duplicate_request_returns_same_receipt_and_single_ledger_entry"
                },
                rationale="중복 재시도 계약은 설명이 아니라 기존 실행 테스트로 확인한다.",
            ),
            ProbeSpec(
                id="PR-ORDER",
                assumption_id="A-ORDER",
                kind="ast_order",
                target_path="synthetic_app/liveops_service/rewards.py",
                params={"function": "claim_reward", "before": "RewardReceipt", "after": "append"},
                rationale="receipt 구성과 ledger append의 실제 소스 순서를 AST line으로 확인한다.",
            ),
        ]

    def replan(self, plan: ImplementationPlan, results: list[ProbeResult]) -> ImplementationPlan:
        evidence_ids = [ref.id for result in results for ref in result.evidence]
        return ImplementationPlan(
            version=plan.version + 1,
            summary="저장소 증거에 맞춰 지역별 timezone·다중 region·idempotency 계약을 보존한 뒤 보너스를 추가한다.",
            evidence_ids=evidence_ids,
            steps=[
                PlanStep(
                    id="P1R",
                    title="기존 지역별 시간 판정 유지",
                    detail="각 region을 기존 is_event_open()에 개별 전달해 REGION_TIMEZONES 정책을 그대로 사용한다.",
                    target_files=["synthetic_app/liveops_service/rewards.py"],
                ),
                PlanStep(
                    id="P2R",
                    title="다중 region 계약 유지",
                    detail="regions: list[str]를 유지하고 eligible_regions 계산 결과를 기존 응답에 보존한다.",
                    target_files=["synthetic_app/liveops_service/rewards.py"],
                ),
                PlanStep(
                    id="P3R",
                    title="보너스 계산을 ledger write 전에 삽입",
                    detail="streak_bonus와 total_coins를 receipt 생성 전에 계산하고 기존 coins는 total_coins와 동일하게 유지한다.",
                    target_files=[
                        "synthetic_app/liveops_service/models.py",
                        "synthetic_app/liveops_service/rewards.py",
                    ],
                ),
                PlanStep(
                    id="P4R",
                    title="재시도 계약 보존",
                    detail="기존 idempotency guard는 함수 최상단에 유지해 동일 요청의 재계산·중복 ledger write를 막는다.",
                    target_files=["synthetic_app/liveops_service/rewards.py"],
                ),
            ],
            assumptions=[],
        )

    def generate_patch(self, plan: ImplementationPlan, workspace: Path) -> PatchSet:
        _ = plan, workspace
        models_old = '''class RewardReceipt(BaseModel):\n    claim_id: str\n    coins: int\n    eligible_regions: list[str]\n'''
        models_new = '''class RewardReceipt(BaseModel):\n    claim_id: str\n    coins: int\n    base_coins: int\n    streak_bonus: int\n    total_coins: int\n    eligible_regions: list[str]\n'''
        rewards_old = '''    eligible_regions = [region for region in request.regions if is_event_open(region, request.now_utc)]\n    base_coins = BASE_COINS if eligible_regions else 0\n\n    receipt = RewardReceipt(\n        claim_id=str(uuid4()),\n        coins=base_coins,\n        eligible_regions=eligible_regions,\n    )\n'''
        rewards_new = '''    eligible_regions = [region for region in request.regions if is_event_open(region, request.now_utc)]\n    base_coins = BASE_COINS if eligible_regions else 0\n    streak_bonus = min(request.streak_days, 7) * 10 if eligible_regions else 0\n    total_coins = base_coins + streak_bonus\n\n    receipt = RewardReceipt(\n        claim_id=str(uuid4()),\n        coins=total_coins,\n        base_coins=base_coins,\n        streak_bonus=streak_bonus,\n        total_coins=total_coins,\n        eligible_regions=eligible_regions,\n    )\n'''
        return PatchSet(
            summary="지역/시간/idempotency 계약을 보존하면서 연속 접속 보너스를 추가한다.",
            edits=[
                PatchEdit(path="synthetic_app/liveops_service/models.py", old=models_old, new=models_new),
                PatchEdit(path="synthetic_app/liveops_service/rewards.py", old=rewards_old, new=rewards_new),
            ],
        )
