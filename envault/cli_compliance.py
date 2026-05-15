"""CLI commands for compliance reporting."""
from __future__ import annotations

import argparse
import getpass
import json
import sys

from envault.compliance import generate_report


def _get_password(args: argparse.Namespace) -> str:
    if hasattr(args, "password") and args.password:
        return args.password
    return getpass.getpass("Vault password: ")


def cmd_compliance_report(args: argparse.Namespace) -> int:
    """Print a compliance report for the current project."""
    password = _get_password(args)
    try:
        report = generate_report(args.project_dir, password)
    except Exception as exc:  # noqa: BLE001
        print(f"error: {exc}", file=sys.stderr)
        return 1

    if args.format == "json":
        print(json.dumps(report.as_dict(), indent=2, default=str))
        return 0

    # Human-readable output
    print(f"Compliance report for: {report.project_dir}")
    print(f"  Total secrets   : {report.total_secrets}")
    print(f"  Compliant       : {report.compliant_count}")
    print(f"  Non-compliant   : {report.non_compliant_count}")
    print()
    for item in report.items:
        status = "OK" if item.compliant else "FAIL"
        flags = []
        if item.has_ttl:
            flags.append("ttl")
        if item.has_acl:
            flags.append("acl")
        if item.is_pinned:
            flags.append("pinned")
        flag_str = ", ".join(flags) if flags else "none"
        print(f"  [{status}] {item.key}  (flags: {flag_str})")
        for v in item.policy_violations:
            print(f"        policy violation: {v}")
        for e in item.lint_errors:
            print(f"        lint error: {e}")

    return 0 if report.non_compliant_count == 0 else 2


def add_compliance_commands(subparsers: argparse._SubParsersAction) -> None:  # noqa: SLF001
    p = subparsers.add_parser("compliance", help="Generate a compliance report")
    p.add_argument("project_dir", help="Project directory")
    p.add_argument("--password", help="Vault password (omit to prompt)")
    p.add_argument(
        "--format",
        choices=["text", "json"],
        default="text",
        help="Output format (default: text)",
    )
    p.set_defaults(func=cmd_compliance_report)
