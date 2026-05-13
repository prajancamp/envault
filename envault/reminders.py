"""Reminder scheduling for secret rotation."""
from __future__ import annotations

import json
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Optional

from envault.store import load_secrets, save_secrets

_REMINDER_PREFIX = "__reminder__"


def _reminder_key(secret_key: str) -> str:
    return f"{_REMINDER_PREFIX}{secret_key}"


def _now_utc() -> datetime:
    return datetime.now(timezone.utc)


def set_reminder(
    vault_dir: str,
    password: str,
    secret_key: str,
    days: int,
    message: str = "",
) -> datetime:
    """Schedule a reminder for *secret_key* in *days* days."""
    secrets = load_secrets(vault_dir, password)
    if secret_key not in secrets:
        raise KeyError(f"Secret '{secret_key}' does not exist.")
    remind_at = _now_utc() + timedelta(days=days)
    payload = json.dumps({"remind_at": remind_at.isoformat(), "message": message})
    secrets[_reminder_key(secret_key)] = payload
    save_secrets(vault_dir, password, secrets)
    return remind_at


def get_reminder(vault_dir: str, password: str, secret_key: str) -> Optional[dict]:
    """Return reminder metadata for *secret_key*, or None if not set."""
    secrets = load_secrets(vault_dir, password)
    raw = secrets.get(_reminder_key(secret_key))
    if raw is None:
        return None
    data = json.loads(raw)
    data["remind_at"] = datetime.fromisoformat(data["remind_at"])
    return data


def remove_reminder(vault_dir: str, password: str, secret_key: str) -> bool:
    """Remove reminder for *secret_key*. Returns True if one existed."""
    secrets = load_secrets(vault_dir, password)
    key = _reminder_key(secret_key)
    if key not in secrets:
        return False
    del secrets[key]
    save_secrets(vault_dir, password, secrets)
    return True


def due_reminders(vault_dir: str, password: str) -> list[dict]:
    """Return all reminders whose remind_at <= now."""
    secrets = load_secrets(vault_dir, password)
    now = _now_utc()
    results = []
    for k, v in secrets.items():
        if k.startswith(_REMINDER_PREFIX):
            secret_key = k[len(_REMINDER_PREFIX):]
            data = json.loads(v)
            remind_at = datetime.fromisoformat(data["remind_at"])
            if remind_at <= now:
                results.append({
                    "key": secret_key,
                    "remind_at": remind_at,
                    "message": data.get("message", ""),
                })
    return results
