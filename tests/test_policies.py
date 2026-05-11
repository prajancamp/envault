"""Tests for envault.policies and envault.cli_policies."""

from __future__ import annotations

import argparse
import pytest

from envault.policies import (
    get_policy,
    list_policies,
    remove_policy,
    set_policy,
    validate,
)
from envault.cli_policies import (
    cmd_policy_list,
    cmd_policy_remove,
    cmd_policy_set,
    cmd_policy_show,
)


@pytest.fixture()
def vault_dir(tmp_path):
    return str(tmp_path)


# ── policy module ────────────────────────────────────────────────────────────

def test_set_and_get_policy(vault_dir):
    set_policy(vault_dir, "API_KEY", r"[A-Za-z0-9]{32}", description="32-char alphanum")
    pol = get_policy(vault_dir, "API_KEY")
    assert pol["pattern"] == r"[A-Za-z0-9]{32}"
    assert pol["description"] == "32-char alphanum"


def test_get_policy_returns_none_when_not_set(vault_dir):
    assert get_policy(vault_dir, "MISSING") is None


def test_set_policy_invalid_regex_raises(vault_dir):
    with pytest.raises(ValueError, match="Invalid regex"):
        set_policy(vault_dir, "KEY", r"[unclosed")


def test_remove_policy_deletes_entry(vault_dir):
    set_policy(vault_dir, "KEY", r".+")
    remove_policy(vault_dir, "KEY")
    assert get_policy(vault_dir, "KEY") is None


def test_remove_policy_noop_when_not_set(vault_dir):
    remove_policy(vault_dir, "GHOST")  # must not raise


def test_list_policies_empty_when_none(vault_dir):
    assert list_policies(vault_dir) == {}


def test_list_policies_returns_all(vault_dir):
    set_policy(vault_dir, "A", r"\d+")
    set_policy(vault_dir, "B", r"[a-z]+")
    result = list_policies(vault_dir)
    assert set(result.keys()) == {"A", "B"}


def test_validate_passes_matching_value(vault_dir):
    set_policy(vault_dir, "PORT", r"\d{4,5}")
    validate(vault_dir, "PORT", "8080")  # must not raise


def test_validate_raises_on_mismatch(vault_dir):
    set_policy(vault_dir, "PORT", r"\d{4,5}", description="4-5 digit port")
    with pytest.raises(ValueError, match="4-5 digit port"):
        validate(vault_dir, "PORT", "abc")


def test_validate_no_policy_is_noop(vault_dir):
    validate(vault_dir, "UNGUARDED", "anything goes")  # must not raise


# ── CLI commands ─────────────────────────────────────────────────────────────

def _ns(vault_dir, **kwargs):
    return argparse.Namespace(project_dir=vault_dir, **kwargs)


def test_cmd_policy_set_success(vault_dir):
    args = _ns(vault_dir, key="SECRET", pattern=r"\w+", description="")
    assert cmd_policy_set(args) == 0
    assert get_policy(vault_dir, "SECRET") is not None


def test_cmd_policy_set_bad_regex_returns_1(vault_dir):
    args = _ns(vault_dir, key="K", pattern=r"[bad", description="")
    assert cmd_policy_set(args) == 1


def test_cmd_policy_show_existing(vault_dir, capsys):
    set_policy(vault_dir, "MY_KEY", r".{8,}", description="min 8 chars")
    args = _ns(vault_dir, key="MY_KEY")
    assert cmd_policy_show(args) == 0
    out = capsys.readouterr().out
    assert "MY_KEY" in out
    assert ".{8,}" in out


def test_cmd_policy_show_missing_returns_1(vault_dir):
    args = _ns(vault_dir, key="NOPE")
    assert cmd_policy_show(args) == 1


def test_cmd_policy_remove_success(vault_dir):
    set_policy(vault_dir, "X", r".*")
    args = _ns(vault_dir, key="X")
    assert cmd_policy_remove(args) == 0
    assert get_policy(vault_dir, "X") is None


def test_cmd_policy_list_output(vault_dir, capsys):
    set_policy(vault_dir, "Z", r"[A-Z]+", description="uppercase only")
    args = _ns(vault_dir)
    assert cmd_policy_list(args) == 0
    out = capsys.readouterr().out
    assert "Z" in out
    assert "[A-Z]+" in out
