"""Tests for envault.search and envault.cli_search."""

from __future__ import annotations

import argparse
import pytest

from envault.store import save_secrets
from envault.search import grep, search_keys, search_values
from envault.cli_search import cmd_search


PASSWORD = "hunter2"

SECRETS = {
    "DATABASE_URL": "postgres://localhost/mydb",
    "DATABASE_POOL": "5",
    "REDIS_URL": "redis://localhost:6379",
    "SECRET_KEY": "supersecret",
    "DEBUG": "false",
}


@pytest.fixture()
def vault_dir(tmp_path):
    save_secrets(str(tmp_path), PASSWORD, SECRETS)
    return str(tmp_path)


# --- search_keys ---

def test_search_keys_wildcard(vault_dir):
    result = search_keys(vault_dir, PASSWORD, "DATABASE_*")
    assert set(result) == {"DATABASE_URL", "DATABASE_POOL"}


def test_search_keys_regex(vault_dir):
    result = search_keys(vault_dir, PASSWORD, r"^(REDIS|DEBUG)$", use_regex=True)
    assert set(result) == {"REDIS_URL", "DEBUG"}


def test_search_keys_no_match(vault_dir):
    result = search_keys(vault_dir, PASSWORD, "NONEXISTENT_*")
    assert result == []


# --- search_values ---

def test_search_values_substring(vault_dir):
    result = search_values(vault_dir, PASSWORD, "localhost")
    keys_found = {k for k, _ in result}
    assert keys_found == {"DATABASE_URL", "REDIS_URL"}


def test_search_values_case_insensitive(vault_dir):
    result = search_values(vault_dir, PASSWORD, "FALSE")
    assert len(result) == 1
    assert result[0][0] == "DEBUG"


def test_search_values_case_sensitive_no_match(vault_dir):
    result = search_values(vault_dir, PASSWORD, "FALSE", case_sensitive=True)
    assert result == []


# --- grep ---

def test_grep_matches_key_and_value(vault_dir):
    # 'secret' matches SECRET_KEY (key) and supersecret (value)
    result = grep(vault_dir, PASSWORD, "*secret*")
    assert "SECRET_KEY" in result


def test_grep_keys_only_flag(vault_dir):
    result = grep(vault_dir, PASSWORD, "*URL*", search_values_flag=False)
    assert set(result.keys()) == {"DATABASE_URL", "REDIS_URL"}


# --- cmd_search ---

def _make_args(project_dir, pattern, *, regex=False, keys_only=False, values_only=False):
    ns = argparse.Namespace(
        project_dir=project_dir,
        pattern=pattern,
        regex=regex,
        keys_only=keys_only,
        values_only=values_only,
    )
    return ns


def test_cmd_search_returns_0_on_match(vault_dir):
    args = _make_args(vault_dir, "DATABASE_*")
    assert cmd_search(args, password=PASSWORD) == 0


def test_cmd_search_returns_0_on_no_match(vault_dir):
    args = _make_args(vault_dir, "NOTHING_*")
    assert cmd_search(args, password=PASSWORD) == 0


def test_cmd_search_returns_1_on_bad_password(vault_dir):
    args = _make_args(vault_dir, "*")
    assert cmd_search(args, password="wrongpassword") == 1
