"""Alias support: map short names to secret keys."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Dict, List, Optional

_ALIAS_FILE = ".envault_aliases.json"


def _alias_path(project_dir: str) -> Path:
    return Path(project_dir) / _ALIAS_FILE


def _load_aliases(project_dir: str) -> Dict[str, str]:
    path = _alias_path(project_dir)
    if not path.exists():
        return {}
    return json.loads(path.read_text())


def _save_aliases(project_dir: str, aliases: Dict[str, str]) -> None:
    path = _alias_path(project_dir)
    path.write_text(json.dumps(aliases, indent=2))


def set_alias(project_dir: str, alias: str, key: str, known_keys: List[str]) -> None:
    """Create or update an alias pointing to a secret key."""
    if key not in known_keys:
        raise KeyError(f"Secret key '{key}' does not exist in the vault.")
    aliases = _load_aliases(project_dir)
    aliases[alias] = key
    _save_aliases(project_dir, aliases)


def remove_alias(project_dir: str, alias: str) -> None:
    """Remove an alias. Raises KeyError if alias does not exist."""
    aliases = _load_aliases(project_dir)
    if alias not in aliases:
        raise KeyError(f"Alias '{alias}' not found.")
    del aliases[alias]
    _save_aliases(project_dir, aliases)


def resolve_alias(project_dir: str, alias: str) -> Optional[str]:
    """Return the secret key for an alias, or None if not found."""
    return _load_aliases(project_dir).get(alias)


def list_aliases(project_dir: str) -> Dict[str, str]:
    """Return all aliases as {alias: key} mapping."""
    return _load_aliases(project_dir)


def resolve_key(project_dir: str, name: str) -> str:
    """Return the real key for a name, resolving alias if needed."""
    resolved = resolve_alias(project_dir, name)
    return resolved if resolved is not None else name
