"""Compliance reporting: generate structured reports on vault health and policy adherence."""
from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from envault.store import load_secrets
from envault.lint import run_lint
from envault.ttl import get_ttl
from envault.access import get_acl
from envault.pinning import is_pinned
from envault.policies import get_policy, list_policies


@dataclass
class ComplianceItem:
    key: str
    has_ttl: bool
    has_acl: bool
    is_pinned: bool
    policy_violations: list[str] = field(default_factory=list)
    lint_errors: list[str] = field(default_factory=list)

    @property
    def compliant(self) -> bool:
        return not self.policy_violations and not self.lint_errors


@dataclass
class ComplianceReport:
    project_dir: str
    total_secrets: int
    compliant_count: int
    non_compliant_count: int
    items: list[ComplianceItem] = field(default_factory=list)

    def as_dict(self) -> dict[str, Any]:
        return {
            "project_dir": self.project_dir,
            "total_secrets": self.total_secrets,
            "compliant_count": self.compliant_count,
            "non_compliant_count": self.non_compliant_count,
            "items": [
                {
                    "key": item.key,
                    "has_ttl": item.has_ttl,
                    "has_acl": item.has_acl,
                    "is_pinned": item.is_pinned,
                    "policy_violations": item.policy_violations,
                    "lint_errors": item.lint_errors,
                    "compliant": item.compliant,
                }
                for item in self.items
            ],
        }


def generate_report(project_dir: str, password: str) -> ComplianceReport:
    """Analyse every secret in the vault and return a ComplianceReport."""
    secrets = load_secrets(project_dir, password)
    lint_result = run_lint(project_dir, password)

    # Map lint errors by key for quick lookup
    lint_errors_by_key: dict[str, list[str]] = {}
    for issue in lint_result.issues:
        lint_errors_by_key.setdefault(issue.key, []).append(issue.message)

    items: list[ComplianceItem] = []
    for key in secrets:
        ttl = get_ttl(project_dir, password, key)
        acl = get_acl(project_dir, password, key)
        pinned = is_pinned(project_dir, password, key)

        violations: list[str] = []
        for policy_name in list_policies(project_dir, password):
            policy = get_policy(project_dir, password, policy_name)
            if policy and not policy.check(key, secrets[key]):
                violations.append(policy_name)

        item = ComplianceItem(
            key=key,
            has_ttl=ttl is not None,
            has_acl=bool(acl),
            is_pinned=pinned,
            policy_violations=violations,
            lint_errors=lint_errors_by_key.get(key, []),
        )
        items.append(item)

    compliant = [i for i in items if i.compliant]
    return ComplianceReport(
        project_dir=project_dir,
        total_secrets=len(items),
        compliant_count=len(compliant),
        non_compliant_count=len(items) - len(compliant),
        items=items,
    )
