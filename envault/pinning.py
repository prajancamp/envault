"""Secret pinning — mark secrets as pinned to prevent accidental deletion or overwrite."""

from __future__ import annotations

from pathlib import Path
from typing import List

from envault.store import load_secrets, _vault_path

_PIN_FILENAME = ".pinned.json"


def _pin_path(vault_dir: Path) -> Path:
    return vault_dir / _PIN_FILENAME


def _load_pins(vault_dir: Path) -> List[str]:
    p = _pin_path(vault_dir)
    if not p.exists():
        return []
    import json
    return json.loads(p.read_text())


def _save_pins(vault_dir: Path, pins: List[str]) -> None:
    import json
    _pin_path(vault_dir).write_text(json.dumps(sorted(set(pins)), indent=2))


def pin_secret(vault_dir: Path, key: str, password: str) -> None:
    """Pin a secret key so it cannot be deleted or overwritten without explicit unpin."""
    secrets = load_secrets(vault_dir, password)
    if key not in secrets:
        raise KeyError(f"Secret '{key}' does not exist.")
    pins = _load_pins(vault_dir)
    if key not in pins:
        pins.append(key)
        _save_pins(vault_dir, pins)


def unpin_secret(vault_dir: Path, key: str) -> None:
    """Remove the pin from a secret key."""
    pins = _load_pins(vault_dir)
    if key in pins:
        pins.remove(key)
        _save_pins(vault_dir, pins)


def is_pinned(vault_dir: Path, key: str) -> bool:
    """Return True if the given key is pinned."""
    return key in _load_pins(vault_dir)


def list_pinned(vault_dir: Path) -> List[str]:
    """Return all currently pinned keys."""
    return list(_load_pins(vault_dir))


def assert_not_pinned(vault_dir: Path, key: str) -> None:
    """Raise ValueError if the key is pinned."""
    if is_pinned(vault_dir, key):
        raise ValueError(
            f"Secret '{key}' is pinned and cannot be modified or deleted. "
            "Unpin it first with 'envault pin remove'."
        )
