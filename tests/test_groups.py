"""Tests for envault.groups."""

from __future__ import annotations

import pytest

from envault.store import save_secrets
from envault.groups import (
    add_to_group,
    delete_group,
    get_group_members,
    list_groups,
    remove_from_group,
)

PASSWORD = "test-password"


@pytest.fixture()
def vault_dir(tmp_path):
    secrets = {"DB_HOST": "localhost", "DB_PORT": "5432", "API_KEY": "secret123"}
    save_secrets(str(tmp_path), PASSWORD, secrets)
    return str(tmp_path)


def test_add_to_group_creates_group(vault_dir):
    add_to_group(vault_dir, PASSWORD, "database", "DB_HOST")
    members = get_group_members(vault_dir, "database")
    assert "DB_HOST" in members


def test_add_to_group_multiple_keys(vault_dir):
    add_to_group(vault_dir, PASSWORD, "database", "DB_HOST")
    add_to_group(vault_dir, PASSWORD, "database", "DB_PORT")
    members = get_group_members(vault_dir, "database")
    assert set(members) == {"DB_HOST", "DB_PORT"}


def test_add_to_group_idempotent(vault_dir):
    add_to_group(vault_dir, PASSWORD, "database", "DB_HOST")
    add_to_group(vault_dir, PASSWORD, "database", "DB_HOST")
    members = get_group_members(vault_dir, "database")
    assert members.count("DB_HOST") == 1


def test_add_to_group_missing_key_raises(vault_dir):
    with pytest.raises(KeyError, match="MISSING_KEY"):
        add_to_group(vault_dir, PASSWORD, "database", "MISSING_KEY")


def test_remove_from_group_returns_true(vault_dir):
    add_to_group(vault_dir, PASSWORD, "database", "DB_HOST")
    result = remove_from_group(vault_dir, "database", "DB_HOST")
    assert result is True
    assert get_group_members(vault_dir, "database") == []


def test_remove_from_group_not_present_returns_false(vault_dir):
    result = remove_from_group(vault_dir, "database", "DB_HOST")
    assert result is False


def test_remove_last_key_deletes_group(vault_dir):
    add_to_group(vault_dir, PASSWORD, "database", "DB_HOST")
    remove_from_group(vault_dir, "database", "DB_HOST")
    assert "database" not in list_groups(vault_dir)


def test_list_groups_empty_when_none_exist(vault_dir):
    assert list_groups(vault_dir) == {}


def test_list_groups_returns_all_groups(vault_dir):
    add_to_group(vault_dir, PASSWORD, "database", "DB_HOST")
    add_to_group(vault_dir, PASSWORD, "api", "API_KEY")
    groups = list_groups(vault_dir)
    assert "database" in groups
    assert "api" in groups


def test_delete_group_returns_true(vault_dir):
    add_to_group(vault_dir, PASSWORD, "database", "DB_HOST")
    result = delete_group(vault_dir, "database")
    assert result is True
    assert list_groups(vault_dir) == {}


def test_delete_nonexistent_group_returns_false(vault_dir):
    result = delete_group(vault_dir, "nonexistent")
    assert result is False


def test_get_group_members_empty_for_unknown_group(vault_dir):
    assert get_group_members(vault_dir, "unknown") == []
