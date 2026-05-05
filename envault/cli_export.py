"""CLI sub-commands for exporting and importing secrets.

Registered by cli.py via ``add_export_commands``.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from envault.audit import record
from envault.cli import _get_password
from envault.export import (
    export_dotenv,
    export_json,
    import_dotenv,
    import_json,
    read_file,
    write_file,
)
from envault.store import load_secrets, save_secrets


def cmd_export(args: argparse.Namespace) -> int:
    """Export secrets to a file (dotenv or JSON)."""
    password = _get_password(confirm=False)
    secrets = load_secrets(args.project_dir, password)

    fmt = args.format.lower()
    if fmt == 'dotenv':
        content = export_dotenv(secrets)
    elif fmt == 'json':
        content = export_json(secrets)
    else:
        print(f'Unknown format: {fmt!r}. Use dotenv or json.', file=sys.stderr)
        return 1

    out_path = Path(args.output)
    write_file(out_path, content)
    record(args.project_dir, 'export', f'format={fmt} dest={out_path}')
    print(f'Exported {len(secrets)} secret(s) to {out_path} [{fmt}].')
    return 0


def cmd_import(args: argparse.Namespace) -> int:
    """Import secrets from a file (dotenv or JSON), merging into vault."""
    password = _get_password(confirm=False)

    in_path = Path(args.input)
    if not in_path.exists():
        print(f'File not found: {in_path}', file=sys.stderr)
        return 1

    text = read_file(in_path)
    fmt = args.format.lower()
    try:
        if fmt == 'dotenv':
            incoming = import_dotenv(text)
        elif fmt == 'json':
            incoming = import_json(text)
        else:
            print(f'Unknown format: {fmt!r}. Use dotenv or json.', file=sys.stderr)
            return 1
    except (ValueError, Exception) as exc:  # noqa: BLE001
        print(f'Failed to parse {in_path}: {exc}', file=sys.stderr)
        return 1

    existing = load_secrets(args.project_dir, password)
    merged = {**existing, **incoming}
    save_secrets(args.project_dir, password, merged)
    added = len(merged) - len(existing)
    updated = len(incoming) - added
    record(args.project_dir, 'import', f'format={fmt} src={in_path} added={added} updated={updated}')
    print(f'Imported {len(incoming)} secret(s) from {in_path} ({added} new, {updated} updated).')
    return 0


def add_export_commands(subparsers: argparse._SubParsersAction) -> None:  # type: ignore[type-arg]
    """Attach export/import sub-commands to an existing subparsers group."""
    # export
    p_export = subparsers.add_parser('export', help='Export secrets to a file.')
    p_export.add_argument('output', help='Destination file path.')
    p_export.add_argument('--format', default='dotenv', choices=['dotenv', 'json'],
                          help='Output format (default: dotenv).')
    p_export.set_defaults(func=cmd_export)

    # import
    p_import = subparsers.add_parser('import', help='Import secrets from a file.')
    p_import.add_argument('input', help='Source file path.')
    p_import.add_argument('--format', default='dotenv', choices=['dotenv', 'json'],
                          help='Input format (default: dotenv).')
    p_import.set_defaults(func=cmd_import)
