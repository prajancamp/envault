"""CLI commands for the watchlist feature."""

from __future__ import annotations

import argparse
import getpass
import sys

from envault.watchlist import (
    add_to_watchlist,
    remove_from_watchlist,
    get_watchlist,
    is_watched,
)


def _get_password(prompt: str = "Vault password: ") -> str:
    return getpass.getpass(prompt)


def _print_error(msg: str) -> None:
    print(f"Error: {msg}", file=sys.stderr)


def cmd_watch_add(args: argparse.Namespace) -> int:
    password = _get_password()
    try:
        add_to_watchlist(args.project_dir, password, args.key, reason=args.reason)
        print(f"Watching '{args.key}'.")
        return 0
    except KeyError as exc:
        _print_error(str(exc))
        return 1
    except Exception as exc:  # noqa: BLE001
        _print_error(str(exc))
        return 1


def cmd_watch_remove(args: argparse.Namespace) -> int:
    removed = remove_from_watchlist(args.project_dir, args.key)
    if removed:
        print(f"Removed '{args.key}' from watchlist.")
        return 0
    _print_error(f"'{args.key}' is not on the watchlist.")
    return 1


def cmd_watch_list(args: argparse.Namespace) -> int:
    items = get_watchlist(args.project_dir)
    if not items:
        print("Watchlist is empty.")
        return 0
    for item in items:
        reason_str = f"  # {item['reason']}" if item["reason"] else ""
        print(f"  {item['key']}{reason_str}")
    return 0


def cmd_watch_status(args: argparse.Namespace) -> int:
    watched = is_watched(args.project_dir, args.key)
    status = "watched" if watched else "not watched"
    print(f"'{args.key}' is {status}.")
    return 0


def add_watchlist_commands(subparsers: argparse._SubParsersAction, parent_parser: argparse.ArgumentParser) -> None:
    watch_parser = subparsers.add_parser("watch", help="Manage the secret watchlist")
    watch_sub = watch_parser.add_subparsers(dest="watch_cmd")

    add_p = watch_sub.add_parser("add", parents=[parent_parser], help="Add a key to the watchlist")
    add_p.add_argument("key", help="Secret key to watch")
    add_p.add_argument("--reason", default="", help="Reason for watching")
    add_p.set_defaults(func=cmd_watch_add)

    rm_p = watch_sub.add_parser("remove", parents=[parent_parser], help="Remove a key from the watchlist")
    rm_p.add_argument("key", help="Secret key to unwatch")
    rm_p.set_defaults(func=cmd_watch_remove)

    list_p = watch_sub.add_parser("list", parents=[parent_parser], help="List all watched keys")
    list_p.set_defaults(func=cmd_watch_list)

    status_p = watch_sub.add_parser("status", parents=[parent_parser], help="Check if a key is watched")
    status_p.add_argument("key", help="Secret key to check")
    status_p.set_defaults(func=cmd_watch_status)
