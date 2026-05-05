"""Append-only audit log for secret read/write operations."""

import json
import os
from datetime import datetime, timezone
from pathlib import Path
from typing import List, Dict, Any, Optional

DEFAULT_LOG_DIR = Path.home() / ".envault"
LOG_FILENAME = "audit.log"


def _log_path(log_dir: Path = DEFAULT_LOG_DIR) -> Path:
    return log_dir / LOG_FILENAME


def _now_iso() -> str:
    return datetime.now(tz=timezone.utc).isoformat(timespec="seconds")


def record(
    action: str,
    project: str,
    key: Optional[str] = None,
    actor: Optional[str] = None,
    log_dir: Path = DEFAULT_LOG_DIR,
) -> None:
    """Append a single audit entry to the log file.

    Parameters
    ----------
    action:  One of 'read', 'write', 'delete', 'list'.
    project: The project whose vault was accessed.
    key:     The specific secret key involved (optional).
    actor:   The OS username performing the action (defaults to current user).
    """
    log_dir.mkdir(parents=True, exist_ok=True)
    entry: Dict[str, Any] = {
        "timestamp": _now_iso(),
        "action": action,
        "project": project,
        "actor": actor or os.getenv("USER") or os.getenv("USERNAME") or "unknown",
    }
    if key is not None:
        entry["key"] = key

    with _log_path(log_dir).open("a", encoding="utf-8") as fh:
        fh.write(json.dumps(entry) + "\n")


def read_log(log_dir: Path = DEFAULT_LOG_DIR) -> List[Dict[str, Any]]:
    """Return all audit entries as a list of dicts (oldest first)."""
    path = _log_path(log_dir)
    if not path.exists():
        return []
    entries = []
    for line in path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if line:
            entries.append(json.loads(line))
    return entries


def filter_log(
    log_dir: Path = DEFAULT_LOG_DIR,
    project: Optional[str] = None,
    action: Optional[str] = None,
) -> List[Dict[str, Any]]:
    """Return audit entries filtered by *project* and/or *action*."""
    entries = read_log(log_dir)
    if project:
        entries = [e for e in entries if e.get("project") == project]
    if action:
        entries = [e for e in entries if e.get("action") == action]
    return entries
