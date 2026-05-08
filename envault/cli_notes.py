"""CLI commands for managing per-secret notes."""
from __future__ import annotations

import argparse
import getpass
import sys

from envault import notes


def _get_password(prompt: str = "Vault password: ") -> str:
    return getpass.getpass(prompt)


def cmd_note_set(args: argparse.Namespace) -> int:
    password = _get_password()
    try:
        notes.set_note(args.project_dir, password, args.key, args.note)
        print(f"Note set for '{args.key}'.")
        return 0
    except KeyError as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 1
    except Exception as exc:  # noqa: BLE001
        print(f"Error: {exc}", file=sys.stderr)
        return 1


def cmd_note_get(args: argparse.Namespace) -> int:
    note = notes.get_note(args.project_dir, args.key)
    if note is None:
        print(f"No note set for '{args.key}'.", file=sys.stderr)
        return 1
    print(note)
    return 0


def cmd_note_remove(args: argparse.Namespace) -> int:
    removed = notes.remove_note(args.project_dir, args.key)
    if not removed:
        print(f"No note found for '{args.key}'.", file=sys.stderr)
        return 1
    print(f"Note removed for '{args.key}'.")
    return 0


def cmd_note_list(args: argparse.Namespace) -> int:
    all_notes = notes.list_notes(args.project_dir)
    if not all_notes:
        print("No notes stored.")
        return 0
    for key, note in sorted(all_notes.items()):
        print(f"{key}: {note}")
    return 0


def cmd_note_purge(args: argparse.Namespace) -> int:
    password = _get_password()
    try:
        removed = notes.purge_orphaned_notes(args.project_dir, password)
        if removed:
            for k in removed:
                print(f"Removed orphaned note: {k}")
        else:
            print("No orphaned notes found.")
        return 0
    except Exception as exc:  # noqa: BLE001
        print(f"Error: {exc}", file=sys.stderr)
        return 1


def add_notes_commands(subparsers: argparse._SubParsersAction, parent_parser: argparse.ArgumentParser) -> None:
    p_set = subparsers.add_parser("note-set", parents=[parent_parser], help="Attach a note to a secret")
    p_set.add_argument("key")
    p_set.add_argument("note")
    p_set.set_defaults(func=cmd_note_set)

    p_get = subparsers.add_parser("note-get", parents=[parent_parser], help="Show note for a secret")
    p_get.add_argument("key")
    p_get.set_defaults(func=cmd_note_get)

    p_rm = subparsers.add_parser("note-remove", parents=[parent_parser], help="Remove note from a secret")
    p_rm.add_argument("key")
    p_rm.set_defaults(func=cmd_note_remove)

    p_ls = subparsers.add_parser("note-list", parents=[parent_parser], help="List all notes")
    p_ls.set_defaults(func=cmd_note_list)

    p_purge = subparsers.add_parser("note-purge", parents=[parent_parser], help="Remove notes for deleted secrets")
    p_purge.set_defaults(func=cmd_note_purge)
