"""CLI commands for secret templates."""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from envault.store import load_secrets
from envault.templates import (
    delete_template,
    list_templates,
    load_template,
    save_template,
    validate_against_template,
)


def _get_password(args: argparse.Namespace) -> str:
    import getpass
    return getpass.getpass("Master password: ")


def cmd_template_save(args: argparse.Namespace) -> int:
    """Save a template from a JSON field spec file."""
    spec_path = Path(args.spec_file)
    if not spec_path.exists():
        print(f"error: spec file not found: {spec_path}", file=sys.stderr)
        return 1
    fields = json.loads(spec_path.read_text(encoding="utf-8"))
    project_dir = Path(args.project_dir)
    save_template(project_dir, args.name, fields)
    print(f"Template '{args.name}' saved ({len(fields)} fields).")
    return 0


def cmd_template_list(args: argparse.Namespace) -> int:
    project_dir = Path(args.project_dir)
    names = list_templates(project_dir)
    if not names:
        print("No templates defined.")
    else:
        for n in names:
            print(n)
    return 0


def cmd_template_show(args: argparse.Namespace) -> int:
    project_dir = Path(args.project_dir)
    try:
        fields = load_template(project_dir, args.name)
    except FileNotFoundError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1
    print(json.dumps(fields, indent=2))
    return 0


def cmd_template_delete(args: argparse.Namespace) -> int:
    project_dir = Path(args.project_dir)
    try:
        delete_template(project_dir, args.name)
    except FileNotFoundError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1
    print(f"Template '{args.name}' deleted.")
    return 0


def cmd_template_validate(args: argparse.Namespace) -> int:
    project_dir = Path(args.project_dir)
    password = _get_password(args)
    secrets = load_secrets(project_dir, password)
    try:
        result = validate_against_template(project_dir, args.name, secrets)
    except FileNotFoundError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1
    missing = result["missing"]
    extra = result["extra"]
    if missing:
        print("Missing required keys:")
        for k in missing:
            print(f"  - {k}")
    if extra and args.strict:
        print("Undeclared keys (strict mode):")
        for k in extra:
            print(f"  + {k}")
    if missing or (extra and args.strict):
        return 1
    print("Validation passed.")
    return 0


def add_template_commands(subparsers: argparse._SubParsersAction, parent: argparse.ArgumentParser) -> None:  # noqa: SLF001
    tp = subparsers.add_parser("template", help="Manage secret templates")
    ts = tp.add_subparsers(dest="template_cmd", required=True)

    p_save = ts.add_parser("save", parents=[parent], help="Save a template from JSON spec")
    p_save.add_argument("name")
    p_save.add_argument("spec_file")
    p_save.set_defaults(func=cmd_template_save)

    p_list = ts.add_parser("list", parents=[parent], help="List templates")
    p_list.set_defaults(func=cmd_template_list)

    p_show = ts.add_parser("show", parents=[parent], help="Show template fields")
    p_show.add_argument("name")
    p_show.set_defaults(func=cmd_template_show)

    p_del = ts.add_parser("delete", parents=[parent], help="Delete a template")
    p_del.add_argument("name")
    p_del.set_defaults(func=cmd_template_delete)

    p_val = ts.add_parser("validate", parents=[parent], help="Validate current secrets against template")
    p_val.add_argument("name")
    p_val.add_argument("--strict", action="store_true", help="Fail on undeclared keys")
    p_val.set_defaults(func=cmd_template_validate)
