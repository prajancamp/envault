"""Tests for envault.labels."""

from __future__ import annotations

import pytest

from envault.labels import filter_by_label, get_labels, remove_label, set_label
from envault.store import save_secrets

PASSWORD = "test-pass"


@pytest.fixture()
def vault_dir(tmp_path):
    save_secrets(str(tmp_path), PASSWORD, {"API_KEY": "abc123", "DB_PASS": "secret"})
    return str(tmp_path)


def test_set_label_adds_label(vault_dir):
    set_label(vault_dir, PASSWORD, "API_KEY", "env", "production")
    labels = get_labels(vault_dir, PASSWORD, "API_KEY")
    assert labels["env"] == "production"


def test_set_label_multiple_labels(vault_dir):
    set_label(vault_dir, PASSWORD, "API_KEY", "env", "staging")
    set_label(vault_dir, PASSWORD, "API_KEY", "team", "backend")
    labels = get_labels(vault_dir, PASSWORD, "API_KEY")
    assert labels["env"] == "staging"
    assert labels["team"] == "backend"


def test_set_label_updates_existing(vault_dir):
    set_label(vault_dir, PASSWORD, "API_KEY", "env", "staging")
    set_label(vault_dir, PASSWORD, "API_KEY", "env", "production")
    labels = get_labels(vault_dir, PASSWORD, "API_KEY")
    assert labels["env"] == "production"


def test_set_label_missing_key_raises(vault_dir):
    with pytest.raises(KeyError):
        set_label(vault_dir, PASSWORD, "MISSING", "env", "production")


def test_get_labels_returns_empty_when_none_set(vault_dir):
    labels = get_labels(vault_dir, PASSWORD, "API_KEY")
    assert labels == {}


def test_remove_label_deletes_entry(vault_dir):
    set_label(vault_dir, PASSWORD, "API_KEY", "env", "production")
    removed = remove_label(vault_dir, PASSWORD, "API_KEY", "env")
    assert removed is True
    assert get_labels(vault_dir, PASSWORD, "API_KEY") == {}


def test_remove_label_returns_false_when_not_set(vault_dir):
    removed = remove_label(vault_dir, PASSWORD, "API_KEY", "nonexistent")
    assert removed is False


def test_remove_label_leaves_other_labels(vault_dir):
    set_label(vault_dir, PASSWORD, "API_KEY", "env", "prod")
    set_label(vault_dir, PASSWORD, "API_KEY", "team", "backend")
    remove_label(vault_dir, PASSWORD, "API_KEY", "env")
    labels = get_labels(vault_dir, PASSWORD, "API_KEY")
    assert "env" not in labels
    assert labels["team"] == "backend"


def test_filter_by_label_returns_matching_keys(vault_dir):
    set_label(vault_dir, PASSWORD, "API_KEY", "env", "production")
    set_label(vault_dir, PASSWORD, "DB_PASS", "env", "production")
    keys = filter_by_label(vault_dir, PASSWORD, "env")
    assert "API_KEY" in keys
    assert "DB_PASS" in keys


def test_filter_by_label_with_value(vault_dir):
    set_label(vault_dir, PASSWORD, "API_KEY", "env", "production")
    set_label(vault_dir, PASSWORD, "DB_PASS", "env", "staging")
    keys = filter_by_label(vault_dir, PASSWORD, "env", "production")
    assert keys == ["API_KEY"]


def test_filter_by_label_empty_when_no_match(vault_dir):
    keys = filter_by_label(vault_dir, PASSWORD, "nonexistent")
    assert keys == []
