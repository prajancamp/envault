"""Favorites — mark frequently-used secrets for quick access."""

from __future__ import annotations

import json
from pathlib import Path
from typing import List

from envault.store import _vault_path, load_secrets


def _favorites_path(project_dir: str) -> Path:
    return _vault_path(project_dir).parent / "favorites.json"


def _load_favorites(project_dir: str) -> List[str]:
    path = _favorites_path(project_dir)
    if not path.exists():
        return []
    return json.loads(path.read_text())


def _save_favorites(project_dir: str, favorites: List[str]) -> None:
    path = _favorites_path(project_dir)
    path.write_text(json.dumps(favorites, indent=2))


def add_favorite(project_dir: str, key: str, password: str) -> None:
    """Mark *key* as a favorite. Raises KeyError if key is not in the vault."""
    secrets = load_secrets(project_dir, password)
    if key not in secrets:
        raise KeyError(f"Secret '{key}' does not exist.")
    favorites = _load_favorites(project_dir)
    if key not in favorites:
        favorites.append(key)
        _save_favorites(project_dir, favorites)


def remove_favorite(project_dir: str, key: str) -> None:
    """Remove *key* from favorites. No-op if not currently a favorite."""
    favorites = _load_favorites(project_dir)
    if key in favorites:
        favorites.remove(key)
        _save_favorites(project_dir, favorites)


def list_favorites(project_dir: str) -> List[str]:
    """Return the list of favorited keys in insertion order."""
    return list(_load_favorites(project_dir))


def is_favorite(project_dir: str, key: str) -> bool:
    """Return True if *key* is currently marked as a favorite."""
    return key in _load_favorites(project_dir)


def get_favorite_secrets(
    project_dir: str, password: str
) -> dict:
    """Return a dict of {key: value} for every favorited key that still exists."""
    secrets = load_secrets(project_dir, password)
    return {k: secrets[k] for k in _load_favorites(project_dir) if k in secrets}
