"""Tests for the envault CLI layer."""

import pytest
from unittest.mock import patch, MagicMock

from envault.cli import build_parser, cmd_set, cmd_get, cmd_delete, cmd_list, cmd_log


PASSWORD = "test-password"
PROJECT = "myapp"


@pytest.fixture()
def tmp_project(tmp_path, monkeypatch):
    """Redirect vault and audit storage to a temp directory."""
    monkeypatch.setenv("ENVAULT_DIR", str(tmp_path))
    import envault.store as store_mod
    import envault.audit as audit_mod
    monkeypatch.setattr(store_mod, "_vault_path",
                        lambda project: tmp_path / f"{project}.vault")
    monkeypatch.setattr(audit_mod, "_log_path",
                        lambda project: tmp_path / f"{project}.log")
    return tmp_path


def _make_args(**kwargs):
    args = MagicMock()
    for k, v in kwargs.items():
        setattr(args, k, v)
    return args


def test_set_and_get_round_trip(tmp_project):
    with patch("envault.cli._get_password", return_value=PASSWORD):
        set_args = _make_args(project=PROJECT, key="DB_URL", value="postgres://localhost/db")
        assert cmd_set(set_args) == 0

        get_args = _make_args(project=PROJECT, key="DB_URL")
        assert cmd_get(get_args) == 0


def test_get_missing_key_returns_1(tmp_project):
    with patch("envault.cli._get_password", return_value=PASSWORD):
        args = _make_args(project=PROJECT, key="MISSING")
        assert cmd_get(args) == 1


def test_delete_existing_key(tmp_project):
    with patch("envault.cli._get_password", return_value=PASSWORD):
        cmd_set(_make_args(project=PROJECT, key="TOKEN", value="abc123"))
        assert cmd_delete(_make_args(project=PROJECT, key="TOKEN")) == 0


def test_delete_missing_key_returns_1(tmp_project):
    with patch("envault.cli._get_password", return_value=PASSWORD):
        assert cmd_delete(_make_args(project=PROJECT, key="GHOST")) == 1


def test_list_shows_keys(tmp_project, capsys):
    with patch("envault.cli._get_password", return_value=PASSWORD):
        cmd_set(_make_args(project=PROJECT, key="API_KEY", value="secret"))
        cmd_set(_make_args(project=PROJECT, key="DEBUG", value="true"))
        cmd_list(_make_args(project=PROJECT))
    captured = capsys.readouterr()
    assert "API_KEY" in captured.out
    assert "DEBUG" in captured.out


def test_list_empty_project(tmp_project, capsys):
    with patch("envault.cli._get_password", return_value=PASSWORD):
        cmd_list(_make_args(project=PROJECT))
    captured = capsys.readouterr()
    assert "No secrets" in captured.out


def test_log_records_actions(tmp_project, capsys):
    with patch("envault.cli._get_password", return_value=PASSWORD):
        cmd_set(_make_args(project=PROJECT, key="X", value="1"))
        cmd_get(_make_args(project=PROJECT, key="X"))
        cmd_log(_make_args(project=PROJECT))
    captured = capsys.readouterr()
    assert "set" in captured.out
    assert "get" in captured.out


def test_build_parser_set():
    parser = build_parser()
    args = parser.parse_args(["set", "proj", "KEY", "VALUE"])
    assert args.command == "set"
    assert args.project == "proj"
    assert args.key == "KEY"
    assert args.value == "VALUE"


def test_build_parser_log_optional_project():
    parser = build_parser()
    args = parser.parse_args(["log"])
    assert args.project is None
    args2 = parser.parse_args(["log", "myapp"])
    assert args2.project == "myapp"
