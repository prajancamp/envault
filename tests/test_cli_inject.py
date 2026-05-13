"""Tests for envault.cli_inject."""
from __future__ import annotations

import argparse
import sys
from pathlib import Path
from unittest.mock import patch

import pytest

from envault.store import save_secrets
from envault.cli_inject import cmd_inject, add_inject_commands


PASSWORD = "s3cr3t"


@pytest.fixture()
def tmp_project(tmp_path: Path) -> Path:
    save_secrets(str(tmp_path), PASSWORD, {"INJECT_VAR": "hello"})
    return tmp_path


def _make_args(project_dir: Path, command: list, **kwargs) -> argparse.Namespace:
    defaults = dict(
        project_dir=str(project_dir),
        password=PASSWORD,
        prefix=None,
        include_expired=False,
        command=command,
    )
    defaults.update(kwargs)
    return argparse.Namespace(**defaults)


def test_inject_returns_exit_code_zero(tmp_project: Path) -> None:
    args = _make_args(tmp_project, [sys.executable, "-c", "import sys; sys.exit(0)"])
    assert cmd_inject(args) == 0


def test_inject_propagates_nonzero_exit(tmp_project: Path) -> None:
    args = _make_args(tmp_project, [sys.executable, "-c", "import sys; sys.exit(7)"])
    assert cmd_inject(args) == 7


def test_inject_no_command_returns_1(tmp_project: Path) -> None:
    args = _make_args(tmp_project, [])
    assert cmd_inject(args) == 1


def test_inject_secret_visible_in_subprocess(tmp_project: Path) -> None:
    script = "import os, sys; sys.exit(0 if os.environ.get('INJECT_VAR') == 'hello' else 1)"
    args = _make_args(tmp_project, [sys.executable, "-c", script])
    assert cmd_inject(args) == 0


def test_inject_prefix_filters_keys(tmp_project: Path) -> None:
    save_secrets(str(tmp_project), PASSWORD, {"INJECT_VAR": "hello", "OTHER_VAR": "world"})
    script = "import os, sys; sys.exit(0 if 'OTHER_VAR' not in os.environ else 1)"
    args = _make_args(tmp_project, [sys.executable, "-c", script], prefix="INJECT_")
    assert cmd_inject(args) == 0


# ---------------------------------------------------------------------------
# Parser registration
# ---------------------------------------------------------------------------

def test_add_inject_commands_registers_subcommand() -> None:
    parser = argparse.ArgumentParser()
    sub = parser.add_subparsers()
    add_inject_commands(sub)
    parsed = parser.parse_args(["inject", "--", "echo", "hi"])
    assert parsed.func is cmd_inject
    assert parsed.command == ["echo", "hi"]


def test_add_inject_commands_prefix_flag() -> None:
    parser = argparse.ArgumentParser()
    sub = parser.add_subparsers()
    add_inject_commands(sub)
    parsed = parser.parse_args(["inject", "--prefix", "APP_", "--", "env"])
    assert parsed.prefix == "APP_"
