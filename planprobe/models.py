from __future__ import annotations

from enum import StrEnum
from typing import Any, Literal

from pydantic import BaseModel, Field


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
