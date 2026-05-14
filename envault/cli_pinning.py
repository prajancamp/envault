"""CLI commands for secret pinning."""

from __future__ import annotations

import argparse
import getpass
import sys
from pathlib import Path

from envault.pinning import pin_secret, unpin_secret, is_pinned, list_pinned


def _get_password() -> str:
    return getpass.getpass("Vault password: ")


def _print_error(msg: str) -> None:
    print(f"Error: {msg}", file=sys.stderr)


def cmd_pin_add(args: argparse.Namespace) -> int:
    vault_dir = Path(args.project)
    password = _get_password()
    try:
        pin_secret(vault_dir, args.key, password)
        print(f"Pinned '{args.key}'.")
        return 0
    except KeyError as exc:
        _print_error(str(exc))
        return 1
    except Exception as exc:  # noqa: BLE001
        _print_error(str(exc))
        return 1


def cmd_pin_remove(args: argparse.Namespace) -> int:
    vault_dir = Path(args.project)
    unpin_secret(vault_dir, args.key)
    print(f"Unpinned '{args.key}'.")
    return 0


def cmd_pin_status(args: argparse.Namespace) -> int:
    vault_dir = Path(args.project)
    pinned = is_pinned(vault_dir, args.key)
    status = "pinned" if pinned else "not pinned"
    print(f"'{args.key}' is {status}.")
    return 0


def cmd_pin_list(args: argparse.Namespace) -> int:
    vault_dir = Path(args.project)
    keys = list_pinned(vault_dir)
    if not keys:
        print("No pinned secrets.")
    else:
        for k in keys:
            print(k)
    return 0


def add_pin_commands(subparsers: argparse._SubParsersAction, parent_parser: argparse.ArgumentParser) -> None:
    pin_parser = subparsers.add_parser("pin", help="Manage pinned secrets")
    pin_sub = pin_parser.add_subparsers(dest="pin_cmd")

    p_add = pin_sub.add_parser("add", parents=[parent_parser], help="Pin a secret")
    p_add.add_argument("key")
    p_add.set_defaults(func=cmd_pin_add)

    p_rm = pin_sub.add_parser("remove", parents=[parent_parser], help="Unpin a secret")
    p_rm.add_argument("key")
    p_rm.set_defaults(func=cmd_pin_remove)

    p_st = pin_sub.add_parser("status", parents=[parent_parser], help="Check if a secret is pinned")
    p_st.add_argument("key")
    p_st.set_defaults(func=cmd_pin_status)

    p_ls = pin_sub.add_parser("list", parents=[parent_parser], help="List all pinned secrets")
    p_ls.set_defaults(func=cmd_pin_list)
