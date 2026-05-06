"""Tests for envault.snapshot."""

from __future__ import annotations

import pytest

from envault.snapshot import (
    create_snapshot,
    delete_snapshot,
    list_snapshots,
    restore_snapshot,
)
from envault.store import load_secrets, save_secrets

PASSWORD = "s3cret"


@pytest.fixture()
def vault_dir(tmp_path):
    """A temporary project directory pre-populated with two secrets."""
    project = str(tmp_path)
    save_secrets(project, PASSWORD, {"DB_URL": "postgres://localhost", "API_KEY": "abc123"})
    return project


def test_create_snapshot_returns_secret_count(vault_dir):
    count = create_snapshot(vault_dir, "v1", PASSWORD)
    assert count == 2


def test_list_snapshots_empty_when_none_exist(tmp_path):
    assert list_snapshots(str(tmp_path)) == []


def test_list_snapshots_returns_snapshot_names(vault_dir):
    create_snapshot(vault_dir, "v1", PASSWORD)
    create_snapshot(vault_dir, "v2", PASSWORD)
    names = list_snapshots(vault_dir)
    assert names == ["v1", "v2"]


def test_restore_snapshot_overwrites_current_secrets(vault_dir):
    create_snapshot(vault_dir, "baseline", PASSWORD)
    # Modify vault after snapshot
    save_secrets(vault_dir, PASSWORD, {"NEW_KEY": "new_value"})
    assert load_secrets(vault_dir, PASSWORD) == {"NEW_KEY": "new_value"}
    # Restore brings back original secrets
    count = restore_snapshot(vault_dir, "baseline", PASSWORD)
    assert count == 2
    restored = load_secrets(vault_dir, PASSWORD)
    assert restored["DB_URL"] == "postgres://localhost"
    assert restored["API_KEY"] == "abc123"


def test_restore_missing_snapshot_raises(vault_dir):
    with pytest.raises(FileNotFoundError, match="ghost"):
        restore_snapshot(vault_dir, "ghost", PASSWORD)


def test_delete_snapshot_removes_it(vault_dir):
    create_snapshot(vault_dir, "temp", PASSWORD)
    assert "temp" in list_snapshots(vault_dir)
    delete_snapshot(vault_dir, "temp")
    assert "temp" not in list_snapshots(vault_dir)


def test_delete_missing_snapshot_raises(vault_dir):
    with pytest.raises(FileNotFoundError):
        delete_snapshot(vault_dir, "nonexistent")


def test_multiple_snapshots_are_independent(vault_dir):
    create_snapshot(vault_dir, "snap_a", PASSWORD)
    save_secrets(vault_dir, PASSWORD, {"ONLY_IN_B": "yes"})
    create_snapshot(vault_dir, "snap_b", PASSWORD)

    restore_snapshot(vault_dir, "snap_a", PASSWORD)
    secrets_a = load_secrets(vault_dir, PASSWORD)
    assert "DB_URL" in secrets_a
    assert "ONLY_IN_B" not in secrets_a

    restore_snapshot(vault_dir, "snap_b", PASSWORD)
    secrets_b = load_secrets(vault_dir, PASSWORD)
    assert "ONLY_IN_B" in secrets_b
    assert "DB_URL" not in secrets_b
