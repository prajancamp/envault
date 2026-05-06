"""Diff two snapshots or a snapshot against the current vault."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, List, Optional, Tuple

from envault.snapshot import _snapshot_path, restore_snapshot
from envault.store import load_secrets


@dataclass
class SecretDiff:
    added: List[str]
    removed: List[str]
    changed: List[str]
    unchanged: List[str]

    @property
    def has_changes(self) -> bool:
        return bool(self.added or self.removed or self.changed)


def _secrets_from_snapshot(
    project_dir: str, snapshot_name: str, password: str
) -> Dict[str, str]:
    """Load secrets from a named snapshot without altering the live vault."""
    snap_file = _snapshot_path(project_dir, snapshot_name)
    if not snap_file.exists():
        raise FileNotFoundError(f"Snapshot not found: {snapshot_name}")
    # Temporarily restore to a side path by reading raw snapshot data.
    # We re-use load_secrets with the snapshot file path directly.
    from envault.store import _load_raw, _vault_path  # local import to avoid cycles
    import json
    from envault.crypto import decrypt

    raw = snap_file.read_text(encoding="utf-8")
    payload = json.loads(raw)
    decrypted: Dict[str, str] = {}
    for key, ciphertext in payload.items():
        decrypted[key] = decrypt(ciphertext, password)
    return decrypted


def diff_snapshots(
    project_dir: str,
    snapshot_a: str,
    snapshot_b: str,
    password: str,
) -> SecretDiff:
    """Return the diff between two named snapshots."""
    secrets_a = _secrets_from_snapshot(project_dir, snapshot_a, password)
    secrets_b = _secrets_from_snapshot(project_dir, snapshot_b, password)
    return _compute_diff(secrets_a, secrets_b)


def diff_snapshot_vs_current(
    project_dir: str,
    snapshot_name: str,
    password: str,
) -> SecretDiff:
    """Return the diff between a snapshot and the live vault."""
    snap_secrets = _secrets_from_snapshot(project_dir, snapshot_name, password)
    current_secrets = load_secrets(project_dir, password)
    return _compute_diff(snap_secrets, current_secrets)


def _compute_diff(
    before: Dict[str, str],
    after: Dict[str, str],
) -> SecretDiff:
    keys_before = set(before)
    keys_after = set(after)

    added = sorted(keys_after - keys_before)
    removed = sorted(keys_before - keys_after)
    common = keys_before & keys_after
    changed = sorted(k for k in common if before[k] != after[k])
    unchanged = sorted(k for k in common if before[k] == after[k])

    return SecretDiff(
        added=added,
        removed=removed,
        changed=changed,
        unchanged=unchanged,
    )
