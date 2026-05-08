"""CLI commands for per-key access control."""
from __future__ import annotations

import argparse
import getpass
import sys

from envault import access


def _get_password(prompt: str = "Vault password: ") -> str:
    return getpass.getpass(prompt)


def _print_error(msg: str) -> None:
    """Print a formatted error message to stderr."""
    print(f"Error: {msg}", file=sys.stderr)


def cmd_acl_set(args: argparse.Namespace) -> int:
    password = _get_password()
    users = [u.strip() for u in args.users.split(",") if u.strip()]
    if not users:
        _print_error("provide at least one username.")
        return 1
    try:
        access.set_acl(args.project_dir, password, args.key, users)
    except KeyError as exc:
        _print_error(str(exc))
        return 1
    print(f"ACL set for '{args.key}': {', '.join(users)}")
    return 0


def cmd_acl_remove(args: argparse.Namespace) -> int:
    password = _get_password()
    try:
        access.remove_acl(args.project_dir, password, args.key)
    except Exception as exc:  # noqa: BLE001
        _print_error(str(exc))
        return 1
    print(f"ACL removed for '{args.key}' (unrestricted).")
    return 0


def cmd_acl_show(args: argparse.Namespace) -> int:
    password = _get_password()
    try:
        users = access.get_acl(args.project_dir, password, args.key)
    except Exception as exc:  # noqa: BLE001
        _print_error(str(exc))
        return 1
    if not users:
        print(f"'{args.key}' is unrestricted (no ACL set).")
    else:
        print(f"Allowed users for '{args.key}': {', '.join(users)}")
    return 0


def add_access_commands(subparsers: argparse._SubParsersAction) -> None:  # type: ignore[type-arg]
    p_set = subparsers.add_parser("acl-set", help="Restrict a secret to specific OS users")
    p_set.add_argument("key", help="Secret key name")
    p_set.add_argument("users", help="Comma-separated list of allowed OS usernames")
    p_set.set_defaults(func=cmd_acl_set)

    p_rm = subparsers.add_parser("acl-remove", help="Remove access restrictions from a secret")
    p_rm.add_argument("key", help="Secret key name")
    p_rm.set_defaults(func=cmd_acl_remove)

    p_show = subparsers.add_parser("acl-show", help="Show allowed users for a secret")
    p_show.add_argument("key", help="Secret key name")
    p_show.set_defaults(func=cmd_acl_show)
