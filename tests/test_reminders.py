"""Tests for envault.reminders."""
from __future__ import annotations

import pytest
from datetime import datetime, timezone
from pathlib import Path

from envault.reminders import (
    due_reminders,
    get_reminder,
    remove_reminder,
    set_reminder,
)
from envault.store import save_secrets

PASSWORD = "testpass"


@pytest.fixture()
def vault_dir(tmp_path: Path) -> str:
    d = str(tmp_path)
    save_secrets(d, PASSWORD, {"API_KEY": "secret123", "DB_PASS": "hunter2"})
    return d


def test_set_reminder_returns_future_datetime(vault_dir):
    remind_at = set_reminder(vault_dir, PASSWORD, "API_KEY", days=30)
    assert isinstance(remind_at, datetime)
    assert remind_at > datetime.now(timezone.utc)


def test_get_reminder_returns_none_when_not_set(vault_dir):
    result = get_reminder(vault_dir, PASSWORD, "API_KEY")
    assert result is None


def test_get_reminder_returns_data_after_set(vault_dir):
    set_reminder(vault_dir, PASSWORD, "API_KEY", days=7, message="rotate soon")
    info = get_reminder(vault_dir, PASSWORD, "API_KEY")
    assert info is not None
    assert isinstance(info["remind_at"], datetime)
    assert info["message"] == "rotate soon"


def test_set_reminder_missing_key_raises(vault_dir):
    with pytest.raises(KeyError):
        set_reminder(vault_dir, PASSWORD, "NONEXISTENT", days=5)


def test_remove_reminder_returns_true_when_exists(vault_dir):
    set_reminder(vault_dir, PASSWORD, "API_KEY", days=10)
    result = remove_reminder(vault_dir, PASSWORD, "API_KEY")
    assert result is True


def test_remove_reminder_returns_false_when_not_set(vault_dir):
    result = remove_reminder(vault_dir, PASSWORD, "API_KEY")
    assert result is False


def test_remove_reminder_clears_data(vault_dir):
    set_reminder(vault_dir, PASSWORD, "DB_PASS", days=3)
    remove_reminder(vault_dir, PASSWORD, "DB_PASS")
    assert get_reminder(vault_dir, PASSWORD, "DB_PASS") is None


def test_due_reminders_empty_when_none_set(vault_dir):
    assert due_reminders(vault_dir, PASSWORD) == []


def test_due_reminders_returns_past_reminders(vault_dir):
    # Force a reminder in the past by setting days=0 then patching remind_at
    from envault.store import load_secrets, save_secrets
    import json
    from datetime import timedelta

    past = (datetime.now(timezone.utc) - timedelta(days=1)).isoformat()
    secrets = load_secrets(vault_dir, PASSWORD)
    secrets["__reminder__API_KEY"] = json.dumps({"remind_at": past, "message": "overdue"})
    save_secrets(vault_dir, PASSWORD, secrets)

    due = due_reminders(vault_dir, PASSWORD)
    assert len(due) == 1
    assert due[0]["key"] == "API_KEY"
    assert due[0]["message"] == "overdue"


def test_due_reminders_excludes_future_reminders(vault_dir):
    set_reminder(vault_dir, PASSWORD, "API_KEY", days=30)
    due = due_reminders(vault_dir, PASSWORD)
    assert due == []
