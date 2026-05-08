"""CLI commands for alias management."""

from __future__ import annotations

import argparse
import sys

from envault import aliases
from envault.store import load_secrets


def _get_password(args: argparse.Namespace) -> str:
    import getpass
    return getpass.getpass("Vault password: ")


def cmd_alias_set(args: argparse.Namespace) -> int:
    password = _get_password(args)
    try:
        secrets = load_secrets(args.project_dir, password)
    except Exception as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1
    try:
        aliases.set_alias(args.project_dir, args.alias, args.key, list(secrets.keys()))
    except KeyError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1
    print(f"Alias '{args.alias}' -> '{args.key}' saved.")
    return 0


def cmd_alias_remove(args: argparse.Namespace) -> int:
    try:
        aliases.remove_alias(args.project_dir, args.alias)
    except KeyError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1
    print(f"Alias '{args.alias}' removed.")
    return 0


def cmd_alias_list(args: argparse.Namespace) -> int:
    mapping = aliases.list_aliases(args.project_dir)
    if not mapping:
        print("No aliases defined.")
        return 0
    for alias, key in sorted(mapping.items()):
        print(f"  {alias} -> {key}")
    return 0


def cmd_alias_resolve(args: argparse.Namespace) -> int:
    key = aliases.resolve_alias(args.project_dir, args.alias)
    if key is None:
        print(f"error: Alias '{args.alias}' not found.", file=sys.stderr)
        return 1
    print(key)
    return 0


def add_alias_commands(subparsers: argparse._SubParsersAction, parent: argparse.ArgumentParser) -> None:
    alias_p = subparsers.add_parser("alias", help="Manage secret key aliases")
    alias_sub = alias_p.add_subparsers(dest="alias_cmd")

    p_set = alias_sub.add_parser("set", parents=[parent], help="Create or update an alias")
    p_set.add_argument("alias", help="Alias name")
    p_set.add_argument("key", help="Target secret key")
    p_set.set_defaults(func=cmd_alias_set)

    p_rm = alias_sub.add_parser("remove", parents=[parent], help="Remove an alias")
    p_rm.add_argument("alias", help="Alias name")
    p_rm.set_defaults(func=cmd_alias_remove)

    p_ls = alias_sub.add_parser("list", parents=[parent], help="List all aliases")
    p_ls.set_defaults(func=cmd_alias_list)

    p_res = alias_sub.add_parser("resolve", parents=[parent], help="Resolve an alias to its key")
    p_res.add_argument("alias", help="Alias name")
    p_res.set_defaults(func=cmd_alias_resolve)
