from __future__ import annotations

from pathlib import Path

from planprobe.agent.deterministic import DeterministicDemoProvider
from planprobe.agent.openai_compat import OpenAICompatibleProvider, ProbeDraft, ProbeDraftList


def test_open_model_probe_candidates_fail_closed_individually(monkeypatch) -> None:
    provider = OpenAICompatibleProvider()
    drafts = ProbeDraftList(
        probes=[
            ProbeDraft(
                id="P-VALID",
                assumption_id="A-REGION",
                kind="field_shape",
                target_path="synthetic_app/liveops_service/models.py",
                params={"class": "RewardRequest", "field": "regions", "expected_shape": "list"},
                rationale="Concrete repository field shape.",
            ),
            ProbeDraft(
                id="P-BAD",
                assumption_id="A-IDEMPOTENCY",
                kind="pytest_node",
                target_path="synthetic_app/liveops_service/rewards.py",
                params={"node": "claim_reward"},
                rationale="Invalid source function masquerading as a pytest node.",
            ),
        ]
    )
    monkeypatch.setattr(provider, "_json", lambda *args, **kwargs: drafts)

    plan = DeterministicDemoProvider().plan("demo request", Path("."))
    probes = provider.compile_probes(plan, Path("."))

    assert [probe.id for probe in probes] == ["P-VALID"]
    assert provider.metrics()["llm_rejected_probes"] == 1
