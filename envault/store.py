"""Persistent encrypted storage for per-project environment variables."""

import json
import os
from pathlib import Path
from typing import Dict, Optional

from envault.crypto import encrypt, decrypt

DEFAULT_VAULT_DIR = Path.home() / ".envault"


def _vault_path(project: str, vault_dir: Path = DEFAULT_VAULT_DIR) -> Path:
    """Return the path to the vault file for a given project."""
    return vault_dir / f"{project}.vault"


def _load_raw(project: str, vault_dir: Path = DEFAULT_VAULT_DIR) -> Optional[str]:
    """Read the raw encrypted payload from disk, or None if it doesn't exist."""
    path = _vault_path(project, vault_dir)
    if not path.exists():
        return None
    return path.read_text(encoding="utf-8")


def _save_raw(project: str, payload: str, vault_dir: Path = DEFAULT_VAULT_DIR) -> None:
    """Write an encrypted payload to disk, creating directories as needed."""
    vault_dir.mkdir(parents=True, exist_ok=True)
    _vault_path(project, vault_dir).write_text(payload, encoding="utf-8")


def load_secrets(
    project: str, password: str, vault_dir: Path = DEFAULT_VAULT_DIR
) -> Dict[str, str]:
    """Decrypt and return all secrets for *project*.

    Returns an empty dict if no vault exists yet.
    Raises ValueError if the password is wrong or the vault is corrupted.
    """
    raw = _load_raw(project, vault_dir)
    if raw is None:
        return {}
    plaintext = decrypt(raw, password)  # raises on bad password / corruption
    return json.loads(plaintext)


def save_secrets(
    project: str,
    secrets: Dict[str, str],
    password: str,
    vault_dir: Path = DEFAULT_VAULT_DIR,
) -> None:
    """Encrypt *secrets* and persist them for *project*."""
    plaintext = json.dumps(secrets)
    payload = encrypt(plaintext, password)
    _save_raw(project, payload, vault_dir)


def set_secret(
    project: str, key: str, value: str, password: str, vault_dir: Path = DEFAULT_VAULT_DIR
) -> None:
    """Add or update a single secret key/value pair for *project*."""
    secrets = load_secrets(project, password, vault_dir)
    secrets[key] = value
    save_secrets(project, secrets, password, vault_dir)


def delete_secret(
    project: str, key: str, password: str, vault_dir: Path = DEFAULT_VAULT_DIR
) -> bool:
    """Remove *key* from the vault. Returns True if the key existed."""
    secrets = load_secrets(project, password, vault_dir)
    existed = key in secrets
    if existed:
        del secrets[key]
        save_secrets(project, secrets, password, vault_dir)
    return existed


def list_projects(vault_dir: Path = DEFAULT_VAULT_DIR) -> list:
    """Return the names of all projects that have a vault on disk."""
    if not vault_dir.exists():
        return []
    return [p.stem for p in sorted(vault_dir.glob("*.vault"))]
