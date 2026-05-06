"""Tests for envault.cli_access (CLI access-control commands)."""
from __future__ import annotations

import argparse
import types
from unittest.mock import patch

import pytest

from envault import access
from envault.cli_access import cmd_acl_set, cmd_acl_remove, cmd_acl_show
from envault.store import save_secrets


@pytest.fixture()
def tmp_project(tmp_path):
    vd = str(tmp_path)
    save_secrets(vd, "secret", {"MY_KEY": "value1", "OTHER": "value2"})
    return vd


def _make_args(project_dir: str, **kwargs) -> argparse.Namespace:
    ns = argparse.Namespace(project_dir=project_dir, **kwargs)
    return ns


def _patch_pw(pw: str):
    return patch("envault.cli_access._get_password", return_value=pw)


def test_acl_set_success(tmp_project):
    args = _make_args(tmp_project, key="MY_KEY", users="alice,bob")
    with _patch_pw("secret"):
        rc = cmd_acl_set(args)
    assert rc == 0
    allowed = access.get_acl(tmp_project, "secret", "MY_KEY")
    assert set(allowed) == {"alice", "bob"}


def test_acl_set_missing_key_returns_1(tmp_project):
    args = _make_args(tmp_project, key="MISSING", users="alice")
    with _patch_pw("secret"):
        rc = cmd_acl_set(args)
    assert rc == 1


def test_acl_set_empty_users_returns_1(tmp_project):
    args = _make_args(tmp_project, key="MY_KEY", users="  ,  ")
    with _patch_pw("secret"):
        rc = cmd_acl_set(args)
    assert rc == 1


def test_acl_remove_success(tmp_project):
    access.set_acl(tmp_project, "secret", "MY_KEY", ["alice"])
    args = _make_args(tmp_project, key="MY_KEY")
    with _patch_pw("secret"):
        rc = cmd_acl_remove(args)
    assert rc == 0
    assert access.get_acl(tmp_project, "secret", "MY_KEY") == []


def test_acl_show_unrestricted(tmp_project, capsys):
    args = _make_args(tmp_project, key="MY_KEY")
    with _patch_pw("secret"):
        rc = cmd_acl_show(args)
    assert rc == 0
    out = capsys.readouterr().out
    assert "unrestricted" in out


def test_acl_show_restricted(tmp_project, capsys):
    access.set_acl(tmp_project, "secret", "OTHER", ["dave"])
    args = _make_args(tmp_project, key="OTHER")
    with _patch_pw("secret"):
        rc = cmd_acl_show(args)
    assert rc == 0
    out = capsys.readouterr().out
    assert "dave" in out
