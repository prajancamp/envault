"""CLI commands for secret label management."""

from __future__ import annotations

import argparse
import getpass
import sys

from envault.labels import filter_by_label, get_labels, remove_label, set_label


def _get_password(args: argparse.Namespace) -> str:
    if hasattr(args, "password") and args.password:
        return args.password
    return getpass.getpass("Vault password: ")


def _print_error(msg: str) -> None:
    print(f"error: {msg}", file=sys.stderr)


def cmd_label_set(args: argparse.Namespace) -> int:
    password = _get_password(args)
    try:
        set_label(args.project_dir, password, args.key, args.label, args.value)
        print(f"Label '{args.label}={args.value}' set on '{args.key}'.")
        return 0
    except KeyError as exc:
        _print_error(str(exc))
        return 1
    except Exception as exc:  # noqa: BLE001
        _print_error(str(exc))
        return 1


def cmd_label_remove(args: argparse.Namespace) -> int:
    password = _get_password(args)
    try:
        removed = remove_label(args.project_dir, password, args.key, args.label)
        if removed:
            print(f"Label '{args.label}' removed from '{args.key}'.")
        else:
            print(f"Label '{args.label}' not found on '{args.key}'.")
        return 0
    except Exception as exc:  # noqa: BLE001
        _print_error(str(exc))
        return 1


def cmd_label_list(args: argparse.Namespace) -> int:
    password = _get_password(args)
    try:
        labels = get_labels(args.project_dir, password, args.key)
        if not labels:
            print(f"No labels on '{args.key}'.")
        else:
            for k, v in sorted(labels.items()):
                print(f"  {k}={v}")
        return 0
    except Exception as exc:  # noqa: BLE001
        _print_error(str(exc))
        return 1


def cmd_label_filter(args: argparse.Namespace) -> int:
    password = _get_password(args)
    try:
        keys = filter_by_label(args.project_dir, password, args.label, args.value)
        if not keys:
            print("No secrets match.")
        else:
            for k in keys:
                print(f"  {k}")
        return 0
    except Exception as exc:  # noqa: BLE001
        _print_error(str(exc))
        return 1


def add_label_commands(subparsers: argparse._SubParsersAction) -> None:  # type: ignore[type-arg]
    common = argparse.ArgumentParser(add_help=False)
    common.add_argument("--password", default="")
    common.add_argument("--project-dir", default=".")

    p_set = subparsers.add_parser("label-set", parents=[common], help="Set a label on a secret")
    p_set.add_argument("key")
    p_set.add_argument("label")
    p_set.add_argument("value")
    p_set.set_defaults(func=cmd_label_set)

    p_rm = subparsers.add_parser("label-remove", parents=[common], help="Remove a label from a secret")
    p_rm.add_argument("key")
    p_rm.add_argument("label")
    p_rm.set_defaults(func=cmd_label_remove)

    p_ls = subparsers.add_parser("label-list", parents=[common], help="List labels on a secret")
    p_ls.add_argument("key")
    p_ls.set_defaults(func=cmd_label_list)

    p_fi = subparsers.add_parser("label-filter", parents=[common], help="Filter secrets by label")
    p_fi.add_argument("label")
    p_fi.add_argument("value", nargs="?", default=None)
    p_fi.set_defaults(func=cmd_label_filter)
