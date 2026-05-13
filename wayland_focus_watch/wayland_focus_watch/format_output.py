"""Format one line of output: timestamp, application name, window title."""

from __future__ import annotations

from datetime import datetime


def format_focus_line(app_name: str, window_title: str) -> str:
    """Return a single human-readable line for the current focus state."""
    ts = datetime.now().strftime("%H:%M:%S")
    app = app_name.strip() or "Unknown"
    title = window_title.strip() or ""
    return f"[{ts}] {app} - {title}"
