"""Secret inheritance: allow a project vault to inherit secrets from a parent vault."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Dict, List, Optional

from envault.store import load_secrets, _vault_path

_INHERIT_FILE = ".envault_inherit"


def _inherit_path(project_dir: str) -> Path:
    return Path(project_dir) / _INHERIT_FILE


def set_parent(project_dir: str, parent_dir: str) -> None:
    """Record *parent_dir* as the inheritance source for *project_dir*."""
    path = _inherit_path(project_dir)
    config: Dict = {}
    if path.exists():
        config = json.loads(path.read_text())
    config["parent"] = str(Path(parent_dir).resolve())
    path.write_text(json.dumps(config, indent=2))


def remove_parent(project_dir: str) -> None:
    """Remove inheritance configuration from *project_dir*."""
    path = _inherit_path(project_dir)
    if not path.exists():
        return
    config = json.loads(path.read_text())
    config.pop("parent", None)
    path.write_text(json.dumps(config, indent=2))


def get_parent(project_dir: str) -> Optional[str]:
    """Return the configured parent directory, or *None* if not set."""
    path = _inherit_path(project_dir)
    if not path.exists():
        return None
    config = json.loads(path.read_text())
    return config.get("parent")


def resolve_secrets(
    project_dir: str,
    password: str,
    override: bool = True,
) -> Dict[str, str]:
    """Return merged secrets: parent secrets combined with child secrets.

    If *override* is True (default) child keys shadow parent keys.
    If *override* is False parent keys take precedence.
    """
    parent_dir = get_parent(project_dir)
    parent_secrets: Dict[str, str] = {}
    if parent_dir is not None:
        vault = _vault_path(parent_dir)
        if vault.exists():
            parent_secrets = load_secrets(parent_dir, password)

    child_secrets = load_secrets(project_dir, password)

    if override:
        merged = {**parent_secrets, **child_secrets}
    else:
        merged = {**child_secrets, **parent_secrets}

    return merged


def inheritance_summary(project_dir: str, password: str) -> Dict:
    """Return a summary dict describing the inheritance state."""
    parent_dir = get_parent(project_dir)
    parent_keys: List[str] = []
    if parent_dir is not None:
        vault = _vault_path(parent_dir)
        if vault.exists():
            parent_keys = list(load_secrets(parent_dir, password).keys())
    child_keys = list(load_secrets(project_dir, password).keys())
    overridden = [k for k in child_keys if k in parent_keys]
    return {
        "parent": parent_dir,
        "parent_keys": parent_keys,
        "child_keys": child_keys,
        "overridden_keys": overridden,
    }
