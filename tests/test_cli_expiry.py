"""Tests for envault.cli_expiry."""

from __future__ import annotations

import argparse
import pytest
from pathlib import Path
from unittest.mock import patch

from envault.store import save_secrets
from envault.ttl import set_ttl
from envault.cli_expiry import cmd_expiry_soon, cmd_expiry_expired, add_expiry_commands

PASSWORD = "clipass"


@pytest.fixture()
def tmp_project(tmp_path: Path) -> Path:
    save_secrets(str(tmp_path), PASSWORD, {"DB_URL": "postgres://", "API_KEY": "secret"})
    return tmp_path


def _make_args(project_dir: str, hours: int = 24, password: str = PASSWORD) -> argparse.Namespace:
    return argparse.Namespace(project_dir=project_dir, hours=hours, password=password)


def _patch_pw(password: str = PASSWORD):
    return patch("envault.cli_expiry._get_password", return_value=password)


def test_expiry_soon_no_ttls_returns_0(tmp_project, capsys):
    args = _make_args(str(tmp_project))
    rc = cmd_expiry_soon(args)
    assert rc == 0
    out = capsys.readouterr().out
    assert "No secrets expiring" in out


def test_expiry_soon_lists_key(tmp_project, capsys):
    set_ttl(str(tmp_project), PASSWORD, "DB_URL", 6)
    args = _make_args(str(tmp_project), hours=24)
    rc = cmd_expiry_soon(args)
    assert rc == 0
    out = capsys.readouterr().out
    assert "DB_URL" in out


def test_expiry_soon_wrong_password_returns_1(tmp_project):
    args = _make_args(str(tmp_project), password="wrongpass")
    rc = cmd_expiry_soon(args)
    assert rc == 1


def test_expiry_expired_no_ttls_returns_0(tmp_project, capsys):
    args = argparse.Namespace(project_dir=str(tmp_project), password=PASSWORD)
    rc = cmd_expiry_expired(args)
    assert rc == 0
    out = capsys.readouterr().out
    assert "No expired" in out


def test_expiry_expired_wrong_password_returns_1(tmp_project):
    args = argparse.Namespace(project_dir=str(tmp_project), password="bad")
    rc = cmd_expiry_expired(args)
    assert rc == 1


def test_add_expiry_commands_registers_subparsers():
    parser = argparse.ArgumentParser()
    sub = parser.add_subparsers()
    add_expiry_commands(sub)
    args = parser.parse_args(["expiry-soon", "/tmp/proj", "--hours", "48"])
    assert args.hours == 48
    args2 = parser.parse_args(["expiry-expired", "/tmp/proj"])
    assert args2.project_dir == "/tmp/proj"
