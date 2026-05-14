"""Tests for envault.dependencies."""

import pytest

from envault.store import save_secrets
from envault.dependencies import (
    add_dependency,
    remove_dependency,
    get_dependencies,
    get_dependents,
    stale_dependents,
)

PASSWORD = "hunter2"


@pytest.fixture()
def vault_dir(tmp_path):
    secrets = {"DB_URL": "postgres://", "DB_PASS": "secret", "API_KEY": "abc123"}
    save_secrets(str(tmp_path), PASSWORD, secrets)
    return str(tmp_path)


def test_add_dependency_records_link(vault_dir):
    add_dependency(vault_dir, PASSWORD, "DB_URL", "DB_PASS")
    assert "DB_PASS" in get_dependencies(vault_dir, "DB_URL")


def test_get_dependencies_empty_when_none_set(vault_dir):
    assert get_dependencies(vault_dir, "API_KEY") == []


def test_add_dependency_idempotent(vault_dir):
    add_dependency(vault_dir, PASSWORD, "DB_URL", "DB_PASS")
    add_dependency(vault_dir, PASSWORD, "DB_URL", "DB_PASS")
    assert get_dependencies(vault_dir, "DB_URL").count("DB_PASS") == 1


def test_add_dependency_missing_key_raises(vault_dir):
    with pytest.raises(KeyError):
        add_dependency(vault_dir, PASSWORD, "MISSING", "DB_PASS")


def test_add_dependency_missing_depends_on_raises(vault_dir):
    with pytest.raises(KeyError):
        add_dependency(vault_dir, PASSWORD, "DB_URL", "NO_SUCH_KEY")


def test_add_dependency_self_raises(vault_dir):
    with pytest.raises(ValueError):
        add_dependency(vault_dir, PASSWORD, "DB_URL", "DB_URL")


def test_remove_dependency_returns_true_when_existed(vault_dir):
    add_dependency(vault_dir, PASSWORD, "DB_URL", "DB_PASS")
    result = remove_dependency(vault_dir, "DB_URL", "DB_PASS")
    assert result is True
    assert get_dependencies(vault_dir, "DB_URL") == []


def test_remove_dependency_returns_false_when_not_present(vault_dir):
    result = remove_dependency(vault_dir, "DB_URL", "DB_PASS")
    assert result is False


def test_get_dependents_returns_keys_that_depend_on_target(vault_dir):
    add_dependency(vault_dir, PASSWORD, "DB_URL", "DB_PASS")
    add_dependency(vault_dir, PASSWORD, "API_KEY", "DB_PASS")
    dependents = get_dependents(vault_dir, "DB_PASS")
    assert set(dependents) == {"DB_URL", "API_KEY"}


def test_get_dependents_empty_when_none(vault_dir):
    assert get_dependents(vault_dir, "DB_PASS") == []


def test_stale_dependents_returns_existing_keys(vault_dir):
    add_dependency(vault_dir, PASSWORD, "DB_URL", "DB_PASS")
    stale = stale_dependents(vault_dir, PASSWORD, "DB_PASS")
    assert "DB_URL" in stale


def test_multiple_dependencies_per_key(vault_dir):
    add_dependency(vault_dir, PASSWORD, "API_KEY", "DB_URL")
    add_dependency(vault_dir, PASSWORD, "API_KEY", "DB_PASS")
    deps = get_dependencies(vault_dir, "API_KEY")
    assert set(deps) == {"DB_URL", "DB_PASS"}
