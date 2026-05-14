"""Tests for envault.cli_pinning."""

from __future__ import annotations

import argparse
from pathlib import Path
from unittest.mock import patch

import pytest

from envault.store import save_secrets
from envault.pinning import pin_secret
from envault.cli_pinning import cmd_pin_add, cmd_pin_remove, cmd_pin_status, cmd_pin_list

PASSWORD = "cli-test-pw"


@pytest.fixture()
def tmp_project(tmp_path: Path) -> Path:
    save_secrets(tmp_path, {"TOKEN": "xyz", "SECRET": "abc"}, PASSWORD)
    return tmp_path


def _make_args(project: Path, **kwargs) -> argparse.Namespace:
    return argparse.Namespace(project=str(project), **kwargs)


def _patch_pw(pw: str = PASSWORD):
    return patch("envault.cli_pinning.getpass.getpass", return_value=pw)


def test_pin_add_success(tmp_project: Path) -> None:
    args = _make_args(tmp_project, key="TOKEN")
    with _patch_pw():
        result = cmd_pin_add(args)
    assert result == 0


def test_pin_add_missing_key_returns_1(tmp_project: Path) -> None:
    args = _make_args(tmp_project, key="DOES_NOT_EXIST")
    with _patch_pw():
        result = cmd_pin_add(args)
    assert result == 1


def test_pin_add_wrong_password_returns_1(tmp_project: Path) -> None:
    args = _make_args(tmp_project, key="TOKEN")
    with _patch_pw("wrong-password"):
        result = cmd_pin_add(args)
    assert result == 1


def test_pin_remove_success(tmp_project: Path) -> None:
    with _patch_pw():
        cmd_pin_add(_make_args(tmp_project, key="TOKEN"))
    args = _make_args(tmp_project, key="TOKEN")
    result = cmd_pin_remove(args)
    assert result == 0


def test_pin_status_pinned(tmp_project: Path, capsys) -> None:
    with _patch_pw():
        cmd_pin_add(_make_args(tmp_project, key="TOKEN"))
    args = _make_args(tmp_project, key="TOKEN")
    result = cmd_pin_status(args)
    assert result == 0
    captured = capsys.readouterr()
    assert "pinned" in captured.out


def test_pin_status_not_pinned(tmp_project: Path, capsys) -> None:
    args = _make_args(tmp_project, key="SECRET")
    result = cmd_pin_status(args)
    assert result == 0
    captured = capsys.readouterr()
    assert "not pinned" in captured.out


def test_pin_list_empty(tmp_project: Path, capsys) -> None:
    args = _make_args(tmp_project)
    result = cmd_pin_list(args)
    assert result == 0
    captured = capsys.readouterr()
    assert "No pinned" in captured.out


def test_pin_list_shows_pinned_keys(tmp_project: Path, capsys) -> None:
    with _patch_pw():
        cmd_pin_add(_make_args(tmp_project, key="TOKEN"))
        cmd_pin_add(_make_args(tmp_project, key="SECRET"))
    args = _make_args(tmp_project)
    result = cmd_pin_list(args)
    assert result == 0
    captured = capsys.readouterr()
    assert "TOKEN" in captured.out
    assert "SECRET" in captured.out
