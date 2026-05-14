"""Tests for envault.backup."""

from __future__ import annotations

import json
import pytest
from pathlib import Path

from envault.store import save_secrets, load_secrets
from envault.snapshot import create_snapshot
from envault.backup import create_backup, restore_backup

PASSWORD = "backup-test-pw"


@pytest.fixture()
def vault_dir(tmp_path: Path):
    project = tmp_path / "project"
    project.mkdir()
    secrets = {"API_KEY": "abc123", "DB_PASS": "secret"}
    save_secrets(project, PASSWORD, secrets)
    return project


def test_create_backup_returns_path(vault_dir):
    dest = vault_dir / "backups"
    path = create_backup(vault_dir, PASSWORD, dest_dir=dest)
    assert path.exists()
    assert path.suffix == ".gz"
    assert "envault-backup-" in path.name


def test_create_backup_includes_vault(vault_dir):
    import tarfile
    dest = vault_dir / "backups"
    path = create_backup(vault_dir, PASSWORD, dest_dir=dest)
    with tarfile.open(path, "r:gz") as tar:
        names = tar.getnames()
    assert "vault.json" in names


def test_create_backup_includes_snapshots(vault_dir):
    import tarfile
    create_snapshot(vault_dir, PASSWORD, "snap1")
    dest = vault_dir / "backups"
    path = create_backup(vault_dir, PASSWORD, dest_dir=dest)
    with tarfile.open(path, "r:gz") as tar:
        names = tar.getnames()
    assert any(n.startswith("snapshots/") for n in names)


def test_create_backup_includes_metadata(vault_dir):
    import tarfile
    dest = vault_dir / "backups"
    path = create_backup(vault_dir, PASSWORD, dest_dir=dest)
    with tarfile.open(path, "r:gz") as tar:
        f = tar.extractfile("backup_meta.json")
        meta = json.loads(f.read())
    assert "created_at" in meta
    assert "project_dir" in meta


def test_restore_backup_recovers_secrets(vault_dir, tmp_path):
    dest = vault_dir / "backups"
    archive = create_backup(vault_dir, PASSWORD, dest_dir=dest)

    new_project = tmp_path / "restored"
    new_project.mkdir()
    summary = restore_backup(archive, new_project)

    assert summary["vault_restored"] is True
    recovered = load_secrets(new_project, PASSWORD)
    assert recovered["API_KEY"] == "abc123"
    assert recovered["DB_PASS"] == "secret"


def test_restore_backup_recovers_snapshots(vault_dir, tmp_path):
    create_snapshot(vault_dir, PASSWORD, "snap1")
    dest = vault_dir / "backups"
    archive = create_backup(vault_dir, PASSWORD, dest_dir=dest)

    new_project = tmp_path / "restored"
    new_project.mkdir()
    summary = restore_backup(archive, new_project)
    assert summary["snapshots_restored"] == 1


def test_restore_backup_raises_if_vault_exists_no_overwrite(vault_dir, tmp_path):
    dest = vault_dir / "backups"
    archive = create_backup(vault_dir, PASSWORD, dest_dir=dest)

    new_project = tmp_path / "restored"
    new_project.mkdir()
    # First restore is fine
    restore_backup(archive, new_project)
    # Second should raise without overwrite
    with pytest.raises(FileExistsError):
        restore_backup(archive, new_project, overwrite=False)


def test_restore_backup_overwrite_replaces_vault(vault_dir, tmp_path):
    dest = vault_dir / "backups"
    archive = create_backup(vault_dir, PASSWORD, dest_dir=dest)

    new_project = tmp_path / "restored"
    new_project.mkdir()
    restore_backup(archive, new_project)
    # Overwrite should succeed without raising
    summary = restore_backup(archive, new_project, overwrite=True)
    assert summary["vault_restored"] is True
