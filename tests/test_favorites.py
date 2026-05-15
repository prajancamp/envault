"""Tests for envault.favorites."""

from __future__ import annotations

import pytest

from envault.store import save_secrets
from envault.favorites import (
    add_favorite,
    remove_favorite,
    list_favorites,
    is_favorite,
    get_favorite_secrets,
)

PASSWORD = "test-password"


@pytest.fixture()
def vault_dir(tmp_path):
    secrets = {"API_KEY": "abc123", "DB_PASS": "s3cr3t", "TOKEN": "tok"}
    save_secrets(str(tmp_path), PASSWORD, secrets)
    return str(tmp_path)


def test_add_favorite_marks_key(vault_dir):
    add_favorite(vault_dir, "API_KEY", PASSWORD)
    assert is_favorite(vault_dir, "API_KEY") is True


def test_add_favorite_missing_key_raises(vault_dir):
    with pytest.raises(KeyError, match="MISSING"):
        add_favorite(vault_dir, "MISSING", PASSWORD)


def test_add_favorite_idempotent(vault_dir):
    add_favorite(vault_dir, "API_KEY", PASSWORD)
    add_favorite(vault_dir, "API_KEY", PASSWORD)
    assert list_favorites(vault_dir).count("API_KEY") == 1


def test_is_favorite_returns_false_when_not_added(vault_dir):
    assert is_favorite(vault_dir, "API_KEY") is False


def test_remove_favorite_clears_key(vault_dir):
    add_favorite(vault_dir, "DB_PASS", PASSWORD)
    remove_favorite(vault_dir, "DB_PASS")
    assert is_favorite(vault_dir, "DB_PASS") is False


def test_remove_favorite_noop_when_not_present(vault_dir):
    # Should not raise even if key was never favorited
    remove_favorite(vault_dir, "API_KEY")


def test_list_favorites_empty_when_none_added(vault_dir):
    assert list_favorites(vault_dir) == []


def test_list_favorites_preserves_insertion_order(vault_dir):
    add_favorite(vault_dir, "TOKEN", PASSWORD)
    add_favorite(vault_dir, "API_KEY", PASSWORD)
    assert list_favorites(vault_dir) == ["TOKEN", "API_KEY"]


def test_get_favorite_secrets_returns_values(vault_dir):
    add_favorite(vault_dir, "API_KEY", PASSWORD)
    add_favorite(vault_dir, "TOKEN", PASSWORD)
    result = get_favorite_secrets(vault_dir, PASSWORD)
    assert result == {"API_KEY": "abc123", "TOKEN": "tok"}


def test_get_favorite_secrets_skips_deleted_keys(vault_dir):
    add_favorite(vault_dir, "API_KEY", PASSWORD)
    # Remove the secret from the vault directly
    from envault.store import load_secrets
    secrets = load_secrets(vault_dir, PASSWORD)
    del secrets["API_KEY"]
    save_secrets(vault_dir, PASSWORD, secrets)
    result = get_favorite_secrets(vault_dir, PASSWORD)
    assert "API_KEY" not in result
