"""Tests for envault.diff — snapshot diffing utilities."""

from __future__ import annotations

import pytest

from envault.snapshot import create_snapshot
from envault.store import load_secrets, save_secrets
from envault.diff import diff_snapshots, diff_snapshot_vs_current, _compute_diff


PASSWORD = "test-password"


@pytest.fixture()
def vault_dir(tmp_path):
    return str(tmp_path)


# ---------------------------------------------------------------------------
# _compute_diff unit tests
# ---------------------------------------------------------------------------

def test_compute_diff_added():
    diff = _compute_diff({"A": "1"}, {"A": "1", "B": "2"})
    assert diff.added == ["B"]
    assert diff.removed == []
    assert diff.changed == []
    assert diff.unchanged == ["A"]


def test_compute_diff_removed():
    diff = _compute_diff({"A": "1", "B": "2"}, {"A": "1"})
    assert diff.removed == ["B"]
    assert diff.added == []


def test_compute_diff_changed():
    diff = _compute_diff({"A": "old"}, {"A": "new"})
    assert diff.changed == ["A"]
    assert diff.unchanged == []


def test_compute_diff_no_changes():
    diff = _compute_diff({"A": "1"}, {"A": "1"})
    assert not diff.has_changes
    assert diff.unchanged == ["A"]


# ---------------------------------------------------------------------------
# Integration tests using real snapshots
# ---------------------------------------------------------------------------

def test_diff_snapshots_detects_changes(vault_dir):
    save_secrets(vault_dir, PASSWORD, {"KEY1": "val1", "KEY2": "val2"})
    create_snapshot(vault_dir, PASSWORD, "snap_a")

    save_secrets(vault_dir, PASSWORD, {"KEY1": "val1_changed", "KEY3": "val3"})
    create_snapshot(vault_dir, PASSWORD, "snap_b")

    diff = diff_snapshots(vault_dir, "snap_a", "snap_b", PASSWORD)
    assert "KEY3" in diff.added
    assert "KEY2" in diff.removed
    assert "KEY1" in diff.changed


def test_diff_snapshot_vs_current(vault_dir):
    save_secrets(vault_dir, PASSWORD, {"FOO": "bar"})
    create_snapshot(vault_dir, PASSWORD, "baseline")

    save_secrets(vault_dir, PASSWORD, {"FOO": "bar", "NEW": "value"})

    diff = diff_snapshot_vs_current(vault_dir, "baseline", PASSWORD)
    assert "NEW" in diff.added
    assert diff.unchanged == ["FOO"]
    assert diff.has_changes


def test_diff_snapshot_missing_raises(vault_dir):
    save_secrets(vault_dir, PASSWORD, {"X": "y"})
    with pytest.raises(FileNotFoundError):
        diff_snapshot_vs_current(vault_dir, "nonexistent", PASSWORD)


def test_diff_identical_snapshots_no_changes(vault_dir):
    save_secrets(vault_dir, PASSWORD, {"A": "1", "B": "2"})
    create_snapshot(vault_dir, PASSWORD, "s1")
    create_snapshot(vault_dir, PASSWORD, "s2")

    diff = diff_snapshots(vault_dir, "s1", "s2", PASSWORD)
    assert not diff.has_changes
    assert sorted(diff.unchanged) == ["A", "B"]
