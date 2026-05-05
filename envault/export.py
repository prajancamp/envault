"""Export and import secrets in portable formats (dotenv, JSON)."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Dict


def export_dotenv(secrets: Dict[str, str]) -> str:
    """Serialize secrets as a .env file string.

    Values containing whitespace or special characters are quoted.
    """
    lines: list[str] = []
    for key, value in sorted(secrets.items()):
        # Quote the value if it contains spaces, quotes, or $
        if any(ch in value for ch in (' ', '"', "'", '$', '\n', '\\')):
            escaped = value.replace('\\', '\\\\').replace('"', '\\"')
            lines.append(f'{key}="{escaped}"')
        else:
            lines.append(f'{key}={value}')
    return '\n'.join(lines) + ('\n' if lines else '')


def import_dotenv(text: str) -> Dict[str, str]:
    """Parse a .env file string into a dict of secrets.

    Supports KEY=VALUE and KEY="VALUE" syntax.  Comments and blank lines
    are ignored.
    """
    secrets: Dict[str, str] = {}
    for raw_line in text.splitlines():
        line = raw_line.strip()
        if not line or line.startswith('#'):
            continue
        if '=' not in line:
            continue
        key, _, raw_value = line.partition('=')
        key = key.strip()
        raw_value = raw_value.strip()
        if len(raw_value) >= 2 and raw_value[0] == '"' and raw_value[-1] == '"':
            raw_value = raw_value[1:-1].replace('\\"', '"').replace('\\\\', '\\')
        secrets[key] = raw_value
    return secrets


def export_json(secrets: Dict[str, str]) -> str:
    """Serialize secrets as a pretty-printed JSON string."""
    return json.dumps(secrets, indent=2, sort_keys=True) + '\n'


def import_json(text: str) -> Dict[str, str]:
    """Parse a JSON string into a dict of secrets.

    Raises ValueError if the JSON is not a flat string→string mapping.
    """
    data = json.loads(text)
    if not isinstance(data, dict):
        raise ValueError('Expected a JSON object at the top level.')
    for k, v in data.items():
        if not isinstance(k, str) or not isinstance(v, str):
            raise ValueError(f'All keys and values must be strings; got {k!r}: {v!r}')
    return data


def write_file(path: Path, content: str) -> None:
    """Write *content* to *path*, creating parent directories as needed."""
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding='utf-8')


def read_file(path: Path) -> str:
    """Read and return the text content of *path*."""
    return path.read_text(encoding='utf-8')
