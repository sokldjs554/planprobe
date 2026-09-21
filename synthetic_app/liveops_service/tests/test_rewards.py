from __future__ import annotations

from datetime import datetime, timezone

import pytest
from pydantic import ValidationError

from synthetic_app.liveops_service.models import RewardRequest
from synthetic_app.liveops_service.rewards import claim_reward
from synthetic_app.liveops_service.state import STATE


@pytest.fixture(autouse=True)
def reset_state() -> None:
    STATE.reset()


def _request(*, key: str = "claim-1", regions: list[str] | None = None, streak_days: int = 3) -> RewardRequest:
    return RewardRequest(
        player_id="player-7",
        regions=regions or ["KR", "JP"],
        idempotency_key=key,
        streak_days=streak_days,
        now_utc=datetime(2026, 10, 1, 2, 0, tzinfo=timezone.utc),
    )


def test_duplicate_request_returns_same_receipt_and_single_ledger_entry() -> None:
    first = claim_reward(_request())
    second = claim_reward(_request())
    assert first == second
    assert len(STATE.ledger) == 1


def test_multi_region_request_is_supported() -> None:
    receipt = claim_reward(_request(regions=["KR", "JP", "US"]))
    assert isinstance(receipt.eligible_regions, list)
    assert set(receipt.eligible_regions).issubset({"KR", "JP", "US"})


def test_negative_streak_is_rejected_by_schema() -> None:
    with pytest.raises(ValidationError):
        _request(streak_days=-1)
