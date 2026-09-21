from __future__ import annotations

from dataclasses import dataclass, field

from synthetic_app.liveops_service.models import RewardReceipt


@dataclass
class RewardState:
    receipts: dict[str, RewardReceipt] = field(default_factory=dict)
    ledger: list[dict[str, object]] = field(default_factory=list)

    def reset(self) -> None:
        self.receipts.clear()
        self.ledger.clear()


STATE = RewardState()
