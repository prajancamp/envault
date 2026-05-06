"""TTL (time-to-live) support for secrets — mark secrets with an expiry
and query / purge expired ones."""

from __future__ import annotations

import datetime
from typing import Dict, List, Optional

from envault.store import load_secrets, save_secrets

# Internal metadata key prefix used to store expiry timestamps
_TTL_PREFIX = "__ttl__:"


def _ttl_key(secret_key: str) -> str:
    return f"{_TTL_PREFIX}{secret_key}"


def _now_utc() -> datetime.datetime:
    return datetime.datetime.now(datetime.timezone.utc)


def set_ttl(
    project_dir: str,
    password: str,
    key: str,
    seconds: int,
) -> datetime.datetime:
    """Attach an expiry to *key*.  Returns the absolute expiry datetime (UTC)."""
    secrets = load_secrets(project_dir, password)
    if key not in secrets:
        raise KeyError(f"Secret '{key}' does not exist.")
    if seconds <= 0:
        raise ValueError("TTL must be a positive number of seconds.")
    expires_at = _now_utc() + datetime.timedelta(seconds=seconds)
    secrets[_ttl_key(key)] = expires_at.isoformat()
    save_secrets(project_dir, password, secrets)
    return expires_at


def get_ttl(project_dir: str, password: str, key: str) -> Optional[datetime.datetime]:
    """Return the expiry datetime for *key*, or None if no TTL is set."""
    secrets = load_secrets(project_dir, password)
    raw = secrets.get(_ttl_key(key))
    if raw is None:
        return None
    return datetime.datetime.fromisoformat(raw)


def remove_ttl(project_dir: str, password: str, key: str) -> bool:
    """Remove the TTL from *key*.  Returns True if a TTL existed."""
    secrets = load_secrets(project_dir, password)
    tk = _ttl_key(key)
    if tk not in secrets:
        return False
    del secrets[tk]
    save_secrets(project_dir, password, secrets)
    return True


def list_expired(project_dir: str, password: str) -> List[str]:
    """Return secret keys whose TTL has passed."""
    secrets = load_secrets(project_dir, password)
    now = _now_utc()
    expired: List[str] = []
    for k, v in secrets.items():
        if k.startswith(_TTL_PREFIX):
            secret_key = k[len(_TTL_PREFIX):]
            if datetime.datetime.fromisoformat(v) <= now:
                expired.append(secret_key)
    return expired


def purge_expired(project_dir: str, password: str) -> Dict[str, str]:
    """Delete all secrets (and their TTL entries) that have expired.
    Returns a mapping of {key: expired_at_iso} for the purged secrets."""
    secrets = load_secrets(project_dir, password)
    now = _now_utc()
    purged: Dict[str, str] = {}
    keys_to_delete: List[str] = []
    for k, v in list(secrets.items()):
        if k.startswith(_TTL_PREFIX):
            secret_key = k[len(_TTL_PREFIX):]
            if datetime.datetime.fromisoformat(v) <= now:
                purged[secret_key] = v
                keys_to_delete.extend([k, secret_key])
    for k in keys_to_delete:
        secrets.pop(k, None)
    if purged:
        save_secrets(project_dir, password, secrets)
    return purged
