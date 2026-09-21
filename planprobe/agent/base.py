from __future__ import annotations

from abc import ABC, abstractmethod
from pathlib import Path

from planprobe.models import ImplementationPlan, PatchSet, ProbeResult, ProbeSpec


class AgentProvider(ABC):
    name: str

    def metrics(self) -> dict[str, int | float | str]:
        return {"llm_calls": 0}

    @abstractmethod
    def plan(self, request_text: str, workspace: Path) -> ImplementationPlan: ...

    @abstractmethod
    def compile_probes(self, plan: ImplementationPlan, workspace: Path) -> list[ProbeSpec]: ...

    @abstractmethod
    def replan(self, plan: ImplementationPlan, results: list[ProbeResult]) -> ImplementationPlan: ...

    @abstractmethod
    def generate_patch(self, plan: ImplementationPlan, workspace: Path) -> PatchSet: ...
