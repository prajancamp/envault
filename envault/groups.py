"""Secret grouping — assign secrets to named groups for bulk operations."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Dict, List

from envault.store import load_secrets

_GROUP_FILE = ".envault_groups.json"


def _groups_path(project_dir: str) -> Path:
    return Path(project_dir) / _GROUP_FILE


def _load_groups(project_dir: str) -> Dict[str, List[str]]:
    p = _groups_path(project_dir)
    if not p.exists():
        return {}
    return json.loads(p.read_text())


def _save_groups(project_dir: str, data: Dict[str, List[str]]) -> None:
    _groups_path(project_dir).write_text(json.dumps(data, indent=2))


def add_to_group(project_dir: str, password: str, group: str, key: str) -> None:
    """Add *key* to *group*. Raises KeyError if the secret key does not exist."""
    secrets = load_secrets(project_dir, password)
    if key not in secrets:
        raise KeyError(f"Secret '{key}' not found in vault.")
    data = _load_groups(project_dir)
    members = data.setdefault(group, [])
    if key not in members:
        members.append(key)
    _save_groups(project_dir, data)


def remove_from_group(project_dir: str, group: str, key: str) -> bool:
    """Remove *key* from *group*. Returns True if removed, False if not present."""
    data = _load_groups(project_dir)
    members = data.get(group, [])
    if key not in members:
        return False
    members.remove(key)
    if not members:
        del data[group]
    _save_groups(project_dir, data)
    return True


def list_groups(project_dir: str) -> Dict[str, List[str]]:
    """Return all groups and their member keys."""
    return _load_groups(project_dir)


def get_group_members(project_dir: str, group: str) -> List[str]:
    """Return the list of secret keys belonging to *group*."""
    return _load_groups(project_dir).get(group, [])


def delete_group(project_dir: str, group: str) -> bool:
    """Delete an entire group. Returns True if it existed."""
    data = _load_groups(project_dir)
    if group not in data:
        return False
    del data[group]
    _save_groups(project_dir, data)
    return True
