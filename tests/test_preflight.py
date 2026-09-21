from __future__ import annotations

import hashlib
from pathlib import Path

from planprobe.cli import DEFAULT_REQUEST
from planprobe.preflight import run_preflight


def _source_digest(root: Path) -> str:
    rows: list[bytes] = []
    for path in sorted((root / "synthetic_app").rglob("*.py")):
        if "__pycache__" in path.parts:
            continue
        rows.append(path.relative_to(root).as_posix().encode() + b"\0" + path.read_bytes())
    return hashlib.sha256(b"\n".join(rows)).hexdigest()


def test_preflight_blocks_before_source_edit() -> None:
    root = Path(__file__).resolve().parents[1]
    before = _source_digest(root)

    packet = run_preflight(
        workspace=root,
        request_text=DEFAULT_REQUEST,
        provider_name="deterministic-demo",
    )

    after = _source_digest(root)
    assert packet.gate.status == "block"
    assert set(packet.gate.blocked_assumptions) == {"A-UTC", "A-REGION"}
    assert packet.gate.source_edits_before_gate == 0
    assert packet.metrics["source_edits"] == 0
    assert before == after


def test_repository_context_supports_non_demo_workspace(tmp_path: Path, monkeypatch) -> None:
    from planprobe.agent.context import repository_context

    (tmp_path / "src").mkdir()
    (tmp_path / "src" / "service.py").write_text("VALUE = 7\n", encoding="utf-8")
    (tmp_path / "node_modules").mkdir()
    (tmp_path / "node_modules" / "ignored.js").write_text("secret", encoding="utf-8")
    monkeypatch.delenv("PLANPROBE_CONTEXT_ROOTS", raising=False)

    packed = repository_context(tmp_path)
    assert "src/service.py" in packed
    assert "VALUE = 7" in packed
    assert "ignored.js" not in packed


def test_untrusted_probe_failure_becomes_unknown(tmp_path: Path) -> None:
    from planprobe.engine.probes import run_probe_fail_closed
    from planprobe.models import ProbeSpec

    spec = ProbeSpec(
        id="PR-MISSING",
        assumption_id="A-MISSING",
        kind="field_shape",
        target_path="missing.py",
        params={"class": "Missing", "field": "value", "expected_shape": "scalar"},
        rationale="Model-proposed missing paths must fail closed rather than crash the preflight.",
    )
    result = run_probe_fail_closed(tmp_path, spec)
    assert result.verdict == "unknown"
    assert result.evidence == []
    assert "FileNotFoundError" in result.observed
