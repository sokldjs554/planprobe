from __future__ import annotations

import time

from fastapi.testclient import TestClient

from planprobe.main import app


def test_demo_api_end_to_end() -> None:
    client = TestClient(app)
    request_text = client.get("/api/demo/request").json()["request_text"]
    created = client.post("/api/runs", json={"request_text": request_text, "provider": "deterministic-demo"})
    assert created.status_code == 202
    run_id = created.json()["id"]
    record = None
    for _ in range(80):
        record = client.get(f"/api/runs/{run_id}").json()
        if record["stage"] in {"complete", "failed"}:
            break
        time.sleep(0.1)
    assert record is not None
    assert record["stage"] == "complete"
    assert record["packet"]["verdict"] == "ready_with_evidence"
