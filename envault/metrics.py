"""Vault metrics and statistics reporting."""

from __future__ import annotations

import dataclasses
from datetime import datetime, timezone
from typing import Dict, List, Optional

from envault.store import load_secrets
from envault.ttl import get_ttl, _ttl_key
from envault.tags import get_tags, _tag_key
from envault.history import get_history
from envault.groups import list_groups, get_group


def _now_utc() -> datetime:
    return datetime.now(timezone.utc)


@dataclasses.dataclass
class VaultMetrics:
    total_secrets: int
    secrets_with_ttl: int
    expired_secrets: int
    tagged_secrets: int
    unique_tags: int
    total_history_events: int
    group_count: int
    secrets_per_group: Dict[str, int]
    oldest_change: Optional[str]
    newest_change: Optional[str]

    def as_dict(self) -> dict:
        return dataclasses.asdict(self)


def compute_metrics(vault_dir: str, password: str) -> VaultMetrics:
    """Compute comprehensive statistics for the vault."""
    secrets = load_secrets(vault_dir, password)
    secret_keys = [k for k in secrets if not k.startswith("__")]
    total = len(secret_keys)

    now = _now_utc()
    secrets_with_ttl = 0
    expired = 0
    for key in secret_keys:
        ttl_dt = get_ttl(vault_dir, password, key)
        if ttl_dt is not None:
            secrets_with_ttl += 1
            if ttl_dt < now:
                expired += 1

    all_tags: List[str] = []
    tagged = 0
    for key in secret_keys:
        tags = get_tags(vault_dir, password, key)
        if tags:
            tagged += 1
            all_tags.extend(tags)
    unique_tags = len(set(all_tags))

    history = get_history(vault_dir)
    total_events = len(history)
    timestamps = [e.get("timestamp") for e in history if e.get("timestamp")]
    oldest = min(timestamps) if timestamps else None
    newest = max(timestamps) if timestamps else None

    groups = list_groups(vault_dir)
    secrets_per_group = {g: len(get_group(vault_dir, g)) for g in groups}

    return VaultMetrics(
        total_secrets=total,
        secrets_with_ttl=secrets_with_ttl,
        expired_secrets=expired,
        tagged_secrets=tagged,
        unique_tags=unique_tags,
        total_history_events=total_events,
        group_count=len(groups),
        secrets_per_group=secrets_per_group,
        oldest_change=oldest,
        newest_change=newest,
    )
