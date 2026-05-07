"""Integration test: add_share_commands registers parsers correctly."""

from __future__ import annotations

import argparse
import pytest
from unittest.mock import patch

from envault.cli_share import add_share_commands
from envault.store import save_secrets


@pytest.fixture()
def parser_with_share():
    parser = argparse.ArgumentParser()
    sub = parser.add_subparsers(dest="command")
    add_share_commands(sub)
    return parser


def test_share_export_subcommand_registered(parser_with_share):
    args = parser_with_share.parse_args(["share-export", "--output", "out.evb"])
    assert args.command == "share-export"
    assert args.output == "out.evb"
    assert args.keys == []


def test_share_export_with_keys(parser_with_share):
    args = parser_with_share.parse_args(["share-export", "--output", "out.evb", "KEY1", "KEY2"])
    assert args.keys == ["KEY1", "KEY2"]


def test_share_import_subcommand_registered(parser_with_share):
    args = parser_with_share.parse_args(["share-import", "bundle.evb"])
    assert args.command == "share-import"
    assert args.bundle == "bundle.evb"
    assert args.overwrite is False


def test_share_import_overwrite_flag(parser_with_share):
    args = parser_with_share.parse_args(["share-import", "--overwrite", "bundle.evb"])
    assert args.overwrite is True


def test_share_export_func_set(parser_with_share):
    from envault.cli_share import cmd_share_export
    args = parser_with_share.parse_args(["share-export", "--output", "x.evb"])
    assert args.func is cmd_share_export


def test_share_import_func_set(parser_with_share):
    from envault.cli_share import cmd_share_import
    args = parser_with_share.parse_args(["share-import", "bundle.evb"])
    assert args.func is cmd_share_import
