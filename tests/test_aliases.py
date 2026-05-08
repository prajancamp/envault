"""Tests for envault.aliases."""

from __future__ import annotations

import pytest

from envault import aliases
from envault.store import save_secrets


@pytest.fixture()
def vault_dir(tmp_path):
    password = "testpass"
    save_secrets(str(tmp_path), password, {"DB_HOST": "localhost", "DB_PORT": "5432"})
    return str(tmp_path)


def test_set_alias_creates_mapping(vault_dir):
    aliases.set_alias(vault_dir, "host", "DB_HOST", ["DB_HOST", "DB_PORT"])
    assert aliases.resolve_alias(vault_dir, "host") == "DB_HOST"


def test_set_alias_updates_existing(vault_dir):
    aliases.set_alias(vault_dir, "port", "DB_HOST", ["DB_HOST", "DB_PORT"])
    aliases.set_alias(vault_dir, "port", "DB_PORT", ["DB_HOST", "DB_PORT"])
    assert aliases.resolve_alias(vault_dir, "port") == "DB_PORT"


def test_set_alias_missing_key_raises(vault_dir):
    with pytest.raises(KeyError, match="MISSING"):
        aliases.set_alias(vault_dir, "bad", "MISSING", ["DB_HOST", "DB_PORT"])


def test_remove_alias_deletes_entry(vault_dir):
    aliases.set_alias(vault_dir, "host", "DB_HOST", ["DB_HOST", "DB_PORT"])
    aliases.remove_alias(vault_dir, "host")
    assert aliases.resolve_alias(vault_dir, "host") is None


def test_remove_alias_missing_raises(vault_dir):
    with pytest.raises(KeyError, match="ghost"):
        aliases.remove_alias(vault_dir, "ghost")


def test_resolve_alias_returns_none_when_not_set(vault_dir):
    assert aliases.resolve_alias(vault_dir, "nope") is None


def test_list_aliases_empty_when_none_exist(vault_dir):
    assert aliases.list_aliases(vault_dir) == {}


def test_list_aliases_returns_all(vault_dir):
    aliases.set_alias(vault_dir, "host", "DB_HOST", ["DB_HOST", "DB_PORT"])
    aliases.set_alias(vault_dir, "port", "DB_PORT", ["DB_HOST", "DB_PORT"])
    result = aliases.list_aliases(vault_dir)
    assert result == {"host": "DB_HOST", "port": "DB_PORT"}


def test_resolve_key_returns_alias_target(vault_dir):
    aliases.set_alias(vault_dir, "host", "DB_HOST", ["DB_HOST", "DB_PORT"])
    assert aliases.resolve_key(vault_dir, "host") == "DB_HOST"


def test_resolve_key_returns_name_when_no_alias(vault_dir):
    assert aliases.resolve_key(vault_dir, "DB_PORT") == "DB_PORT"
