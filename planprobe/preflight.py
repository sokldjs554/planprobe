from __future__ import annotations

import time
from pathlib import Path

from planprobe.agent.factory import build_provider
from planprobe.engine.gate import decide_gate
from planprobe.engine.probes import run_probe_fail_closed
from planprobe.models import PreflightPacket


def run_preflight(
    workspace: Path,
    request_text: str,
    provider_name: str,
) -> PreflightPacket:
    """Run the pre-code half of PlanProbe without modifying source files."""

    root = workspace.expanduser().resolve()
    if not root.exists() or not root.is_dir():
        raise ValueError(f"workspace must be an existing directory: {root}")

    started = time.perf_counter()
    provider = build_provider(provider_name)
    plan = provider.plan(request_text, root)
    probes = provider.compile_probes(plan, root)
    results = [run_probe_fail_closed(root, probe) for probe in probes]
    gate = decide_gate(plan, results)

    return PreflightPacket(
        request_text=request_text,
        provider=provider.name,
        workspace=str(root),
        initial_plan=plan,
        probes=probes,
        probe_results=results,
        gate=gate,
        metrics={
            "assumptions": len(plan.assumptions),
            "verified": sum(result.verdict == "verified" for result in results),
            "contradicted": sum(result.verdict == "contradicted" for result in results),
            "unknown": sum(result.verdict == "unknown" for result in results),
            "source_edits": gate.source_edits_before_gate,
            "preflight_ms": int((time.perf_counter() - started) * 1000),
            **provider.metrics(),
        },
        limitations=[
            "Preflight does not generate or apply patches.",
            "Only allowlisted repository probes can decide premise verdicts.",
            "A load-bearing contradicted or unknown premise returns a blocking gate.",
            "External-model quality is not claimed without a captured run artifact.",
        ],
    )
