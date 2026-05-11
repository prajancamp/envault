"""Password / value policy enforcement for envault secrets."""

from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any

_POLICY_FILENAME = ".envault_policies.json"


def _policy_path(project_dir: str) -> Path:
    return Path(project_dir) / _POLICY_FILENAME


def _load_policies(project_dir: str) -> dict[str, Any]:
    path = _policy_path(project_dir)
    if not path.exists():
        return {}
    return json.loads(path.read_text())


def _save_policies(project_dir: str, data: dict[str, Any]) -> None:
    _policy_path(project_dir).write_text(json.dumps(data, indent=2))


def set_policy(project_dir: str, key: str, pattern: str, description: str = "") -> None:
    """Attach a regex policy to *key*.  The value must match *pattern* on write."""
    try:
        re.compile(pattern)
    except re.error as exc:
        raise ValueError(f"Invalid regex pattern: {exc}") from exc
    policies = _load_policies(project_dir)
    policies[key] = {"pattern": pattern, "description": description}
    _save_policies(project_dir, policies)


def remove_policy(project_dir: str, key: str) -> None:
    """Remove the policy attached to *key* (no-op if none exists)."""
    policies = _load_policies(project_dir)
    policies.pop(key, None)
    _save_policies(project_dir, policies)


def get_policy(project_dir: str, key: str) -> dict[str, str] | None:
    """Return the policy dict for *key*, or *None* if not set."""
    return _load_policies(project_dir).get(key)


def list_policies(project_dir: str) -> dict[str, dict[str, str]]:
    """Return all policies keyed by secret name."""
    return _load_policies(project_dir)


def validate(project_dir: str, key: str, value: str) -> None:
    """Raise *ValueError* if *value* does not satisfy the policy for *key*."""
    policy = get_policy(project_dir, key)
    if policy is None:
        return
    pattern = policy["pattern"]
    if not re.fullmatch(pattern, value):
        desc = policy.get("description") or f"must match /{pattern}/"
        raise ValueError(f"Value for '{key}' violates policy: {desc}")
