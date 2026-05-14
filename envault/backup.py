"""Backup and restore the entire vault to/from a compressed archive."""

from __future__ import annotations

import json
import tarfile
import io
from datetime import datetime, timezone
from pathlib import Path

from envault.store import load_secrets, save_secrets
from envault.snapshot import _snapshot_dir, list_snapshots, _snapshot_path


def _now_utc() -> str:
    return datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")


def _backup_filename(project_dir: Path) -> str:
    return f"envault-backup-{_now_utc()}.tar.gz"


def create_backup(project_dir: Path, password: str, dest_dir: Path | None = None) -> Path:
    """Create a compressed backup archive containing the vault and all snapshots.

    Returns the path to the created archive.
    """
    dest_dir = dest_dir or project_dir
    dest_dir.mkdir(parents=True, exist_ok=True)
    archive_path = dest_dir / _backup_filename(project_dir)

    vault_file = project_dir / ".envault" / "vault.json"
    snap_dir = _snapshot_dir(project_dir)

    with tarfile.open(archive_path, "w:gz") as tar:
        if vault_file.exists():
            tar.add(vault_file, arcname="vault.json")

        if snap_dir.exists():
            for snap_file in sorted(snap_dir.glob("*.json")):
                tar.add(snap_file, arcname=f"snapshots/{snap_file.name}")

        # Store metadata
        meta = {
            "created_at": _now_utc(),
            "project_dir": str(project_dir),
            "snapshot_count": len(list_snapshots(project_dir)),
        }
        meta_bytes = json.dumps(meta, indent=2).encode()
        info = tarfile.TarInfo(name="backup_meta.json")
        info.size = len(meta_bytes)
        tar.addfile(info, io.BytesIO(meta_bytes))

    return archive_path


def restore_backup(archive_path: Path, project_dir: Path, overwrite: bool = False) -> dict:
    """Restore a vault backup from a compressed archive.

    Returns a summary dict with counts of restored items.
    """
    vault_dir = project_dir / ".envault"
    vault_file = vault_dir / "vault.json"

    if vault_file.exists() and not overwrite:
        raise FileExistsError(
            "Vault already exists. Pass overwrite=True to replace it."
        )

    vault_dir.mkdir(parents=True, exist_ok=True)
    snap_dir = _snapshot_dir(project_dir)
    snap_dir.mkdir(parents=True, exist_ok=True)

    restored_snapshots = 0
    restored_vault = False
    meta = {}

    with tarfile.open(archive_path, "r:gz") as tar:
        for member in tar.getmembers():
            f = tar.extractfile(member)
            if f is None:
                continue
            data = f.read()
            if member.name == "vault.json":
                vault_file.write_bytes(data)
                restored_vault = True
            elif member.name.startswith("snapshots/"):
                snap_name = Path(member.name).name
                (snap_dir / snap_name).write_bytes(data)
                restored_snapshots += 1
            elif member.name == "backup_meta.json":
                meta = json.loads(data)

    return {
        "vault_restored": restored_vault,
        "snapshots_restored": restored_snapshots,
        "original_project": meta.get("project_dir", "unknown"),
        "backup_created_at": meta.get("created_at", "unknown"),
    }
