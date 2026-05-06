"""Vault locking: temporarily lock a vault so no reads or writes are allowed."""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path

_LOCK_FILENAME = ".vault.lock"


def _lock_path(vault_dir: str | Path) -> Path:
    return Path(vault_dir) / _LOCK_FILENAME


def _now_utc() -> str:
    return datetime.now(timezone.utc).isoformat()


def lock_vault(vault_dir: str | Path, reason: str = "", actor: str = "envault") -> dict:
    """Create a lock file in *vault_dir*. Raises RuntimeError if already locked."""
    path = _lock_path(vault_dir)
    if path.exists():
        info = json.loads(path.read_text())
        raise RuntimeError(
            f"Vault is already locked (locked_at={info['locked_at']}, reason={info['reason']!r})"
        )
    Path(vault_dir).mkdir(parents=True, exist_ok=True)
    payload = {"locked_at": _now_utc(), "reason": reason, "actor": actor}
    path.write_text(json.dumps(payload))
    return payload


def unlock_vault(vault_dir: str | Path) -> None:
    """Remove the lock file. Raises RuntimeError if vault is not locked."""
    path = _lock_path(vault_dir)
    if not path.exists():
        raise RuntimeError("Vault is not locked.")
    path.unlink()


def is_locked(vault_dir: str | Path) -> bool:
    """Return True if a lock file exists."""
    return _lock_path(vault_dir).exists()


def lock_info(vault_dir: str | Path) -> dict | None:
    """Return lock metadata dict, or None if not locked."""
    path = _lock_path(vault_dir)
    if not path.exists():
        return None
    return json.loads(path.read_text())


def assert_unlocked(vault_dir: str | Path) -> None:
    """Raise RuntimeError with details if the vault is locked."""
    info = lock_info(vault_dir)
    if info:
        raise RuntimeError(
            f"Vault is locked (locked_at={info['locked_at']}, reason={info['reason']!r}). "
            "Run 'envault unlock' to proceed."
        )
