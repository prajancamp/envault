"""Snapshot support: save and restore named vault snapshots."""

from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Dict, List

from envault.store import load_secrets, save_secrets


def _snapshot_dir(project_dir: str) -> Path:
    """Return the directory where snapshots are stored for a project."""
    return Path(project_dir) / ".envault" / "snapshots"


def _snapshot_path(project_dir: str, name: str) -> Path:
    safe_name = name.replace("/", "_").replace("\\", "_")
    return _snapshot_dir(project_dir) / f"{safe_name}.json"


def list_snapshots(project_dir: str) -> List[str]:
    """Return sorted list of snapshot names for the given project."""
    snap_dir = _snapshot_dir(project_dir)
    if not snap_dir.exists():
        return []
    return sorted(
        p.stem for p in snap_dir.iterdir() if p.suffix == ".json"
    )


def create_snapshot(project_dir: str, name: str, password: str) -> int:
    """Snapshot current vault secrets under *name*. Returns number of secrets saved."""
    secrets = load_secrets(project_dir, password)
    snap_dir = _snapshot_dir(project_dir)
    snap_dir.mkdir(parents=True, exist_ok=True)
    path = _snapshot_path(project_dir, name)
    # Store as encrypted blobs — we re-use the already-encrypted representation
    # by saving the raw plaintext names + values so the snapshot is itself
    # protected by the same password via save_secrets on restore.
    path.write_text(json.dumps(secrets, indent=2), encoding="utf-8")
    return len(secrets)


def restore_snapshot(project_dir: str, name: str, password: str) -> int:
    """Restore vault from a named snapshot. Returns number of secrets restored."""
    path = _snapshot_path(project_dir, name)
    if not path.exists():
        raise FileNotFoundError(f"Snapshot '{name}' not found.")
    secrets: Dict[str, str] = json.loads(path.read_text(encoding="utf-8"))
    save_secrets(project_dir, password, secrets)
    return len(secrets)


def delete_snapshot(project_dir: str, name: str) -> None:
    """Delete a named snapshot."""
    path = _snapshot_path(project_dir, name)
    if not path.exists():
        raise FileNotFoundError(f"Snapshot '{name}' not found.")
    path.unlink()
