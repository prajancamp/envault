"""Tests for envault.bookmarks."""

from __future__ import annotations

import pytest

from envault.bookmarks import (
    add_bookmark,
    get_bookmark_note,
    is_bookmarked,
    list_bookmarks,
    remove_bookmark,
)
from envault.store import save_secrets

PASSWORD = "test-pass"


@pytest.fixture()
def vault_dir(tmp_path):
    save_secrets(str(tmp_path), PASSWORD, {"DB_URL": "postgres://localhost", "API_KEY": "abc123"})
    return str(tmp_path)


def test_add_bookmark_marks_key(vault_dir):
    add_bookmark(vault_dir, PASSWORD, "DB_URL")
    assert is_bookmarked(vault_dir, "DB_URL")


def test_add_bookmark_stores_note(vault_dir):
    add_bookmark(vault_dir, PASSWORD, "API_KEY", note="primary API key")
    assert get_bookmark_note(vault_dir, "API_KEY") == "primary API key"


def test_add_bookmark_missing_key_raises(vault_dir):
    with pytest.raises(KeyError):
        add_bookmark(vault_dir, PASSWORD, "NONEXISTENT")


def test_is_bookmarked_returns_false_when_not_added(vault_dir):
    assert not is_bookmarked(vault_dir, "DB_URL")


def test_add_bookmark_idempotent(vault_dir):
    add_bookmark(vault_dir, PASSWORD, "DB_URL", note="first")
    add_bookmark(vault_dir, PASSWORD, "DB_URL", note="second")
    assert get_bookmark_note(vault_dir, "DB_URL") == "second"


def test_remove_bookmark_returns_true_when_existed(vault_dir):
    add_bookmark(vault_dir, PASSWORD, "DB_URL")
    assert remove_bookmark(vault_dir, "DB_URL") is True
    assert not is_bookmarked(vault_dir, "DB_URL")


def test_remove_bookmark_returns_false_when_not_present(vault_dir):
    assert remove_bookmark(vault_dir, "DB_URL") is False


def test_list_bookmarks_empty_when_none_added(vault_dir):
    assert list_bookmarks(vault_dir) == []


def test_list_bookmarks_returns_all_entries(vault_dir):
    add_bookmark(vault_dir, PASSWORD, "API_KEY", note="key")
    add_bookmark(vault_dir, PASSWORD, "DB_URL")
    items = list_bookmarks(vault_dir)
    keys = [i["key"] for i in items]
    assert "API_KEY" in keys
    assert "DB_URL" in keys


def test_list_bookmarks_sorted_by_key(vault_dir):
    add_bookmark(vault_dir, PASSWORD, "DB_URL")
    add_bookmark(vault_dir, PASSWORD, "API_KEY")
    keys = [i["key"] for i in list_bookmarks(vault_dir)]
    assert keys == sorted(keys)


def test_get_bookmark_note_returns_none_when_not_bookmarked(vault_dir):
    assert get_bookmark_note(vault_dir, "DB_URL") is None
