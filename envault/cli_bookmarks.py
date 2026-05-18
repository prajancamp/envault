"""CLI commands for bookmark management."""

from __future__ import annotations

import argparse
import getpass
import sys

from envault.bookmarks import (
    add_bookmark,
    is_bookmarked,
    list_bookmarks,
    remove_bookmark,
    get_bookmark_note,
)


def _get_password(args: argparse.Namespace) -> str:
    return args.password or getpass.getpass("Vault password: ")


def cmd_bookmark_add(args: argparse.Namespace) -> int:
    password = _get_password(args)
    try:
        add_bookmark(args.project_dir, password, args.key, args.note or "")
        print(f"Bookmarked '{args.key}'.")
        return 0
    except KeyError as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 1


def cmd_bookmark_remove(args: argparse.Namespace) -> int:
    existed = remove_bookmark(args.project_dir, args.key)
    if not existed:
        print(f"Error: '{args.key}' is not bookmarked.", file=sys.stderr)
        return 1
    print(f"Removed bookmark for '{args.key}'.")
    return 0


def cmd_bookmark_list(args: argparse.Namespace) -> int:
    items = list_bookmarks(args.project_dir)
    if not items:
        print("No bookmarks.")
        return 0
    for item in items:
        note_part = f"  # {item['note']}" if item["note"] else ""
        print(f"{item['key']}{note_part}")
    return 0


def cmd_bookmark_check(args: argparse.Namespace) -> int:
    if is_bookmarked(args.project_dir, args.key):
        note = get_bookmark_note(args.project_dir, args.key)
        print(f"'{args.key}' is bookmarked." + (f" Note: {note}" if note else ""))
        return 0
    print(f"'{args.key}' is not bookmarked.")
    return 1


def add_bookmark_commands(subparsers: argparse._SubParsersAction) -> None:  # type: ignore[type-arg]
    p_add = subparsers.add_parser("bookmark-add", help="Bookmark a secret")
    p_add.add_argument("key")
    p_add.add_argument("--note", default="", help="Optional note")
    p_add.add_argument("--password", default="")
    p_add.set_defaults(func=cmd_bookmark_add)

    p_rm = subparsers.add_parser("bookmark-remove", help="Remove a bookmark")
    p_rm.add_argument("key")
    p_rm.set_defaults(func=cmd_bookmark_remove)

    p_ls = subparsers.add_parser("bookmark-list", help="List all bookmarks")
    p_ls.set_defaults(func=cmd_bookmark_list)

    p_chk = subparsers.add_parser("bookmark-check", help="Check if a key is bookmarked")
    p_chk.add_argument("key")
    p_chk.set_defaults(func=cmd_bookmark_check)
