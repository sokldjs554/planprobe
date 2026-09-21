from __future__ import annotations

import pytest
from pydantic import ValidationError

from planprobe.models import ProbeSpec


def test_pytest_node_rejects_source_function_as_test_node() -> None:
    with pytest.raises(ValidationError, match="target_path::"):
        ProbeSpec(
            id="P1",
            assumption_id="A1",
            kind="pytest_node",
            target_path="synthetic_app/liveops_service/rewards.py",
            params={"node": "claim_reward"},
            rationale="Model output must not turn a source function into a pytest node.",
        )


def test_pytest_node_accepts_exact_existing_test_shape() -> None:
    spec = ProbeSpec(
        id="P1",
        assumption_id="A1",
        kind="pytest_node",
        target_path="synthetic_app/liveops_service/tests/test_rewards.py",
        params={
            "node": (
                "synthetic_app/liveops_service/tests/test_rewards.py"
                "::test_duplicate_request_returns_same_receipt_and_single_ledger_entry"
            )
        },
        rationale="Exact test nodes are executable repository evidence.",
    )
    assert spec.params["node"].startswith(spec.target_path + "::")


def test_probe_contract_rejects_missing_kind_params() -> None:
    with pytest.raises(ValidationError, match="missing params"):
        ProbeSpec(
            id="P1",
            assumption_id="A1",
            kind="ast_order",
            target_path="synthetic_app/liveops_service/rewards.py",
            params={"function": "claim_reward", "before": "RewardReceipt"},
            rationale="Incomplete kind-specific params must fail before execution.",
        )


def test_probe_target_path_cannot_escape_workspace() -> None:
    with pytest.raises(ValidationError, match="relative repository path"):
        ProbeSpec(
            id="P1",
            assumption_id="A1",
            kind="field_shape",
            target_path="../outside.py",
            params={"class": "X", "field": "value", "expected_shape": "scalar"},
            rationale="Model-generated paths cannot escape the selected repository.",
        )
