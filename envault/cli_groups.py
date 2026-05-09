"""CLI commands for secret group management."""

from __future__ import annotations

import argparse
import getpass
import sys

from envault.groups import (
    add_to_group,
    delete_group,
    get_group_members,
    list_groups,
    remove_from_group,
)


def _get_password(prompt: str = "Vault password: ") -> str:
    return getpass.getpass(prompt)


def cmd_group_add(args: argparse.Namespace) -> int:
    password = _get_password()
    try:
        add_to_group(args.project_dir, password, args.group, args.key)
        print(f"Added '{args.key}' to group '{args.group}'.")
        return 0
    except KeyError as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 1


def cmd_group_remove(args: argparse.Namespace) -> int:
    removed = remove_from_group(args.project_dir, args.group, args.key)
    if removed:
        print(f"Removed '{args.key}' from group '{args.group}'.")
        return 0
    print(f"Key '{args.key}' was not in group '{args.group}'.", file=sys.stderr)
    return 1


def cmd_group_list(args: argparse.Namespace) -> int:
    groups = list_groups(args.project_dir)
    if not groups:
        print("No groups defined.")
        return 0
    for group, members in sorted(groups.items()):
        print(f"{group}: {', '.join(members) if members else '(empty)'}")
    return 0


def cmd_group_show(args: argparse.Namespace) -> int:
    members = get_group_members(args.project_dir, args.group)
    if not members:
        print(f"Group '{args.group}' is empty or does not exist.")
        return 0
    for key in members:
        print(key)
    return 0


def cmd_group_delete(args: argparse.Namespace) -> int:
    deleted = delete_group(args.project_dir, args.group)
    if deleted:
        print(f"Deleted group '{args.group}'.")
        return 0
    print(f"Group '{args.group}' does not exist.", file=sys.stderr)
    return 1


def add_group_commands(subparsers: argparse._SubParsersAction, parent_parser: argparse.ArgumentParser) -> None:  # type: ignore[type-arg]
    grp = subparsers.add_parser("group", help="Manage secret groups")
    gsub = grp.add_subparsers(dest="group_cmd", required=True)

    p_add = gsub.add_parser("add", parents=[parent_parser], help="Add a key to a group")
    p_add.add_argument("group")
    p_add.add_argument("key")
    p_add.set_defaults(func=cmd_group_add)

    p_rem = gsub.add_parser("remove", parents=[parent_parser], help="Remove a key from a group")
    p_rem.add_argument("group")
    p_rem.add_argument("key")
    p_rem.set_defaults(func=cmd_group_remove)

    p_list = gsub.add_parser("list", parents=[parent_parser], help="List all groups")
    p_list.set_defaults(func=cmd_group_list)

    p_show = gsub.add_parser("show", parents=[parent_parser], help="Show members of a group")
    p_show.add_argument("group")
    p_show.set_defaults(func=cmd_group_show)

    p_del = gsub.add_parser("delete", parents=[parent_parser], help="Delete a group")
    p_del.add_argument("group")
    p_del.set_defaults(func=cmd_group_delete)
