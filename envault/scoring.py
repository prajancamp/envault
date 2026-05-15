"""Secret strength scoring for envault vault entries."""
from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Dict, List

from envault.store import load_secrets


@dataclass
class SecretScore:
    key: str
    score: int          # 0-100
    grade: str          # A / B / C / D / F
    issues: List[str] = field(default_factory=list)


@dataclass
class VaultScoreReport:
    scores: List[SecretScore] = field(default_factory=list)

    @property
    def average_score(self) -> float:
        if not self.scores:
            return 0.0
        return sum(s.score for s in self.scores) / len(self.scores)

    @property
    def grade_distribution(self) -> Dict[str, int]:
        dist: Dict[str, int] = {g: 0 for g in ("A", "B", "C", "D", "F")}
        for s in self.scores:
            dist[s.grade] += 1
        return dist


def _grade(score: int) -> str:
    if score >= 80:
        return "A"
    if score >= 60:
        return "B"
    if score >= 40:
        return "C"
    if score >= 20:
        return "D"
    return "F"


def score_value(key: str, value: str) -> SecretScore:
    """Evaluate the strength of a single secret value."""
    issues: List[str] = []
    points = 100

    if not value:
        issues.append("empty value")
        return SecretScore(key=key, score=0, grade="F", issues=issues)

    if len(value) < 8:
        issues.append("value too short (< 8 chars)")
        points -= 30

    if value.lower() in ("password", "secret", "changeme", "todo", "fixme", "placeholder", "example"):
        issues.append("common placeholder detected")
        points -= 40

    if re.fullmatch(r"[a-z]+", value):
        issues.append("only lowercase letters")
        points -= 20

    if re.fullmatch(r"\d+", value):
        issues.append("only digits")
        points -= 20

    if len(set(value)) < 4:
        issues.append("low character variety")
        points -= 15

    score = max(0, min(100, points))
    return SecretScore(key=key, score=score, grade=_grade(score), issues=issues)


def compute_vault_scores(vault_dir: str, password: str) -> VaultScoreReport:
    secrets = load_secrets(vault_dir, password)
    scores = [score_value(k, v) for k, v in secrets.items()]
    return VaultScoreReport(scores=scores)
