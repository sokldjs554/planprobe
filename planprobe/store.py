from __future__ import annotations

import json
import sqlite3
from pathlib import Path
from threading import Lock

from planprobe.models import RunPacket, RunRecord, RunStage


class RunStore:
    def __init__(self, path: Path) -> None:
        self.path = path
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self._lock = Lock()
        with self._connect() as conn:
            conn.execute("PRAGMA journal_mode=WAL")
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS runs (
                    id TEXT PRIMARY KEY,
                    request_text TEXT NOT NULL,
                    provider TEXT NOT NULL,
                    stage TEXT NOT NULL,
                    status_message TEXT NOT NULL,
                    events_json TEXT NOT NULL,
                    packet_json TEXT
                )
                """
            )

    def _connect(self) -> sqlite3.Connection:
        return sqlite3.connect(self.path, timeout=30)

    def create(self, run_id: str, request_text: str, provider: str) -> None:
        with self._lock, self._connect() as conn:
            conn.execute(
                "INSERT INTO runs VALUES (?, ?, ?, ?, ?, ?, ?)",
                (run_id, request_text, provider, RunStage.QUEUED.value, "Queued", "[]", None),
            )

    def update(
        self,
        run_id: str,
        *,
        stage: RunStage | None = None,
        status_message: str | None = None,
        event: dict[str, object] | None = None,
        packet: RunPacket | None = None,
    ) -> None:
        with self._lock, self._connect() as conn:
            row = conn.execute(
                "SELECT stage, status_message, events_json, packet_json FROM runs WHERE id = ?", (run_id,)
            ).fetchone()
            if row is None:
                raise KeyError(run_id)
            events = json.loads(row[2])
            if event is not None:
                events.append(event)
            conn.execute(
                "UPDATE runs SET stage=?, status_message=?, events_json=?, packet_json=? WHERE id=?",
                (
                    stage.value if stage else row[0],
                    status_message if status_message is not None else row[1],
                    json.dumps(events, ensure_ascii=False),
                    packet.model_dump_json() if packet is not None else row[3],
                    run_id,
                ),
            )

    def get(self, run_id: str) -> RunRecord:
        with self._connect() as conn:
            row = conn.execute(
                "SELECT id, request_text, provider, stage, status_message, events_json, packet_json FROM runs WHERE id=?",
                (run_id,),
            ).fetchone()
        if row is None:
            raise KeyError(run_id)
        return RunRecord(
            id=row[0],
            request_text=row[1],
            provider=row[2],
            stage=RunStage(row[3]),
            status_message=row[4],
            events=json.loads(row[5]),
            packet=RunPacket.model_validate_json(row[6]) if row[6] else None,
        )

    def list(self, limit: int = 20) -> list[RunRecord]:
        with self._connect() as conn:
            ids = [row[0] for row in conn.execute("SELECT id FROM runs ORDER BY rowid DESC LIMIT ?", (limit,))]
        return [self.get(run_id) for run_id in ids]
