"""Tests that bookmark subcommands are correctly registered on a parser."""

from __future__ import annotations

import argparse
import pytest

from envault.cli_bookmarks import add_bookmark_commands


@pytest.fixture()
def parser_with_bookmarks():
    parser = argparse.ArgumentParser()
    subparsers = parser.add_subparsers()
    add_bookmark_commands(subparsers)
    return parser


def test_bookmark_add_subcommand_registered(parser_with_bookmarks):
    args = parser_with_bookmarks.parse_args(["bookmark-add", "MY_KEY"])
    assert args.key == "MY_KEY"


def test_bookmark_add_with_note_flag(parser_with_bookmarks):
    args = parser_with_bookmarks.parse_args(["bookmark-add", "MY_KEY", "--note", "critical"])
    assert args.note == "critical"


def test_bookmark_add_password_flag(parser_with_bookmarks):
    args = parser_with_bookmarks.parse_args(["bookmark-add", "MY_KEY", "--password", "s3cr3t"])
    assert args.password == "s3cr3t"


def test_bookmark_remove_subcommand_registered(parser_with_bookmarks):
    args = parser_with_bookmarks.parse_args(["bookmark-remove", "MY_KEY"])
    assert args.key == "MY_KEY"


def test_bookmark_list_subcommand_registered(parser_with_bookmarks):
    args = parser_with_bookmarks.parse_args(["bookmark-list"])
    assert hasattr(args, "func")


def test_bookmark_check_subcommand_registered(parser_with_bookmarks):
    args = parser_with_bookmarks.parse_args(["bookmark-check", "MY_KEY"])
    assert args.key == "MY_KEY"
