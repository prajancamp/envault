"""Secret templates: define required keys with optional defaults and descriptions."""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any


def _template_dir(project_dir: Path) -> Path:
    return project_dir / ".envault" / "templates"


def _template_path(project_dir: Path, name: str) -> Path:
    return _template_dir(project_dir) / f"{name}.json"


def save_template(
    project_dir: Path,
    name: str,
    fields: dict[str, dict[str, Any]],
) -> None:
    """Persist a template.  *fields* maps key -> {description, default, required}."""
    _template_dir(project_dir).mkdir(parents=True, exist_ok=True)
    path = _template_path(project_dir, name)
    path.write_text(json.dumps(fields, indent=2), encoding="utf-8")


def load_template(project_dir: Path, name: str) -> dict[str, dict[str, Any]]:
    """Load a template by name.  Raises FileNotFoundError if absent."""
    path = _template_path(project_dir, name)
    if not path.exists():
        raise FileNotFoundError(f"Template '{name}' not found.")
    return json.loads(path.read_text(encoding="utf-8"))


def list_templates(project_dir: Path) -> list[str]:
    """Return sorted list of template names."""
    tdir = _template_dir(project_dir)
    if not tdir.exists():
        return []
    return sorted(p.stem for p in tdir.glob("*.json"))


def delete_template(project_dir: Path, name: str) -> None:
    """Remove a template.  Raises FileNotFoundError if absent."""
    path = _template_path(project_dir, name)
    if not path.exists():
        raise FileNotFoundError(f"Template '{name}' not found.")
    path.unlink()


def validate_against_template(
    project_dir: Path,
    name: str,
    secrets: dict[str, str],
) -> dict[str, list[str]]:
    """Check *secrets* against the template.

    Returns a dict with keys:
      'missing'  – required keys absent from secrets
      'extra'    – keys in secrets not declared in the template
    """
    fields = load_template(project_dir, name)
    missing = [
        key
        for key, meta in fields.items()
        if meta.get("required", True) and key not in secrets
    ]
    declared = set(fields.keys())
    extra = [k for k in secrets if k not in declared]
    return {"missing": missing, "extra": extra}
