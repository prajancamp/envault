"""env_inject.py — Inject vault secrets into a subprocess environment."""
from __future__ import annotations

import os
import subprocess
from typing import Dict, List, Optional

from envault.store import load_secrets
from envault.ttl import get_ttl
from datetime import datetime, timezone


def _now_utc() -> datetime:
    return datetime.now(timezone.utc)


def build_env(
    project_dir: str,
    password: str,
    *,
    prefix: Optional[str] = None,
    skip_expired: bool = True,
    extra_env: Optional[Dict[str, str]] = None,
) -> Dict[str, str]:
    """Return an env dict with vault secrets merged into the current environment.

    Args:
        project_dir: Path to the project whose vault to load.
        password: Vault password.
        prefix: If set, only inject keys that start with this prefix.
        skip_expired: When True, silently skip keys whose TTL has passed.
        extra_env: Additional key/value pairs to layer on top.

    Returns:
        A copy of os.environ updated with the selected secrets.
    """
    secrets = load_secrets(project_dir, password)
    env = os.environ.copy()

    for key, value in secrets.items():
        if prefix and not key.startswith(prefix):
            continue
        if skip_expired:
            ttl = get_ttl(project_dir, password, key)
            if ttl is not None and ttl < _now_utc():
                continue
        env[key] = value

    if extra_env:
        env.update(extra_env)

    return env


def run_with_secrets(
    project_dir: str,
    password: str,
    command: List[str],
    *,
    prefix: Optional[str] = None,
    skip_expired: bool = True,
) -> int:
    """Run *command* with vault secrets injected, returning the exit code."""
    env = build_env(
        project_dir,
        password,
        prefix=prefix,
        skip_expired=skip_expired,
    )
    result = subprocess.run(command, env=env)  # noqa: S603
    return result.returncode
