"""
Read focused-window state written by the Trackora GNOME Shell extension.

The Shell extension is the only component that talks to Mutter; Python only
consumes ``~/.local/share/trackora/current_window.json`` (or ``$XDG_DATA_HOME``).
"""

from __future__ import annotations

import json
import os
from dataclasses import dataclass
from pathlib import Path
from typing import Any


@dataclass(frozen=True)
class WindowState:
    """Snapshot mirrored from the JSON file."""

    app: str
    title: str
    timestamp: str


def default_state_path() -> Path:
    """``$XDG_DATA_HOME/trackora/current_window.json`` or the XDG default."""
    base = os.environ.get("XDG_DATA_HOME") or str(Path.home() / ".local" / "share")
    return Path(base).expanduser() / "trackora" / "current_window.json"


def load_window_state(path: Path | None = None) -> WindowState | None:
    """
    Load and validate window state from disk.

    Returns ``None`` when the file is missing, unreadable, not valid JSON, or
    does not contain the expected string fields. Never raises to callers.
    """
    p = path or default_state_path()
    try:
        raw = p.read_text(encoding="utf-8")
    except OSError:
        return None

    try:
        data: Any = json.loads(raw)
    except json.JSONDecodeError:
        return None

    if not isinstance(data, dict):
        return None

    app = data.get("app")
    title = data.get("title")
    ts = data.get("timestamp")
    if not isinstance(app, str) or not isinstance(title, str):
        return None
    if not isinstance(ts, str):
        ts = ""

    return WindowState(app=app, title=title, timestamp=ts)
