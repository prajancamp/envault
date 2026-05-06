"""Per-key change history tracking for envault."""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from envault.store import _vault_path


def _history_dir(project_dir: Path) -> Path:
    return _vault_path(project_dir).parent / "history"


def _history_path(project_dir: Path, key: str) -> Path:
    safe = key.replace("/", "__").replace("\\", "__")
    return _history_dir(project_dir) / f"{safe}.json"


def _now_utc() -> str:
    return datetime.now(timezone.utc).isoformat()


def record_change(
    project_dir: Path,
    key: str,
    action: str,
    actor: str = "user",
) -> None:
    """Append a change event for *key* to its history file."""
    history_dir = _history_dir(project_dir)
    history_dir.mkdir(parents=True, exist_ok=True)

    path = _history_path(project_dir, key)
    events: list[dict[str, Any]] = []
    if path.exists():
        events = json.loads(path.read_text(encoding="utf-8"))

    events.append({"timestamp": _now_utc(), "action": action, "actor": actor})
    path.write_text(json.dumps(events, indent=2), encoding="utf-8")


def get_history(
    project_dir: Path,
    key: str,
) -> list[dict[str, Any]]:
    """Return the list of change events for *key*, oldest first."""
    path = _history_path(project_dir, key)
    if not path.exists():
        return []
    return json.loads(path.read_text(encoding="utf-8"))


def clear_history(project_dir: Path, key: str) -> int:
    """Delete the history file for *key*. Returns number of events removed."""
    path = _history_path(project_dir, key)
    if not path.exists():
        return 0
    events = json.loads(path.read_text(encoding="utf-8"))
    count = len(events)
    path.unlink()
    return count


def list_tracked_keys(project_dir: Path) -> list[str]:
    """Return all keys that have at least one history entry."""
    history_dir = _history_dir(project_dir)
    if not history_dir.exists():
        return []
    return sorted(p.stem.replace("__", "/") for p in history_dir.glob("*.json"))
