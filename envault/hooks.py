"""Per-project lifecycle hooks — run shell commands on vault events."""
from __future__ import annotations

import json
import subprocess
from pathlib import Path
from typing import Dict, List, Optional

_HOOKS_FILENAME = ".envault_hooks.json"

# Supported events
EVENTS = ["pre_set", "post_set", "pre_get", "post_get", "pre_delete", "post_delete"]


def _hooks_path(project_dir: Path) -> Path:
    return project_dir / _HOOKS_FILENAME


def _load_hooks(project_dir: Path) -> Dict[str, List[str]]:
    path = _hooks_path(project_dir)
    if not path.exists():
        return {}
    try:
        data = json.loads(path.read_text())
        return {k: v for k, v in data.items() if k in EVENTS}
    except (json.JSONDecodeError, ValueError):
        return {}


def _save_hooks(project_dir: Path, hooks: Dict[str, List[str]]) -> None:
    _hooks_path(project_dir).write_text(json.dumps(hooks, indent=2))


def set_hook(project_dir: Path, event: str, command: str) -> None:
    """Register *command* to run on *event*. Appends if a hook already exists."""
    if event not in EVENTS:
        raise ValueError(f"Unknown event '{event}'. Valid events: {EVENTS}")
    hooks = _load_hooks(project_dir)
    hooks.setdefault(event, [])
    if command not in hooks[event]:
        hooks[event].append(command)
    _save_hooks(project_dir, hooks)


def remove_hook(project_dir: Path, event: str, command: Optional[str] = None) -> None:
    """Remove *command* from *event*, or clear all commands for *event* if None."""
    if event not in EVENTS:
        raise ValueError(f"Unknown event '{event}'. Valid events: {EVENTS}")
    hooks = _load_hooks(project_dir)
    if command is None:
        hooks.pop(event, None)
    else:
        hooks[event] = [c for c in hooks.get(event, []) if c != command]
        if not hooks[event]:
            hooks.pop(event)
    _save_hooks(project_dir, hooks)


def list_hooks(project_dir: Path) -> Dict[str, List[str]]:
    """Return all registered hooks keyed by event name."""
    return _load_hooks(project_dir)


def fire(project_dir: Path, event: str, env: Optional[Dict[str, str]] = None) -> List[int]:
    """Run all commands registered for *event*. Returns list of exit codes."""
    if event not in EVENTS:
        raise ValueError(f"Unknown event '{event}'. Valid events: {EVENTS}")
    hooks = _load_hooks(project_dir)
    results: List[int] = []
    for cmd in hooks.get(event, []):
        result = subprocess.run(cmd, shell=True, cwd=project_dir, env=env)  # noqa: S602
        results.append(result.returncode)
    return results
