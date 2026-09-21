from __future__ import annotations

import json
import os
import time
import urllib.request

BASE_URL = os.getenv("BASE_URL", "http://127.0.0.1:8000").rstrip("/")
EXPECTED_COMMIT = os.getenv("EXPECTED_COMMIT", "").strip()
TIMEOUT = int(os.getenv("SMOKE_TIMEOUT_SECONDS", "600"))


def request_json(path: str, method: str = "GET", payload: dict[str, object] | None = None) -> dict[str, object]:
    body = None if payload is None else json.dumps(payload).encode()
    req = urllib.request.Request(BASE_URL + path, data=body, method=method, headers={"Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=30) as response:
        return json.loads(response.read().decode())


def main() -> None:
    deadline = time.monotonic() + TIMEOUT
    while True:
        release = request_json("/api/release")
        if not EXPECTED_COMMIT or release.get("commit") == EXPECTED_COMMIT:
            break
        if time.monotonic() > deadline:
            raise RuntimeError(f"expected deployed commit {EXPECTED_COMMIT}, got {release}")
        time.sleep(5)
    request_text = str(request_json("/api/demo/request")["request_text"])
    created = request_json("/api/runs", method="POST", payload={"request_text": request_text, "provider": "deterministic-demo"})
    run_id = str(created["id"])
    record: dict[str, object] | None = None
    while time.monotonic() < deadline:
        record = request_json(f"/api/runs/{run_id}")
        if record.get("stage") in {"complete", "failed"}:
            break
        time.sleep(1)
    if record is None or record.get("stage") != "complete":
        raise RuntimeError(f"run failed: {record}")
    packet = record["packet"]
    assert isinstance(packet, dict)
    assert packet["verdict"] == "ready_with_evidence"
    assert packet["first_gate"]["status"] == "block"
    assert packet["first_gate"]["source_edits_before_gate"] == 0
    assert set(packet["first_gate"]["blocked_assumptions"]) == {"A-UTC", "A-REGION"}
    print(json.dumps({"release": release, "run_id": run_id, "verdict": packet["verdict"]}, ensure_ascii=False))


if __name__ == "__main__":
    main()
