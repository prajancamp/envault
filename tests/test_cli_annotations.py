"""Tests for envault.cli_annotations."""
from __future__ import annotations

import argparse
import types

import pytest

from envault.cli_annotations import (
    add_annotation_commands,
    cmd_annotation_get,
    cmd_annotation_list,
    cmd_annotation_remove,
    cmd_annotation_set,
)
from envault.store import set_secret

PASSWORD = "cli-pass"


@pytest.fixture()
def tmp_project(tmp_path):
    set_secret(str(tmp_path), PASSWORD, "TOKEN", "abc123")
    return str(tmp_path)


def _make_args(**kwargs):
    defaults = {"vault_dir": ".", "password": PASSWORD}
    defaults.update(kwargs)
    return types.SimpleNamespace(**defaults)


def test_annotation_set_success(tmp_project):
    args = _make_args(vault_dir=tmp_project, key="TOKEN", text="Auth token for CI")
    assert cmd_annotation_set(args) == 0


def test_annotation_set_missing_key_returns_1(tmp_project):
    args = _make_args(vault_dir=tmp_project, key="NONEXISTENT", text="text")
    assert cmd_annotation_set(args) == 1


def test_annotation_get_returns_0_when_set(tmp_project, capsys):
    args_set = _make_args(vault_dir=tmp_project, key="TOKEN", text="My note")
    cmd_annotation_set(args_set)

    args_get = _make_args(vault_dir=tmp_project, key="TOKEN")
    rc = cmd_annotation_get(args_get)
    assert rc == 0
    assert "My note" in capsys.readouterr().out


def test_annotation_get_returns_1_when_not_set(tmp_project):
    args = _make_args(vault_dir=tmp_project, key="TOKEN")
    assert cmd_annotation_get(args) == 1


def test_annotation_remove_success(tmp_project):
    args_set = _make_args(vault_dir=tmp_project, key="TOKEN", text="to remove")
    cmd_annotation_set(args_set)
    args_rm = _make_args(vault_dir=tmp_project, key="TOKEN")
    assert cmd_annotation_remove(args_rm) == 0


def test_annotation_remove_returns_1_when_not_set(tmp_project):
    args = _make_args(vault_dir=tmp_project, key="TOKEN")
    assert cmd_annotation_remove(args) == 1


def test_annotation_list_empty(tmp_project, capsys):
    args = _make_args(vault_dir=tmp_project)
    rc = cmd_annotation_list(args)
    assert rc == 0
    assert "No annotations" in capsys.readouterr().out


def test_annotation_list_shows_entries(tmp_project, capsys):
    cmd_annotation_set(_make_args(vault_dir=tmp_project, key="TOKEN", text="a note"))
    args = _make_args(vault_dir=tmp_project)
    rc = cmd_annotation_list(args)
    assert rc == 0
    out = capsys.readouterr().out
    assert "TOKEN" in out
    assert "a note" in out


def test_add_annotation_commands_registers_subcommands():
    parser = argparse.ArgumentParser()
    subs = parser.add_subparsers()
    add_annotation_commands(subs)
    choices = list(subs.choices.keys())
    assert "annotation-set" in choices
    assert "annotation-get" in choices
    assert "annotation-remove" in choices
    assert "annotation-list" in choices
