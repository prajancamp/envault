"""Tests for envault.watchlist."""

from __future__ import annotations

import pytest

from envault.store import save_secrets
from envault.watchlist import (
    add_to_watchlist,
    remove_from_watchlist,
    is_watched,
    get_watchlist,
    watchlist_summary,
)

PASSWORD = "test-password"


@pytest.fixture()
def vault_dir(tmp_path):
    project = str(tmp_path)
    save_secrets(project, PASSWORD, {"API_KEY": "abc123", "DB_PASS": "secret"})
    return project


def test_add_to_watchlist_marks_key(vault_dir):
    add_to_watchlist(vault_dir, PASSWORD, "API_KEY")
    assert is_watched(vault_dir, "API_KEY") is True


def test_add_to_watchlist_stores_reason(vault_dir):
    add_to_watchlist(vault_dir, PASSWORD, "DB_PASS", reason="sensitive credential")
    items = get_watchlist(vault_dir)
    entry = next(i for i in items if i["key"] == "DB_PASS")
    assert entry["reason"] == "sensitive credential"


def test_add_to_watchlist_missing_key_raises(vault_dir):
    with pytest.raises(KeyError, match="MISSING_KEY"):
        add_to_watchlist(vault_dir, PASSWORD, "MISSING_KEY")


def test_is_watched_returns_false_when_not_added(vault_dir):
    assert is_watched(vault_dir, "API_KEY") is False


def test_remove_from_watchlist_returns_true_when_present(vault_dir):
    add_to_watchlist(vault_dir, PASSWORD, "API_KEY")
    result = remove_from_watchlist(vault_dir, "API_KEY")
    assert result is True
    assert is_watched(vault_dir, "API_KEY") is False


def test_remove_from_watchlist_returns_false_when_absent(vault_dir):
    result = remove_from_watchlist(vault_dir, "API_KEY")
    assert result is False


def test_get_watchlist_empty_when_none_added(vault_dir):
    assert get_watchlist(vault_dir) == []


def test_get_watchlist_returns_all_watched_keys(vault_dir):
    add_to_watchlist(vault_dir, PASSWORD, "API_KEY", reason="r1")
    add_to_watchlist(vault_dir, PASSWORD, "DB_PASS", reason="r2")
    items = get_watchlist(vault_dir)
    keys = [i["key"] for i in items]
    assert "API_KEY" in keys
    assert "DB_PASS" in keys


def test_get_watchlist_is_sorted(vault_dir):
    add_to_watchlist(vault_dir, PASSWORD, "DB_PASS")
    add_to_watchlist(vault_dir, PASSWORD, "API_KEY")
    keys = [i["key"] for i in get_watchlist(vault_dir)]
    assert keys == sorted(keys)


def test_watchlist_summary_counts(vault_dir):
    add_to_watchlist(vault_dir, PASSWORD, "API_KEY")
    add_to_watchlist(vault_dir, PASSWORD, "DB_PASS")
    summary = watchlist_summary(vault_dir)
    assert summary["total_watched"] == 2
    assert set(summary["keys"]) == {"API_KEY", "DB_PASS"}


def test_watchlist_summary_empty(vault_dir):
    summary = watchlist_summary(vault_dir)
    assert summary["total_watched"] == 0
    assert summary["keys"] == []
