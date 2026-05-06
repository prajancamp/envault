"""CLI commands for managing secret TTLs."""

from __future__ import annotations

import argparse
import getpass
import sys

from envault import ttl as ttl_mod


def _get_password(prompt: str = "Vault password: ") -> str:
    return getpass.getpass(prompt)


def cmd_ttl_set(args: argparse.Namespace) -> int:
    password = _get_password()
    try:
        expires_at = ttl_mod.set_ttl(
            args.project_dir, password, args.key, args.seconds
        )
        print(f"TTL set for '{args.key}': expires at {expires_at.isoformat()}")
        return 0
    except KeyError as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 1
    except ValueError as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 1


def cmd_ttl_get(args: argparse.Namespace) -> int:
    password = _get_password()
    expires_at = ttl_mod.get_ttl(args.project_dir, password, args.key)
    if expires_at is None:
        print(f"No TTL set for '{args.key}'.")
    else:
        print(f"'{args.key}' expires at {expires_at.isoformat()}")
    return 0


def cmd_ttl_remove(args: argparse.Namespace) -> int:
    password = _get_password()
    removed = ttl_mod.remove_ttl(args.project_dir, password, args.key)
    if removed:
        print(f"TTL removed from '{args.key}'.")
    else:
        print(f"No TTL was set for '{args.key}'.")
    return 0


def cmd_ttl_purge(args: argparse.Namespace) -> int:
    password = _get_password()
    purged = ttl_mod.purge_expired(args.project_dir, password)
    if not purged:
        print("No expired secrets found.")
    else:
        print(f"Purged {len(purged)} expired secret(s):")
        for key, expired_at in purged.items():
            print(f"  {key}  (expired {expired_at})")
    return 0


def add_ttl_commands(subparsers: argparse._SubParsersAction, parent: argparse.ArgumentParser) -> None:  # noqa: SLF001
    # ttl-set
    p_set = subparsers.add_parser("ttl-set", parents=[parent], help="Set a TTL on a secret.")
    p_set.add_argument("key", help="Secret key name.")
    p_set.add_argument("seconds", type=int, help="Seconds until the secret expires.")
    p_set.set_defaults(func=cmd_ttl_set)

    # ttl-get
    p_get = subparsers.add_parser("ttl-get", parents=[parent], help="Show TTL for a secret.")
    p_get.add_argument("key", help="Secret key name.")
    p_get.set_defaults(func=cmd_ttl_get)

    # ttl-remove
    p_rm = subparsers.add_parser("ttl-remove", parents=[parent], help="Remove TTL from a secret.")
    p_rm.add_argument("key", help="Secret key name.")
    p_rm.set_defaults(func=cmd_ttl_remove)

    # ttl-purge
    p_purge = subparsers.add_parser("ttl-purge", parents=[parent], help="Delete all expired secrets.")
    p_purge.set_defaults(func=cmd_ttl_purge)
