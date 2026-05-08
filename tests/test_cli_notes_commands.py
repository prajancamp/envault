"""Tests that note subcommands are correctly registered on a parser."""
from __future__ import annotations

import argparse

import pytest

from envault.cli_notes import add_notes_commands


@pytest.fixture()
def parser_with_notes():
    parent = argparse.ArgumentParser(add_help=False)
    parent.add_argument("--project-dir", dest="project_dir", default=".")
    main = argparse.ArgumentParser()
    sub = main.add_subparsers(dest="command")
    add_notes_commands(sub, parent)
    return main


def test_note_set_subcommand_registered(parser_with_notes):
    args = parser_with_notes.parse_args(["note-set", "MY_KEY", "some note"])
    assert args.key == "MY_KEY"
    assert args.note == "some note"


def test_note_get_subcommand_registered(parser_with_notes):
    args = parser_with_notes.parse_args(["note-get", "MY_KEY"])
    assert args.key == "MY_KEY"


def test_note_remove_subcommand_registered(parser_with_notes):
    args = parser_with_notes.parse_args(["note-remove", "MY_KEY"])
    assert args.key == "MY_KEY"


def test_note_list_subcommand_registered(parser_with_notes):
    args = parser_with_notes.parse_args(["note-list"])
    assert args.command == "note-list"


def test_note_purge_subcommand_registered(parser_with_notes):
    args = parser_with_notes.parse_args(["note-purge"])
    assert args.command == "note-purge"


def test_note_set_func_is_callable(parser_with_notes):
    args = parser_with_notes.parse_args(["note-set", "K", "v"])
    assert callable(args.func)


def test_note_list_func_is_callable(parser_with_notes):
    args = parser_with_notes.parse_args(["note-list"])
    assert callable(args.func)
