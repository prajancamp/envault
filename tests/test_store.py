"""Tests for envault.store — encrypted per-project secret storage."""

import pytest
from pathlib import Path

from envault.store import (
    load_secrets,
    save_secrets,
    set_secret,
    delete_secret,
    list_projects,
)

PASSWORD = "hunter2"
PROJECT = "my-app"


@pytest.fixture()
def vault_dir(tmp_path: Path) -> Path:
    return tmp_path / "vaults"


def test_load_secrets_returns_empty_when_no_vault(vault_dir):
    result = load_secrets(PROJECT, PASSWORD, vault_dir)
    assert result == {}


def test_save_and_load_round_trip(vault_dir):
    secrets = {"DB_URL": "postgres://localhost/db", "API_KEY": "abc123"}
    save_secrets(PROJECT, secrets, PASSWORD, vault_dir)
    loaded = load_secrets(PROJECT, PASSWORD, vault_dir)
    assert loaded == secrets


def test_vault_file_is_created_on_disk(vault_dir):
    save_secrets(PROJECT, {"X": "1"}, PASSWORD, vault_dir)
    assert (vault_dir / f"{PROJECT}.vault").exists()


def test_set_secret_adds_new_key(vault_dir):
    set_secret(PROJECT, "FOO", "bar", PASSWORD, vault_dir)
    assert load_secrets(PROJECT, PASSWORD, vault_dir)["FOO"] == "bar"


def test_set_secret_updates_existing_key(vault_dir):
    set_secret(PROJECT, "FOO", "bar", PASSWORD, vault_dir)
    set_secret(PROJECT, "FOO", "baz", PASSWORD, vault_dir)
    assert load_secrets(PROJECT, PASSWORD, vault_dir)["FOO"] == "baz"


def test_delete_secret_removes_key(vault_dir):
    set_secret(PROJECT, "TO_DELETE", "value", PASSWORD, vault_dir)
    existed = delete_secret(PROJECT, "TO_DELETE", PASSWORD, vault_dir)
    assert existed is True
    assert "TO_DELETE" not in load_secrets(PROJECT, PASSWORD, vault_dir)


def test_delete_secret_returns_false_for_missing_key(vault_dir):
    assert delete_secret(PROJECT, "GHOST", PASSWORD, vault_dir) is False


def test_load_secrets_wrong_password_raises(vault_dir):
    save_secrets(PROJECT, {"K": "V"}, PASSWORD, vault_dir)
    with pytest.raises(Exception):
        load_secrets(PROJECT, "wrong-password", vault_dir)


def test_list_projects_empty_when_no_vault_dir(vault_dir):
    assert list_projects(vault_dir) == []


def test_list_projects_returns_project_names(vault_dir):
    for name in ("alpha", "beta", "gamma"):
        save_secrets(name, {"K": "V"}, PASSWORD, vault_dir)
    assert list_projects(vault_dir) == ["alpha", "beta", "gamma"]


def test_multiple_projects_are_isolated(vault_dir):
    save_secrets("proj-a", {"SECRET": "for-a"}, PASSWORD, vault_dir)
    save_secrets("proj-b", {"SECRET": "for-b"}, PASSWORD, vault_dir)
    assert load_secrets("proj-a", PASSWORD, vault_dir)["SECRET"] == "for-a"
    assert load_secrets("proj-b", PASSWORD, vault_dir)["SECRET"] == "for-b"
