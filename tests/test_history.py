"""Tests for envault.history."""

import pytest
from pathlib import Path

from envault.history import (
    record_change,
    get_history,
    clear_history,
    list_tracked_keys,
)


@pytest.fixture()
def vault_dir(tmp_path: Path) -> Path:
    return tmp_path


def test_get_history_empty_when_no_records(vault_dir: Path) -> None:
    assert get_history(vault_dir, "MY_KEY") == []


def test_record_change_creates_entry(vault_dir: Path) -> None:
    record_change(vault_dir, "MY_KEY", action="set")
    history = get_history(vault_dir, "MY_KEY")
    assert len(history) == 1
    assert history[0]["action"] == "set"
    assert "timestamp" in history[0]
    assert history[0]["actor"] == "user"


def test_record_change_appends_multiple_events(vault_dir: Path) -> None:
    record_change(vault_dir, "DB_PASS", action="set")
    record_change(vault_dir, "DB_PASS", action="set")
    record_change(vault_dir, "DB_PASS", action="delete")
    history = get_history(vault_dir, "DB_PASS")
    assert len(history) == 3
    assert history[-1]["action"] == "delete"


def test_record_change_custom_actor(vault_dir: Path) -> None:
    record_change(vault_dir, "API_KEY", action="set", actor="ci-bot")
    history = get_history(vault_dir, "API_KEY")
    assert history[0]["actor"] == "ci-bot"


def test_clear_history_returns_event_count(vault_dir: Path) -> None:
    record_change(vault_dir, "TOKEN", action="set")
    record_change(vault_dir, "TOKEN", action="set")
    removed = clear_history(vault_dir, "TOKEN")
    assert removed == 2


def test_clear_history_removes_entries(vault_dir: Path) -> None:
    record_change(vault_dir, "TOKEN", action="set")
    clear_history(vault_dir, "TOKEN")
    assert get_history(vault_dir, "TOKEN") == []


def test_clear_history_nonexistent_key_returns_zero(vault_dir: Path) -> None:
    assert clear_history(vault_dir, "GHOST") == 0


def test_list_tracked_keys_empty_when_no_history(vault_dir: Path) -> None:
    assert list_tracked_keys(vault_dir) == []


def test_list_tracked_keys_returns_all_keys(vault_dir: Path) -> None:
    record_change(vault_dir, "ALPHA", action="set")
    record_change(vault_dir, "BETA", action="set")
    record_change(vault_dir, "GAMMA", action="delete")
    keys = list_tracked_keys(vault_dir)
    assert keys == ["ALPHA", "BETA", "GAMMA"]


def test_list_tracked_keys_no_duplicates(vault_dir: Path) -> None:
    record_change(vault_dir, "KEY", action="set")
    record_change(vault_dir, "KEY", action="set")
    keys = list_tracked_keys(vault_dir)
    assert keys.count("KEY") == 1
