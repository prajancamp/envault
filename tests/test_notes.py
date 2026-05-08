"""Tests for envault.notes."""
from __future__ import annotations

import pytest

from envault.store import save_secrets
from envault import notes


PASSWORD = "hunter2"


@pytest.fixture()
def vault_dir(tmp_path):
    save_secrets(str(tmp_path), PASSWORD, {"API_KEY": "abc", "DB_PASS": "secret"})
    return str(tmp_path)


def test_set_and_get_note(vault_dir):
    notes.set_note(vault_dir, PASSWORD, "API_KEY", "Production API key")
    assert notes.get_note(vault_dir, "API_KEY") == "Production API key"


def test_get_note_returns_none_when_not_set(vault_dir):
    assert notes.get_note(vault_dir, "API_KEY") is None


def test_set_note_missing_key_raises(vault_dir):
    with pytest.raises(KeyError):
        notes.set_note(vault_dir, PASSWORD, "NONEXISTENT", "some note")


def test_set_note_wrong_password_raises(vault_dir):
    with pytest.raises(Exception):
        notes.set_note(vault_dir, "wrongpassword", "API_KEY", "note")


def test_remove_note_returns_true_when_exists(vault_dir):
    notes.set_note(vault_dir, PASSWORD, "API_KEY", "to be removed")
    result = notes.remove_note(vault_dir, "API_KEY")
    assert result is True
    assert notes.get_note(vault_dir, "API_KEY") is None


def test_remove_note_returns_false_when_not_set(vault_dir):
    result = notes.remove_note(vault_dir, "API_KEY")
    assert result is False


def test_list_notes_returns_all(vault_dir):
    notes.set_note(vault_dir, PASSWORD, "API_KEY", "note one")
    notes.set_note(vault_dir, PASSWORD, "DB_PASS", "note two")
    all_notes = notes.list_notes(vault_dir)
    assert all_notes == {"API_KEY": "note one", "DB_PASS": "note two"}


def test_list_notes_empty_when_none_set(vault_dir):
    assert notes.list_notes(vault_dir) == {}


def test_purge_orphaned_notes(vault_dir):
    notes.set_note(vault_dir, PASSWORD, "API_KEY", "keep")
    # Manually inject an orphaned note
    from envault.notes import _load_notes, _save_notes
    raw = _load_notes(vault_dir)
    raw["GHOST_KEY"] = "orphan"
    _save_notes(vault_dir, raw)

    removed = notes.purge_orphaned_notes(vault_dir, PASSWORD)
    assert removed == ["GHOST_KEY"]
    assert notes.get_note(vault_dir, "GHOST_KEY") is None
    assert notes.get_note(vault_dir, "API_KEY") == "keep"


def test_purge_no_orphans_returns_empty(vault_dir):
    notes.set_note(vault_dir, PASSWORD, "API_KEY", "valid")
    removed = notes.purge_orphaned_notes(vault_dir, PASSWORD)
    assert removed == []
