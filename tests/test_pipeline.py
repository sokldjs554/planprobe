from __future__ import annotations

from pathlib import Path

from planprobe.cli import DEFAULT_REQUEST
from planprobe.engine.pipeline import PlanProbePipeline
from planprobe.store import RunStore


def test_pipeline_blocks_before_code_then_replans_and_passes(tmp_path: Path) -> None:
    root = Path(__file__).resolve().parents[1]
    store = RunStore(tmp_path / "runs.db")
    pipeline = PlanProbePipeline(root, store)
    pipeline.runs_root = tmp_path / "run-artifacts"
    run_id = pipeline.start(DEFAULT_REQUEST)
    packet = pipeline.execute(run_id)

    assert packet.first_gate.status == "block"
    assert packet.first_gate.source_edits_before_gate == 0
    assert set(packet.first_gate.blocked_assumptions) == {"A-UTC", "A-REGION"}
    assert packet.revised_plan.version == 2
    assert packet.revised_plan.evidence_ids
    assert packet.verdict == "ready_with_evidence"
    assert all(check.status == "pass" for check in packet.checks)
    assert {edit.path for edit in packet.patch.edits} == {
        "synthetic_app/liveops_service/models.py",
        "synthetic_app/liveops_service/rewards.py",
    }
