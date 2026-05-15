"""
Read focused-window state written by the Trackora GNOME Shell extension.

The Shell extension is the only component that talks to Mutter; Python only
consumes ``~/.local/share/trackora/current_window.json`` (or ``$XDG_DATA_HOME``).
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from trackora.models.window_state import WindowState
from trackora.utils.paths import default_state_path


@dataclass(frozen=True)
class WindowStateReadResult:
    """Result of reading the extension-written window-state JSON."""

    state: WindowState | None
    error: str | None = None


def load_window_state(path: Path | None = None) -> WindowState | None:
    """
    Load and validate window state from disk.

    Returns ``None`` when the file is missing, unreadable, not valid JSON, or
    does not contain the expected string fields. Never raises to callers.
    """
    return read_window_state(path).state


def read_window_state(path: Path | None = None) -> WindowStateReadResult:
    """Load window state and preserve the reason when the read is invalid."""
    p = path or default_state_path()
    try:
        raw = p.read_text(encoding="utf-8")
    except OSError:
        return WindowStateReadResult(
            state=None,
            error=f"Window state file not available: {p}",
        )

    try:
        data: Any = json.loads(raw)
    except json.JSONDecodeError:
        return WindowStateReadResult(
            state=None,
            error=f"Window state file is not valid JSON: {p}",
        )

    if not isinstance(data, dict):
        return WindowStateReadResult(
            state=None,
            error="Window state JSON must be an object",
        )

    app = data.get("app")
    title = data.get("title")
    ts = data.get("timestamp")
    if not isinstance(app, str) or not isinstance(title, str):
        return WindowStateReadResult(
            state=None,
            error="Window state JSON must contain string app and title fields",
        )
    if not isinstance(ts, str):
        ts = ""

    return WindowStateReadResult(
        state=WindowState(app=app, title=title, timestamp=ts),
        error=None,
    )
