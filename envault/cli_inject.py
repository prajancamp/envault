"""cli_inject.py — CLI commands for injecting secrets into subprocesses."""
from __future__ import annotations

import argparse
import getpass
import sys
from typing import List

from envault.env_inject import run_with_secrets


def _get_password(args: argparse.Namespace) -> str:
    if hasattr(args, "password") and args.password:
        return args.password
    return getpass.getpass("Vault password: ")


def cmd_inject(args: argparse.Namespace) -> int:
    """envault inject [--prefix PREFIX] -- COMMAND [ARGS...]"""
    if not args.command:
        print("error: no command specified", file=sys.stderr)
        return 1

    password = _get_password(args)

    try:
        exit_code = run_with_secrets(
            args.project_dir,
            password,
            args.command,
            prefix=args.prefix,
            skip_expired=not args.include_expired,
        )
    except ValueError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1

    return exit_code


def add_inject_commands(subparsers: argparse._SubParsersAction) -> None:  # type: ignore[type-arg]
    p = subparsers.add_parser(
        "inject",
        help="Run a command with vault secrets injected into its environment",
    )
    p.add_argument(
        "--prefix",
        default=None,
        metavar="PREFIX",
        help="Only inject keys that start with PREFIX",
    )
    p.add_argument(
        "--include-expired",
        action="store_true",
        default=False,
        help="Include secrets whose TTL has already expired",
    )
    p.add_argument(
        "--password",
        default=None,
        help="Vault password (will prompt if omitted)",
    )
    p.add_argument(
        "command",
        nargs=argparse.REMAINDER,
        help="Command to execute",
    )
    p.set_defaults(func=cmd_inject)
