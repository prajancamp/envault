"""Search and filter secrets within a vault."""

from __future__ import annotations

import fnmatch
import re
from typing import Dict, List, Optional, Tuple

from envault.store import load_secrets


def search_keys(
    project_dir: str,
    password: str,
    pattern: str,
    *,
    use_regex: bool = False,
) -> List[str]:
    """Return secret keys matching *pattern*.

    By default *pattern* is treated as a Unix shell-style wildcard
    (``fnmatch``).  Pass ``use_regex=True`` to treat it as a regular
    expression instead.
    """
    secrets = load_secrets(project_dir, password)
    keys = list(secrets.keys())

    if use_regex:
        compiled = re.compile(pattern)
        return [k for k in keys if compiled.search(k)]

    return fnmatch.filter(keys, pattern)


def search_values(
    project_dir: str,
    password: str,
    substring: str,
    *,
    case_sensitive: bool = False,
) -> List[Tuple[str, str]]:
    """Return ``(key, value)`` pairs whose *value* contains *substring*.

    The search is case-insensitive by default.
    """
    secrets = load_secrets(project_dir, password)

    needle = substring if case_sensitive else substring.lower()

    results: List[Tuple[str, str]] = []
    for key, value in secrets.items():
        haystack = value if case_sensitive else value.lower()
        if needle in haystack:
            results.append((key, value))

    return results


def grep(
    project_dir: str,
    password: str,
    pattern: str,
    *,
    search_keys_flag: bool = True,
    search_values_flag: bool = True,
    use_regex: bool = False,
) -> Dict[str, str]:
    """Broad search across keys and/or values; returns matching ``{key: value}`` dict."""
    secrets = load_secrets(project_dir, password)
    matched: Dict[str, str] = {}

    check = (lambda s: bool(re.search(pattern, s))) if use_regex else (
        lambda s: fnmatch.fnmatch(s, pattern)
    )

    for key, value in secrets.items():
        if (search_keys_flag and check(key)) or (search_values_flag and check(value)):
            matched[key] = value

    return matched
