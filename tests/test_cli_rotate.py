"""Tests for the rotate CLI sub-command."""

from __future__ import annotations

import argparse
from pathlib import Path
from unittest.mock import patch

import pytest

from envault.store import save_secrets, load_secrets
from envault.cli_rotate import cmd_rotate, add_rotate_commands


@pytest.fixture()
def tmp_project(tmp_path: Path) -> Path:
    save_secrets(tmp_path, "old-pass", {"KEY": "value"})
    return tmp_path


def _make_args(project_dir: str) -> argparse.Namespace:
    ns = argparse.Namespace()
    ns.project_dir = project_dir
    return ns


def _patch_prompts(old: str, new: str, confirm: str | None = None):
    """Patch getpass.getpass to return passwords in sequence."""
    responses = [old, new, confirm if confirm is not None else new]
    return patch("getpass.getpass", side_effect=responses)


def test_rotate_success(tmp_project: Path) -> None:
    args = _make_args(str(tmp_project))
    with _patch_prompts("old-pass", "new-pass"):
        rc = cmd_rotate(args)
    assert rc == 0
    secrets = load_secrets(tmp_project, "new-pass")
    assert secrets["KEY"] == "value"


def test_rotate_wrong_old_password_returns_1(tmp_project: Path) -> None:
    args = _make_args(str(tmp_project))
    with _patch_prompts("bad-pass", "new-pass"):
        rc = cmd_rotate(args)
    assert rc == 1


def test_rotate_same_password_returns_1(tmp_project: Path) -> None:
    args = _make_args(str(tmp_project))
    with _patch_prompts("old-pass", "old-pass"):
        rc = cmd_rotate(args)
    assert rc == 1


def test_add_rotate_commands_registers_subparser() -> None:
    parser = argparse.ArgumentParser()
    sub = parser.add_subparsers()
    add_rotate_commands(sub)
    ns = parser.parse_args(["rotate", "/some/path"])
    assert ns.project_dir == "/some/path"
    assert ns.func is cmd_rotate
