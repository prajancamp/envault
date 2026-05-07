"""Tests for CLI share-export and share-import commands."""

from __future__ import annotations

import argparse
import pytest
from unittest.mock import patch

from envault.cli_share import cmd_share_export, cmd_share_import
from envault.store import save_secrets, load_secrets


@pytest.fixture()
def tmp_project(tmp_path):
    project = tmp_path / "proj"
    project.mkdir()
    save_secrets(str(project), "vaultpw", {"KEY1": "val1", "KEY2": "val2"})
    return tmp_path, project


def _make_export_args(project_dir, output, keys=None):
    ns = argparse.Namespace()
    ns.project_dir = str(project_dir)
    ns.output = output
    ns.keys = keys or []
    return ns


def _make_import_args(project_dir, bundle, overwrite=False):
    ns = argparse.Namespace()
    ns.project_dir = str(project_dir)
    ns.bundle = bundle
    ns.overwrite = overwrite
    return ns


def _patch_passwords(*passwords):
    return patch("envault.cli_share._get_password", side_effect=list(passwords))


def test_share_export_success(tmp_project, tmp_path):
    _, project = tmp_project
    out = str(tmp_path / "out.evb")
    args = _make_export_args(project, out)
    with _patch_passwords("vaultpw", "bundlepw"):
        rc = cmd_share_export(args)
    assert rc == 0
    from pathlib import Path
    assert Path(out).exists()


def test_share_export_missing_key_returns_1(tmp_project, tmp_path):
    _, project = tmp_project
    out = str(tmp_path / "out.evb")
    args = _make_export_args(project, out, keys=["NO_SUCH_KEY"])
    with _patch_passwords("vaultpw", "bundlepw"):
        rc = cmd_share_export(args)
    assert rc == 1


def test_share_import_success(tmp_project, tmp_path):
    _, project = tmp_project
    out = str(tmp_path / "out.evb")
    export_args = _make_export_args(project, out)
    with _patch_passwords("vaultpw", "bundlepw"):
        cmd_share_export(export_args)

    target = tmp_path / "target"
    target.mkdir()
    save_secrets(str(target), "pw2", {})

    import_args = _make_import_args(target, out)
    with _patch_passwords("pw2", "bundlepw"):
        rc = cmd_share_import(import_args)
    assert rc == 0
    loaded = load_secrets(str(target), "pw2")
    assert loaded["KEY1"] == "val1"


def test_share_import_missing_bundle_returns_1(tmp_project, tmp_path):
    _, project = tmp_project
    import_args = _make_import_args(project, str(tmp_path / "nonexistent.evb"))
    with _patch_passwords("vaultpw", "bundlepw"):
        rc = cmd_share_import(import_args)
    assert rc == 1


def test_share_import_wrong_bundle_password_returns_1(tmp_project, tmp_path):
    _, project = tmp_project
    out = str(tmp_path / "out.evb")
    with _patch_passwords("vaultpw", "bundlepw"):
        cmd_share_export(_make_export_args(project, out))

    target = tmp_path / "target"
    target.mkdir()
    save_secrets(str(target), "pw2", {})

    import_args = _make_import_args(target, out)
    with _patch_passwords("pw2", "wrongpw"):
        rc = cmd_share_import(import_args)
    assert rc == 1
