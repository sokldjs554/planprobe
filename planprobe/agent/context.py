from __future__ import annotations

import os
from pathlib import Path

_ALLOWED_SUFFIXES = {".py", ".toml", ".json", ".yaml", ".yml", ".ts", ".tsx", ".js", ".jsx"}
_EXCLUDED_PARTS = {
    ".git",
    ".hg",
    ".svn",
    ".venv",
    "venv",
    "node_modules",
    "__pycache__",
    ".pytest_cache",
    ".mypy_cache",
    ".ruff_cache",
    "dist",
    "build",
}


def _roots(workspace: Path) -> list[Path]:
    explicit = os.getenv("PLANPROBE_CONTEXT_ROOTS", "").strip()
    if explicit:
        roots: list[Path] = []
        base = workspace.resolve()
        for raw in explicit.split(","):
            candidate = (base / raw.strip()).resolve()
            if candidate == base or base in candidate.parents:
                if candidate.exists():
                    roots.append(candidate)
        if roots:
            return roots

    preferred = workspace / "synthetic_app" / "liveops_service"
    if preferred.exists():
        return [preferred]
    return [workspace]


def repository_context(workspace: Path, *, max_chars: int = 24_000) -> str:
    """Build a bounded repository source pack for local or hosted model routes.

    Repository text is untrusted data. Model output never owns verification authority.
    """

    chunks: list[str] = []
    used = 0
    base = workspace.resolve()

    for root in _roots(base):
        for path in sorted(root.rglob("*")):
            if not path.is_file() or path.suffix not in _ALLOWED_SUFFIXES:
                continue
            if any(part in _EXCLUDED_PARTS for part in path.parts):
                continue
            try:
                if path.stat().st_size > 512_000:
                    continue
            except OSError:
                continue
            rel = path.relative_to(base).as_posix()
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
