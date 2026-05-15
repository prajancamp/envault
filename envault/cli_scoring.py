"""CLI commands for secret strength scoring."""
from __future__ import annotations

import argparse
import getpass
import json
import sys

from envault.scoring import compute_vault_scores


def _get_password(args: argparse.Namespace) -> str:
    if hasattr(args, "password") and args.password:
        return args.password
    return getpass.getpass("Vault password: ")


def cmd_score(args: argparse.Namespace) -> int:
    password = _get_password(args)
    try:
        report = compute_vault_scores(args.project_dir, password)
    except Exception as exc:  # noqa: BLE001
        print(f"error: {exc}", file=sys.stderr)
        return 1

    if args.format == "json":
        data = {
            "average_score": round(report.average_score, 2),
            "grade_distribution": report.grade_distribution,
            "secrets": [
                {
                    "key": s.key,
                    "score": s.score,
                    "grade": s.grade,
                    "issues": s.issues,
                }
                for s in report.scores
            ],
        }
        print(json.dumps(data, indent=2))
        return 0

    # text output
    if not report.scores:
        print("No secrets found.")
        return 0

    print(f"{'KEY':<30} {'SCORE':>5}  {'GRADE':>5}  ISSUES")
    print("-" * 70)
    for s in sorted(report.scores, key=lambda x: x.score):
        issues_str = "; ".join(s.issues) if s.issues else "-"
        print(f"{s.key:<30} {s.score:>5}  {s.grade:>5}  {issues_str}")
    print("-" * 70)
    dist = report.grade_distribution
    print(
        f"Average score: {report.average_score:.1f}  "
        + "  ".join(f"{g}:{n}" for g, n in dist.items() if n)
    )
    return 0


def add_scoring_commands(subparsers: argparse._SubParsersAction) -> None:  # type: ignore[type-arg]
    p = subparsers.add_parser("score", help="Show strength scores for vault secrets")
    p.add_argument("--format", choices=["text", "json"], default="text")
    p.add_argument("--password", default="")
    p.add_argument("project_dir")
    p.set_defaults(func=cmd_score)
