from __future__ import annotations

import json
import statistics
import tempfile
from pathlib import Path

from planprobe.cli import DEFAULT_REQUEST
from planprobe.engine.pipeline import PlanProbePipeline
from planprobe.store import RunStore

ROOT = Path(__file__).resolve().parents[1]


def main() -> None:
    rows: list[dict[str, object]] = []
    with tempfile.TemporaryDirectory(prefix="planprobe-eval-") as temp:
        base = Path(temp)
        store = RunStore(base / "runs.db")
        pipeline = PlanProbePipeline(ROOT, store)
        pipeline.runs_root = base / "artifacts"
        for _ in range(5):
            run_id = pipeline.start(DEFAULT_REQUEST)
            packet = pipeline.execute(run_id)
            rows.append(
                {
                    "run_id": run_id,
                    "verdict": packet.verdict,
                    "blocked": packet.first_gate.blocked_assumptions,
                    "contradicted": packet.metrics["contradicted_assumptions"],
                    "source_edits_before_gate": packet.metrics["source_edits_before_gate"],
                    "checks": f'{packet.metrics["checks_passed"]}/{packet.metrics["checks_total"]}',
                    "pipeline_ms": packet.metrics["pipeline_ms"],
                }
            )
    result = {
        "runs": rows,
        "summary": {
            "runs": len(rows),
            "ready": sum(row["verdict"] == "ready_with_evidence" for row in rows),
            "median_pipeline_ms": statistics.median(float(row["pipeline_ms"]) for row in rows),
            "all_precode_edits_zero": all(row["source_edits_before_gate"] == 0 for row in rows),
        },
        "scope": "deterministic orchestration repeatability only; not an LLM quality benchmark",
    }
    out = ROOT / "artifacts" / "evaluation.json"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
