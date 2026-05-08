"""Integration tests for envault.cli_hooks CLI commands."""
from __future__ import annotations

import argparse
from pathlib import Path

import pytest

from envault import hooks as hk
from envault.cli_hooks import add_hook_commands, cmd_hook_list, cmd_hook_remove, cmd_hook_set


@pytest.fixture()
def tmp_project(tmp_path: Path) -> Path:
    return tmp_path


def _make_args(project_dir: Path, **kwargs) -> argparse.Namespace:
    ns = argparse.Namespace(project_dir=str(project_dir))
    for k, v in kwargs.items():
        setattr(ns, k, v)
    return ns


def test_hook_set_success(tmp_project: Path) -> None:
    args = _make_args(tmp_project, event="post_set", command="echo done")
    rc = cmd_hook_set(args)
    assert rc == 0
    assert hk.list_hooks(tmp_project)["post_set"] == ["echo done"]


def test_hook_set_invalid_event_returns_1(tmp_project: Path) -> None:
    args = _make_args(tmp_project, event="bad", command="echo x")
    # argparse choices enforcement means we simulate a ValueError path
    # by patching the event after namespace creation
    args.event = "totally_invalid"
    rc = cmd_hook_set(args)
    assert rc == 1


def test_hook_remove_specific_command(tmp_project: Path) -> None:
    hk.set_hook(tmp_project, "pre_get", "echo a")
    hk.set_hook(tmp_project, "pre_get", "echo b")
    args = _make_args(tmp_project, event="pre_get", command="echo a")
    rc = cmd_hook_remove(args)
    assert rc == 0
    assert hk.list_hooks(tmp_project)["pre_get"] == ["echo b"]


def test_hook_remove_all_commands(tmp_project: Path) -> None:
    hk.set_hook(tmp_project, "pre_get", "echo a")
    args = _make_args(tmp_project, event="pre_get", command=None)
    rc = cmd_hook_remove(args)
    assert rc == 0
    assert "pre_get" not in hk.list_hooks(tmp_project)


def test_hook_list_empty(tmp_project: Path, capsys) -> None:
    args = _make_args(tmp_project)
    rc = cmd_hook_list(args)
    assert rc == 0
    captured = capsys.readouterr()
    assert "No hooks" in captured.out


def test_hook_list_shows_registered_hooks(tmp_project: Path, capsys) -> None:
    hk.set_hook(tmp_project, "post_set", "make deploy")
    args = _make_args(tmp_project)
    rc = cmd_hook_list(args)
    assert rc == 0
    captured = capsys.readouterr()
    assert "post_set" in captured.out
    assert "make deploy" in captured.out


def test_add_hook_commands_registers_subparsers() -> None:
    parser = argparse.ArgumentParser()
    sub = parser.add_subparsers()
    add_hook_commands(sub)
    args = parser.parse_args(["hook-list", "--help"] if False else ["hook-list"])
    # No AttributeError means subcommand was registered
    assert True
