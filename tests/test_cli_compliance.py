"""Tests for envault.cli_compliance."""
from __future__ import annotations

import argparse
import json

import pytest

from envault.store import save_secrets
from envault.cli_compliance import cmd_compliance_report, add_compliance_commands


PASSWORD = "pw"


@pytest.fixture()
def tmp_project(tmp_path):
    save_secrets(str(tmp_path), PASSWORD, {"MY_KEY": "my_value"})
    return tmp_path


def _make_args(project_dir, fmt="text", password=PASSWORD):
    ns = argparse.Namespace()
    ns.project_dir = str(project_dir)
    ns.format = fmt
    ns.password = password
    return ns


def test_compliance_text_returns_0_for_clean_vault(tmp_project, capsys):
    args = _make_args(tmp_project)
    rc = cmd_compliance_report(args)
    assert rc == 0
    out = capsys.readouterr().out
    assert "MY_KEY" in out


def test_compliance_json_output_is_valid(tmp_project, capsys):
    args = _make_args(tmp_project, fmt="json")
    rc = cmd_compliance_report(args)
    assert rc == 0
    out = capsys.readouterr().out
    data = json.loads(out)
    assert "total_secrets" in data
    assert "items" in data


def test_compliance_returns_2_for_non_compliant(tmp_path, capsys):
    save_secrets(str(tmp_path), PASSWORD, {"BAD": ""})
    args = _make_args(tmp_path)
    rc = cmd_compliance_report(args)
    assert rc == 2


def test_compliance_wrong_password_returns_1(tmp_project, capsys):
    args = _make_args(tmp_project, password="wrong")
    rc = cmd_compliance_report(args)
    assert rc == 1
    err = capsys.readouterr().err
    assert "error" in err.lower()


def test_add_compliance_commands_registers_subcommand():
    parser = argparse.ArgumentParser()
    sub = parser.add_subparsers()
    add_compliance_commands(sub)
    args = parser.parse_args(["compliance", "/some/dir", "--format", "json"])
    assert args.format == "json"
    assert args.project_dir == "/some/dir"
    assert args.func is cmd_compliance_report
