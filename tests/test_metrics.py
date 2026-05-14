"""Tests for envault.metrics."""

from __future__ import annotations

import pytest
from pathlib import Path

from envault.store import save_secrets, load_secrets
from envault.ttl import set_ttl
from envault.tags import set_tag
from envault.history import record_change
from envault.groups import add_to_group
from envault.metrics import compute_metrics, VaultMetrics

PASSWORD = "metrics-test-pw"


@pytest.fixture
def vault_dir(tmp_path: Path) -> str:
    return str(tmp_path)


def _seed(vault_dir: str) -> None:
    secrets = {"API_KEY": "abc123", "DB_PASS": "secret", "TOKEN": "tok"}
    save_secrets(vault_dir, PASSWORD, secrets)


def test_metrics_empty_vault(vault_dir: str) -> None:
    save_secrets(vault_dir, PASSWORD, {})
    m = compute_metrics(vault_dir, PASSWORD)
    assert m.total_secrets == 0
    assert m.secrets_with_ttl == 0
    assert m.expired_secrets == 0
    assert m.tagged_secrets == 0
    assert m.unique_tags == 0
    assert m.group_count == 0


def test_metrics_total_secrets(vault_dir: str) -> None:
    _seed(vault_dir)
    m = compute_metrics(vault_dir, PASSWORD)
    assert m.total_secrets == 3


def test_metrics_secrets_with_ttl(vault_dir: str) -> None:
    _seed(vault_dir)
    set_ttl(vault_dir, PASSWORD, "API_KEY", days=10)
    set_ttl(vault_dir, PASSWORD, "TOKEN", days=5)
    m = compute_metrics(vault_dir, PASSWORD)
    assert m.secrets_with_ttl == 2
    assert m.expired_secrets == 0


def test_metrics_tagged_secrets_and_unique_tags(vault_dir: str) -> None:
    _seed(vault_dir)
    set_tag(vault_dir, PASSWORD, "API_KEY", "prod")
    set_tag(vault_dir, PASSWORD, "API_KEY", "critical")
    set_tag(vault_dir, PASSWORD, "DB_PASS", "prod")
    m = compute_metrics(vault_dir, PASSWORD)
    assert m.tagged_secrets == 2
    assert m.unique_tags == 2  # 'prod' and 'critical'


def test_metrics_history_events(vault_dir: str) -> None:
    _seed(vault_dir)
    record_change(vault_dir, "API_KEY", "set", actor="alice")
    record_change(vault_dir, "DB_PASS", "set", actor="bob")
    record_change(vault_dir, "API_KEY", "delete", actor="alice")
    m = compute_metrics(vault_dir, PASSWORD)
    assert m.total_history_events == 3
    assert m.oldest_change is not None
    assert m.newest_change is not None


def test_metrics_groups(vault_dir: str) -> None:
    _seed(vault_dir)
    add_to_group(vault_dir, PASSWORD, "backend", "API_KEY")
    add_to_group(vault_dir, PASSWORD, "backend", "DB_PASS")
    add_to_group(vault_dir, PASSWORD, "auth", "TOKEN")
    m = compute_metrics(vault_dir, PASSWORD)
    assert m.group_count == 2
    assert m.secrets_per_group["backend"] == 2
    assert m.secrets_per_group["auth"] == 1


def test_metrics_as_dict(vault_dir: str) -> None:
    _seed(vault_dir)
    m = compute_metrics(vault_dir, PASSWORD)
    d = m.as_dict()
    assert isinstance(d, dict)
    assert "total_secrets" in d
    assert "secrets_per_group" in d
