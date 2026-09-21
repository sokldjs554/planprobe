from __future__ import annotations

from datetime import datetime
from uuid import uuid4
from zoneinfo import ZoneInfo

from synthetic_app.liveops_service.config import (
    EVENT_END_LOCAL_HOUR,
    EVENT_START_LOCAL_HOUR,
    REGION_TIMEZONES,
)
from synthetic_app.liveops_service.models import RewardReceipt, RewardRequest
from synthetic_app.liveops_service.state import STATE

BASE_COINS = 100


def is_event_open(region: str, now_utc: datetime) -> bool:
    zone_name = REGION_TIMEZONES[region]
    local_hour = now_utc.astimezone(ZoneInfo(zone_name)).hour
    return EVENT_START_LOCAL_HOUR <= local_hour < EVENT_END_LOCAL_HOUR


def claim_reward(request: RewardRequest) -> RewardReceipt:
    existing = STATE.receipts.get(request.idempotency_key)
    if existing is not None:
        return existing

    eligible_regions = [region for region in request.regions if is_event_open(region, request.now_utc)]
    base_coins = BASE_COINS if eligible_regions else 0

    receipt = RewardReceipt(
        claim_id=str(uuid4()),
        coins=base_coins,
        eligible_regions=eligible_regions,
    )
    STATE.receipts[request.idempotency_key] = receipt
    STATE.ledger.append(
        {
            "player_id": request.player_id,
            "claim_id": receipt.claim_id,
            "coins": receipt.coins,
            "regions": list(eligible_regions),
        }
    )
    return receipt
