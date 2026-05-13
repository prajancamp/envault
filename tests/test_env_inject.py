"""Tests for envault.env_inject."""
from __future__ import annotations

import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

import pytest

from envault.store import save_secrets
from envault.ttl import set_ttl
from envault.env_inject import build_env, run_with_secrets


@pytest.fixture()
def vault_dir(tmp_path: Path) -> Path:
    return tmp_path


PASSWORD = "hunter2"


def _seed(project_dir: Path, secrets: dict) -> None:
    save_secrets(str(project_dir), PASSWORD, secrets)


# ---------------------------------------------------------------------------
# build_env
# ---------------------------------------------------------------------------

def test_build_env_injects_secrets(vault_dir: Path) -> None:
    _seed(vault_dir, {"DB_HOST": "localhost", "DB_PORT": "5432"})
    env = build_env(str(vault_dir), PASSWORD)
    assert env["DB_HOST"] == "localhost"
    assert env["DB_PORT"] == "5432"


def test_build_env_merges_os_environ(vault_dir: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("EXISTING_VAR", "yes")
    _seed(vault_dir, {"NEW_VAR": "new"})
    env = build_env(str(vault_dir), PASSWORD)
    assert env["EXISTING_VAR"] == "yes"
    assert env["NEW_VAR"] == "new"


def test_build_env_prefix_filter(vault_dir: Path) -> None:
    _seed(vault_dir, {"APP_KEY": "1", "DB_KEY": "2"})
    env = build_env(str(vault_dir), PASSWORD, prefix="APP_")
    assert "APP_KEY" in env
    assert "DB_KEY" not in env


def test_build_env_skips_expired_by_default(vault_dir: Path) -> None:
    _seed(vault_dir, {"OLD_SECRET": "gone"})
    past = datetime.now(timezone.utc) - timedelta(seconds=1)
    set_ttl(str(vault_dir), PASSWORD, "OLD_SECRET", past)
    env = build_env(str(vault_dir), PASSWORD)
    assert "OLD_SECRET" not in env


def test_build_env_include_expired_flag(vault_dir: Path) -> None:
    _seed(vault_dir, {"OLD_SECRET": "still_here"})
    past = datetime.now(timezone.utc) - timedelta(seconds=1)
    set_ttl(str(vault_dir), PASSWORD, "OLD_SECRET", past)
    env = build_env(str(vault_dir), PASSWORD, skip_expired=False)
    assert env["OLD_SECRET"] == "still_here"


def test_build_env_extra_env_overrides(vault_dir: Path) -> None:
    _seed(vault_dir, {"KEY": "original"})
    env = build_env(str(vault_dir), PASSWORD, extra_env={"KEY": "override"})
    assert env["KEY"] == "override"


# ---------------------------------------------------------------------------
# run_with_secrets
# ---------------------------------------------------------------------------

def test_run_with_secrets_returns_exit_code(vault_dir: Path) -> None:
    _seed(vault_dir, {"PING": "pong"})
    code = run_with_secrets(
        str(vault_dir), PASSWORD, [sys.executable, "-c", "import sys; sys.exit(0)"]
    )
    assert code == 0


def test_run_with_secrets_nonzero_exit(vault_dir: Path) -> None:
    _seed(vault_dir, {})
    code = run_with_secrets(
        str(vault_dir), PASSWORD, [sys.executable, "-c", "import sys; sys.exit(42)"]
    )
    assert code == 42
