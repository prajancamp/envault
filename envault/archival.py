"""Archival — mark secrets as archived (soft-delete) and restore them."""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List, Optional

from envault.store import _vault_path, load_secrets, save_secrets


def _archive_path(project_dir: str) -> Path:
    return Path(project_dir) / ".envault" / "archived.json"


def _now_utc() -> str:
    return datetime.now(timezone.utc).isoformat()


def _load_archive(project_dir: str) -> Dict[str, dict]:
    path = _archive_path(project_dir)
    if not path.exists():
        return {}
    return json.loads(path.read_text())


def _save_archive(project_dir: str, data: Dict[str, dict]) -> None:
    path = _archive_path(project_dir)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2))


def archive_secret(
    project_dir: str,
    password: str,
    key: str,
    reason: Optional[str] = None,
) -> dict:
    """Move *key* from the live vault into the archive store."""
    secrets = load_secrets(project_dir, password)
    if key not in secrets:
        raise KeyError(f"Secret '{key}' not found in vault.")

    archived = _load_archive(project_dir)
    archived[key] = {
        "value": secrets.pop(key),
        "archived_at": _now_utc(),
        "reason": reason or "",
    }
    save_secrets(project_dir, password, secrets)
    _save_archive(project_dir, archived)
    return archived[key]


def restore_secret(project_dir: str, password: str, key: str) -> str:
    """Move *key* from the archive back into the live vault."""
    archived = _load_archive(project_dir)
    if key not in archived:
        raise KeyError(f"Archived secret '{key}' not found.")

    secrets = load_secrets(project_dir, password)
    value = archived.pop(key)["value"]
    secrets[key] = value
    save_secrets(project_dir, password, secrets)
    _save_archive(project_dir, archived)
    return value


def list_archived(project_dir: str) -> List[dict]:
    """Return a list of archived-secret metadata records (no values)."""
    archived = _load_archive(project_dir)
    return [
        {"key": k, "archived_at": v["archived_at"], "reason": v["reason"]}
        for k, v in archived.items()
    ]


def purge_archived(project_dir: str, key: str) -> None:
    """Permanently delete an archived secret (no restore possible)."""
    archived = _load_archive(project_dir)
    if key not in archived:
        raise KeyError(f"Archived secret '{key}' not found.")
    del archived[key]
    _save_archive(project_dir, archived)
