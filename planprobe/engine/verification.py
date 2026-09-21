from __future__ import annotations

import os
import subprocess
import sys
import tempfile
import time
from pathlib import Path

from planprobe.models import CheckResult


ACCEPTANCE_TEST = r'''
from __future__ import annotations
from datetime import datetime, timezone
from synthetic_app.liveops_service.models import RewardRequest
from synthetic_app.liveops_service.rewards import claim_reward
from synthetic_app.liveops_service.state import STATE


def test_streak_bonus_preserves_multi_region_and_idempotency():
    STATE.reset()
    req = RewardRequest(
        player_id="player-acceptance",
        regions=["KR", "JP", "US"],
        idempotency_key="acceptance-1",
        streak_days=5,
        now_utc=datetime(2026, 10, 1, 2, 0, tzinfo=timezone.utc),
    )
    first = claim_reward(req)
    second = claim_reward(req)
    assert first == second
    assert len(STATE.ledger) == 1
    assert first.base_coins == 100
    assert first.streak_bonus == 50
    assert first.total_coins == 150
    assert first.coins == first.total_coins
    assert isinstance(first.eligible_regions, list)


def test_bonus_is_capped_at_seven_days():
    STATE.reset()
    req = RewardRequest(
        player_id="player-cap",
        regions=["KR"],
        idempotency_key="acceptance-cap",
        streak_days=30,
        now_utc=datetime(2026, 10, 1, 2, 0, tzinfo=timezone.utc),
    )
    receipt = claim_reward(req)
    assert receipt.streak_bonus == 70
'''


def run_checks(workspace: Path) -> list[CheckResult]:
    checks = [_run_existing_tests(workspace), _run_acceptance_tests(workspace)]
    return checks


def _run_existing_tests(workspace: Path) -> CheckResult:
    return _run_pytest(
        workspace,
        "existing-contract-tests",
        ["synthetic_app/liveops_service/tests"],
    )


def _run_acceptance_tests(workspace: Path) -> CheckResult:
    with tempfile.TemporaryDirectory(prefix="planprobe-acceptance-") as temp:
        path = Path(temp) / "test_feature_acceptance.py"
        path.write_text(ACCEPTANCE_TEST, encoding="utf-8")
        return _run_pytest(workspace, "generated-acceptance-tests", [str(path)])


def _run_pytest(workspace: Path, name: str, targets: list[str]) -> CheckResult:
    started = time.perf_counter()
    completed = subprocess.run(
        [sys.executable, "-m", "pytest", "-q", *targets],
        cwd=workspace,
        capture_output=True,
        text=True,
        timeout=45,
        check=False,
        env={**os.environ, "PYTHONPATH": str(workspace)},
    )
    detail = (completed.stdout + completed.stderr).strip()[-1200:]
    return CheckResult(
        name=name,
        status="pass" if completed.returncode == 0 else "fail",
        detail=detail,
        duration_ms=int((time.perf_counter() - started) * 1000),
    )
