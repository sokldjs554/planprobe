from __future__ import annotations

from pathlib import Path

from planprobe.agent.deterministic import DeterministicDemoProvider
from planprobe.engine.probes import run_probe
from planprobe.engine.workspace import create_workspace


def test_demo_probes_find_two_false_and_two_true_assumptions(tmp_path: Path) -> None:
    root = Path(__file__).resolve().parents[1]
    workspace = create_workspace(root, tmp_path / "run")
    provider = DeterministicDemoProvider()
    plan = provider.plan("demo request", workspace)
    probes = provider.compile_probes(plan, workspace)
    results = [run_probe(workspace, probe) for probe in probes]
    verdicts = {result.assumption_id: result.verdict for result in results}
    assert verdicts == {
        "A-UTC": "contradicted",
        "A-REGION": "contradicted",
        "A-IDEMPOTENCY": "verified",
        "A-ORDER": "verified",
    }
