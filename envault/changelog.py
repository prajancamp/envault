"""Per-secret changelog: human-readable summaries attached to history events."""

from __future__ import annotations

import json
from pathlib import Path
from typing import List, Optional

from envault.store import _vault_path, load_secrets


def _changelog_path(project_dir: str) -> Path:
    return _vault_path(project_dir).parent / ".envault" / "changelog.json"


def _load_changelog(project_dir: str) -> dict:
    path = _changelog_path(project_dir)
    if not path.exists():
        return {}
    return json.loads(path.read_text())


def _save_changelog(project_dir: str, data: dict) -> None:
    path = _changelog_path(project_dir)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2))


def add_entry(project_dir: str, password: str, key: str, summary: str, actor: str = "user") -> dict:
    """Attach a changelog summary to *key*. Raises KeyError if key does not exist."""
    secrets = load_secrets(project_dir, password)
    if key not in secrets:
        raise KeyError(f"Secret '{key}' does not exist.")

    from envault.history import _now_utc
    data = _load_changelog(project_dir)
    entry = {"actor": actor, "summary": summary, "timestamp": _now_utc()}
    data.setdefault(key, []).append(entry)
    _save_changelog(project_dir, data)
    return entry


def get_entries(project_dir: str, key: str) -> List[dict]:
    """Return all changelog entries for *key*, oldest first."""
    data = _load_changelog(project_dir)
    return list(data.get(key, []))


def remove_entries(project_dir: str, key: str) -> int:
    """Delete all changelog entries for *key*. Returns number of entries removed."""
    data = _load_changelog(project_dir)
    removed = data.pop(key, [])
    _save_changelog(project_dir, data)
    return len(removed)


def list_keys_with_changelog(project_dir: str) -> List[str]:
    """Return keys that have at least one changelog entry."""
    data = _load_changelog(project_dir)
    return [k for k, v in data.items() if v]
