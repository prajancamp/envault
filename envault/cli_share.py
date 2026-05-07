"""CLI commands for sharing encrypted secret bundles between projects."""

from __future__ import annotations

import argparse
import getpass
import sys

from envault.share import export_bundle, import_bundle


def _get_password(prompt: str = "Vault password: ") -> str:
    return getpass.getpass(prompt)


def cmd_share_export(args: argparse.Namespace) -> int:
    password = _get_password("Vault password: ")
    bundle_password = _get_password("Bundle password: ")
    keys = args.keys if args.keys else None
    try:
        count = export_bundle(
            args.project_dir,
            password,
            keys,
            bundle_password,
            args.output,
        )
        print(f"Exported {count} secret(s) to {args.output}")
        return 0
    except KeyError as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 1
    except Exception as exc:  # noqa: BLE001
        print(f"Export failed: {exc}", file=sys.stderr)
        return 1


def cmd_share_import(args: argparse.Namespace) -> int:
    password = _get_password("Vault password: ")
    bundle_password = _get_password("Bundle password: ")
    try:
        result = import_bundle(
            args.project_dir,
            password,
            bundle_password,
            args.bundle,
            overwrite=args.overwrite,
        )
        print(
            f"Imported {result['imported']} secret(s), "
            f"skipped {result['skipped']} existing."
        )
        return 0
    except FileNotFoundError:
        print(f"Bundle file not found: {args.bundle}", file=sys.stderr)
        return 1
    except Exception as exc:  # noqa: BLE001
        print(f"Import failed: {exc}", file=sys.stderr)
        return 1


def add_share_commands(subparsers: argparse._SubParsersAction) -> None:  # type: ignore[type-arg]
    p_export = subparsers.add_parser("share-export", help="Export secrets to an encrypted bundle")
    p_export.add_argument("--project-dir", default=".", help="Project directory")
    p_export.add_argument("--output", required=True, help="Output bundle file path")
    p_export.add_argument("keys", nargs="*", help="Keys to export (default: all)")
    p_export.set_defaults(func=cmd_share_export)

    p_import = subparsers.add_parser("share-import", help="Import secrets from an encrypted bundle")
    p_import.add_argument("--project-dir", default=".", help="Project directory")
    p_import.add_argument("--overwrite", action="store_true", help="Overwrite existing keys")
    p_import.add_argument("bundle", help="Bundle file path")
    p_import.set_defaults(func=cmd_share_import)
