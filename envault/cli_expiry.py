"""CLI commands for expiry notifications."""

from __future__ import annotations

import argparse
import getpass
import sys
from datetime import timezone

from envault.expiry import expiring_soon, already_expired


def _get_password(args: argparse.Namespace) -> str:
    pw = getattr(args, "password", None)
    if pw:
        return pw
    return getpass.getpass("Vault password: ")


def cmd_expiry_soon(args: argparse.Namespace) -> int:
    """List secrets expiring within the given window (default 24 h)."""
    password = _get_password(args)
    try:
        results = expiring_soon(args.project_dir, password, within_hours=args.hours)
    except Exception as exc:  # noqa: BLE001
        print(f"Error: {exc}", file=sys.stderr)
        return 1
    if not results:
        print(f"No secrets expiring within {args.hours} hour(s).")
        return 0
    print(f"Secrets expiring within {args.hours} hour(s):")
    for key, expiry in results:
        print(f"  {key}  ->  {expiry.astimezone(timezone.utc).isoformat()}")
    return 0


def cmd_expiry_expired(args: argparse.Namespace) -> int:
    """List secrets that have already expired."""
    password = _get_password(args)
    try:
        results = already_expired(args.project_dir, password)
    except Exception as exc:  # noqa: BLE001
        print(f"Error: {exc}", file=sys.stderr)
        return 1
    if not results:
        print("No expired secrets found.")
        return 0
    print("Already-expired secrets:")
    for key, expiry in results:
        print(f"  {key}  ->  {expiry.astimezone(timezone.utc).isoformat()}")
    return 0


def add_expiry_commands(subparsers: argparse._SubParsersAction) -> None:  # noqa: SLF001
    # expiry soon
    p_soon = subparsers.add_parser("expiry-soon", help="List secrets expiring soon")
    p_soon.add_argument("project_dir", help="Path to project directory")
    p_soon.add_argument(
        "--hours", type=int, default=24, help="Look-ahead window in hours (default: 24)"
    )
    p_soon.add_argument("--password", default=None, help="Vault password")
    p_soon.set_defaults(func=cmd_expiry_soon)

    # expiry expired
    p_exp = subparsers.add_parser("expiry-expired", help="List already-expired secrets")
    p_exp.add_argument("project_dir", help="Path to project directory")
    p_exp.add_argument("--password", default=None, help="Vault password")
    p_exp.set_defaults(func=cmd_expiry_expired)
