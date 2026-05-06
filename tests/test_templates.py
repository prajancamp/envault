"""Tests for envault.templates."""
from __future__ import annotations

import pytest
from pathlib import Path

from envault.templates import (
    delete_template,
    list_templates,
    load_template,
    save_template,
    validate_against_template,
)


@pytest.fixture()
def vault_dir(tmp_path: Path) -> Path:
    return tmp_path


SAMPLE_FIELDS = {
    "DB_HOST": {"description": "Database host", "required": True},
    "DB_PORT": {"description": "Database port", "required": False, "default": "5432"},
    "API_KEY": {"description": "External API key", "required": True},
}


def test_save_and_load_round_trip(vault_dir: Path) -> None:
    save_template(vault_dir, "web", SAMPLE_FIELDS)
    loaded = load_template(vault_dir, "web")
    assert loaded == SAMPLE_FIELDS


def test_list_templates_empty_when_none_exist(vault_dir: Path) -> None:
    assert list_templates(vault_dir) == []


def test_list_templates_returns_names(vault_dir: Path) -> None:
    save_template(vault_dir, "alpha", {})
    save_template(vault_dir, "beta", {})
    assert list_templates(vault_dir) == ["alpha", "beta"]


def test_load_template_raises_when_missing(vault_dir: Path) -> None:
    with pytest.raises(FileNotFoundError, match="ghost"):
        load_template(vault_dir, "ghost")


def test_delete_template_removes_it(vault_dir: Path) -> None:
    save_template(vault_dir, "tmp", {})
    delete_template(vault_dir, "tmp")
    assert "tmp" not in list_templates(vault_dir)


def test_delete_template_raises_when_missing(vault_dir: Path) -> None:
    with pytest.raises(FileNotFoundError):
        delete_template(vault_dir, "nope")


def test_validate_no_issues(vault_dir: Path) -> None:
    save_template(vault_dir, "svc", SAMPLE_FIELDS)
    secrets = {"DB_HOST": "localhost", "API_KEY": "secret123"}
    result = validate_against_template(vault_dir, "svc", secrets)
    assert result["missing"] == []
    assert result["extra"] == []


def test_validate_detects_missing_required(vault_dir: Path) -> None:
    save_template(vault_dir, "svc", SAMPLE_FIELDS)
    secrets = {"DB_HOST": "localhost"}  # API_KEY missing
    result = validate_against_template(vault_dir, "svc", secrets)
    assert "API_KEY" in result["missing"]


def test_validate_optional_key_not_flagged_as_missing(vault_dir: Path) -> None:
    save_template(vault_dir, "svc", SAMPLE_FIELDS)
    secrets = {"DB_HOST": "localhost", "API_KEY": "key"}  # DB_PORT optional, absent
    result = validate_against_template(vault_dir, "svc", secrets)
    assert "DB_PORT" not in result["missing"]


def test_validate_detects_extra_keys(vault_dir: Path) -> None:
    save_template(vault_dir, "svc", SAMPLE_FIELDS)
    secrets = {"DB_HOST": "h", "API_KEY": "k", "UNKNOWN_VAR": "x"}
    result = validate_against_template(vault_dir, "svc", secrets)
    assert "UNKNOWN_VAR" in result["extra"]


def test_save_overwrites_existing_template(vault_dir: Path) -> None:
    save_template(vault_dir, "svc", SAMPLE_FIELDS)
    new_fields = {"NEW_KEY": {"required": True}}
    save_template(vault_dir, "svc", new_fields)
    loaded = load_template(vault_dir, "svc")
    assert loaded == new_fields
