from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, Field


class RewardRequest(BaseModel):
    player_id: str
    regions: list[str] = Field(min_length=1)
    idempotency_key: str
    streak_days: int = Field(default=0, ge=0, le=30)
    now_utc: datetime


class RewardReceipt(BaseModel):
    claim_id: str
    coins: int
    eligible_regions: list[str]
