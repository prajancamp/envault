"""Unit tests for envault.hooks."""
from __future__ import annotations

import json
from pathlib import Path

import pytest

from envault import hooks as hk


@pytest.fixture()
def vault_dir(tmp_path: Path) -> Path:
    return tmp_path


def test_list_hooks_empty_when_none_exist(vault_dir: Path) -> None:
    assert hk.list_hooks(vault_dir) == {}


def test_set_hook_registers_command(vault_dir: Path) -> None:
    hk.set_hook(vault_dir, "post_set", "echo hello")
    result = hk.list_hooks(vault_dir)
    assert result["post_set"] == ["echo hello"]


def test_set_hook_appends_multiple_commands(vault_dir: Path) -> None:
    hk.set_hook(vault_dir, "post_set", "echo first")
    hk.set_hook(vault_dir, "post_set", "echo second")
    result = hk.list_hooks(vault_dir)
    assert result["post_set"] == ["echo first", "echo second"]


def test_set_hook_idempotent(vault_dir: Path) -> None:
    hk.set_hook(vault_dir, "post_set", "echo hello")
    hk.set_hook(vault_dir, "post_set", "echo hello")
    result = hk.list_hooks(vault_dir)
    assert result["post_set"].count("echo hello") == 1


def test_set_hook_invalid_event_raises(vault_dir: Path) -> None:
    with pytest.raises(ValueError, match="Unknown event"):
        hk.set_hook(vault_dir, "bad_event", "echo x")


def test_remove_hook_specific_command(vault_dir: Path) -> None:
    hk.set_hook(vault_dir, "pre_get", "echo a")
    hk.set_hook(vault_dir, "pre_get", "echo b")
    hk.remove_hook(vault_dir, "pre_get", "echo a")
    result = hk.list_hooks(vault_dir)
    assert result["pre_get"] == ["echo b"]


def test_remove_hook_clears_all_when_no_command(vault_dir: Path) -> None:
    hk.set_hook(vault_dir, "pre_get", "echo a")
    hk.set_hook(vault_dir, "pre_get", "echo b")
    hk.remove_hook(vault_dir, "pre_get")
    assert "pre_get" not in hk.list_hooks(vault_dir)


def test_remove_hook_invalid_event_raises(vault_dir: Path) -> None:
    with pytest.raises(ValueError, match="Unknown event"):
        hk.remove_hook(vault_dir, "nope")


def test_fire_runs_command_returns_exit_codes(vault_dir: Path) -> None:
    hk.set_hook(vault_dir, "post_delete", "exit 0")
    codes = hk.fire(vault_dir, "post_delete")
    assert codes == [0]


def test_fire_returns_empty_when_no_hooks(vault_dir: Path) -> None:
    codes = hk.fire(vault_dir, "post_set")
    assert codes == []


def test_fire_invalid_event_raises(vault_dir: Path) -> None:
    with pytest.raises(ValueError, match="Unknown event"):
        hk.fire(vault_dir, "unknown_event")


def test_hooks_file_persists_to_disk(vault_dir: Path) -> None:
    hk.set_hook(vault_dir, "pre_set", "echo persisted")
    raw = json.loads((vault_dir / ".envault_hooks.json").read_text())
    assert raw["pre_set"] == ["echo persisted"]
