"""Tests for envault.cli_reminders."""
from __future__ import annotations

import argparse
import json
from datetime import datetime, timedelta, timezone
from pathlib import Path
from unittest.mock import patch

import pytest

from envault.cli_reminders import (
    cmd_reminder_due,
    cmd_reminder_get,
    cmd_reminder_remove,
    cmd_reminder_set,
)
from envault.store import load_secrets, save_secrets

PASSWORD = "clipass"


@pytest.fixture()
def tmp_project(tmp_path: Path) -> str:
    d = str(tmp_path)
    save_secrets(d, PASSWORD, {"MY_KEY": "myvalue"})
    return d


def _make_args(project_dir, **kwargs) -> argparse.Namespace:
    return argparse.Namespace(project_dir=project_dir, **kwargs)


def _patch_pw(password: str):
    return patch("envault.cli_reminders.getpass.getpass", return_value=password)


def test_reminder_set_success(tmp_project):
    args = _make_args(tmp_project, key="MY_KEY", days=14, message="check this")
    with _patch_pw(PASSWORD):
        rc = cmd_reminder_set(args)
    assert rc == 0


def test_reminder_set_missing_key_returns_1(tmp_project):
    args = _make_args(tmp_project, key="NOPE", days=7, message="")
    with _patch_pw(PASSWORD):
        rc = cmd_reminder_set(args)
    assert rc == 1


def test_reminder_get_shows_info(tmp_project, capsys):
    set_args = _make_args(tmp_project, key="MY_KEY", days=5, message="soon")
    with _patch_pw(PASSWORD):
        cmd_reminder_set(set_args)
    get_args = _make_args(tmp_project, key="MY_KEY")
    with _patch_pw(PASSWORD):
        rc = cmd_reminder_get(get_args)
    assert rc == 0
    out = capsys.readouterr().out
    assert "MY_KEY" in out
    assert "soon" in out


def test_reminder_get_no_reminder(tmp_project, capsys):
    args = _make_args(tmp_project, key="MY_KEY")
    with _patch_pw(PASSWORD):
        rc = cmd_reminder_get(args)
    assert rc == 0
    assert "No reminder" in capsys.readouterr().out


def test_reminder_remove_success(tmp_project, capsys):
    set_args = _make_args(tmp_project, key="MY_KEY", days=3, message="")
    with _patch_pw(PASSWORD):
        cmd_reminder_set(set_args)
    rm_args = _make_args(tmp_project, key="MY_KEY")
    with _patch_pw(PASSWORD):
        rc = cmd_reminder_remove(rm_args)
    assert rc == 0
    assert "removed" in capsys.readouterr().out


def test_reminder_due_lists_overdue(tmp_project, capsys):
    past = (datetime.now(timezone.utc) - timedelta(days=2)).isoformat()
    secrets = load_secrets(tmp_project, PASSWORD)
    secrets["__reminder__MY_KEY"] = json.dumps({"remind_at": past, "message": "urgent"})
    save_secrets(tmp_project, PASSWORD, secrets)

    args = _make_args(tmp_project)
    with _patch_pw(PASSWORD):
        rc = cmd_reminder_due(args)
    assert rc == 0
    out = capsys.readouterr().out
    assert "MY_KEY" in out
    assert "urgent" in out


def test_reminder_due_empty(tmp_project, capsys):
    args = _make_args(tmp_project)
    with _patch_pw(PASSWORD):
        rc = cmd_reminder_due(args)
    assert rc == 0
    assert "No reminders" in capsys.readouterr().out
