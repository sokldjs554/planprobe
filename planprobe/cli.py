from __future__ import annotations

import argparse
import tempfile
from pathlib import Path

from planprobe.engine.pipeline import PlanProbePipeline
from planprobe.preflight import run_preflight
from planprobe.store import RunStore

DEFAULT_REQUEST = (
    "글로벌 이벤트 보상에 연속 접속 보너스를 추가해주세요. 기존 중복 요청 재시도 안전성과 "
    "지역별 이벤트 시간 판정, 다중 지역 요청은 깨지지 않아야 합니다."
)


def main() -> None:
    parser = argparse.ArgumentParser(prog="planprobe")
    parser.add_argument("command", choices=["demo", "preflight"])
    parser.add_argument("--provider", default="deterministic-demo")
    parser.add_argument("--request", default=DEFAULT_REQUEST)
    parser.add_argument("--workspace", default=".")
    parser.add_argument("--output")
    args = parser.parse_args()

    if args.command == "demo":
        with tempfile.TemporaryDirectory(prefix="planprobe-cli-") as temp:
            root = Path(__file__).resolve().parent.parent
            store = RunStore(Path(temp) / "runs.db")
            pipeline = PlanProbePipeline(root, store)
            pipeline.runs_root = Path(temp) / "runs"
            run_id = pipeline.start(args.request, args.provider)
            packet = pipeline.execute(run_id)
            print(packet.model_dump_json(indent=2))
        return

    packet = run_preflight(
        workspace=Path(args.workspace),
        request_text=args.request,
        provider_name=args.provider,
    )
    rendered = packet.model_dump_json(indent=2)
    if args.output:
        path = Path(args.output)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(rendered + "\n", encoding="utf-8")
    print(rendered)
    if packet.gate.status == "block":
        raise SystemExit(2)
    raise SystemExit(0)


if __name__ == "__main__":
    main()
