"""Command-line interface for envault."""

import sys
import getpass
import argparse

from envault.store import load_secrets, save_secrets, set_secret, delete_secret, list_keys
from envault.audit import record, read_log


def _get_password(prompt: str = "Vault password: ") -> str:
    return getpass.getpass(prompt)


def cmd_set(args: argparse.Namespace) -> int:
    password = _get_password()
    secrets = load_secrets(args.project, password)
    set_secret(secrets, args.key, args.value)
    save_secrets(args.project, password, secrets)
    record(args.project, "set", args.key)
    print(f"[envault] Set '{args.key}' in project '{args.project}'.")
    return 0


def cmd_get(args: argparse.Namespace) -> int:
    password = _get_password()
    secrets = load_secrets(args.project, password)
    value = secrets.get(args.key)
    if value is None:
        print(f"[envault] Key '{args.key}' not found in project '{args.project}'.", file=sys.stderr)
        return 1
    record(args.project, "get", args.key)
    print(value)
    return 0


def cmd_delete(args: argparse.Namespace) -> int:
    password = _get_password()
    secrets = load_secrets(args.project, password)
    removed = delete_secret(secrets, args.key)
    if not removed:
        print(f"[envault] Key '{args.key}' not found.", file=sys.stderr)
        return 1
    save_secrets(args.project, password, secrets)
    record(args.project, "delete", args.key)
    print(f"[envault] Deleted '{args.key}' from project '{args.project}'.")
    return 0


def cmd_list(args: argparse.Namespace) -> int:
    password = _get_password()
    secrets = load_secrets(args.project, password)
    keys = list_keys(secrets)
    if not keys:
        print(f"[envault] No secrets found in project '{args.project}'.")
    else:
        for k in keys:
            print(k)
    return 0


def cmd_log(args: argparse.Namespace) -> int:
    entries = read_log(args.project)
    if not entries:
        print(f"[envault] No audit log entries for project '{args.project}'.")
    else:
        for entry in entries:
            project_part = f"[{entry['project']}] " if not args.project else ""
            print(f"{entry['timestamp']}  {project_part}{entry['action']:8s}  {entry['key']}")
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="envault",
        description="Secure local environment variable manager.",
    )
    sub = parser.add_subparsers(dest="command", required=True)

    for cmd_name in ("set", "get", "delete", "list"):
        p = sub.add_parser(cmd_name, help=f"{cmd_name} a secret")
        p.add_argument("project", help="Project name")
        if cmd_name in ("set", "get", "delete"):
            p.add_argument("key", help="Secret key name")
        if cmd_name == "set":
            p.add_argument("value", help="Secret value")

    p_log = sub.add_parser("log", help="Show audit log")
    p_log.add_argument("project", nargs="?", default=None, help="Filter by project")

    return parser


def main() -> None:
    parser = build_parser()
    args = parser.parse_args()
    handlers = {"set": cmd_set, "get": cmd_get, "delete": cmd_delete, "list": cmd_list, "log": cmd_log}
    sys.exit(handlers[args.command](args))


if __name__ == "__main__":
    main()
