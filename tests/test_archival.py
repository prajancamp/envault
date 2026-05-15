"""Tests for envault.archival."""

from __future__ import annotations

import pytest

from envault.store import save_secrets
from envault.archival import (
    archive_secret,
    restore_secret,
    list_archived,
    purge_archived,
)


PASSWORD = "test-pass"


@pytest.fixture()
def vault_dir(tmp_path):
    project = str(tmp_path)
    save_secrets(project, PASSWORD, {"API_KEY": "abc123", "DB_PASS": "secret"})
    return project


# ---------------------------------------------------------------------------
# archive_secret
# ---------------------------------------------------------------------------

def test_archive_secret_removes_from_live_vault(vault_dir):
    from envault.store import load_secrets
    archive_secret(vault_dir, PASSWORD, "API_KEY")
    secrets = load_secrets(vault_dir, PASSWORD)
    assert "API_KEY" not in secrets


def test_archive_secret_returns_metadata(vault_dir):
    meta = archive_secret(vault_dir, PASSWORD, "API_KEY", reason="rotating")
    assert meta["value"] == "abc123"
    assert meta["reason"] == "rotating"
    assert "archived_at" in meta


def test_archive_secret_missing_key_raises(vault_dir):
    with pytest.raises(KeyError, match="MISSING"):
        archive_secret(vault_dir, PASSWORD, "MISSING")


def test_archive_secret_persists_across_calls(vault_dir):
    archive_secret(vault_dir, PASSWORD, "API_KEY")
    listing = list_archived(vault_dir)
    keys = [r["key"] for r in listing]
    assert "API_KEY" in keys


# ---------------------------------------------------------------------------
# restore_secret
# ---------------------------------------------------------------------------

def test_restore_secret_brings_key_back(vault_dir):
    from envault.store import load_secrets
    archive_secret(vault_dir, PASSWORD, "API_KEY")
    restore_secret(vault_dir, PASSWORD, "API_KEY")
    secrets = load_secrets(vault_dir, PASSWORD)
    assert secrets["API_KEY"] == "abc123"


def test_restore_secret_removes_from_archive(vault_dir):
    archive_secret(vault_dir, PASSWORD, "API_KEY")
    restore_secret(vault_dir, PASSWORD, "API_KEY")
    listing = list_archived(vault_dir)
    assert all(r["key"] != "API_KEY" for r in listing)


def test_restore_secret_missing_raises(vault_dir):
    with pytest.raises(KeyError, match="GHOST"):
        restore_secret(vault_dir, PASSWORD, "GHOST")


# ---------------------------------------------------------------------------
# list_archived
# ---------------------------------------------------------------------------

def test_list_archived_empty_when_none_archived(vault_dir):
    assert list_archived(vault_dir) == []


def test_list_archived_does_not_expose_values(vault_dir):
    archive_secret(vault_dir, PASSWORD, "DB_PASS")
    listing = list_archived(vault_dir)
    assert len(listing) == 1
    assert "value" not in listing[0]


# ---------------------------------------------------------------------------
# purge_archived
# ---------------------------------------------------------------------------

def test_purge_archived_deletes_permanently(vault_dir):
    archive_secret(vault_dir, PASSWORD, "API_KEY")
    purge_archived(vault_dir, "API_KEY")
    assert list_archived(vault_dir) == []


def test_purge_archived_missing_raises(vault_dir):
    with pytest.raises(KeyError, match="NOPE"):
        purge_archived(vault_dir, "NOPE")
