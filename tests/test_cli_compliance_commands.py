"""Structural tests — verify compliance subcommand is wired correctly."""
from __future__ import annotations

import argparse

import pytest

from envault.cli_compliance import add_compliance_commands, cmd_compliance_report


@pytest.fixture()
def parser_with_compliance():
    parser = argparse.ArgumentParser(prog="envault")
    sub = parser.add_subparsers(dest="command")
    add_compliance_commands(sub)
    return parser


def test_compliance_subcommand_registered(parser_with_compliance):
    args = parser_with_compliance.parse_args(["compliance", "/proj"])
    assert args.command == "compliance"


def test_compliance_default_format_is_text(parser_with_compliance):
    args = parser_with_compliance.parse_args(["compliance", "/proj"])
    assert args.format == "text"


def test_compliance_json_format_flag(parser_with_compliance):
    args = parser_with_compliance.parse_args(["compliance", "/proj", "--format", "json"])
    assert args.format == "json"


def test_compliance_password_flag(parser_with_compliance):
    args = parser_with_compliance.parse_args(
        ["compliance", "/proj", "--password", "s3cr3t"]
    )
    assert args.password == "s3cr3t"


def test_compliance_func_points_to_cmd(parser_with_compliance):
    args = parser_with_compliance.parse_args(["compliance", "/proj"])
    assert args.func is cmd_compliance_report
