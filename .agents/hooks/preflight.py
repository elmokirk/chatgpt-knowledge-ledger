"""Workspace-local mutation preflight: rejects global targets and real-data defaults."""
from pathlib import Path

WORKSPACE=Path(__file__).resolve().parents[2]
FORBIDDEN=(Path.home()/"Downloads",Path.home()/".codex"/"skills",Path.home()/".claude"/"skills")

def assert_workspace_target(path: str) -> Path:
    resolved=Path(path).resolve()
    if any(resolved == p.resolve() or p.resolve() in resolved.parents for p in FORBIDDEN):
        raise PermissionError(f"forbidden default target: {resolved}")
    if WORKSPACE.resolve() not in resolved.parents and resolved != WORKSPACE.resolve():
        raise PermissionError(f"target outside workspace: {resolved}")
    return resolved

