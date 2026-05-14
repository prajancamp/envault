"""Per-key access control: restrict which OS users may read a secret."""
from __future__ import annotations

import getpass
from typing import List

from envault.store import load_secrets, save_secrets

_ACL_PREFIX = "__acl__."


def _acl_key(secret_key: str) -> str:
    return f"{_ACL_PREFIX}{secret_key}"


def set_acl(vault_dir: str, password: str, secret_key: str, allowed_users: List[str]) -> None:
    """Set the list of OS users allowed to read *secret_key*."""
    if not allowed_users:
        raise ValueError("allowed_users must not be empty; use remove_acl() to lift restrictions.")
    secrets = load_secrets(vault_dir, password)
    if secret_key not in secrets:
        raise KeyError(f"Secret '{secret_key}' does not exist.")
    acl_entry = ",".join(sorted(set(allowed_users)))
    secrets[_acl_key(secret_key)] = acl_entry
    save_secrets(vault_dir, password, secrets)


def remove_acl(vault_dir: str, password: str, secret_key: str) -> None:
    """Remove access restrictions for *secret_key* (allow everyone)."""
    secrets = load_secrets(vault_dir, password)
    key = _acl_key(secret_key)
    if key in secrets:
        del secrets[key]
        save_secrets(vault_dir, password, secrets)


def get_acl(vault_dir: str, password: str, secret_key: str) -> List[str]:
    """Return the list of allowed users, or [] meaning unrestricted."""
    secrets = load_secrets(vault_dir, password)
    key = _acl_key(secret_key)
    if key not in secrets:
        return []
    raw = secrets[key]
    return [u for u in raw.split(",") if u]


def check_access(vault_dir: str, password: str, secret_key: str, username: str | None = None) -> bool:
    """Return True if *username* (defaults to current OS user) may read *secret_key*."""
    allowed = get_acl(vault_dir, password, secret_key)
    if not allowed:
        return True
    user = username or getpass.getuser()
    return user in allowed
