"""CLI commands for managing per-project lifecycle hooks."""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

from envault import hooks as hk


def _print_error(msg: str) -> None:
    print(f"Error: {msg}", file=sys.stderr)


def cmd_hook_set(args: argparse.Namespace) -> int:
    project_dir = Path(args.project_dir)
    try:
        hk.set_hook(project_dir, args.event, args.command)
        print(f"Hook registered: [{args.event}] -> {args.command!r}")
        return 0
    except ValueError as exc:
        _print_error(str(exc))
        return 1


def cmd_hook_remove(args: argparse.Namespace) -> int:
    project_dir = Path(args.project_dir)
    command = getattr(args, "command", None)
    try:
        hk.remove_hook(project_dir, args.event, command)
        if command:
            print(f"Hook removed: [{args.event}] -> {command!r}")
        else:
            print(f"All hooks removed for event: {args.event}")
        return 0
    except ValueError as exc:
        _print_error(str(exc))
        return 1


def cmd_hook_list(args: argparse.Namespace) -> int:
    project_dir = Path(args.project_dir)
    all_hooks = hk.list_hooks(project_dir)
    if not all_hooks:
        print("No hooks registered.")
        return 0
    for event, commands in sorted(all_hooks.items()):
        for cmd in commands:
            print(f"{event}: {cmd}")
    return 0


def add_hook_commands(subparsers: argparse._SubParsersAction) -> None:  # noqa: SLF001
    # hook set
    p_set = subparsers.add_parser("hook-set", help="Register a lifecycle hook")
    p_set.add_argument("event", choices=hk.EVENTS, help="Vault event to hook into")
    p_set.add_argument("command", help="Shell command to run")
    p_set.set_defaults(func=cmd_hook_set)

    # hook remove
    p_rm = subparsers.add_parser("hook-remove", help="Remove a lifecycle hook")
    p_rm.add_argument("event", choices=hk.EVENTS, help="Event to remove hook from")
    p_rm.add_argument("command", nargs="?", default=None,
                      help="Specific command to remove (omit to clear all)")
    p_rm.set_defaults(func=cmd_hook_remove)

    # hook list
    p_ls = subparsers.add_parser("hook-list", help="List all registered hooks")
    p_ls.set_defaults(func=cmd_hook_list)
