"""Tests for envault.lint."""
import pytest

from envault.store import save_secrets
from envault.lint import lint_secrets, LintResult


@pytest.fixture
def vault_dir(tmp_path):
    return str(tmp_path)


PASSWORD = "testpass"


def _seed(vault_dir, secrets):
    save_secrets(vault_dir, PASSWORD, secrets)


def test_lint_empty_vault_returns_no_issues(vault_dir):
    _seed(vault_dir, {})
    result = lint_secrets(vault_dir, PASSWORD)
    assert isinstance(result, LintResult)
    assert result.issues == []


def test_lint_detects_empty_value(vault_dir):
    _seed(vault_dir, {"MY_KEY": ""})
    result = lint_secrets(vault_dir, PASSWORD)
    rule_ids = [i.rule_id for i in result.issues]
    assert "E001" in rule_ids
    assert result.has_errors


def test_lint_detects_placeholder_value(vault_dir):
    _seed(vault_dir, {"MY_KEY": "changeme"})
    result = lint_secrets(vault_dir, PASSWORD)
    rule_ids = [i.rule_id for i in result.issues]
    assert "W001" in rule_ids


def test_lint_detects_lowercase_key(vault_dir):
    _seed(vault_dir, {"my_key": "somevalue"})
    result = lint_secrets(vault_dir, PASSWORD)
    rule_ids = [i.rule_id for i in result.issues]
    assert "W002" in rule_ids


def test_lint_detects_whitespace_in_value(vault_dir):
    _seed(vault_dir, {"MY_KEY": "  value  "})
    result = lint_secrets(vault_dir, PASSWORD)
    rule_ids = [i.rule_id for i in result.issues]
    assert "W003" in rule_ids


def test_lint_detects_short_value(vault_dir):
    _seed(vault_dir, {"MY_KEY": "abc"})
    result = lint_secrets(vault_dir, PASSWORD)
    rule_ids = [i.rule_id for i in result.issues]
    assert "W004" in rule_ids


def test_lint_no_issues_for_clean_secret(vault_dir):
    _seed(vault_dir, {"MY_KEY": "a-very-strong-secret-value-123!"})
    result = lint_secrets(vault_dir, PASSWORD)
    assert result.issues == []
    assert not result.has_errors


def test_lint_by_key_groups_issues(vault_dir):
    _seed(vault_dir, {"bad_key": "  "})
    result = lint_secrets(vault_dir, PASSWORD)
    by_key = result.by_key()
    assert "bad_key" in by_key
    rule_ids = [i.rule_id for i in by_key["bad_key"]]
    # empty (E001) + whitespace (W003) + lowercase key (W002)
    assert "E001" in rule_ids
    assert "W002" in rule_ids


def test_lint_rule_filter_applies(vault_dir):
    _seed(vault_dir, {"my_key": "changeme"})
    result = lint_secrets(vault_dir, PASSWORD, rules=["W001"])
    rule_ids = [i.rule_id for i in result.issues]
    assert "W001" in rule_ids
    assert "W002" not in rule_ids


def test_lint_placeholder_variants(vault_dir):
    for placeholder in ["TODO", "<your-secret>", "${SECRET}", "xxx"]:
        _seed(vault_dir, {"MY_KEY": placeholder})
        result = lint_secrets(vault_dir, PASSWORD, rules=["W001"])
        rule_ids = [i.rule_id for i in result.issues]
        assert "W001" in rule_ids, f"Expected W001 for placeholder: {placeholder!r}"
