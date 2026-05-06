"""Tag-based grouping and filtering of secrets."""
from __future__ import annotations

from typing import Dict, List, Optional

from envault.store import load_secrets, save_secrets

_TAG_PREFIX = "__tag__"


def _tag_key(secret_key: str) -> str:
    return f"{_TAG_PREFIX}{secret_key}"


def set_tag(project_dir: str, password: str, secret_key: str, tag: str) -> None:
    """Attach a tag to an existing secret."""
    secrets = load_secrets(project_dir, password)
    if secret_key not in secrets:
        raise KeyError(f"Secret '{secret_key}' does not exist.")
    meta_key = _tag_key(secret_key)
    existing = secrets.get(meta_key, "")
    tags = set(t for t in existing.split(",") if t)
    tags.add(tag)
    secrets[meta_key] = ",".join(sorted(tags))
    save_secrets(project_dir, password, secrets)


def remove_tag(project_dir: str, password: str, secret_key: str, tag: str) -> None:
    """Remove a tag from a secret."""
    secrets = load_secrets(project_dir, password)
    meta_key = _tag_key(secret_key)
    existing = secrets.get(meta_key, "")
    tags = set(t for t in existing.split(",") if t)
    tags.discard(tag)
    if tags:
        secrets[meta_key] = ",".join(sorted(tags))
    elif meta_key in secrets:
        del secrets[meta_key]
    save_secrets(project_dir, password, secrets)


def get_tags(project_dir: str, password: str, secret_key: str) -> List[str]:
    """Return the list of tags for a secret."""
    secrets = load_secrets(project_dir, password)
    meta_key = _tag_key(secret_key)
    raw = secrets.get(meta_key, "")
    return sorted(t for t in raw.split(",") if t)


def filter_by_tag(project_dir: str, password: str, tag: str) -> Dict[str, str]:
    """Return secrets (key -> value) that carry the given tag."""
    secrets = load_secrets(project_dir, password)
    result: Dict[str, str] = {}
    for key, value in secrets.items():
        if key.startswith(_TAG_PREFIX):
            continue
        meta_key = _tag_key(key)
        tags = set(t for t in secrets.get(meta_key, "").split(",") if t)
        if tag in tags:
            result[key] = value
    return result


def list_all_tags(project_dir: str, password: str) -> Dict[str, List[str]]:
    """Return a mapping of secret_key -> [tags] for all tagged secrets."""
    secrets = load_secrets(project_dir, password)
    result: Dict[str, List[str]] = {}
    for key in secrets:
        if key.startswith(_TAG_PREFIX):
            continue
        meta_key = _tag_key(key)
        tags = sorted(t for t in secrets.get(meta_key, "").split(",") if t)
        if tags:
            result[key] = tags
    return result
