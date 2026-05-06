"""Tests for envault.tags module."""
from __future__ import annotations

import pytest

from envault.store import save_secrets
from envault.tags import (
    filter_by_tag,
    get_tags,
    list_all_tags,
    remove_tag,
    set_tag,
)

PASSWORD = "test-password"


@pytest.fixture()
def vault_dir(tmp_path):
    save_secrets(str(tmp_path), PASSWORD, {"DB_URL": "postgres://", "API_KEY": "abc123", "SECRET": "shhh"})
    return str(tmp_path)


def test_set_tag_adds_tag(vault_dir):
    set_tag(vault_dir, PASSWORD, "DB_URL", "database")
    tags = get_tags(vault_dir, PASSWORD, "DB_URL")
    assert "database" in tags


def test_set_tag_multiple_tags(vault_dir):
    set_tag(vault_dir, PASSWORD, "API_KEY", "external")
    set_tag(vault_dir, PASSWORD, "API_KEY", "sensitive")
    tags = get_tags(vault_dir, PASSWORD, "API_KEY")
    assert "external" in tags
    assert "sensitive" in tags


def test_set_tag_idempotent(vault_dir):
    set_tag(vault_dir, PASSWORD, "DB_URL", "database")
    set_tag(vault_dir, PASSWORD, "DB_URL", "database")
    tags = get_tags(vault_dir, PASSWORD, "DB_URL")
    assert tags.count("database") == 1


def test_set_tag_missing_key_raises(vault_dir):
    with pytest.raises(KeyError, match="MISSING"):
        set_tag(vault_dir, PASSWORD, "MISSING", "any")


def test_remove_tag_removes_tag(vault_dir):
    set_tag(vault_dir, PASSWORD, "DB_URL", "database")
    set_tag(vault_dir, PASSWORD, "DB_URL", "prod")
    remove_tag(vault_dir, PASSWORD, "DB_URL", "prod")
    tags = get_tags(vault_dir, PASSWORD, "DB_URL")
    assert "prod" not in tags
    assert "database" in tags


def test_remove_tag_nonexistent_is_noop(vault_dir):
    remove_tag(vault_dir, PASSWORD, "DB_URL", "ghost")
    tags = get_tags(vault_dir, PASSWORD, "DB_URL")
    assert "ghost" not in tags


def test_get_tags_empty_when_none_set(vault_dir):
    tags = get_tags(vault_dir, PASSWORD, "DB_URL")
    assert tags == []


def test_filter_by_tag_returns_matching_secrets(vault_dir):
    set_tag(vault_dir, PASSWORD, "DB_URL", "database")
    set_tag(vault_dir, PASSWORD, "API_KEY", "external")
    result = filter_by_tag(vault_dir, PASSWORD, "database")
    assert "DB_URL" in result
    assert "API_KEY" not in result


def test_filter_by_tag_excludes_meta_keys(vault_dir):
    set_tag(vault_dir, PASSWORD, "DB_URL", "database")
    result = filter_by_tag(vault_dir, PASSWORD, "database")
    for key in result:
        assert not key.startswith("__tag__")


def test_list_all_tags_returns_mapping(vault_dir):
    set_tag(vault_dir, PASSWORD, "DB_URL", "database")
    set_tag(vault_dir, PASSWORD, "API_KEY", "external")
    set_tag(vault_dir, PASSWORD, "API_KEY", "sensitive")
    mapping = list_all_tags(vault_dir, PASSWORD)
    assert mapping["DB_URL"] == ["database"]
    assert "external" in mapping["API_KEY"]
    assert "sensitive" in mapping["API_KEY"]
    assert "SECRET" not in mapping


def test_list_all_tags_empty_when_none_set(vault_dir):
    mapping = list_all_tags(vault_dir, PASSWORD)
    assert mapping == {}
