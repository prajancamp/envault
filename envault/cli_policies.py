"""CLI commands for managing secret value policies."""

from __future__ import annotations

import argparse
import sys

from envault.policies import (
    get_policy,
    list_policies,
    remove_policy,
    set_policy,
)


def _print_error(msg: str) -> None:
    print(f"error: {msg}", file=sys.stderr)


def cmd_policy_set(args: argparse.Namespace) -> int:
    try:
        set_policy(
            args.project_dir,
            args.key,
            args.pattern,
            description=args.description or "",
        )
        print(f"Policy set for '{args.key}': {args.pattern}")
        return 0
    except ValueError as exc:
        _print_error(str(exc))
        return 1


def cmd_policy_remove(args: argparse.Namespace) -> int:
    remove_policy(args.project_dir, args.key)
    print(f"Policy removed for '{args.key}'.")
    return 0


def cmd_policy_show(args: argparse.Namespace) -> int:
    policy = get_policy(args.project_dir, args.key)
    if policy is None:
        _print_error(f"No policy set for '{args.key}'.")
        return 1
    print(f"key:         {args.key}")
    print(f"pattern:     {policy['pattern']}")
    print(f"description: {policy.get('description') or '(none)'}")
    return 0


def cmd_policy_list(args: argparse.Namespace) -> int:
    policies = list_policies(args.project_dir)
    if not policies:
        print("No policies defined.")
        return 0
    for key, pol in sorted(policies.items()):
        desc = pol.get("description") or ""
        suffix = f"  # {desc}" if desc else ""
        print(f"{key}: {pol['pattern']}{suffix}")
    return 0


def add_policy_commands(subparsers: argparse._SubParsersAction, parent_parser: argparse.ArgumentParser) -> None:  # noqa: SLF001
    p_set = subparsers.add_parser("policy-set", parents=[parent_parser], help="Attach a regex policy to a key")
    p_set.add_argument("key")
    p_set.add_argument("pattern", help="Python regex that the value must fully match")
    p_set.add_argument("--description", default="", help="Human-readable description of the policy")
    p_set.set_defaults(func=cmd_policy_set)

    p_rm = subparsers.add_parser("policy-remove", parents=[parent_parser], help="Remove policy for a key")
    p_rm.add_argument("key")
    p_rm.set_defaults(func=cmd_policy_remove)

    p_show = subparsers.add_parser("policy-show", parents=[parent_parser], help="Show policy for a key")
    p_show.add_argument("key")
    p_show.set_defaults(func=cmd_policy_show)

    p_list = subparsers.add_parser("policy-list", parents=[parent_parser], help="List all policies")
    p_list.set_defaults(func=cmd_policy_list)
