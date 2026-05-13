"""CLI commands for reminder management."""
from __future__ import annotations

import argparse
import getpass
import sys

from envault.reminders import due_reminders, get_reminder, remove_reminder, set_reminder


def _get_password(args: argparse.Namespace) -> str:
    return getpass.getpass("Vault password: ")


def cmd_reminder_set(args: argparse.Namespace) -> int:
    password = _get_password(args)
    try:
        remind_at = set_reminder(
            args.project_dir, password, args.key, args.days,
            message=args.message or "",
        )
    except KeyError as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 1
    print(f"Reminder set for '{args.key}' at {remind_at.isoformat()}")
    return 0


def cmd_reminder_get(args: argparse.Namespace) -> int:
    password = _get_password(args)
    info = get_reminder(args.project_dir, password, args.key)
    if info is None:
        print(f"No reminder set for '{args.key}'.")
        return 0
    print(f"Key:       {args.key}")
    print(f"Remind at: {info['remind_at'].isoformat()}")
    if info.get("message"):
        print(f"Message:   {info['message']}")
    return 0


def cmd_reminder_remove(args: argparse.Namespace) -> int:
    password = _get_password(args)
    removed = remove_reminder(args.project_dir, password, args.key)
    if removed:
        print(f"Reminder for '{args.key}' removed.")
    else:
        print(f"No reminder found for '{args.key}'.")
    return 0


def cmd_reminder_due(args: argparse.Namespace) -> int:
    password = _get_password(args)
    due = due_reminders(args.project_dir, password)
    if not due:
        print("No reminders are currently due.")
        return 0
    for item in due:
        msg = f"  [{item['remind_at'].isoformat()}] {item['key']}"
        if item["message"]:
            msg += f" — {item['message']}"
        print(msg)
    return 0


def add_reminder_commands(subparsers: argparse._SubParsersAction) -> None:
    p_set = subparsers.add_parser("reminder-set", help="Schedule a rotation reminder")
    p_set.add_argument("key")
    p_set.add_argument("days", type=int, help="Days from now")
    p_set.add_argument("--message", default="", help="Optional reminder note")
    p_set.set_defaults(func=cmd_reminder_set)

    p_get = subparsers.add_parser("reminder-get", help="Show reminder for a key")
    p_get.add_argument("key")
    p_get.set_defaults(func=cmd_reminder_get)

    p_rm = subparsers.add_parser("reminder-remove", help="Remove a reminder")
    p_rm.add_argument("key")
    p_rm.set_defaults(func=cmd_reminder_remove)

    p_due = subparsers.add_parser("reminder-due", help="List due reminders")
    p_due.set_defaults(func=cmd_reminder_due)
