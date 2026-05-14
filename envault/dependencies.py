"""Secret dependency tracking — declare that one secret depends on another.

If a dependency is rotated or deleted, dependents can be flagged.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Dict, List

from envault.store import _vault_path, load_secrets


def _dep_path(project_dir: str) -> Path:
    return _vault_path(project_dir).parent / "dependencies.json"


def _load_deps(project_dir: str) -> Dict[str, List[str]]:
    p = _dep_path(project_dir)
    if not p.exists():
        return {}
    return json.loads(p.read_text())


def _save_deps(project_dir: str, data: Dict[str, List[str]]) -> None:
    _dep_path(project_dir).write_text(json.dumps(data, indent=2))


def add_dependency(project_dir: str, password: str, key: str, depends_on: str) -> None:
    """Record that *key* depends on *depends_on*.

    Both keys must exist in the vault.
    """
    secrets = load_secrets(project_dir, password)
    if key not in secrets:
        raise KeyError(f"Key not found in vault: {key}")
    if depends_on not in secrets:
        raise KeyError(f"Key not found in vault: {depends_on}")
    if key == depends_on:
        raise ValueError("A key cannot depend on itself.")

    data = _load_deps(project_dir)
    deps = data.get(key, [])
    if depends_on not in deps:
        deps.append(depends_on)
    data[key] = deps
    _save_deps(project_dir, data)


def remove_dependency(project_dir: str, key: str, depends_on: str) -> bool:
    """Remove a declared dependency.  Returns True if it existed."""
    data = _load_deps(project_dir)
    deps = data.get(key, [])
    if depends_on not in deps:
        return False
    deps.remove(depends_on)
    if deps:
        data[key] = deps
    else:
        data.pop(key, None)
    _save_deps(project_dir, data)
    return True


def get_dependencies(project_dir: str, key: str) -> List[str]:
    """Return the list of keys that *key* depends on."""
    return _load_deps(project_dir).get(key, [])


def get_dependents(project_dir: str, key: str) -> List[str]:
    """Return all keys that declare a dependency on *key*."""
    data = _load_deps(project_dir)
    return [k for k, deps in data.items() if key in deps]


def stale_dependents(project_dir: str, password: str, changed_key: str) -> List[str]:
    """Return dependents of *changed_key* that still exist in the vault."""
    secrets = load_secrets(project_dir, password)
    return [k for k in get_dependents(project_dir, changed_key) if k in secrets]
