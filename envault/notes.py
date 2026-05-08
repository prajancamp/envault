"""Per-secret notes/annotations stored alongside the vault."""
from __future__ import annotations

import json
from pathlib import Path
from typing import Optional

from envault.store import _vault_path, load_secrets


def _notes_path(project_dir: str) -> Path:
    return Path(_vault_path(project_dir)).parent / ".envault_notes.json"


def _load_notes(project_dir: str) -> dict:
    path = _notes_path(project_dir)
    if not path.exists():
        return {}
    return json.loads(path.read_text())


def _save_notes(project_dir: str, notes: dict) -> None:
    path = _notes_path(project_dir)
    path.write_text(json.dumps(notes, indent=2))


def set_note(project_dir: str, password: str, key: str, note: str) -> None:
    """Attach a note to an existing secret key."""
    secrets = load_secrets(project_dir, password)
    if key not in secrets:
        raise KeyError(f"Secret '{key}' does not exist.")
    notes = _load_notes(project_dir)
    notes[key] = note
    _save_notes(project_dir, notes)


def get_note(project_dir: str, key: str) -> Optional[str]:
    """Return the note for *key*, or None if no note is set."""
    notes = _load_notes(project_dir)
    return notes.get(key)


def remove_note(project_dir: str, key: str) -> bool:
    """Remove the note for *key*.  Returns True if a note existed."""
    notes = _load_notes(project_dir)
    if key not in notes:
        return False
    del notes[key]
    _save_notes(project_dir, notes)
    return True


def list_notes(project_dir: str) -> dict:
    """Return all key → note mappings."""
    return dict(_load_notes(project_dir))


def purge_orphaned_notes(project_dir: str, password: str) -> list:
    """Remove notes whose secret key no longer exists.  Returns removed keys."""
    secrets = load_secrets(project_dir, password)
    notes = _load_notes(project_dir)
    orphans = [k for k in notes if k not in secrets]
    for k in orphans:
        del notes[k]
    if orphans:
        _save_notes(project_dir, notes)
    return orphans
