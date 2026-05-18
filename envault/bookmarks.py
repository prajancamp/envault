"""Bookmarks: mark frequently-accessed secrets for quick retrieval."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Dict, List, Optional

from envault.store import load_secrets


def _bookmarks_path(project_dir: str) -> Path:
    return Path(project_dir) / ".envault" / "bookmarks.json"


def _load_bookmarks(project_dir: str) -> Dict[str, str]:
    path = _bookmarks_path(project_dir)
    if not path.exists():
        return {}
    return json.loads(path.read_text())


def _save_bookmarks(project_dir: str, data: Dict[str, str]) -> None:
    path = _bookmarks_path(project_dir)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2))


def add_bookmark(project_dir: str, password: str, key: str, note: str = "") -> None:
    """Bookmark *key*, optionally storing a short note."""
    secrets = load_secrets(project_dir, password)
    if key not in secrets:
        raise KeyError(f"Secret '{key}' does not exist.")
    bookmarks = _load_bookmarks(project_dir)
    bookmarks[key] = note
    _save_bookmarks(project_dir, bookmarks)


def remove_bookmark(project_dir: str, key: str) -> bool:
    """Remove bookmark for *key*. Returns True if it existed."""
    bookmarks = _load_bookmarks(project_dir)
    if key not in bookmarks:
        return False
    del bookmarks[key]
    _save_bookmarks(project_dir, bookmarks)
    return True


def is_bookmarked(project_dir: str, key: str) -> bool:
    return key in _load_bookmarks(project_dir)


def get_bookmark_note(project_dir: str, key: str) -> Optional[str]:
    bookmarks = _load_bookmarks(project_dir)
    return bookmarks.get(key)


def list_bookmarks(project_dir: str) -> List[Dict[str, str]]:
    """Return list of {key, note} dicts sorted by key."""
    bookmarks = _load_bookmarks(project_dir)
    return [{"key": k, "note": v} for k, v in sorted(bookmarks.items())]
