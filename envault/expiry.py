"""Secret expiry notifications — list secrets expiring within a given window."""

from __future__ import annotations

from datetime import datetime, timezone, timedelta
from typing import List, Tuple, Optional

from envault.store import load_secrets
from envault.ttl import get_ttl


def _now_utc() -> datetime:
    return datetime.now(tz=timezone.utc)


def expiring_soon(
    project_dir: str,
    password: str,
    within_hours: int = 24,
) -> List[Tuple[str, datetime]]:
    """Return list of (key, expiry_datetime) for secrets expiring within *within_hours*."""
    secrets = load_secrets(project_dir, password)
    cutoff = _now_utc() + timedelta(hours=within_hours)
    results: List[Tuple[str, datetime]] = []
    for key in secrets:
        expiry: Optional[datetime] = get_ttl(project_dir, password, key)
        if expiry is not None and expiry <= cutoff:
            results.append((key, expiry))
    results.sort(key=lambda t: t[1])
    return results


def already_expired(
    project_dir: str,
    password: str,
) -> List[Tuple[str, datetime]]:
    """Return list of (key, expiry_datetime) for secrets that have already expired."""
    now = _now_utc()
    secrets = load_secrets(project_dir, password)
    results: List[Tuple[str, datetime]] = []
    for key in secrets:
        expiry: Optional[datetime] = get_ttl(project_dir, password, key)
        if expiry is not None and expiry <= now:
            results.append((key, expiry))
    results.sort(key=lambda t: t[1])
    return results


def expiry_summary(project_dir: str, password: str, within_hours: int = 24) -> dict:
    """Return a summary dict with 'expiring_soon' and 'already_expired' lists."""
    return {
        "expiring_soon": expiring_soon(project_dir, password, within_hours),
        "already_expired": already_expired(project_dir, password),
    }
