from __future__ import annotations

import argparse
import json
import os
import tempfile
import time
from pathlib import Path

from planprobe.cli import DEFAULT_REQUEST
from planprobe.engine.pipeline import PlanProbePipeline
from planprobe.store import RunStore

ROOT = Path(__file__).resolve().parents[1]


def main() -> None:
    parser = argparse.ArgumentParser(description="Run one real-model PlanProbe smoke and persist auditable metadata.")
    parser.add_argument("--provider", choices=["openai-compatible", "anthropic"], required=True)
    parser.add_argument("--request", default=DEFAULT_REQUEST)
    parser.add_argument("--out", default="artifacts/model-smoke.json")
    args = parser.parse_args()

    started = time.perf_counter()
    result: dict[str, object] = {
        "provider": args.provider,
        "status": "started",
        "request": args.request,
        "model": (
            os.getenv("PLANPROBE_OPENAI_MODEL", "qwen2.5-coder:7b")
            if args.provider == "openai-compatible"
            else os.getenv("PLANPROBE_ANTHROPIC_MODEL", "claude-sonnet-4-5")
        ),
    }
    try:
        with tempfile.TemporaryDirectory(prefix="planprobe-model-smoke-") as temp:
            root = Path(temp)
            store = RunStore(root / "runs.db")
            pipeline = PlanProbePipeline(ROOT, store)
            pipeline.runs_root = root / "runs"
            run_id = pipeline.start(args.request, args.provider)
            packet = pipeline.execute(run_id)
            result.update(
                {
                    "status": "complete",
                    "run_id": run_id,
                    "verdict": packet.verdict,
                    "gate": packet.first_gate.status,
                    "blocked_assumptions": packet.first_gate.blocked_assumptions,
                    "metrics": packet.metrics,
                    "checks": [item.model_dump() for item in packet.checks],
                }
            )
    except Exception as exc:
        result.update({"status": "failed", "error_type": type(exc).__name__, "error": str(exc)})
    result["wall_ms"] = round((time.perf_counter() - started) * 1000, 3)
    out = ROOT / args.out
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps(result, ensure_ascii=False, indent=2))
    if result["status"] != "complete":
        raise SystemExit(1)


if __name__ == "__main__":
    main()
