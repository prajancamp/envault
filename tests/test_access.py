"""Tests for envault.access (per-key access control)."""
from __future__ import annotations

import pytest

from envault import access
from envault.store import load_secrets, save_secrets


@pytest.fixture()
def vault_dir(tmp_path):
    vd = str(tmp_path)
    save_secrets(vd, "pw", {"DB_URL": "postgres://localhost", "API_KEY": "abc123"})
    return vd


def test_set_acl_stores_allowed_users(vault_dir):
    access.set_acl(vault_dir, "pw", "DB_URL", ["alice", "bob"])
    allowed = access.get_acl(vault_dir, "pw", "DB_URL")
    assert set(allowed) == {"alice", "bob"}


def test_get_acl_returns_empty_when_not_set(vault_dir):
    result = access.get_acl(vault_dir, "pw", "DB_URL")
    assert result == []


def test_set_acl_deduplicates_users(vault_dir):
    access.set_acl(vault_dir, "pw", "DB_URL", ["alice", "alice", "bob"])
    allowed = access.get_acl(vault_dir, "pw", "DB_URL")
    assert len(allowed) == 2
    assert set(allowed) == {"alice", "bob"}


def test_set_acl_missing_key_raises(vault_dir):
    with pytest.raises(KeyError):
        access.set_acl(vault_dir, "pw", "NONEXISTENT", ["alice"])


def test_remove_acl_clears_restriction(vault_dir):
    access.set_acl(vault_dir, "pw", "DB_URL", ["alice"])
    access.remove_acl(vault_dir, "pw", "DB_URL")
    assert access.get_acl(vault_dir, "pw", "DB_URL") == []


def test_remove_acl_noop_when_not_set(vault_dir):
    # Should not raise
    access.remove_acl(vault_dir, "pw", "DB_URL")


def test_check_access_unrestricted_always_true(vault_dir):
    assert access.check_access(vault_dir, "pw", "DB_URL", username="anyone") is True


def test_check_access_allowed_user_returns_true(vault_dir):
    access.set_acl(vault_dir, "pw", "API_KEY", ["carol"])
    assert access.check_access(vault_dir, "pw", "API_KEY", username="carol") is True


def test_check_access_denied_user_returns_false(vault_dir):
    access.set_acl(vault_dir, "pw", "API_KEY", ["carol"])
    assert access.check_access(vault_dir, "pw", "API_KEY", username="eve") is False


def test_acl_keys_not_visible_as_plain_secrets(vault_dir):
    access.set_acl(vault_dir, "pw", "DB_URL", ["alice"])
    secrets = load_secrets(vault_dir, "pw")
    plain_keys = [k for k in secrets if not k.startswith("__acl__.")]
    assert "DB_URL" in plain_keys
    assert "API_KEY" in plain_keys
    assert all(not k.startswith("__acl__.") for k in plain_keys)
