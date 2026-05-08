"""Tests for envault.expiry."""

from __future__ import annotations

import pytest
from datetime import datetime, timezone, timedelta
from pathlib import Path
from unittest.mock import patch

from envault.store import save_secrets
from envault.ttl import set_ttl
from envault.expiry import expiring_soon, already_expired, expiry_summary

PASSWORD = "testpass"


@pytest.fixture()
def vault_dir(tmp_path: Path) -> str:
    secrets = {"KEY_A": "alpha", "KEY_B": "beta", "KEY_C": "gamma"}
    save_secrets(str(tmp_path), PASSWORD, secrets)
    return str(tmp_path)


def _future(hours: float) -> datetime:
    return datetime.now(tz=timezone.utc) + timedelta(hours=hours)


def _past(hours: float) -> datetime:
    return datetime.now(tz=timezone.utc) - timedelta(hours=hours)


def test_expiring_soon_returns_keys_within_window(vault_dir):
    set_ttl(vault_dir, PASSWORD, "KEY_A", 12)   # expires in 12 h — within 24 h
    set_ttl(vault_dir, PASSWORD, "KEY_B", 48)   # expires in 48 h — outside 24 h
    results = expiring_soon(vault_dir, PASSWORD, within_hours=24)
    keys = [k for k, _ in results]
    assert "KEY_A" in keys
    assert "KEY_B" not in keys


def test_expiring_soon_empty_when_no_ttls(vault_dir):
    results = expiring_soon(vault_dir, PASSWORD, within_hours=24)
    assert results == []


def test_expiring_soon_sorted_by_expiry(vault_dir):
    set_ttl(vault_dir, PASSWORD, "KEY_C", 20)
    set_ttl(vault_dir, PASSWORD, "KEY_A", 5)
    results = expiring_soon(vault_dir, PASSWORD, within_hours=24)
    keys = [k for k, _ in results]
    assert keys.index("KEY_A") < keys.index("KEY_C")


def test_already_expired_returns_past_keys(vault_dir):
    # Manually inject a past TTL by mocking datetime inside set_ttl
    future_dt = _future(1)   # set real TTL
    set_ttl(vault_dir, PASSWORD, "KEY_A", 1)
    # Now mock _now_utc so the key appears expired
    past = _past(2)
    with patch("envault.expiry._now_utc", return_value=_future(2)):
        results = already_expired(vault_dir, PASSWORD)
    keys = [k for k, _ in results]
    assert "KEY_A" in keys


def test_already_expired_empty_when_no_ttls(vault_dir):
    results = already_expired(vault_dir, PASSWORD)
    assert results == []


def test_expiry_summary_structure(vault_dir):
    summary = expiry_summary(vault_dir, PASSWORD, within_hours=24)
    assert "expiring_soon" in summary
    assert "already_expired" in summary
    assert isinstance(summary["expiring_soon"], list)
    assert isinstance(summary["already_expired"], list)
