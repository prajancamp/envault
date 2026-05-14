"""Lint secrets in the vault against common quality rules."""
from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Dict, List, Optional

from envault.store import load_secrets

# Rules: (rule_id, description, checker)
_RULES = []


def _rule(rule_id: str, description: str):
    """Decorator to register a lint rule."""
    def decorator(fn):
        _RULES.append((rule_id, description, fn))
        return fn
    return decorator


@dataclass
class LintIssue:
    key: str
    rule_id: str
    description: str
    severity: str = "warning"  # "warning" | "error"


@dataclass
class LintResult:
    issues: List[LintIssue] = field(default_factory=list)

    @property
    def has_errors(self) -> bool:
        return any(i.severity == "error" for i in self.issues)

    def by_key(self) -> Dict[str, List[LintIssue]]:
        out: Dict[str, List[LintIssue]] = {}
        for issue in self.issues:
            out.setdefault(issue.key, []).append(issue)
        return out


@_rule("E001", "Secret value is empty")
def _check_empty(key: str, value: str) -> Optional[LintIssue]:
    if not value.strip():
        return LintIssue(key=key, rule_id="E001",
                         description="Secret value is empty", severity="error")
    return None


@_rule("W001", "Secret value looks like a placeholder")
def _check_placeholder(key: str, value: str) -> Optional[LintIssue]:
    placeholders = re.compile(
        r'^(todo|fixme|placeholder|changeme|replace.?me|xxx+|<[^>]+>|\$\{[^}]+\})$',
        re.IGNORECASE,
    )
    if placeholders.match(value.strip()):
        return LintIssue(key=key, rule_id="W001",
                         description="Value looks like a placeholder")
    return None


@_rule("W002", "Secret key uses lowercase letters (prefer UPPER_SNAKE_CASE)")
def _check_key_case(key: str, value: str) -> Optional[LintIssue]:
    if key != key.upper():
        return LintIssue(key=key, rule_id="W002",
                         description="Key is not UPPER_SNAKE_CASE")
    return None


@_rule("W003", "Secret value contains leading or trailing whitespace")
def _check_whitespace(key: str, value: str) -> Optional[LintIssue]:
    if value != value.strip():
        return LintIssue(key=key, rule_id="W003",
                         description="Value has leading or trailing whitespace")
    return None


@_rule("W004", "Short secret value (fewer than 8 characters) may be weak")
def _check_short_value(key: str, value: str) -> Optional[LintIssue]:
    if 0 < len(value.strip()) < 8:
        return LintIssue(key=key, rule_id="W004",
                         description=f"Value is only {len(value.strip())} character(s) long")
    return None


def lint_secrets(project_dir: str, password: str,
                 rules: Optional[List[str]] = None) -> LintResult:
    """Run all (or selected) lint rules against the vault secrets."""
    secrets = load_secrets(project_dir, password)
    result = LintResult()
    active_rules = [
        (rid, desc, fn) for rid, desc, fn in _RULES
        if rules is None or rid in rules
    ]
    for key, value in secrets.items():
        for _rid, _desc, checker in active_rules:
            issue = checker(key, value)
            if issue:
                result.issues.append(issue)
    return result
