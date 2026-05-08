"""Tests for envault.cli_notes."""
from __future__ import annotations

import argparse
from unittest.mock import patch

import pytest

from envault.store import save_secrets
from envault import cli_notes


PASSWORD = "hunter2"


@pytest.fixture()
def tmp_project(tmp_path):
    save_secrets(str(tmp_path), PASSWORD, {"MY_KEY": "myvalue"})
    return str(tmp_path)


def _make_args(**kwargs) -> argparse.Namespace:
    defaults = {"project_dir": None}
    defaults.update(kwargs)
    return argparse.Namespace(**defaults)


def _patch_pw(pw: str = PASSWORD):
    return patch("envault.cli_notes._get_password", return_value=pw)


def test_note_set_and_get(tmp_project, capsys):
    args = _make_args(project_dir=tmp_project, key="MY_KEY", note="Important key")
    with _patch_pw():
        rc = cli_notes.cmd_note_set(args)
    assert rc == 0

    get_args = _make_args(project_dir=tmp_project, key="MY_KEY")
    rc2 = cli_notes.cmd_note_get(get_args)
    captured = capsys.readouterr()
    assert rc2 == 0
    assert "Important key" in captured.out


def test_note_set_missing_key_returns_1(tmp_project):
    args = _make_args(project_dir=tmp_project, key="NOPE", note="x")
    with _patch_pw():
        rc = cli_notes.cmd_note_set(args)
    assert rc == 1


def test_note_get_missing_returns_1(tmp_project, capsys):
    args = _make_args(project_dir=tmp_project, key="MY_KEY")
    rc = cli_notes.cmd_note_get(args)
    assert rc == 1


def test_note_remove_existing(tmp_project):
    from envault import notes
    notes.set_note(tmp_project, PASSWORD, "MY_KEY", "temp")
    args = _make_args(project_dir=tmp_project, key="MY_KEY")
    rc = cli_notes.cmd_note_remove(args)
    assert rc == 0


def test_note_remove_missing_returns_1(tmp_project):
    args = _make_args(project_dir=tmp_project, key="MY_KEY")
    rc = cli_notes.cmd_note_remove(args)
    assert rc == 1


def test_note_list_empty(tmp_project, capsys):
    args = _make_args(project_dir=tmp_project)
    rc = cli_notes.cmd_note_list(args)
    captured = capsys.readouterr()
    assert rc == 0
    assert "No notes" in captured.out


def test_note_list_shows_entries(tmp_project, capsys):
    from envault import notes
    notes.set_note(tmp_project, PASSWORD, "MY_KEY", "a note here")
    args = _make_args(project_dir=tmp_project)
    rc = cli_notes.cmd_note_list(args)
    captured = capsys.readouterr()
    assert rc == 0
    assert "MY_KEY" in captured.out
    assert "a note here" in captured.out


def test_note_purge_no_orphans(tmp_project, capsys):
    args = _make_args(project_dir=tmp_project)
    with _patch_pw():
        rc = cli_notes.cmd_note_purge(args)
    captured = capsys.readouterr()
    assert rc == 0
    assert "No orphaned" in captured.out
