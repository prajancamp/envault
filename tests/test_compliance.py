"""Tests for envault.compliance."""
from __future__ import annotations

import pytest

from envault.store import save_secrets
from envault.ttl import set_ttl
from envault.access import set_acl
from envault.compliance import generate_report, ComplianceReport, ComplianceItem


PASSWORD = "testpass"


@pytest.fixture()
def vault_dir(tmp_path):
    return str(tmp_path)


def _seed(vault_dir: str, secrets: dict) -> None:
    save_secrets(vault_dir, PASSWORD, secrets)


def test_compliance_empty_vault_returns_report(vault_dir):
    _seed(vault_dir, {})
    report = generate_report(vault_dir, PASSWORD)
    assert isinstance(report, ComplianceReport)
    assert report.total_secrets == 0
    assert report.compliant_count == 0
    assert report.non_compliant_count == 0
    assert report.items == []


def test_compliance_single_clean_secret(vault_dir):
    _seed(vault_dir, {"API_KEY": "abc123"})
    report = generate_report(vault_dir, PASSWORD)
    assert report.total_secrets == 1
    assert len(report.items) == 1
    item = report.items[0]
    assert item.key == "API_KEY"
    assert item.compliant  # no lint errors, no policy violations


def test_compliance_detects_lint_error_empty_value(vault_dir):
    _seed(vault_dir, {"EMPTY_KEY": ""})
    report = generate_report(vault_dir, PASSWORD)
    assert report.total_secrets == 1
    item = report.items[0]
    assert item.key == "EMPTY_KEY"
    assert len(item.lint_errors) >= 1
    assert not item.compliant
    assert report.non_compliant_count == 1


def test_compliance_has_ttl_flag(vault_dir):
    _seed(vault_dir, {"DB_PASS": "secret"})
    set_ttl(vault_dir, PASSWORD, "DB_PASS", 3600)
    report = generate_report(vault_dir, PASSWORD)
    item = next(i for i in report.items if i.key == "DB_PASS")
    assert item.has_ttl is True


def test_compliance_no_ttl_flag(vault_dir):
    _seed(vault_dir, {"DB_PASS": "secret"})
    report = generate_report(vault_dir, PASSWORD)
    item = next(i for i in report.items if i.key == "DB_PASS")
    assert item.has_ttl is False


def test_compliance_has_acl_flag(vault_dir):
    _seed(vault_dir, {"TOKEN": "xyz"})
    set_acl(vault_dir, PASSWORD, "TOKEN", ["alice"])
    report = generate_report(vault_dir, PASSWORD)
    item = next(i for i in report.items if i.key == "TOKEN")
    assert item.has_acl is True


def test_compliance_as_dict_structure(vault_dir):
    _seed(vault_dir, {"KEY": "val"})
    report = generate_report(vault_dir, PASSWORD)
    d = report.as_dict()
    assert "total_secrets" in d
    assert "items" in d
    assert isinstance(d["items"], list)
    if d["items"]:
        assert "key" in d["items"][0]
        assert "compliant" in d["items"][0]


def test_compliance_multiple_secrets_counts(vault_dir):
    _seed(vault_dir, {"A": "good", "B": "", "C": "also_good"})
    report = generate_report(vault_dir, PASSWORD)
    assert report.total_secrets == 3
    # B has empty value -> lint error -> non-compliant
    assert report.non_compliant_count >= 1
    assert report.compliant_count + report.non_compliant_count == report.total_secrets
