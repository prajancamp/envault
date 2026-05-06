"""Tests for envault.ttl."""

from __future__ import annotations

import datetime
import time

import pytest

from envault.store import save_secrets
from envault import ttl as ttl_mod

PASSWORD = "test-password"


@pytest.fixture()
def vault_dir(tmp_path):
    save_secrets(str(tmp_path), PASSWORD, {"API_KEY": "abc123", "DB_URL": "postgres://"})
    return str(tmp_path)


def test_set_ttl_returns_future_datetime(vault_dir):
    before = datetime.datetime.now(datetime.timezone.utc)
    expires_at = ttl_mod.set_ttl(vault_dir, PASSWORD, "API_KEY", 60)
    after = datetime.datetime.now(datetime.timezone.utc)
    assert expires_at > before
    assert expires_at <= after + datetime.timedelta(seconds=60)


def test_get_ttl_returns_none_when_not_set(vault_dir):
    result = ttl_mod.get_ttl(vault_dir, PASSWORD, "API_KEY")
    assert result is None


def test_get_ttl_returns_datetime_after_set(vault_dir):
    ttl_mod.set_ttl(vault_dir, PASSWORD, "API_KEY", 120)
    result = ttl_mod.get_ttl(vault_dir, PASSWORD, "API_KEY")
    assert isinstance(result, datetime.datetime)


def test_set_ttl_missing_key_raises(vault_dir):
    with pytest.raises(KeyError, match="MISSING"):
        ttl_mod.set_ttl(vault_dir, PASSWORD, "MISSING", 60)


def test_set_ttl_non_positive_seconds_raises(vault_dir):
    with pytest.raises(ValueError, match="positive"):
        ttl_mod.set_ttl(vault_dir, PASSWORD, "API_KEY", 0)


def test_remove_ttl_returns_true_when_existed(vault_dir):
    ttl_mod.set_ttl(vault_dir, PASSWORD, "API_KEY", 60)
    assert ttl_mod.remove_ttl(vault_dir, PASSWORD, "API_KEY") is True


def test_remove_ttl_returns_false_when_not_set(vault_dir):
    assert ttl_mod.remove_ttl(vault_dir, PASSWORD, "API_KEY") is False


def test_list_expired_empty_when_no_ttls(vault_dir):
    assert ttl_mod.list_expired(vault_dir, PASSWORD) == []


def test_list_expired_returns_past_keys(vault_dir):
    # Use a negative-offset trick: set TTL then manually backdate the stored value
    from envault.store import load_secrets, save_secrets as _save
    ttl_mod.set_ttl(vault_dir, PASSWORD, "API_KEY", 3600)
    secrets = load_secrets(vault_dir, PASSWORD)
    past = (datetime.datetime.now(datetime.timezone.utc) - datetime.timedelta(seconds=1)).isoformat()
    secrets[ttl_mod._ttl_key("API_KEY")] = past
    _save(vault_dir, PASSWORD, secrets)
    expired = ttl_mod.list_expired(vault_dir, PASSWORD)
    assert "API_KEY" in expired


def test_purge_expired_removes_secret_and_metadata(vault_dir):
    from envault.store import load_secrets, save_secrets as _save
    ttl_mod.set_ttl(vault_dir, PASSWORD, "API_KEY", 3600)
    secrets = load_secrets(vault_dir, PASSWORD)
    past = (datetime.datetime.now(datetime.timezone.utc) - datetime.timedelta(seconds=1)).isoformat()
    secrets[ttl_mod._ttl_key("API_KEY")] = past
    _save(vault_dir, PASSWORD, secrets)

    purged = ttl_mod.purge_expired(vault_dir, PASSWORD)
    assert "API_KEY" in purged

    remaining = load_secrets(vault_dir, PASSWORD)
    assert "API_KEY" not in remaining
    assert ttl_mod._ttl_key("API_KEY") not in remaining


def test_purge_expired_leaves_non_expired_intact(vault_dir):
    ttl_mod.set_ttl(vault_dir, PASSWORD, "DB_URL", 3600)  # not expired
    purged = ttl_mod.purge_expired(vault_dir, PASSWORD)
    assert "DB_URL" not in purged
    from envault.store import load_secrets
    assert "DB_URL" in load_secrets(vault_dir, PASSWORD)
