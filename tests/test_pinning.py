"""Tests for envault.pinning."""

from __future__ import annotations

import pytest
from pathlib import Path

from envault.store import save_secrets
from envault.pinning import (
    pin_secret,
    unpin_secret,
    is_pinned,
    list_pinned,
    assert_not_pinned,
)

PASSWORD = "test-password"


@pytest.fixture()
def vault_dir(tmp_path: Path) -> Path:
    secrets = {"API_KEY": "abc123", "DB_PASS": "secret"}
    save_secrets(tmp_path, secrets, PASSWORD)
    return tmp_path


def test_pin_secret_marks_key(vault_dir: Path) -> None:
    pin_secret(vault_dir, "API_KEY", PASSWORD)
    assert is_pinned(vault_dir, "API_KEY") is True


def test_unpin_secret_clears_key(vault_dir: Path) -> None:
    pin_secret(vault_dir, "API_KEY", PASSWORD)
    unpin_secret(vault_dir, "API_KEY")
    assert is_pinned(vault_dir, "API_KEY") is False


def test_is_pinned_returns_false_when_not_pinned(vault_dir: Path) -> None:
    assert is_pinned(vault_dir, "DB_PASS") is False


def test_list_pinned_empty_when_none_pinned(vault_dir: Path) -> None:
    assert list_pinned(vault_dir) == []


def test_list_pinned_returns_all_pinned_keys(vault_dir: Path) -> None:
    pin_secret(vault_dir, "API_KEY", PASSWORD)
    pin_secret(vault_dir, "DB_PASS", PASSWORD)
    result = list_pinned(vault_dir)
    assert sorted(result) == ["API_KEY", "DB_PASS"]


def test_pin_secret_idempotent(vault_dir: Path) -> None:
    pin_secret(vault_dir, "API_KEY", PASSWORD)
    pin_secret(vault_dir, "API_KEY", PASSWORD)
    assert list_pinned(vault_dir).count("API_KEY") == 1


def test_pin_missing_key_raises(vault_dir: Path) -> None:
    with pytest.raises(KeyError, match="MISSING"):
        pin_secret(vault_dir, "MISSING", PASSWORD)


def test_assert_not_pinned_raises_when_pinned(vault_dir: Path) -> None:
    pin_secret(vault_dir, "API_KEY", PASSWORD)
    with pytest.raises(ValueError, match="pinned"):
        assert_not_pinned(vault_dir, "API_KEY")


def test_assert_not_pinned_passes_when_not_pinned(vault_dir: Path) -> None:
    # Should not raise
    assert_not_pinned(vault_dir, "DB_PASS")


def test_unpin_nonexistent_key_is_noop(vault_dir: Path) -> None:
    # Should not raise
    unpin_secret(vault_dir, "NONEXISTENT")
