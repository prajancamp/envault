"""Key rotation: re-encrypt all secrets under a new master password."""

from __future__ import annotations

from pathlib import Path
from typing import Optional

from envault.audit import record
from envault.store import load_secrets, save_secrets


def rotate_password(
    project_dir: Path,
    old_password: str,
    new_password: str,
    *,
    dry_run: bool = False,
) -> int:
    """Re-encrypt every secret in *project_dir* from *old_password* to *new_password*.

    Returns the number of secrets that were re-encrypted.
    Raises ``ValueError`` if *old_password* is wrong (propagated from crypto layer).
    If *dry_run* is True the vault is not written and no audit entry is created.
    """
    secrets = load_secrets(project_dir, old_password)
    count = len(secrets)

    if not dry_run:
        save_secrets(project_dir, new_password, secrets)
        record(
            project_dir,
            "rotate",
            key="*",
            detail=f"re-encrypted {count} secret(s)",
        )

    return count


def rotate_summary(
    project_dir: Path,
    old_password: str,
    new_password: str,
) -> dict:
    """Return a summary dict without mutating the vault (dry-run wrapper)."""
    count = rotate_password(project_dir, old_password, new_password, dry_run=True)
    return {"project_dir": str(project_dir), "secrets_count": count, "dry_run": True}
