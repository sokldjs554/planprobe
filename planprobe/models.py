from __future__ import annotations

from enum import StrEnum
from typing import Any, Literal

from pydantic import BaseModel, Field, model_validator


class RunStage(StrEnum):
    QUEUED = "queued"
    PLANNING = "planning"
    EXTRACTING = "extracting_assumptions"
    PROBING = "probing"
    BLOCKED = "blocked_before_code"
    REPLANNING = "replanning"
    CODING = "coding"
    VERIFYING = "verifying"
    COMPLETE = "complete"
    FAILED = "failed"


class PlanStep(BaseModel):
    id: str
    title: str
    detail: str
    target_files: list[str] = Field(default_factory=list)


class Assumption(BaseModel):
    id: str
    claim: str
    load_bearing: bool = True
    why_it_matters: str
    plan_step_ids: list[str]


class ImplementationPlan(BaseModel):
    version: int
    summary: str
    steps: list[PlanStep]
    assumptions: list[Assumption]
    evidence_ids: list[str] = Field(default_factory=list)


ProbeKind = Literal["mapping_all_equal", "field_shape", "pytest_node", "ast_order", "function_signature"]


class ProbeSpec(BaseModel):
    id: str
    assumption_id: str
    kind: ProbeKind
    target_path: str
    params: dict[str, Any]
    rationale: str

    @model_validator(mode="after")
    def validate_probe_contract(self) -> ProbeSpec:
        normalized_target = self.target_path.replace("\\", "/").strip()
        if (
            not normalized_target
            or normalized_target.startswith("/")
            or ".." in normalized_target.split("/")
        ):
            raise ValueError("target_path must be a relative repository path")

        required_by_kind: dict[ProbeKind, set[str]] = {
            "mapping_all_equal": {"symbol", "expected_value"},
            "field_shape": {"class", "field", "expected_shape"},
            "pytest_node": {"node"},
            "ast_order": {"function", "before", "after"},
            "function_signature": {"function", "expected_params"},
        }
        missing = sorted(key for key in required_by_kind[self.kind] if key not in self.params)
        if missing:
            raise ValueError(f"{self.kind} probe is missing params: {missing}")

        if self.kind == "field_shape" and self.params["expected_shape"] not in {"scalar", "list"}:
            raise ValueError("field_shape expected_shape must be scalar or list")

        if self.kind == "pytest_node":
            node = str(self.params["node"])
            prefix = f"{normalized_target}::"
            if not node.startswith(prefix):
                raise ValueError("pytest_node params.node must start with target_path::")
            test_name = node.rsplit("::", 1)[-1]
            if not test_name.startswith("test_"):
                raise ValueError("pytest_node must reference an exact test_* function")

        if self.kind == "function_signature":
            expected_params = self.params["expected_params"]
            if not isinstance(expected_params, list) or not all(isinstance(item, str) for item in expected_params):
                raise ValueError("function_signature expected_params must be a list of strings")
            if self.params.get("mode", "subset") not in {"subset", "exact"}:
                raise ValueError("function_signature mode must be subset or exact")

        return self


class EvidenceRef(BaseModel):
    id: str
    path: str
    line_start: int | None = None
    line_end: int | None = None
    snippet: str


AssumptionVerdict = Literal["verified", "contradicted", "unknown"]


class ProbeResult(BaseModel):
    probe_id: str
    assumption_id: str
    verdict: AssumptionVerdict
    observed: str
    expected: str
    evidence: list[EvidenceRef]
    duration_ms: float


class GateDecision(BaseModel):
    status: Literal["pass", "block"]
    blocked_assumptions: list[str]
    reason: str
    source_edits_before_gate: int = 0


class PatchEdit(BaseModel):
    path: str
    old: str
    new: str


class PatchSet(BaseModel):
    summary: str
    edits: list[PatchEdit]


class CheckResult(BaseModel):
    name: str
    status: Literal["pass", "fail"]
    detail: str
    duration_ms: int


class RunPacket(BaseModel):
    run_id: str
    request_text: str
    provider: str
    initial_plan: ImplementationPlan
    probes: list[ProbeSpec]
    probe_results: list[ProbeResult]
    first_gate: GateDecision
    revised_plan: ImplementationPlan | None
    patch: PatchSet | None
    checks: list[CheckResult]
    verdict: Literal["ready_with_evidence", "blocked"]
    metrics: dict[str, int | float | str]
    limitations: list[str]


class PreflightPacket(BaseModel):
    request_text: str
    provider: str
    workspace: str
    initial_plan: ImplementationPlan
    probes: list[ProbeSpec]
    probe_results: list[ProbeResult]
    gate: GateDecision
    metrics: dict[str, int | float | str]
    limitations: list[str]


class RunRecord(BaseModel):
    id: str
    request_text: str
    provider: str
    stage: RunStage
    status_message: str
    events: list[dict[str, Any]] = Field(default_factory=list)
    packet: RunPacket | None = None
