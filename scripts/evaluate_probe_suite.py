from __future__ import annotations

import json
from pathlib import Path

from planprobe.eval.probe_suite import write_probe_suite

ROOT = Path(__file__).resolve().parents[1]


def main() -> None:
    result = write_probe_suite(ROOT / "artifacts" / "probe-suite.json")
    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
