"""CLI sub-commands for searching secrets."""

from __future__ import annotations

import argparse
import sys

from envault.search import grep, search_keys, search_values


def _get_password() -> str:  # pragma: no cover
    import getpass
    return getpass.getpass("Vault password: ")


def cmd_search(args: argparse.Namespace, *, password: str | None = None) -> int:
    """Search keys and/or values matching a pattern."""
    pw = password or _get_password()

    try:
        results = grep(
            args.project_dir,
            pw,
            args.pattern,
            search_keys_flag=not args.values_only,
            search_values_flag=not args.keys_only,
            use_regex=args.regex,
        )
    except Exception as exc:  # noqa: BLE001
        print(f"error: {exc}", file=sys.stderr)
        return 1

    if not results:
        print("No matches found.")
        return 0

    for key, value in sorted(results.items()):
        if args.keys_only:
            print(key)
        else:
            print(f"{key}={value}")

    return 0


def add_search_commands(
    subparsers: argparse._SubParsersAction,  # type: ignore[type-arg]
) -> None:
    """Register the ``search`` sub-command on *subparsers*."""
    p = subparsers.add_parser(
        "search",
        help="Search secrets by key or value pattern.",
    )
    p.add_argument("project_dir", help="Path to the project directory.")
    p.add_argument("pattern", help="Pattern to search for (fnmatch or regex).")
    p.add_argument(
        "--regex",
        action="store_true",
        default=False,
        help="Treat PATTERN as a regular expression.",
    )
    p.add_argument(
        "--keys-only",
        action="store_true",
        default=False,
        help="Only search key names.",
    )
    p.add_argument(
        "--values-only",
        action="store_true",
        default=False,
        help="Only search values.",
    )
    p.set_defaults(func=cmd_search)
