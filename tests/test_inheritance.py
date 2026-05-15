"""Tests for envault.inheritance."""

from __future__ import annotations

import pytest

from envault.store import save_secrets
from envault.inheritance import (
    get_parent,
    inheritance_summary,
    remove_parent,
    resolve_secrets,
    set_parent,
)

PASSWORD = "test-pass"


@pytest.fixture()
def vault_dir(tmp_path):
    parent = tmp_path / "parent"
    child = tmp_path / "child"
    parent.mkdir()
    child.mkdir()
    return parent, child


def test_set_and_get_parent(vault_dir):
    parent, child = vault_dir
    set_parent(str(child), str(parent))
    result = get_parent(str(child))
    assert result == str(parent.resolve())


def test_get_parent_returns_none_when_not_set(vault_dir):
    _, child = vault_dir
    assert get_parent(str(child)) is None


def test_remove_parent_clears_config(vault_dir):
    parent, child = vault_dir
    set_parent(str(child), str(parent))
    remove_parent(str(child))
    assert get_parent(str(child)) is None


def test_remove_parent_noop_when_not_set(vault_dir):
    _, child = vault_dir
    remove_parent(str(child))  # should not raise


def test_resolve_secrets_merges_parent_and_child(vault_dir):
    parent, child = vault_dir
    save_secrets(str(parent), {"SHARED": "from-parent", "PARENT_ONLY": "p"}, PASSWORD)
    save_secrets(str(child), {"SHARED": "from-child", "CHILD_ONLY": "c"}, PASSWORD)
    set_parent(str(child), str(parent))

    merged = resolve_secrets(str(child), PASSWORD)
    assert merged["PARENT_ONLY"] == "p"
    assert merged["CHILD_ONLY"] == "c"
    assert merged["SHARED"] == "from-child"  # child overrides parent


def test_resolve_secrets_parent_wins_when_override_false(vault_dir):
    parent, child = vault_dir
    save_secrets(str(parent), {"KEY": "parent-value"}, PASSWORD)
    save_secrets(str(child), {"KEY": "child-value"}, PASSWORD)
    set_parent(str(child), str(parent))

    merged = resolve_secrets(str(child), PASSWORD, override=False)
    assert merged["KEY"] == "parent-value"


def test_resolve_secrets_no_parent_returns_child_only(vault_dir):
    _, child = vault_dir
    save_secrets(str(child), {"ONLY": "here"}, PASSWORD)
    merged = resolve_secrets(str(child), PASSWORD)
    assert merged == {"ONLY": "here"}


def test_inheritance_summary_shows_overridden_keys(vault_dir):
    parent, child = vault_dir
    save_secrets(str(parent), {"SHARED": "p", "PARENT_ONLY": "p2"}, PASSWORD)
    save_secrets(str(child), {"SHARED": "c", "CHILD_ONLY": "c2"}, PASSWORD)
    set_parent(str(child), str(parent))

    summary = inheritance_summary(str(child), PASSWORD)
    assert summary["parent"] == str(parent.resolve())
    assert "SHARED" in summary["overridden_keys"]
    assert "PARENT_ONLY" not in summary["overridden_keys"]
    assert set(summary["parent_keys"]) == {"SHARED", "PARENT_ONLY"}
    assert set(summary["child_keys"]) == {"SHARED", "CHILD_ONLY"}


def test_inheritance_summary_no_parent(vault_dir):
    _, child = vault_dir
    save_secrets(str(child), {"A": "1"}, PASSWORD)
    summary = inheritance_summary(str(child), PASSWORD)
    assert summary["parent"] is None
    assert summary["parent_keys"] == []
    assert summary["overridden_keys"] == []
