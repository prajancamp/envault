"""CLI commands for managing secret tags."""
from __future__ import annotations

import argparse
import getpass
import sys

from envault.tags import (
    filter_by_tag,
    get_tags,
    list_all_tags,
    remove_tag,
    set_tag,
)


def _get_password(prompt: str = "Vault password: ") -> str:
    return getpass.getpass(prompt)


def cmd_tag_set(args: argparse.Namespace) -> int:
    password = _get_password()
    try:
        set_tag(args.project_dir, password, args.key, args.tag)
        print(f"Tag '{args.tag}' added to '{args.key}'.")
        return 0
    except KeyError as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 1
    except Exception as exc:  # noqa: BLE001
        print(f"Error: {exc}", file=sys.stderr)
        return 1


def cmd_tag_remove(args: argparse.Namespace) -> int:
    password = _get_password()
    try:
        remove_tag(args.project_dir, password, args.key, args.tag)
        print(f"Tag '{args.tag}' removed from '{args.key}'.")
        return 0
    except Exception as exc:  # noqa: BLE001
        print(f"Error: {exc}", file=sys.stderr)
        return 1


def cmd_tag_list(args: argparse.Namespace) -> int:
    password = _get_password()
    try:
        if args.key:
            tags = get_tags(args.project_dir, password, args.key)
            if tags:
                print(", ".join(tags))
            else:
                print(f"No tags for '{args.key}'.")
        else:
            mapping = list_all_tags(args.project_dir, password)
            if not mapping:
                print("No tags defined.")
            else:
                for key, tags in sorted(mapping.items()):
                    print(f"{key}: {', '.join(tags)}")
        return 0
    except Exception as exc:  # noqa: BLE001
        print(f"Error: {exc}", file=sys.stderr)
        return 1


def cmd_tag_filter(args: argparse.Namespace) -> int:
    password = _get_password()
    try:
        secrets = filter_by_tag(args.project_dir, password, args.tag)
        if not secrets:
            print(f"No secrets tagged '{args.tag}'.")
        else:
            for key in sorted(secrets):
                print(key)
        return 0
    except Exception as exc:  # noqa: BLE001
        print(f"Error: {exc}", file=sys.stderr)
        return 1


def add_tag_commands(subparsers: argparse._SubParsersAction, parent_parser: argparse.ArgumentParser) -> None:  # type: ignore[type-arg]
    tag_p = subparsers.add_parser("tag", help="Manage secret tags", parents=[parent_parser])
    tag_sub = tag_p.add_subparsers(dest="tag_cmd", required=True)

    p_set = tag_sub.add_parser("set", help="Add a tag to a secret")
    p_set.add_argument("key")
    p_set.add_argument("tag")
    p_set.set_defaults(func=cmd_tag_set)

    p_rm = tag_sub.add_parser("remove", help="Remove a tag from a secret")
    p_rm.add_argument("key")
    p_rm.add_argument("tag")
    p_rm.set_defaults(func=cmd_tag_remove)

    p_ls = tag_sub.add_parser("list", help="List tags")
    p_ls.add_argument("key", nargs="?", default=None, help="Secret key (omit for all)")
    p_ls.set_defaults(func=cmd_tag_list)

    p_filter = tag_sub.add_parser("filter", help="List secrets with a given tag")
    p_filter.add_argument("tag")
    p_filter.set_defaults(func=cmd_tag_filter)
