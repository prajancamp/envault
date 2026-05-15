"""Tests for envault.scoring."""
from __future__ import annotations

import os
import pytest

from envault.store import save_secrets
from envault.scoring import (
    score_value,
    compute_vault_scores,
    SecretScore,
    VaultScoreReport,
)

PASSWORD = "test-pass"


@pytest.fixture()
def vault_dir(tmp_path):
    return str(tmp_path)


# ---------------------------------------------------------------------------
# score_value unit tests
# ---------------------------------------------------------------------------

def test_score_empty_value_is_zero():
    s = score_value("KEY", "")
    assert s.score == 0
    assert s.grade == "F"
    assert any("empty" in i for i in s.issues)


def test_score_short_value_penalised():
    s = score_value("KEY", "abc")
    assert s.score < 100
    assert any("short" in i for i in s.issues)


def test_score_placeholder_penalised():
    s = score_value("KEY", "password")
    assert s.score < 60
    assert any("placeholder" in i for i in s.issues)


def test_score_only_digits_penalised():
    s = score_value("KEY", "12345678")
    assert any("digit" in i for i in s.issues)


def test_score_strong_value_high_score():
    s = score_value("API_KEY", "xK9#mP2$qL7!nR4@")
    assert s.score >= 80
    assert s.grade == "A"
    assert s.issues == []


def test_grade_boundaries():
    assert score_value("K", "xK9#mP2$qL7!nR4@").grade == "A"


# ---------------------------------------------------------------------------
# compute_vault_scores integration tests
# ---------------------------------------------------------------------------

def test_compute_vault_scores_empty_vault(vault_dir):
    save_secrets(vault_dir, PASSWORD, {})
    report = compute_vault_scores(vault_dir, PASSWORD)
    assert isinstance(report, VaultScoreReport)
    assert report.scores == []
    assert report.average_score == 0.0


def test_compute_vault_scores_returns_one_entry_per_secret(vault_dir):
    save_secrets(vault_dir, PASSWORD, {"A": "val1", "B": "val2"})
    report = compute_vault_scores(vault_dir, PASSWORD)
    assert len(report.scores) == 2
    keys = {s.key for s in report.scores}
    assert keys == {"A", "B"}


def test_average_score_is_mean(vault_dir):
    save_secrets(vault_dir, PASSWORD, {"K": "xK9#mP2$qL7!nR4@"})
    report = compute_vault_scores(vault_dir, PASSWORD)
    assert report.average_score == report.scores[0].score


def test_grade_distribution_counts(vault_dir):
    save_secrets(vault_dir, PASSWORD, {
        "GOOD": "xK9#mP2$qL7!nR4@",
        "BAD": "password",
    })
    report = compute_vault_scores(vault_dir, PASSWORD)
    dist = report.grade_distribution
    assert sum(dist.values()) == 2


def test_compute_vault_scores_wrong_password_raises(vault_dir):
    save_secrets(vault_dir, PASSWORD, {"K": "v"})
    with pytest.raises(Exception):
        compute_vault_scores(vault_dir, "wrong")
