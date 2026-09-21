from __future__ import annotations

import shutil
from pathlib import Path


def create_workspace(project_root: Path, run_root: Path) -> Path:
    workspace = run_root / "workspace"
    if workspace.exists():
        shutil.rmtree(workspace)
    workspace.mkdir(parents=True)
    shutil.copytree(project_root / "synthetic_app", workspace / "synthetic_app")
    return workspace
