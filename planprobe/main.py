from __future__ import annotations

import os
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field

from planprobe.engine.pipeline import PlanProbePipeline
from planprobe.store import RunStore

PROJECT_ROOT = Path(__file__).resolve().parent.parent
STATE_DIR = Path(os.getenv("PLANPROBE_STATE_DIR", PROJECT_ROOT / ".planprobe"))
STORE = RunStore(STATE_DIR / "runs.db")
PIPELINE = PlanProbePipeline(PROJECT_ROOT, STORE)
EXECUTOR = ThreadPoolExecutor(max_workers=2, thread_name_prefix="planprobe")

app = FastAPI(title="PlanProbe", version="0.1.0", description="Pre-code assumption falsification gate for AI coding workflows.")


class RunRequest(BaseModel):
    request_text: str = Field(min_length=12, max_length=5000)
    provider: str = "deterministic-demo"


@app.get("/api/health")
def health() -> dict[str, str]:
    return {"status": "ok", "service": "planprobe", "version": "0.1.0"}


@app.get("/api/release")
def release() -> dict[str, str]:
    return {"service": "planprobe", "version": "0.1.0", "commit": os.getenv("RENDER_GIT_COMMIT", "unknown")}


@app.get("/api/demo/request")
def demo_request() -> dict[str, str]:
    from planprobe.cli import DEFAULT_REQUEST

    return {"request_text": DEFAULT_REQUEST}


@app.post("/api/runs", status_code=202)
def create_run(body: RunRequest) -> dict[str, str]:
    if body.provider not in {"deterministic-demo", "openai-compatible", "vllm", "anthropic"}:
        raise HTTPException(status_code=400, detail="Unsupported provider")
    run_id = PIPELINE.start(body.request_text, body.provider)
    EXECUTOR.submit(PIPELINE.execute, run_id)
    return {"id": run_id, "stage": "queued"}


@app.get("/api/runs/{run_id}")
def get_run(run_id: str) -> dict[str, object]:
    try:
        return STORE.get(run_id).model_dump(mode="json")
    except KeyError as exc:
        raise HTTPException(status_code=404, detail="Run not found") from exc


STATIC = PROJECT_ROOT / "planprobe" / "static"
app.mount("/static", StaticFiles(directory=STATIC), name="static")


@app.get("/", include_in_schema=False)
def index() -> FileResponse:
    return FileResponse(STATIC / "index.html")
