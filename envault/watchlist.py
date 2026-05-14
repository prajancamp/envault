"""Watchlist: flag secrets for monitoring and alert on access or modification."""

from __future__ import annotations

import json
from pathlib import Path
from typing import List, Optional

from envault.store import load_secrets, _vault_path


def _watchlist_path(project_dir: str) -> Path:
    return Path(_vault_path(project_dir)).parent / ".watchlist.json"


def _load_watchlist(project_dir: str) -> dict:
    path = _watchlist_path(project_dir)
    if not path.exists():
        return {}
    return json.loads(path.read_text())


def _save_watchlist(project_dir: str, data: dict) -> None:
    path = _watchlist_path(project_dir)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2))


def add_to_watchlist(project_dir: str, password: str, key: str, reason: Optional[str] = None) -> None:
    """Add a secret key to the watchlist."""
    secrets = load_secrets(project_dir, password)
    if key not in secrets:
        raise KeyError(f"Secret '{key}' does not exist.")
    data = _load_watchlist(project_dir)
    data[key] = {"reason": reason or "", "watched": True}
    _save_watchlist(project_dir, data)


def remove_from_watchlist(project_dir: str, key: str) -> bool:
    """Remove a key from the watchlist. Returns True if it was present."""
    data = _load_watchlist(project_dir)
    if key not in data:
        return False
    del data[key]
    _save_watchlist(project_dir, data)
    return True


def is_watched(project_dir: str, key: str) -> bool:
    """Return True if the key is on the watchlist."""
    return key in _load_watchlist(project_dir)


def get_watchlist(project_dir: str) -> List[dict]:
    """Return all watched keys with their metadata."""
    data = _load_watchlist(project_dir)
    return [
        {"key": k, "reason": v.get("reason", "")}
        for k, v in sorted(data.items())
    ]


def watchlist_summary(project_dir: str) -> dict:
    """Return a summary dict suitable for display."""
    items = get_watchlist(project_dir)
    return {
        "total_watched": len(items),
        "keys": [i["key"] for i in items],
    }
