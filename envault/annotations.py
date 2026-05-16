"""Per-secret inline annotations (short descriptive metadata)."""
from __future__ import annotations

import json
from pathlib import Path
from typing import Dict, Optional

from envault.store import _vault_path, load_secrets

_ANNOTATION_FILE = ".annotations.json"


def _annotation_path(vault_dir: str) -> Path:
    return Path(vault_dir) / _ANNOTATION_FILE


def _load_annotations(vault_dir: str) -> Dict[str, str]:
    p = _annotation_path(vault_dir)
    if not p.exists():
        return {}
    return json.loads(p.read_text(encoding="utf-8"))


def _save_annotations(vault_dir: str, data: Dict[str, str]) -> None:
    p = _annotation_path(vault_dir)
    p.write_text(json.dumps(data, indent=2), encoding="utf-8")


def set_annotation(vault_dir: str, password: str, key: str, text: str) -> None:
    """Attach a short annotation to *key*.  Raises KeyError if key is absent."""
    secrets = load_secrets(vault_dir, password)
    if key not in secrets:
        raise KeyError(f"Secret '{key}' not found in vault.")
    data = _load_annotations(vault_dir)
    data[key] = text
    _save_annotations(vault_dir, data)


def get_annotation(vault_dir: str, key: str) -> Optional[str]:
    """Return the annotation for *key*, or None if none is set."""
    return _load_annotations(vault_dir).get(key)


def remove_annotation(vault_dir: str, key: str) -> bool:
    """Remove the annotation for *key*.  Returns True if one existed."""
    data = _load_annotations(vault_dir)
    if key not in data:
        return False
    del data[key]
    _save_annotations(vault_dir, data)
    return True


def list_annotations(vault_dir: str) -> Dict[str, str]:
    """Return all key→annotation mappings."""
    return dict(_load_annotations(vault_dir))


def clear_annotation_for_deleted_keys(vault_dir: str, password: str) -> int:
    """Prune annotations whose keys no longer exist; returns pruned count."""
    secrets = load_secrets(vault_dir, password)
    data = _load_annotations(vault_dir)
    stale = [k for k in data if k not in secrets]
    for k in stale:
        del data[k]
    if stale:
        _save_annotations(vault_dir, data)
    return len(stale)
