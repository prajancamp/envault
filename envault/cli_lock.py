"""CLI commands for vault locking/unlocking."""

from __future__ import annotations

import argparse
import sys

from envault.lock import lock_vault, unlock_vault, lock_info, is_locked


def cmd_lock(args: argparse.Namespace) -> int:
    """Lock the vault, preventing further reads/writes."""
    try:
        info = lock_vault(
            vault_dir=args.project_dir,
            reason=args.reason or "",
            actor=args.actor or "envault",
        )
        print(f"Vault locked at {info['locked_at']}")
        if info["reason"]:
            print(f"Reason: {info['reason']}")
        return 0
    except RuntimeError as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 1


def cmd_unlock(args: argparse.Namespace) -> int:
    """Unlock the vault."""
    try:
        unlock_vault(vault_dir=args.project_dir)
        print("Vault unlocked.")
        return 0
    except RuntimeError as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 1


def cmd_lock_status(args: argparse.Namespace) -> int:
    """Print current lock status."""
    info = lock_info(vault_dir=args.project_dir)
    if info is None:
        print("Vault is unlocked.")
    else:
        print(f"Vault is LOCKED")
        print(f"  Locked at : {info['locked_at']}")
        print(f"  Actor     : {info['actor']}")
        print(f"  Reason    : {info['reason'] or '(none)'}")
    return 0


def add_lock_commands(subparsers: argparse._SubParsersAction) -> None:  # noqa: SLF001
    p_lock = subparsers.add_parser("lock", help="Lock the vault")
    p_lock.add_argument("--reason", default="", help="Optional reason for locking")
    p_lock.add_argument("--actor", default="envault", help="Actor performing the lock")
    p_lock.set_defaults(func=cmd_lock)

    p_unlock = subparsers.add_parser("unlock", help="Unlock the vault")
    p_unlock.set_defaults(func=cmd_unlock)

    p_status = subparsers.add_parser("lock-status", help="Show vault lock status")
    p_status.set_defaults(func=cmd_lock_status)
