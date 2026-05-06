"""Tests for envault.lock and envault.cli_lock."""

from __future__ import annotations

import argparse
import pytest

from envault.lock import (
    lock_vault,
    unlock_vault,
    is_locked,
    lock_info,
    assert_unlocked,
)
from envault.cli_lock import cmd_lock, cmd_unlock, cmd_lock_status


@pytest.fixture()
def vault_dir(tmp_path):
    return tmp_path / "project"


# --- lock_vault ---

def test_lock_creates_lock_file(vault_dir):
    lock_vault(vault_dir)
    assert is_locked(vault_dir)


def test_lock_returns_metadata(vault_dir):
    info = lock_vault(vault_dir, reason="maintenance", actor="alice")
    assert info["reason"] == "maintenance"
    assert info["actor"] == "alice"
    assert "locked_at" in info


def test_lock_twice_raises(vault_dir):
    lock_vault(vault_dir)
    with pytest.raises(RuntimeError, match="already locked"):
        lock_vault(vault_dir)


# --- unlock_vault ---

def test_unlock_removes_lock_file(vault_dir):
    lock_vault(vault_dir)
    unlock_vault(vault_dir)
    assert not is_locked(vault_dir)


def test_unlock_when_not_locked_raises(vault_dir):
    with pytest.raises(RuntimeError, match="not locked"):
        unlock_vault(vault_dir)


# --- lock_info / assert_unlocked ---

def test_lock_info_none_when_unlocked(vault_dir):
    assert lock_info(vault_dir) is None


def test_lock_info_returns_dict_when_locked(vault_dir):
    lock_vault(vault_dir, reason="test")
    info = lock_info(vault_dir)
    assert isinstance(info, dict)
    assert info["reason"] == "test"


def test_assert_unlocked_passes_when_unlocked(vault_dir):
    assert_unlocked(vault_dir)  # should not raise


def test_assert_unlocked_raises_when_locked(vault_dir):
    lock_vault(vault_dir, reason="deploy")
    with pytest.raises(RuntimeError, match="locked"):
        assert_unlocked(vault_dir)


# --- CLI commands ---

def _args(vault_dir, **kwargs):
    ns = argparse.Namespace(project_dir=str(vault_dir), reason="", actor="envault")
    for k, v in kwargs.items():
        setattr(ns, k, v)
    return ns


def test_cmd_lock_success(vault_dir):
    assert cmd_lock(_args(vault_dir)) == 0
    assert is_locked(vault_dir)


def test_cmd_lock_already_locked_returns_1(vault_dir):
    lock_vault(vault_dir)
    assert cmd_lock(_args(vault_dir)) == 1


def test_cmd_unlock_success(vault_dir):
    lock_vault(vault_dir)
    assert cmd_unlock(_args(vault_dir)) == 0
    assert not is_locked(vault_dir)


def test_cmd_unlock_not_locked_returns_1(vault_dir):
    assert cmd_unlock(_args(vault_dir)) == 1


def test_cmd_lock_status_locked(vault_dir, capsys):
    lock_vault(vault_dir, reason="ci", actor="bot")
    assert cmd_lock_status(_args(vault_dir)) == 0
    out = capsys.readouterr().out
    assert "LOCKED" in out
    assert "ci" in out


def test_cmd_lock_status_unlocked(vault_dir, capsys):
    assert cmd_lock_status(_args(vault_dir)) == 0
    out = capsys.readouterr().out
    assert "unlocked" in out.lower()
