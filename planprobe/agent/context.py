from __future__ import annotations

from pathlib import Path

_ALLOWED_ROOTS = ("synthetic_app/liveops_service",)
_ALLOWED_SUFFIXES = {".py", ".toml", ".json", ".yaml", ".yml"}


def repository_context(workspace: Path, *, max_chars: int = 24_000) -> str:
    """Build a bounded, deterministic repository context for remote/local model routes.

    A filesystem path is not useful to a remote model, so PlanProbe sends an explicit source pack.
    Repository text is treated as untrusted data; callers must keep verification authority outside the model.
    """
    chunks: list[str] = []
    used = 0
    for root_name in _ALLOWED_ROOTS:
        root = workspace / root_name
        if not root.exists():
            continue
        for path in sorted(root.rglob("*")):
            if not path.is_file() or path.suffix not in _ALLOWED_SUFFIXES:
                continue
            if any(part in {"__pycache__", ".pytest_cache"} for part in path.parts):
                continue
            rel = path.relative_to(workspace).as_posix()
            text = path.read_text(encoding="utf-8", errors="replace")
            block = f"\n<repository-file path={rel!r}>\n{text}\n</repository-file>\n"
            remaining = max_chars - used
            if remaining <= 0:
                break
            if len(block) > remaining:
                block = block[:remaining] + "\n<TRUNCATED/>\n"
            chunks.append(block)
            used += len(block)
        if used >= max_chars:
            break
    if not chunks:
        return "<repository-context empty='true'/>"
    return "".join(chunks)
