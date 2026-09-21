from __future__ import annotations

from pathlib import Path

import pytest

from planprobe.engine.patching import apply_patch
from planprobe.models import PatchEdit, PatchSet


def test_generated_patch_cannot_edit_tests(tmp_path: Path) -> None:
    workspace = tmp_path / "workspace"
    target = workspace / "synthetic_app/liveops_service/tests"
    target.mkdir(parents=True)
    (target / "test_x.py").write_text("x = 1\n", encoding="utf-8")
    patch = PatchSet(
        summary="bad",
        edits=[PatchEdit(path="synthetic_app/liveops_service/tests/test_x.py", old="x = 1", new="x = 2")],
    )
    with pytest.raises(ValueError):
        apply_patch(workspace, patch)
