"""Tests for envault.rotate."""

from __future__ import annotations

import pytest
from pathlib import Path

from envault.store import load_secrets, save_secrets
from envault.rotate import rotate_password, rotate_summary


@pytest.fixture()
def vault_dir(tmp_path: Path) -> Path:
    secrets = {"DB_URL": "postgres://localhost/db", "API_KEY": "secret123"}
    save_secrets(tmp_path, "old-pass", secrets)
    return tmp_path


def test_rotate_returns_secret_count(vault_dir: Path) -> None:
    count = rotate_password(vault_dir, "old-pass", "new-pass")
    assert count == 2


def test_rotate_new_password_decrypts_correctly(vault_dir: Path) -> None:
    rotate_password(vault_dir, "old-pass", "new-pass")
    secrets = load_secrets(vault_dir, "new-pass")
    assert secrets["DB_URL"] == "postgres://localhost/db"
    assert secrets["API_KEY"] == "secret123"


def test_rotate_old_password_no_longer_works(vault_dir: Path) -> None:
    rotate_password(vault_dir, "old-pass", "new-pass")
    with pytest.raises(Exception):
        load_secrets(vault_dir, "old-pass")


def test_rotate_wrong_old_password_raises(vault_dir: Path) -> None:
    with pytest.raises(Exception):
        rotate_password(vault_dir, "wrong-pass", "new-pass")


def test_rotate_dry_run_does_not_write(vault_dir: Path) -> None:
    rotate_password(vault_dir, "old-pass", "new-pass", dry_run=True)
    # Old password must still work
    secrets = load_secrets(vault_dir, "old-pass")
    assert "DB_URL" in secrets


def test_rotate_summary_returns_dict(vault_dir: Path) -> None:
    summary = rotate_summary(vault_dir, "old-pass", "new-pass")
    assert summary["secrets_count"] == 2
    assert summary["dry_run"] is True


def test_rotate_empty_vault(tmp_path: Path) -> None:
    save_secrets(tmp_path, "old-pass", {})
    count = rotate_password(tmp_path, "old-pass", "new-pass")
    assert count == 0
    assert load_secrets(tmp_path, "new-pass") == {}
