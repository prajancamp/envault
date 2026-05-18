"""Tests for envault.cli_bookmarks."""

from __future__ import annotations

import argparse
import pytest

from envault.bookmarks import add_bookmark
from envault.cli_bookmarks import (
    cmd_bookmark_add,
    cmd_bookmark_check,
    cmd_bookmark_list,
    cmd_bookmark_remove,
)
from envault.store import save_secrets

PASSWORD = "cli-pass"


@pytest.fixture()
def tmp_project(tmp_path):
    save_secrets(str(tmp_path), PASSWORD, {"MY_KEY": "value1", "OTHER": "value2"})
    return str(tmp_path)


def _make_args(**kwargs) -> argparse.Namespace:
    defaults = {"project_dir": None, "password": PASSWORD, "key": None, "note": ""}
    defaults.update(kwargs)
    return argparse.Namespace(**defaults)


def _patch_pw(monkeypatch):
    monkeypatch.setattr("envault.cli_bookmarks.getpass.getpass", lambda _: PASSWORD)


def test_bookmark_add_success(tmp_project):
    args = _make_args(project_dir=tmp_project, key="MY_KEY", note="important")
    assert cmd_bookmark_add(args) == 0


def test_bookmark_add_missing_key_returns_1(tmp_project):
    args = _make_args(project_dir=tmp_project, key="MISSING")
    assert cmd_bookmark_add(args) == 1


def test_bookmark_remove_success(tmp_project):
    add_bookmark(tmp_project, PASSWORD, "MY_KEY")
    args = _make_args(project_dir=tmp_project, key="MY_KEY")
    assert cmd_bookmark_remove(args) == 0


def test_bookmark_remove_not_present_returns_1(tmp_project):
    args = _make_args(project_dir=tmp_project, key="MY_KEY")
    assert cmd_bookmark_remove(args) == 1


def test_bookmark_list_empty(tmp_project, capsys):
    args = _make_args(project_dir=tmp_project)
    assert cmd_bookmark_list(args) == 0
    out = capsys.readouterr().out
    assert "No bookmarks" in out


def test_bookmark_list_shows_entries(tmp_project, capsys):
    add_bookmark(tmp_project, PASSWORD, "MY_KEY", note="note here")
    args = _make_args(project_dir=tmp_project)
    cmd_bookmark_list(args)
    out = capsys.readouterr().out
    assert "MY_KEY" in out
    assert "note here" in out


def test_bookmark_check_bookmarked_returns_0(tmp_project):
    add_bookmark(tmp_project, PASSWORD, "MY_KEY")
    args = _make_args(project_dir=tmp_project, key="MY_KEY")
    assert cmd_bookmark_check(args) == 0


def test_bookmark_check_not_bookmarked_returns_1(tmp_project):
    args = _make_args(project_dir=tmp_project, key="MY_KEY")
    assert cmd_bookmark_check(args) == 1
