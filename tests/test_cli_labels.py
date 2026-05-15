"""Tests for envault.cli_labels."""

from __future__ import annotations

import argparse

import pytest

from envault.cli_labels import (
    add_label_commands,
    cmd_label_filter,
    cmd_label_list,
    cmd_label_remove,
    cmd_label_set,
)
from envault.labels import set_label
from envault.store import save_secrets

PASSWORD = "cli-test-pass"


@pytest.fixture()
def tmp_project(tmp_path):
    save_secrets(str(tmp_path), PASSWORD, {"API_KEY": "abc123", "DB_PASS": "secret"})
    return tmp_path


def _make_args(tmp_path, **kwargs):
    ns = argparse.Namespace(project_dir=str(tmp_path), password=PASSWORD)
    for k, v in kwargs.items():
        setattr(ns, k, v)
    return ns


def test_label_set_success(tmp_project):
    args = _make_args(tmp_project, key="API_KEY", label="env", value="prod")
    assert cmd_label_set(args) == 0


def test_label_set_missing_key_returns_1(tmp_project):
    args = _make_args(tmp_project, key="MISSING", label="env", value="prod")
    assert cmd_label_set(args) == 1


def test_label_list_shows_labels(tmp_project, capsys):
    set_label(str(tmp_project), PASSWORD, "API_KEY", "env", "prod")
    args = _make_args(tmp_project, key="API_KEY")
    rc = cmd_label_list(args)
    assert rc == 0
    out = capsys.readouterr().out
    assert "env=prod" in out


def test_label_list_no_labels_message(tmp_project, capsys):
    args = _make_args(tmp_project, key="API_KEY")
    rc = cmd_label_list(args)
    assert rc == 0
    assert "No labels" in capsys.readouterr().out


def test_label_remove_existing(tmp_project, capsys):
    set_label(str(tmp_project), PASSWORD, "API_KEY", "env", "prod")
    args = _make_args(tmp_project, key="API_KEY", label="env")
    rc = cmd_label_remove(args)
    assert rc == 0
    assert "removed" in capsys.readouterr().out


def test_label_remove_nonexistent(tmp_project, capsys):
    args = _make_args(tmp_project, key="API_KEY", label="ghost")
    rc = cmd_label_remove(args)
    assert rc == 0
    assert "not found" in capsys.readouterr().out


def test_label_filter_returns_matching(tmp_project, capsys):
    set_label(str(tmp_project), PASSWORD, "API_KEY", "tier", "gold")
    args = _make_args(tmp_project, label="tier", value=None)
    rc = cmd_label_filter(args)
    assert rc == 0
    assert "API_KEY" in capsys.readouterr().out


def test_label_filter_no_match_message(tmp_project, capsys):
    args = _make_args(tmp_project, label="missing", value=None)
    rc = cmd_label_filter(args)
    assert rc == 0
    assert "No secrets match" in capsys.readouterr().out


def test_add_label_commands_registers_subcommands():
    parser = argparse.ArgumentParser()
    sub = parser.add_subparsers()
    add_label_commands(sub)
    known = {a.dest for a in sub._group_actions}  # type: ignore[attr-defined]
    # parse each subcommand to confirm registration
    for cmd in ("label-set", "label-remove", "label-list", "label-filter"):
        parsed, _ = parser.parse_known_args([cmd, "--help"] if False else [cmd, "k"] if cmd != "label-filter" else [cmd, "l"])
