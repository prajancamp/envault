"""Tests verifying reminder subcommands are registered correctly."""
from __future__ import annotations

import argparse

import pytest

from envault.cli_reminders import add_reminder_commands


@pytest.fixture()
def parser_with_reminders() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser()
    parser.add_argument("--project-dir", default="/tmp/test")
    subparsers = parser.add_subparsers(dest="command")
    add_reminder_commands(subparsers)
    return parser


def test_reminder_set_subcommand_registered(parser_with_reminders):
    args = parser_with_reminders.parse_args(["reminder-set", "MY_KEY", "30"])
    assert args.command == "reminder-set"
    assert args.key == "MY_KEY"
    assert args.days == 30


def test_reminder_set_with_message(parser_with_reminders):
    args = parser_with_reminders.parse_args(
        ["reminder-set", "MY_KEY", "7", "--message", "rotate me"]
    )
    assert args.message == "rotate me"


def test_reminder_get_subcommand_registered(parser_with_reminders):
    args = parser_with_reminders.parse_args(["reminder-get", "MY_KEY"])
    assert args.command == "reminder-get"
    assert args.key == "MY_KEY"


def test_reminder_remove_subcommand_registered(parser_with_reminders):
    args = parser_with_reminders.parse_args(["reminder-remove", "MY_KEY"])
    assert args.command == "reminder-remove"
    assert args.key == "MY_KEY"


def test_reminder_due_subcommand_registered(parser_with_reminders):
    args = parser_with_reminders.parse_args(["reminder-due"])
    assert args.command == "reminder-due"
    assert hasattr(args, "func")
