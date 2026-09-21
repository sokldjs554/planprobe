from __future__ import annotations

import hashlib
import json
import statistics
import tempfile
from dataclasses import dataclass
from pathlib import Path
from typing import Literal

from planprobe.engine.gate import decide_gate
from planprobe.engine.probes import run_probe
from planprobe.models import Assumption, ImplementationPlan, PlanStep, ProbeSpec

PremiseClass = Literal[
    "schema",
    "timezone_config",
    "idempotency_retry",
    "state_order",
    "backward_compatibility",
    "authorization_ownership",
]
ExpectedVerdict = Literal["verified", "contradicted", "unknown"]


@dataclass(frozen=True)
class ProbeCase:
    id: str
    premise_class: PremiseClass
    claim: str
    files: dict[str, str]
    probe: ProbeSpec
    expected_verdict: ExpectedVerdict
    load_bearing: bool = True

    @property
    def expected_gate(self) -> Literal["pass", "block"]:
        if not self.load_bearing:
            return "pass"
        return "pass" if self.expected_verdict == "verified" else "block"


def _probe(
    *,
    case_id: str,
    assumption_id: str,
    kind: str,
    target_path: str,
    params: dict[str, object],
) -> ProbeSpec:
    return ProbeSpec(
        id=f"PR-{case_id}",
        assumption_id=assumption_id,
        kind=kind,  # type: ignore[arg-type]
        target_path=target_path,
        params=params,
        rationale="Deterministic evaluation probe generated from the frozen contract suite.",
    )


def build_probe_cases() -> list[ProbeCase]:
    cases: list[ProbeCase] = []

    # Schema cardinality/type: verified, contradicted, unknown, verified-list.
    cases.extend(
        [
            ProbeCase(
                id="SCHEMA-01",
                premise_class="schema",
                claim="RewardRequest.region is scalar.",
                files={"app/models.py": "class RewardRequest:\n    region: str\n"},
                probe=_probe(
                    case_id="SCHEMA-01",
                    assumption_id="A-SCHEMA-01",
                    kind="field_shape",
                    target_path="app/models.py",
                    params={"class": "RewardRequest", "field": "region", "expected_shape": "scalar"},
                ),
                expected_verdict="verified",
            ),
            ProbeCase(
                id="SCHEMA-02",
                premise_class="schema",
                claim="RewardRequest.regions is scalar.",
                files={"app/models.py": "class RewardRequest:\n    regions: list[str]\n"},
                probe=_probe(
                    case_id="SCHEMA-02",
                    assumption_id="A-SCHEMA-02",
                    kind="field_shape",
                    target_path="app/models.py",
                    params={"class": "RewardRequest", "field": "regions", "expected_shape": "scalar"},
                ),
                expected_verdict="contradicted",
            ),
            ProbeCase(
                id="SCHEMA-03",
                premise_class="schema",
                claim="RewardRequest.region exists and is scalar.",
                files={"app/models.py": "class RewardRequest:\n    player_id: str\n"},
                probe=_probe(
                    case_id="SCHEMA-03",
                    assumption_id="A-SCHEMA-03",
                    kind="field_shape",
                    target_path="app/models.py",
                    params={"class": "RewardRequest", "field": "region", "expected_shape": "scalar"},
                ),
                expected_verdict="unknown",
            ),
            ProbeCase(
                id="SCHEMA-04",
                premise_class="schema",
                claim="Audience.regions is a list.",
                files={"app/models.py": "class Audience:\n    regions: list[str]\n"},
                probe=_probe(
                    case_id="SCHEMA-04",
                    assumption_id="A-SCHEMA-04",
                    kind="field_shape",
                    target_path="app/models.py",
                    params={"class": "Audience", "field": "regions", "expected_shape": "list"},
                ),
                expected_verdict="verified",
            ),
        ]
    )

    # Timezone/config policy.
    cases.extend(
        [
            ProbeCase(
                id="TIME-01",
                premise_class="timezone_config",
                claim="Every region uses UTC.",
                files={
                    "app/config.py": 'REGION_TIMEZONES: dict[str, str] = {"KR": "UTC", "JP": "UTC", "US": "UTC"}\n'
                },
                probe=_probe(
                    case_id="TIME-01",
                    assumption_id="A-TIME-01",
                    kind="mapping_all_equal",
                    target_path="app/config.py",
                    params={"symbol": "REGION_TIMEZONES", "expected_value": "UTC"},
                ),
                expected_verdict="verified",
            ),
            ProbeCase(
                id="TIME-02",
                premise_class="timezone_config",
                claim="Every region uses UTC.",
                files={
                    "app/config.py": 'REGION_TIMEZONES: dict[str, str] = {"KR": "Asia/Seoul", "JP": "Asia/Tokyo", "US": "America/Los_Angeles"}\n'
                },
                probe=_probe(
                    case_id="TIME-02",
                    assumption_id="A-TIME-02",
                    kind="mapping_all_equal",
                    target_path="app/config.py",
                    params={"symbol": "REGION_TIMEZONES", "expected_value": "UTC"},
                ),
                expected_verdict="contradicted",
            ),
            ProbeCase(
                id="TIME-03",
                premise_class="timezone_config",
                claim="Every region uses UTC.",
                files={"app/config.py": 'DEFAULT_TIMEZONE = "UTC"\n'},
                probe=_probe(
                    case_id="TIME-03",
                    assumption_id="A-TIME-03",
                    kind="mapping_all_equal",
                    target_path="app/config.py",
                    params={"symbol": "REGION_TIMEZONES", "expected_value": "UTC"},
                ),
                expected_verdict="unknown",
            ),
            ProbeCase(
                id="TIME-04",
                premise_class="timezone_config",
                claim="Every regional settlement runs in Asia/Seoul.",
                files={
                    "app/config.py": 'SETTLEMENT_ZONES: dict[str, str] = {"A": "Asia/Seoul", "B": "Asia/Seoul"}\n'
                },
                probe=_probe(
                    case_id="TIME-04",
                    assumption_id="A-TIME-04",
                    kind="mapping_all_equal",
                    target_path="app/config.py",
                    params={"symbol": "SETTLEMENT_ZONES", "expected_value": "Asia/Seoul"},
                ),
                expected_verdict="verified",
            ),
        ]
    )

    # Idempotency/retry. The probe runs immutable existing tests rather than trusting prose.
    cases.extend(
        [
            ProbeCase(
                id="IDEM-01",
                premise_class="idempotency_retry",
                claim="Duplicate claim keys reuse a single receipt.",
                files={
                    "app/__init__.py": "",
                    "app/reward.py": (
                        "seen = {}\n"
                        "def claim(key: str) -> object:\n"
                        "    if key in seen:\n"
                        "        return seen[key]\n"
                        "    receipt = object()\n"
                        "    seen[key] = receipt\n"
                        "    return receipt\n"
                    ),
                    "tests/test_contract.py": (
                        "from app.reward import claim, seen\n"
                        "def test_retry_contract():\n"
                        "    seen.clear()\n"
                        "    a = claim('k')\n"
                        "    b = claim('k')\n"
                        "    assert a is b\n"
                        "    assert len(seen) == 1\n"
                    ),
                },
                probe=_probe(
                    case_id="IDEM-01",
                    assumption_id="A-IDEM-01",
                    kind="pytest_node",
                    target_path="tests/test_contract.py",
                    params={"node": "tests/test_contract.py::test_retry_contract"},
                ),
                expected_verdict="verified",
            ),
            ProbeCase(
                id="IDEM-02",
                premise_class="idempotency_retry",
                claim="Duplicate claim keys reuse a single receipt.",
                files={
                    "app/__init__.py": "",
                    "app/reward.py": (
                        "seen = []\n"
                        "def claim(key: str) -> object:\n"
                        "    receipt = object()\n"
                        "    seen.append((key, receipt))\n"
                        "    return receipt\n"
                    ),
                    "tests/test_contract.py": (
                        "from app.reward import claim, seen\n"
                        "def test_retry_contract():\n"
                        "    seen.clear()\n"
                        "    a = claim('k')\n"
                        "    b = claim('k')\n"
                        "    assert a is b\n"
                        "    assert len(seen) == 1\n"
                    ),
                },
                probe=_probe(
                    case_id="IDEM-02",
                    assumption_id="A-IDEM-02",
                    kind="pytest_node",
                    target_path="tests/test_contract.py",
                    params={"node": "tests/test_contract.py::test_retry_contract"},
                ),
                expected_verdict="contradicted",
            ),
            ProbeCase(
                id="IDEM-03",
                premise_class="idempotency_retry",
                claim="A frozen retry regression test exists.",
                files={
                    "app/__init__.py": "",
                    "tests/test_contract.py": "def test_other_contract():\n    assert True\n",
                },
                probe=_probe(
                    case_id="IDEM-03",
                    assumption_id="A-IDEM-03",
                    kind="pytest_node",
                    target_path="tests/test_contract.py",
                    params={"node": "tests/test_contract.py::test_retry_contract"},
                ),
                expected_verdict="unknown",
            ),
            ProbeCase(
                id="IDEM-04",
                premise_class="idempotency_retry",
                claim="Retry after a cached result does not append another ledger row.",
                files={
                    "app/__init__.py": "",
                    "app/reward.py": (
                        "cache = {}\nledger = []\n"
                        "def claim(key: str) -> dict[str, str]:\n"
                        "    if key in cache:\n"
                        "        return cache[key]\n"
                        "    receipt = {'key': key}\n"
                        "    cache[key] = receipt\n"
                        "    ledger.append(receipt)\n"
                        "    return receipt\n"
                    ),
                    "tests/test_contract.py": (
                        "from app.reward import cache, claim, ledger\n"
                        "def test_retry_after_success_has_one_ledger_row():\n"
                        "    cache.clear(); ledger.clear()\n"
                        "    claim('same'); claim('same'); claim('same')\n"
                        "    assert len(ledger) == 1\n"
                    ),
                },
                probe=_probe(
                    case_id="IDEM-04",
                    assumption_id="A-IDEM-04",
                    kind="pytest_node",
                    target_path="tests/test_contract.py",
                    params={"node": "tests/test_contract.py::test_retry_after_success_has_one_ledger_row"},
                ),
                expected_verdict="verified",
            ),
        ]
    )

    # State/call ordering.
    cases.extend(
        [
            ProbeCase(
                id="ORDER-01",
                premise_class="state_order",
                claim="Receipt creation happens before ledger append.",
                files={
                    "app/service.py": (
                        "def Receipt():\n    return object()\n"
                        "class Ledger:\n    def append(self, x):\n        return None\n"
                        "ledger = Ledger()\n"
                        "def claim():\n    receipt = Receipt()\n    ledger.append(receipt)\n    return receipt\n"
                    )
                },
                probe=_probe(
                    case_id="ORDER-01",
                    assumption_id="A-ORDER-01",
                    kind="ast_order",
                    target_path="app/service.py",
                    params={"function": "claim", "before": "Receipt", "after": "append"},
                ),
                expected_verdict="verified",
            ),
            ProbeCase(
                id="ORDER-02",
                premise_class="state_order",
                claim="Validation happens before persistence.",
                files={
                    "app/service.py": (
                        "def validate():\n    return None\n"
                        "def save():\n    return None\n"
                        "def publish():\n    save()\n    validate()\n"
                    )
                },
                probe=_probe(
                    case_id="ORDER-02",
                    assumption_id="A-ORDER-02",
                    kind="ast_order",
                    target_path="app/service.py",
                    params={"function": "publish", "before": "validate", "after": "save"},
                ),
                expected_verdict="contradicted",
            ),
            ProbeCase(
                id="ORDER-03",
                premise_class="state_order",
                claim="A reservation occurs before commit.",
                files={"app/service.py": "def checkout():\n    return True\n"},
                probe=_probe(
                    case_id="ORDER-03",
                    assumption_id="A-ORDER-03",
                    kind="ast_order",
                    target_path="app/service.py",
                    params={"function": "checkout", "before": "reserve", "after": "commit"},
                ),
                expected_verdict="unknown",
            ),
            ProbeCase(
                id="ORDER-04",
                premise_class="state_order",
                claim="Capacity check happens before allocation.",
                files={
                    "app/service.py": (
                        "def check_capacity():\n    return True\n"
                        "def allocate():\n    return None\n"
                        "def assign():\n    check_capacity()\n    allocate()\n"
                    )
                },
                probe=_probe(
                    case_id="ORDER-04",
                    assumption_id="A-ORDER-04",
                    kind="ast_order",
                    target_path="app/service.py",
                    params={"function": "assign", "before": "check_capacity", "after": "allocate"},
                ),
                expected_verdict="verified",
            ),
        ]
    )

    # Backward compatibility through public function signatures.
    cases.extend(
        [
            ProbeCase(
                id="COMPAT-01",
                premise_class="backward_compatibility",
                claim="publish_event still accepts event_id and locale.",
                files={"app/api.py": "def publish_event(event_id: str, locale: str, dry_run: bool = False):\n    return None\n"},
                probe=_probe(
                    case_id="COMPAT-01",
                    assumption_id="A-COMPAT-01",
                    kind="function_signature",
                    target_path="app/api.py",
                    params={"function": "publish_event", "expected_params": ["event_id", "locale"], "mode": "subset"},
                ),
                expected_verdict="verified",
            ),
            ProbeCase(
                id="COMPAT-02",
                premise_class="backward_compatibility",
                claim="publish_event still accepts event_id and locale.",
                files={"app/api.py": "def publish_event(event_id: str, language_code: str):\n    return None\n"},
                probe=_probe(
                    case_id="COMPAT-02",
                    assumption_id="A-COMPAT-02",
                    kind="function_signature",
                    target_path="app/api.py",
                    params={"function": "publish_event", "expected_params": ["event_id", "locale"], "mode": "subset"},
                ),
                expected_verdict="contradicted",
            ),
            ProbeCase(
                id="COMPAT-03",
                premise_class="backward_compatibility",
                claim="legacy_claim still exposes its historical API.",
                files={"app/api.py": "def claim_v2(player_id: str):\n    return None\n"},
                probe=_probe(
                    case_id="COMPAT-03",
                    assumption_id="A-COMPAT-03",
                    kind="function_signature",
                    target_path="app/api.py",
                    params={"function": "legacy_claim", "expected_params": ["player_id"], "mode": "subset"},
                ),
                expected_verdict="unknown",
            ),
            ProbeCase(
                id="COMPAT-04",
                premise_class="backward_compatibility",
                claim="reward_quote has the frozen two-argument signature.",
                files={"app/api.py": "def reward_quote(player_id: str, region: str):\n    return 0\n"},
                probe=_probe(
                    case_id="COMPAT-04",
                    assumption_id="A-COMPAT-04",
                    kind="function_signature",
                    target_path="app/api.py",
                    params={"function": "reward_quote", "expected_params": ["player_id", "region"], "mode": "exact"},
                ),
                expected_verdict="verified",
            ),
        ]
    )

    # Authorization/ownership guards are checked as executable source-order contracts.
    cases.extend(
        [
            ProbeCase(
                id="AUTH-01",
                premise_class="authorization_ownership",
                claim="Ownership authorization executes before profile update.",
                files={
                    "app/service.py": (
                        "def authorize_owner():\n    return True\n"
                        "def update_profile():\n    return None\n"
                        "def edit_profile():\n    authorize_owner()\n    update_profile()\n"
                    )
                },
                probe=_probe(
                    case_id="AUTH-01",
                    assumption_id="A-AUTH-01",
                    kind="ast_order",
                    target_path="app/service.py",
                    params={"function": "edit_profile", "before": "authorize_owner", "after": "update_profile"},
                ),
                expected_verdict="verified",
            ),
            ProbeCase(
                id="AUTH-02",
                premise_class="authorization_ownership",
                claim="Ownership authorization executes before profile update.",
                files={
                    "app/service.py": (
                        "def authorize_owner():\n    return True\n"
                        "def update_profile():\n    return None\n"
                        "def edit_profile():\n    update_profile()\n    authorize_owner()\n"
                    )
                },
                probe=_probe(
                    case_id="AUTH-02",
                    assumption_id="A-AUTH-02",
                    kind="ast_order",
                    target_path="app/service.py",
                    params={"function": "edit_profile", "before": "authorize_owner", "after": "update_profile"},
                ),
                expected_verdict="contradicted",
            ),
            ProbeCase(
                id="AUTH-03",
                premise_class="authorization_ownership",
                claim="Admin authorization is established before deletion.",
                files={"app/service.py": "def delete_event():\n    return None\n"},
                probe=_probe(
                    case_id="AUTH-03",
                    assumption_id="A-AUTH-03",
                    kind="ast_order",
                    target_path="app/service.py",
                    params={"function": "delete_event", "before": "require_admin", "after": "delete"},
                ),
                expected_verdict="unknown",
            ),
            ProbeCase(
                id="AUTH-04",
                premise_class="authorization_ownership",
                claim="Permission check happens before destructive deletion.",
                files={
                    "app/service.py": (
                        "def require_permission():\n    return True\n"
                        "def delete():\n    return None\n"
                        "def remove_banner():\n    require_permission()\n    delete()\n"
                    )
                },
                probe=_probe(
                    case_id="AUTH-04",
                    assumption_id="A-AUTH-04",
                    kind="ast_order",
                    target_path="app/service.py",
                    params={"function": "remove_banner", "before": "require_permission", "after": "delete"},
                ),
                expected_verdict="verified",
            ),
        ]
    )

    return cases


def _write_fixture(root: Path, files: dict[str, str]) -> None:
    for rel, content in files.items():
        path = root / rel
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content, encoding="utf-8")


def _source_digest(root: Path) -> str:
    rows: list[bytes] = []
    for path in sorted(root.rglob("*.py")):
        if any(part in {"__pycache__", ".pytest_cache"} for part in path.parts):
            continue
        rel = path.relative_to(root).as_posix().encode("utf-8")
        rows.append(rel + b"\0" + path.read_bytes())
    return hashlib.sha256(b"\n".join(rows)).hexdigest()


def _plan_for(case: ProbeCase) -> ImplementationPlan:
    return ImplementationPlan(
        version=1,
        summary=f"Frozen contract-suite case {case.id}",
        steps=[PlanStep(id="P1", title="Candidate plan", detail=case.claim, target_files=[case.probe.target_path])],
        assumptions=[
            Assumption(
                id=case.probe.assumption_id,
                claim=case.claim,
                load_bearing=case.load_bearing,
                why_it_matters="Evaluation case: a false or unknown load-bearing premise must block source generation.",
                plan_step_ids=["P1"],
            )
        ],
    )


def _p95(values: list[float]) -> float:
    if not values:
        return 0.0
    ordered = sorted(values)
    index = max(0, min(len(ordered) - 1, int((len(ordered) - 1) * 0.95 + 0.999999)))
    return ordered[index]


def run_probe_suite() -> dict[str, object]:
    rows: list[dict[str, object]] = []
    cases = build_probe_cases()
    with tempfile.TemporaryDirectory(prefix="planprobe-contract-suite-") as temp:
        suite_root = Path(temp)
        for case in cases:
            workspace = suite_root / case.id
            workspace.mkdir(parents=True, exist_ok=True)
            _write_fixture(workspace, case.files)
            before = _source_digest(workspace)
            result = run_probe(workspace, case.probe)
            after = _source_digest(workspace)
            plan = _plan_for(case)
            gate = decide_gate(plan, [result])
            rows.append(
                {
                    "id": case.id,
                    "premise_class": case.premise_class,
                    "expected_verdict": case.expected_verdict,
                    "actual_verdict": result.verdict,
                    "verdict_correct": result.verdict == case.expected_verdict,
                    "expected_gate": case.expected_gate,
                    "actual_gate": gate.status,
                    "gate_correct": gate.status == case.expected_gate,
                    "source_unchanged": before == after,
                    "duration_ms": result.duration_ms,
                    "observed": result.observed,
                }
            )

    by_class: dict[str, dict[str, int]] = {}
    for row in rows:
        key = str(row["premise_class"])
        bucket = by_class.setdefault(key, {"cases": 0, "verdict_correct": 0, "gate_correct": 0})
        bucket["cases"] += 1
        bucket["verdict_correct"] += int(bool(row["verdict_correct"]))
        bucket["gate_correct"] += int(bool(row["gate_correct"]))

    durations = [float(str(row["duration_ms"])) for row in rows]
    false_blocks = sum(
        1 for row in rows if row["expected_gate"] == "pass" and row["actual_gate"] == "block"
    )
    missed_blocks = sum(
        1 for row in rows if row["expected_gate"] == "block" and row["actual_gate"] == "pass"
    )
    unknowns = sum(1 for row in rows if row["actual_verdict"] == "unknown")
    summary = {
        "cases": len(rows),
        "premise_classes": len(by_class),
        "verdict_correct": sum(bool(row["verdict_correct"]) for row in rows),
        "gate_correct": sum(bool(row["gate_correct"]) for row in rows),
        "source_unchanged": sum(bool(row["source_unchanged"]) for row in rows),
        "false_blocks": false_blocks,
        "missed_blocks": missed_blocks,
        "unknown_results": unknowns,
        "median_probe_ms": round(statistics.median(durations), 3),
        "p95_probe_ms": round(_p95(durations), 3),
    }
    return {
        "suite": "planprobe-deterministic-repository-contract-v1",
        "scope": (
            "Deterministic probe/gate mechanics benchmark. It measures whether frozen repository facts "
            "are classified and gated correctly; it is not an LLM coding-quality benchmark."
        ),
        "summary": summary,
        "by_class": by_class,
        "rows": rows,
    }


def write_probe_suite(path: Path) -> dict[str, object]:
    result = run_probe_suite()
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
    return result
