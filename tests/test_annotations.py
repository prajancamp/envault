"""Tests for envault.annotations."""
from __future__ import annotations

import pytest

from envault.annotations import (
    clear_annotation_for_deleted_keys,
    get_annotation,
    list_annotations,
    remove_annotation,
    set_annotation,
)
from envault.store import set_secret

PASSWORD = "test-pass"


@pytest.fixture()
def vault_dir(tmp_path):
    set_secret(str(tmp_path), PASSWORD, "DB_URL", "postgres://localhost/mydb")
    set_secret(str(tmp_path), PASSWORD, "API_KEY", "secret123")
    return str(tmp_path)


def test_set_and_get_annotation(vault_dir):
    set_annotation(vault_dir, PASSWORD, "DB_URL", "Primary database connection string")
    assert get_annotation(vault_dir, "DB_URL") == "Primary database connection string"


def test_get_annotation_returns_none_when_not_set(vault_dir):
    assert get_annotation(vault_dir, "API_KEY") is None


def test_set_annotation_missing_key_raises(vault_dir):
    with pytest.raises(KeyError, match="MISSING_KEY"):
        set_annotation(vault_dir, PASSWORD, "MISSING_KEY", "some text")


def test_set_annotation_wrong_password_raises(vault_dir):
    with pytest.raises(Exception):
        set_annotation(vault_dir, "wrong-password", "DB_URL", "text")


def test_remove_annotation_returns_true_when_exists(vault_dir):
    set_annotation(vault_dir, PASSWORD, "DB_URL", "A note")
    assert remove_annotation(vault_dir, "DB_URL") is True
    assert get_annotation(vault_dir, "DB_URL") is None


def test_remove_annotation_returns_false_when_not_set(vault_dir):
    assert remove_annotation(vault_dir, "API_KEY") is False


def test_list_annotations_empty_when_none_set(vault_dir):
    assert list_annotations(vault_dir) == {}


def test_list_annotations_returns_all(vault_dir):
    set_annotation(vault_dir, PASSWORD, "DB_URL", "db note")
    set_annotation(vault_dir, PASSWORD, "API_KEY", "api note")
    result = list_annotations(vault_dir)
    assert result == {"DB_URL": "db note", "API_KEY": "api note"}


def test_set_annotation_overwrites_existing(vault_dir):
    set_annotation(vault_dir, PASSWORD, "DB_URL", "first")
    set_annotation(vault_dir, PASSWORD, "DB_URL", "second")
    assert get_annotation(vault_dir, "DB_URL") == "second"


def test_clear_annotation_for_deleted_keys(vault_dir):
    set_annotation(vault_dir, PASSWORD, "DB_URL", "a note")
    # Manually inject a stale annotation without going through set_secret
    from envault.annotations import _load_annotations, _save_annotations
    data = _load_annotations(vault_dir)
    data["GHOST_KEY"] = "stale"
    _save_annotations(vault_dir, data)

    pruned = clear_annotation_for_deleted_keys(vault_dir, PASSWORD)
    assert pruned == 1
    assert get_annotation(vault_dir, "GHOST_KEY") is None
    assert get_annotation(vault_dir, "DB_URL") == "a note"
