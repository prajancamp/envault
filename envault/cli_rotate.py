"""CLI sub-commands for password rotation."""

from __future__ import annotations

import argparse
import getpass
import sys
from pathlib import Path

from envault.rotate import rotate_password


def _prompt(msg: str, confirm: bool = False) -> str:
    pwd = getpass.getpass(msg)
    if confirm:
        pwd2 = getpass.getpass("Confirm new password: ")
        if pwd != pwd2:
            print("error: passwords do not match", file=sys.stderr)
            sys.exit(1)
    return pwd


def cmd_rotate(args: argparse.Namespace) -> int:
    """Rotate the master password for a project vault."""
    project_dir = Path(args.project_dir).resolve()

    old_password = getpass.getpass("Current password: ")
    new_password = _prompt("New password: ", confirm=True)

    if old_password == new_password:
        print("error: new password must differ from current password", file=sys.stderr)
        return 1

    try:
        count = rotate_password(project_dir, old_password, new_password)
    except Exception as exc:  # noqa: BLE001
        print(f"error: {exc}", file=sys.stderr)
        return 1

    print(f"Rotated password for {project_dir} ({count} secret(s) re-encrypted).")
    return 0


def add_rotate_commands(subparsers: argparse._SubParsersAction) -> None:  # noqa: SLF001
    p = subparsers.add_parser("rotate", help="Rotate the master password for a vault")
    p.add_argument(
        "project_dir",
        nargs="?",
        default=".",
        help="Path to the project directory (default: current directory)",
    )
    p.set_defaults(func=cmd_rotate)
