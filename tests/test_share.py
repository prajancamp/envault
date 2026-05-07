"""Tests for envault.share — encrypted bundle export/import."""

from __future__ import annotations

import json
import pytest

from envault.share import export_bundle, import_bundle
from envault.store import load_secrets, save_secrets
from envault.crypto import decrypt


@pytest.fixture()
def vault_dir(tmp_path):
    project = tmp_path / "myproject"
    project.mkdir()
    secrets = {"DB_HOST": "localhost", "DB_PASS": "s3cr3t", "API_KEY": "abc123"}
    save_secrets(str(project), "vaultpw", secrets)
    return str(project)


def test_export_bundle_creates_file(vault_dir, tmp_path):
    out = str(tmp_path / "bundle.evb")
    count = export_bundle(vault_dir, "vaultpw", None, "bundlepw", out)
    assert count == 3
    from pathlib import Path
    assert Path(out).exists()


def test_export_bundle_content_is_encrypted(vault_dir, tmp_path):
    out = str(tmp_path / "bundle.evb")
    export_bundle(vault_dir, "vaultpw", None, "bundlepw", out)
    from pathlib import Path
    raw = Path(out).read_text()
    assert "DB_PASS" not in raw
    payload = decrypt(raw, "bundlepw")
    data = json.loads(payload)
    assert data["DB_PASS"] == "s3cr3t"


def test_export_bundle_subset_of_keys(vault_dir, tmp_path):
    out = str(tmp_path / "bundle.evb")
    count = export_bundle(vault_dir, "vaultpw", ["DB_HOST", "API_KEY"], "bundlepw", out)
    assert count == 2
    from pathlib import Path
    payload = decrypt(Path(out).read_text(), "bundlepw")
    data = json.loads(payload)
    assert "DB_HOST" in data
    assert "DB_PASS" not in data


def test_export_bundle_missing_key_raises(vault_dir, tmp_path):
    out = str(tmp_path / "bundle.evb")
    with pytest.raises(KeyError, match="MISSING_KEY"):
        export_bundle(vault_dir, "vaultpw", ["MISSING_KEY"], "bundlepw", out)


def test_import_bundle_round_trip(vault_dir, tmp_path):
    out = str(tmp_path / "bundle.evb")
    export_bundle(vault_dir, "vaultpw", None, "bundlepw", out)

    new_project = tmp_path / "newproject"
    new_project.mkdir()
    save_secrets(str(new_project), "vaultpw2", {})

    result = import_bundle(str(new_project), "vaultpw2", "bundlepw", out)
    assert result["imported"] == 3
    assert result["skipped"] == 0

    loaded = load_secrets(str(new_project), "vaultpw2")
    assert loaded["DB_HOST"] == "localhost"


def test_import_bundle_skips_existing_without_overwrite(vault_dir, tmp_path):
    out = str(tmp_path / "bundle.evb")
    export_bundle(vault_dir, "vaultpw", None, "bundlepw", out)

    target = tmp_path / "target"
    target.mkdir()
    save_secrets(str(target), "pw", {"DB_HOST": "other"})

    result = import_bundle(str(target), "pw", "bundlepw", out)
    assert result["skipped"] == 1
    assert result["imported"] == 2
    loaded = load_secrets(str(target), "pw")
    assert loaded["DB_HOST"] == "other"


def test_import_bundle_overwrites_when_flag_set(vault_dir, tmp_path):
    out = str(tmp_path / "bundle.evb")
    export_bundle(vault_dir, "vaultpw", None, "bundlepw", out)

    target = tmp_path / "target"
    target.mkdir()
    save_secrets(str(target), "pw", {"DB_HOST": "other"})

    result = import_bundle(str(target), "pw", "bundlepw", out, overwrite=True)
    assert result["imported"] == 3
    loaded = load_secrets(str(target), "pw")
    assert loaded["DB_HOST"] == "localhost"


def test_import_bundle_wrong_bundle_password_raises(vault_dir, tmp_path):
    out = str(tmp_path / "bundle.evb")
    export_bundle(vault_dir, "vaultpw", None, "bundlepw", out)

    target = tmp_path / "target"
    target.mkdir()
    save_secrets(str(target), "pw", {})

    with pytest.raises(Exception):
        import_bundle(str(target), "pw", "wrongpw", out)
