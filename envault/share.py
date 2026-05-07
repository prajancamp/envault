"""Secure secret sharing between projects via encrypted export bundles."""

from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Dict, List, Optional

from envault.crypto import encrypt, decrypt
from envault.store import load_secrets, save_secrets


def _bundle_path(path: str) -> Path:
    return Path(path)


def export_bundle(
    project_dir: str,
    password: str,
    keys: Optional[List[str]],
    bundle_password: str,
    output_path: str,
) -> int:
    """Export selected (or all) secrets as an encrypted bundle file.

    Returns the number of secrets exported.
    """
    secrets = load_secrets(project_dir, password)
    if keys:
        missing = [k for k in keys if k not in secrets]
        if missing:
            raise KeyError(f"Keys not found in vault: {missing}")
        subset = {k: secrets[k] for k in keys}
    else:
        subset = dict(secrets)

    payload = json.dumps(subset)
    token = encrypt(payload, bundle_password)

    dest = _bundle_path(output_path)
    dest.parent.mkdir(parents=True, exist_ok=True)
    dest.write_text(token, encoding="utf-8")
    return len(subset)


def import_bundle(
    project_dir: str,
    password: str,
    bundle_password: str,
    bundle_path: str,
    overwrite: bool = False,
) -> Dict[str, int]:
    """Import secrets from an encrypted bundle into the current vault.

    Returns a dict with 'imported' and 'skipped' counts.
    """
    token = _bundle_path(bundle_path).read_text(encoding="utf-8")
    payload = decrypt(token, bundle_password)
    incoming: Dict[str, str] = json.loads(payload)

    secrets = load_secrets(project_dir, password)
    imported = 0
    skipped = 0
    for k, v in incoming.items():
        if k in secrets and not overwrite:
            skipped += 1
        else:
            secrets[k] = v
            imported += 1

    save_secrets(project_dir, password, secrets)
    return {"imported": imported, "skipped": skipped}
