"""CLI commands for managing per-secret annotations."""
from __future__ import annotations

import argparse
import getpass
import sys

from envault import annotations as ann


def _get_password(args: argparse.Namespace) -> str:
    return args.password if getattr(args, "password", None) else getpass.getpass("Vault password: ")


def _print_error(msg: str) -> None:
    print(f"Error: {msg}", file=sys.stderr)


def cmd_annotation_set(args: argparse.Namespace) -> int:
    pw = _get_password(args)
    try:
        ann.set_annotation(args.vault_dir, pw, args.key, args.text)
        print(f"Annotation set for '{args.key}'.")
        return 0
    except KeyError as exc:
        _print_error(str(exc))
        return 1
    except Exception as exc:  # noqa: BLE001
        _print_error(str(exc))
        return 1


def cmd_annotation_get(args: argparse.Namespace) -> int:
    text = ann.get_annotation(args.vault_dir, args.key)
    if text is None:
        print(f"No annotation for '{args.key}'.")
        return 1
    print(text)
    return 0


def cmd_annotation_remove(args: argparse.Namespace) -> int:
    removed = ann.remove_annotation(args.vault_dir, args.key)
    if removed:
        print(f"Annotation removed for '{args.key}'.")
        return 0
    print(f"No annotation found for '{args.key}'.")
    return 1


def cmd_annotation_list(args: argparse.Namespace) -> int:
    data = ann.list_annotations(args.vault_dir)
    if not data:
        print("No annotations set.")
        return 0
    for key, text in sorted(data.items()):
        print(f"{key}: {text}")
    return 0


def add_annotation_commands(subparsers: argparse._SubParsersAction) -> None:  # type: ignore[type-arg]
    common = argparse.ArgumentParser(add_help=False)
    common.add_argument("--vault-dir", default=".", dest="vault_dir")
    common.add_argument("--password", default=None)

    p_set = subparsers.add_parser("annotation-set", parents=[common], help="Attach annotation to a secret")
    p_set.add_argument("key")
    p_set.add_argument("text")
    p_set.set_defaults(func=cmd_annotation_set)

    p_get = subparsers.add_parser("annotation-get", parents=[common], help="Show annotation for a secret")
    p_get.add_argument("key")
    p_get.set_defaults(func=cmd_annotation_get)

    p_rm = subparsers.add_parser("annotation-remove", parents=[common], help="Remove annotation from a secret")
    p_rm.add_argument("key")
    p_rm.set_defaults(func=cmd_annotation_remove)

    p_ls = subparsers.add_parser("annotation-list", parents=[common], help="List all annotations")
    p_ls.set_defaults(func=cmd_annotation_list)
