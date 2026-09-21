from __future__ import annotations

from pathlib import Path

from planprobe.models import PatchSet

ALLOWED_PREFIX = "synthetic_app/liveops_service/"
DENIED_PARTS = {"tests", "test", ".github", "planprobe"}


def apply_patch(workspace: Path, patch: PatchSet) -> list[str]:
    changed: list[str] = []
    for edit in patch.edits:
        if not edit.path.startswith(ALLOWED_PREFIX):
            raise ValueError(f"patch path is not allowlisted: {edit.path}")
        parts = Path(edit.path).parts
        if any(part in DENIED_PARTS or part.startswith("test") for part in parts):
            raise ValueError(f"patch cannot modify verification surface: {edit.path}")
        path = (workspace / edit.path).resolve()
        if workspace.resolve() not in path.parents:
            raise ValueError("patch path escaped workspace")
        text = path.read_text(encoding="utf-8")
        if text.count(edit.old) != 1:
            raise ValueError(f"exact replacement must match once: {edit.path}")
        path.write_text(text.replace(edit.old, edit.new), encoding="utf-8")
        changed.append(edit.path)
    return changed
