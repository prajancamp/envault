"""Tests for envault.changelog."""

import pytest

from envault.store import save_secrets
from envault.changelog import (
    add_entry,
    get_entries,
    remove_entries,
    list_keys_with_changelog,
)


PASSWORD = "test-pass"


@pytest.fixture()
def vault_dir(tmp_path):
    project = str(tmp_path)
    save_secrets(project, PASSWORD, {"API_KEY": "abc123", "DB_URL": "postgres://"})
    return project


def test_add_entry_returns_dict_with_expected_fields(vault_dir):
    entry = add_entry(vault_dir, PASSWORD, "API_KEY", "Rotated after breach.")
    assert entry["summary"] == "Rotated after breach."
    assert entry["actor"] == "user"
    assert "timestamp" in entry


def test_get_entries_empty_when_none_added(vault_dir):
    assert get_entries(vault_dir, "API_KEY") == []


def test_get_entries_returns_added_entries(vault_dir):
    add_entry(vault_dir, PASSWORD, "API_KEY", "First change.")
    add_entry(vault_dir, PASSWORD, "API_KEY", "Second change.")
    entries = get_entries(vault_dir, "API_KEY")
    assert len(entries) == 2
    assert entries[0]["summary"] == "First change."
    assert entries[1]["summary"] == "Second change."


def test_add_entry_custom_actor(vault_dir):
    entry = add_entry(vault_dir, PASSWORD, "DB_URL", "Updated host.", actor="ci-bot")
    assert entry["actor"] == "ci-bot"


def test_add_entry_missing_key_raises(vault_dir):
    with pytest.raises(KeyError, match="MISSING_KEY"):
        add_entry(vault_dir, PASSWORD, "MISSING_KEY", "This should fail.")


def test_add_entry_wrong_password_raises(vault_dir):
    from envault.crypto import DecryptionError
    with pytest.raises(DecryptionError):
        add_entry(vault_dir, "wrong-pass", "API_KEY", "Should not work.")


def test_remove_entries_returns_count(vault_dir):
    add_entry(vault_dir, PASSWORD, "API_KEY", "Entry one.")
    add_entry(vault_dir, PASSWORD, "API_KEY", "Entry two.")
    count = remove_entries(vault_dir, "API_KEY")
    assert count == 2


def test_remove_entries_clears_key(vault_dir):
    add_entry(vault_dir, PASSWORD, "API_KEY", "Some note.")
    remove_entries(vault_dir, "API_KEY")
    assert get_entries(vault_dir, "API_KEY") == []


def test_remove_entries_nonexistent_key_returns_zero(vault_dir):
    assert remove_entries(vault_dir, "GHOST_KEY") == 0


def test_list_keys_with_changelog_empty_when_no_entries(vault_dir):
    assert list_keys_with_changelog(vault_dir) == []


def test_list_keys_with_changelog_returns_keys(vault_dir):
    add_entry(vault_dir, PASSWORD, "API_KEY", "Changed.")
    add_entry(vault_dir, PASSWORD, "DB_URL", "Updated.")
    keys = list_keys_with_changelog(vault_dir)
    assert set(keys) == {"API_KEY", "DB_URL"}


def test_entries_are_persisted_across_calls(vault_dir):
    add_entry(vault_dir, PASSWORD, "API_KEY", "Persisted entry.")
    entries = get_entries(vault_dir, "API_KEY")
    assert len(entries) == 1
    assert entries[0]["summary"] == "Persisted entry."
