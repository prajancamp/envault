"""Integration tests for CLI template commands."""
from __future__ import annotations

import argparse
import json
from pathlib import Path
from unittest.mock import patch

import pytest

from envault.cli_templates import (
    cmd_template_delete,
    cmd_template_list,
    cmd_template_save,
    cmd_template_show,
    cmd_template_validate,
)
from envault.store import save_secrets
from envault.templates import save_template

PASSWORD = "cli-test-pw"

SAMPLE_FIELDS = {
    "DB_HOST": {"description": "host", "required": True},
    "API_KEY": {"description": "key", "required": True},
}


@pytest.fixture()
def tmp_project(tmp_path: Path) -> Path:
    return tmp_path


def _make_args(project_dir: Path, **kwargs) -> argparse.Namespace:
    defaults = {"project_dir": str(project_dir)}
    defaults.update(kwargs)
    return argparse.Namespace(**defaults)


def test_template_save_creates_template(tmp_project: Path, tmp_path: Path) -> None:
    spec = tmp_path / "spec.json"
    spec.write_text(json.dumps(SAMPLE_FIELDS), encoding="utf-8")
    args = _make_args(tmp_project, name="web", spec_file=str(spec))
    assert cmd_template_save(args) == 0


def test_template_save_missing_spec_returns_1(tmp_project: Path) -> None:
    args = _make_args(tmp_project, name="web", spec_file="/no/such/file.json")
    assert cmd_template_save(args) == 1


def test_template_list_shows_names(tmp_project: Path, capsys) -> None:
    save_template(tmp_project, "alpha", {})
    save_template(tmp_project, "beta", {})
    args = _make_args(tmp_project)
    assert cmd_template_list(args) == 0
    out = capsys.readouterr().out
    assert "alpha" in out
    assert "beta" in out


def test_template_list_empty_message(tmp_project: Path, capsys) -> None:
    args = _make_args(tmp_project)
    cmd_template_list(args)
    assert "No templates" in capsys.readouterr().out


def test_template_show_outputs_json(tmp_project: Path, capsys) -> None:
    save_template(tmp_project, "svc", SAMPLE_FIELDS)
    args = _make_args(tmp_project, name="svc")
    assert cmd_template_show(args) == 0
    data = json.loads(capsys.readouterr().out)
    assert data == SAMPLE_FIELDS


def test_template_show_missing_returns_1(tmp_project: Path) -> None:
    args = _make_args(tmp_project, name="ghost")
    assert cmd_template_show(args) == 1


def test_template_delete_removes(tmp_project: Path) -> None:
    save_template(tmp_project, "old", {})
    args = _make_args(tmp_project, name="old")
    assert cmd_template_delete(args) == 0


def test_template_delete_missing_returns_1(tmp_project: Path) -> None:
    args = _make_args(tmp_project, name="nope")
    assert cmd_template_delete(args) == 1


def test_template_validate_pass(tmp_project: Path) -> None:
    save_template(tmp_project, "svc", SAMPLE_FIELDS)
    save_secrets(tmp_project, {"DB_HOST": "localhost", "API_KEY": "abc"}, PASSWORD)
    args = _make_args(tmp_project, name="svc", strict=False)
    with patch("envault.cli_templates._get_password", return_value=PASSWORD):
        assert cmd_template_validate(args) == 0


def test_template_validate_missing_key_returns_1(tmp_project: Path) -> None:
    save_template(tmp_project, "svc", SAMPLE_FIELDS)
    save_secrets(tmp_project, {"DB_HOST": "localhost"}, PASSWORD)  # API_KEY absent
    args = _make_args(tmp_project, name="svc", strict=False)
    with patch("envault.cli_templates._get_password", return_value=PASSWORD):
        assert cmd_template_validate(args) == 1


def test_template_validate_strict_extra_returns_1(tmp_project: Path) -> None:
    save_template(tmp_project, "svc", SAMPLE_FIELDS)
    save_secrets(tmp_project, {"DB_HOST": "h", "API_KEY": "k", "EXTRA": "x"}, PASSWORD)
    args = _make_args(tmp_project, name="svc", strict=True)
    with patch("envault.cli_templates._get_password", return_value=PASSWORD):
        assert cmd_template_validate(args) == 1
