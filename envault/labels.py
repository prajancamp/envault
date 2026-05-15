"""Label management for vault secrets — attach freeform key-value labels."""

from __future__ import annotations

from typing import Dict, List, Optional

from envault.store import load_secrets, save_secrets

_LABEL_PREFIX = "__label__"


def _label_key(secret_key: str) -> str:
    return f"{_LABEL_PREFIX}{secret_key}"


def set_label(vault_dir: str, password: str, secret_key: str, label: str, value: str) -> None:
    """Attach or update a label on *secret_key*."""
    secrets = load_secrets(vault_dir, password)
    if secret_key not in secrets:
        raise KeyError(f"Secret '{secret_key}' does not exist.")
    meta_key = _label_key(secret_key)
    raw = secrets.get(meta_key, "")
    labels = _parse_labels(raw)
    labels[label] = value
    secrets[meta_key] = _serialize_labels(labels)
    save_secrets(vault_dir, password, secrets)


def remove_label(vault_dir: str, password: str, secret_key: str, label: str) -> bool:
    """Remove a single label from *secret_key*. Returns True if it existed."""
    secrets = load_secrets(vault_dir, password)
    meta_key = _label_key(secret_key)
    labels = _parse_labels(secrets.get(meta_key, ""))
    if label not in labels:
        return False
    del labels[label]
    secrets[meta_key] = _serialize_labels(labels)
    save_secrets(vault_dir, password, secrets)
    return True


def get_labels(vault_dir: str, password: str, secret_key: str) -> Dict[str, str]:
    """Return all labels attached to *secret_key*."""
    secrets = load_secrets(vault_dir, password)
    return _parse_labels(secrets.get(_label_key(secret_key), ""))


def filter_by_label(vault_dir: str, password: str, label: str, value: Optional[str] = None) -> List[str]:
    """Return secret keys that have *label* (optionally matching *value*)."""
    secrets = load_secrets(vault_dir, password)
    results: List[str] = []
    for k, v in secrets.items():
        if not k.startswith(_LABEL_PREFIX):
            continue
        secret_key = k[len(_LABEL_PREFIX):]
        labels = _parse_labels(v)
        if label in labels:
            if value is None or labels[label] == value:
                results.append(secret_key)
    return sorted(results)


# ── internal helpers ──────────────────────────────────────────────────────────

def _parse_labels(raw: str) -> Dict[str, str]:
    """Parse 'key=value,key2=value2' into a dict."""
    if not raw:
        return {}
    result: Dict[str, str] = {}
    for pair in raw.split(","):
        if "=" in pair:
            k, _, v = pair.partition("=")
            result[k.strip()] = v.strip()
    return result


def _serialize_labels(labels: Dict[str, str]) -> str:
    return ",".join(f"{k}={v}" for k, v in sorted(labels.items()))
